# in src/knowledge/retriever.py (Real Implementation)
import chromadb
from langchain_community.embeddings import OllamaEmbeddings
import os

CHROMA_PERSIST_DIRECTORY = os.environ.get("CHROMA_PERSIST_DIRECTORY", "chroma_db")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "mxbai-embed-large")

class Retriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
        self.collection = self.client.get_or_create_collection(name="the_board_knowledge")
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        print(f"[KNOWLEDGE] Initialized retriever with directory: {CHROMA_PERSIST_DIRECTORY}")

    def query(self, query_text: str, n_results: int = 5) -> list[str]:
        """Finds the most relevant document chunks for a given query."""
        try:
            query_embedding = self.embeddings.embed_query(query_text)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            documents = results['documents'][0] if results['documents'] else []
            print(f"[KNOWLEDGE] Query '{query_text}' returned {len(documents)} results")
            return documents
        except Exception as e:
            print(f"[KNOWLEDGE] Error during query '{query_text}': {e}")
            return []

# Singleton instance for the app
knowledge_retriever = Retriever()
