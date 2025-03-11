import unittest

from Core.Embedding import Embedding
from Core.Logger import Logger


class SimpleTests(unittest.TestCase):
    embedding: Embedding

    @classmethod
    def setUpClass(cls) -> None:
        cls.embedding = Embedding("nomic-embed-text", embedding_length=100)
        print("setup complete!")

    def test_innit(self):
        embedder = Embedding("nomic-embed-text")
        print("Embedder: Created")

    def test_embedding(self):
        # embed a single sentence
        response = self.embedding.embed("Hello, how are you?")
        print(f"{str(response)[:150].strip()}...")

    def test_embedding_file(self):
        # embed a file
        self.embedding.embed_file("/Users/chromatischer/PycharmProjects/AI-Assist/Resources/SystemPrompt.md")
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
        persist_datab = Embedding("nomic-embed-text", db_path=self.path)
        emb = persist_datab.embed("Hello, how are you?")
        persist_datab.save_to_collection(text="Hello, how are you?", embedding=emb)
        Logger.log(str(len(persist_datab)))
        second = Embedding("nomic-embed-text", db_path=self.path)
        print(f"{second.query_by_embedding(second.embed('Hello, how are you?'))}")

class PdfEmbeddingTests(unittest.TestCase):


if __name__ == '__main__':
    unittest.main()
