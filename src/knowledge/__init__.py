"""
Knowledge management package for the_board.

This package provides document ingestion and retrieval capabilities for RAG workflows.
"""

from .ingest import ingest_documents, CHROMA_PERSIST_DIRECTORY, EMBEDDING_MODEL
from .retriever import knowledge_retriever, Retriever

__all__ = [
    "ingest_documents", 
    "CHROMA_PERSIST_DIRECTORY", 
    "EMBEDDING_MODEL",
    "knowledge_retriever",
    "Retriever"
]
