"""Optional knowledge services; core planning runs without ChromaDB installed."""

try:
    from .ingest import ingest_documents, CHROMA_PERSIST_DIRECTORY, EMBEDDING_MODEL
except ImportError:
    ingest_documents = None
    CHROMA_PERSIST_DIRECTORY = "chroma_db"
    EMBEDDING_MODEL = "mxbai-embed-large"

from .retriever import knowledge_retriever, Retriever

__all__ = ["ingest_documents", "CHROMA_PERSIST_DIRECTORY", "EMBEDDING_MODEL", "knowledge_retriever", "Retriever"]
