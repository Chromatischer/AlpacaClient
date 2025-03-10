from math import ceil
from typing import Any

import chromadb
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

    def __init__(self, model: str, db_path: str | None = None, embedding_length: int = 512):
        self.model = model
        self.embedding_length = embedding_length
        self.client = Client()
        self.db_client = chromadb.Client()
        Logger.log("Connected to the ollama API", priority=Priority.NORMAL)
        Logger.log("Loading model", priority=Priority.NORMAL)
        try:
            self.collection = self.db_client.get_collection("embeddings")
        except Exception as e:
            print("Error:", e)
            Logger.log("Failed to load embeddings", priority=Priority.NORMAL)
            self.collection = self.db_client.create_collection("embeddings")
            Logger.log("Created new collection!", priority=Priority.HIGH)

        if db_path is not None:
            Logger.log("Loading embeddings from file", priority=Priority.NORMAL)
            self.collection.from_json(load_json(db_path))


        if not any((model in m["model"]) for m in self.client.list().models):
            for m in self.client.list().models:
                print(m["model"], model, model in m["model"])
            raise ValueError(f"Model {model} not found in the ollama API")

        Logger.log("Embedder loaded", priority=Priority.NORMAL)

    def embed(self, text: str) -> EmbedResponse:
        """
        Embed a text using the model
        :param text: The text to embed
        :return: The embedding response
        """
        return self.client.embed(self.model, text)["embeddings"]

    def embed_file(self, file_path: str):
        """
        Embed a file using the model and store the embedding in the database
        :param file_path: The file path to embed
        """
        with open(file_path, "rb") as file:
            Logger.log(f"Embedding content of file: {file_path}", priority=Priority.NORMAL)
            content = file.read().decode("utf-8")
            self._embed_long(content, file_path, token_count=self.embedding_length)

    def _embed_long(self, content: str, file_path: str, token_count: int = 512):
        """
        Embed a long content by splitting it into chunks and embedding each chunk
        Saves the embeddings in the database
        :param content: The content to embed
        :param file_path: The path to the file containing the content to add to the metadata
        :param token_count: The number of tokens to embed with each chunk
        """
        chunks: list[str] = []

        current_position = 0
        for i in range(ceil(len(content.split()) / 512)):  # Split the file into chunks of 512 words + 1
            chunk = " ".join(content.split()[current_position:current_position + token_count])  # Split the file into chunks of 512 words starting from the current position
            chunks.append(chunk)
            current_position += token_count  # Move the current position to the next 512 words

        for i, chunk in enumerate(chunks):  # Iterate over each 512 word chunk
            embedding = self.embed(chunk)  # Embed the chunk
            # The embedding is stored in the database with the id of the chunk and the path to the document for
            # future reference and manual lookup
            self.collection: Collection
            self.collection.add(ids=[str(i)], embeddings=embedding, documents=chunk, metadatas=[{"source": file_path}])

    def embed_pdf(self, pdf_path: str):
        """
        Using the pypdf library, extract the text from the pdf and embed it using the model
        Saves the embeddings in the database
        :param pdf_path: The path to the pdf file
        """
        # Use the pypdf library to extract the text from the pdf
        reader = PdfReader(pdf_path)
        Logger.log(f"Embedding content of pdf: {pdf_path}", priority=Priority.NORMAL)
        for page in reader.pages:
            Logger.log(f"Page: {page} / {reader.pages}", priority=Priority.NORMAL)
            self._embed_long(page.extract_text(), pdf_path, token_count=self.embedding_length)

    def save_db(self, path: str):
        #save_json(, path=path)
        print(self.collection.model_dump_json())

    def query_by_embedding(self, embedding: list[float], number_of_results: int = 1):
        return self.collection.query(query_embeddings=embedding, n_results=number_of_results)

    def query_part_by_embedding(self, embedding: list[float], number_of_results: int = 1):
        return self.query_by_embedding(embedding, number_of_results=number_of_results)["documents"][0][0]