import unittest

from Core.Embedding import Embedding
from Core.Logger import Logger
from Core.Priority import Priority

MODEL = "nomic-embed-text:latest"

class SimpleTests(unittest.TestCase):
    embedding: Embedding

    @classmethod
    def setUpClass(cls) -> None:
        cls.embedding = Embedding(MODEL, embedding_length=100)
        print("setup complete!")

    def test_innit(self):
        embedder = Embedding(MODEL)
        print("Embedder: Created")

    def test_embedding(self):
        # embed a single sentence
        response = self.embedding.embed("Hello, how are you?")
        print(f"{str(response)[:150].strip()}...")

    def test_embedding_file(self):
        # embed a file
        self.embedding.embed_file("/Resources/SystemPrompts/SystemPrompt.md")
        print("File embedded")

    def test_query(self):
        # query the database
        query = self.embedding.embed("Who are you?")
        print(f"Query: {query}")
        print(f"{self.embedding.query_by_embedding(query, number_of_results=2)}")
        print(f"{self.embedding.query_document_by_embedding(query)}")

class PersistenceTests(unittest.TestCase):
    path: str = "/Users/chromatischer/PycharmProjects/AI-Assist/Resources"
    def test_persistence(self):
        persist_datab = Embedding(MODEL, db_path=self.path)
        emb = persist_datab.embed("Hello, how are you?")
        persist_datab.save_to_collection(text="Hello, how are you?", embedding=emb)
        Logger.log(str(len(persist_datab)))
        second = Embedding(MODEL, db_path=self.path)
        print(f"{second.query_by_embedding(second.embed('Hello, how are you?'))}")

class PdfEmbeddingTests(unittest.TestCase):
    def test_embedding_pdf(self):
        embedding = Embedding(MODEL, embedding_length=50)
        embedding.embed_pdf("/Users/chromatischer/PycharmProjects/AI-Assist/Temp/Motivationsschreiben.pdf", overlap=5)
        Logger.log(str(len(embedding)), priority=Priority.NORMAL)
        query = embedding.embed("Which clubs are you in?")
        print(embedding.query_by_embedding(embedding=query, number_of_results=2))
        print(embedding.query_document_by_embedding(embedding=query, number_of_results=2))




if __name__ == '__main__':
    unittest.main()
