from math import ceil
from typing import Any

import chromadb
from chromadb import Settings
from chromadb.types import Collection
from ollama import Client, EmbedResponse
from pypdf import PdfReader

from Core.Logger import Logger
from Core.Priority import Priority
from Utils.FileLoader import save_json, load_json


class Embedding:
    # A class to handle embedding models basing on the ollama API library
    model: str
    client: Client
    collection: Collection
    embedding_length: int
    collection_name: str

    def __init__(self, model: str, db_path: str | None = None, embedding_length: int = 512, collection_name: str = "embeddings"):
        self.model = model
        self.embedding_length = embedding_length
        self.client = Client()
        self.collection_name = collection_name
        Logger.log("Connected to the ollama API", priority=Priority.NORMAL)

        if db_path is not None:
            Logger.log(f"ChromaDB Persistent at location {db_path}", priority=Priority.NORMAL)
            self.db_client = chromadb.Client(Settings(persist_directory=db_path))
        else:
            Logger.log(f"ChromaDB In-Memory because db_path is: {db_path}", priority=Priority.NORMAL)
            self.db_client = chromadb.Client()

        success = True
        try:
            self.collection = self.db_client.get_collection(self.collection_name)
        except Exception as e:
            print("Error:", e)
            success = False
            Logger.log("Failed to load embeddings", priority=Priority.NORMAL)
            self.collection = self.db_client.create_collection(self.collection_name)
            #Logger.log("Created new collection!", priority=Priority.HIGH)

        Logger.log(f"{success and 'Loaded' or 'Created'} Collection: [{self.collection_name}]", priority=Priority.HIGH)

        if not any((model in m["model"]) for m in self.client.list().models):
            for m in self.client.list().models:
                print(m["model"], model, model in m["model"])
            raise ValueError(f"Model {model} not found in the ollama API")

        Logger.log("Embedder loaded", priority=Priority.NORMAL)

    def embed(self, text: str) -> EmbedResponse:
        """
        Embed a text using the model and return the embedding
        :param text: The text to embed
        :return: The embedding of the text
        """
        return self.client.embed(self.model, text)["embeddings"]

    def __len__(self) -> int:
        return self.collection.count()

    def save_to_collection(self,text: str, embedding: list[float], source: str = "None"):
        """
        Add an embedding to the database
        :param text: The text that had been embedded
        :param embedding: The embedding of the text
        :param source: Optional source of the text
        """
        self.collection.add(ids=[str(len(self))], embeddings=embedding, documents=[text], metadatas=[{"source": source}])

    def embed_file(self, file_path: str, overlap: int = 0):
        """
        Embed a file using the model and store the embedding in the database
        :param file_path: The file path to embed
        :param overlap: The number of tokens to overlap between chunks adds 2overlap tokens to each chunk
        """
        with open(file_path, "rb") as file:
            Logger.log(f"Embedding content of file: {file_path}", priority=Priority.NORMAL)
            content = file.read().decode("utf-8")
            self._embed_long(content, file_path, token_count=self.embedding_length, overlap=overlap)

    def _embed_long(self, content: str, source_str: str, token_count: int = 512, overlap: int = 0, auto_balance: bool = True):
        """
        Embed a long content by splitting it into chunks and embedding each chunk
        Saves the embeddings in the database
        :param content: The content to embed
        :param source_str: The path to the file containing the content to add to the metadata
        :param token_count: The number of tokens to embed with each chunk
        :param overlap: The number of tokens to overlap between chunks adds 2overlap tokens to each chunk
        """

        if auto_balance and overlap > 0:
            token_count -= 2 * overlap

        chunks: list[str] = []

        current_position = 0
        for i in range(ceil(len(content.split()) / token_count)):  # Split the file into chunks of 512 words + 1
            chunk = " ".join(content.split()[max(current_position - overlap, 0):min(current_position + token_count + overlap, len(content.split()))])  # Split the file into chunks of 512 words starting from the current position
            chunks.append(chunk)
            current_position += token_count  # Move the current position to the next 512 words

        for i, chunk in enumerate(chunks):  # Iterate over each 512 word chunk
            embedding = self.embed(chunk)  # Embed the chunk
            # The embedding is stored in the database with the id of the chunk and the path to the document for
            # future reference and manual lookup
            self.collection: Collection
            self.collection.add(ids=[str(i)], embeddings=embedding, documents=chunk, metadatas=[{"source": source_str}])

    def embed_pdf(self, pdf_path: str, overlap: int = 0):
        """
        Using the pypdf library, extract the text from the pdf and embed it using the model
        Saves the embeddings in the database
        :param overlap: The number of tokens to overlap between chunks adds 2overlap tokens to each chunk
        :param pdf_path: The path to the pdf file
        """
        # Use the pypdf library to extract the text from the pdf
        reader = PdfReader(pdf_path)
        Logger.log(f"Embedding content of pdf: {pdf_path}", priority=Priority.NORMAL)
        for page in reader.pages:
            Logger.log(f"Page: {page} / {reader.pages}", priority=Priority.NORMAL)
            self._embed_long(content=page.extract_text(), source_str=pdf_path, token_count=self.embedding_length, overlap=overlap)

    # noinspection SpellCheckingInspection
    def query_by_embedding(self, embedding: list[float], number_of_results: int = 1) -> dict:
        """
        Query the database using an embedding
        :param embedding: The embedding to query with
        :param number_of_results: The number of results to return
        :return: The results of the query {"ids": [id], "documents": [document], "uris": [uri], "data": [data], "metadatas": [metadata], "distances": [distance], "included": [included]}
        """
        return self.collection.query(query_embeddings=embedding, n_results=number_of_results)

    def query_document_by_embedding(self, embedding: list[float], number_of_results: int = 1) -> str:
        """
        Only return the document from the query
        :param embedding: The embedding to query with
        :param number_of_results: The number of results to return
        :return: String of the document that was embedded and best fits the query
        """
        return self.query_by_embedding(embedding, number_of_results=number_of_results)["documents"][0][0]

