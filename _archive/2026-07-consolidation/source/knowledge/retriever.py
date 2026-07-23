"""Best-effort ChromaDB retrieval with a no-op local fallback."""
import os

CHROMA_PERSIST_DIRECTORY = os.environ.get("CHROMA_PERSIST_DIRECTORY", "chroma_db")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "mxbai-embed-large")


class Retriever:
    def __init__(self) -> None:
        self.client = self.collection = self.embeddings = None
        try:
            import chromadb
            from langchain_community.embeddings import OllamaEmbeddings
            self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
            self.collection = self.client.get_or_create_collection(name="the_board_knowledge")
            self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        except ImportError:
            pass

    def query(self, query_text: str, n_results: int = 5) -> list[str]:
        if not self.collection or not self.embeddings:
            return []
        try:
            results = self.collection.query(query_embeddings=[self.embeddings.embed_query(query_text)], n_results=n_results)
            return results.get("documents", [[]])[0] or []
        except Exception:
            return []


knowledge_retriever = Retriever()
