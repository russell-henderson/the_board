# in src/knowledge/ingest.py (Real Implementation)
import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
import os

CHROMA_PERSIST_DIRECTORY = os.environ.get("CHROMA_PERSIST_DIRECTORY", "chroma_db")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "mxbai-embed-large")

def ingest_documents(file_paths: list[str]):
    """Loads, splits, embeds, and stores documents in ChromaDB."""
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
    collection = client.get_or_create_collection(name="the_board_knowledge")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    for file_path in file_paths:
        print(f"[KNOWLEDGE] Ingesting {file_path}...")
        try:
            loader = PyPDFLoader(file_path)
            docs = loader.load_and_split(text_splitter)
            
            texts_to_embed = [doc.page_content for doc in docs]
            embedded_vectors = embeddings.embed_documents(texts_to_embed)
            
            doc_ids = [f"{os.path.basename(file_path)}-{i}" for i in range(len(docs))]
            
            collection.add(
                ids=doc_ids,
                embeddings=embedded_vectors,
                documents=texts_to_embed,
                metadatas=[doc.metadata for doc in docs]
            )
            print(f"[KNOWLEDGE] Successfully ingested {len(docs)} chunks from {file_path}")
        except Exception as e:
            print(f"[KNOWLEDGE] Error ingesting {file_path}: {e}")
            continue
    
    print("[KNOWLEDGE] Ingestion complete.")

# To run this, you would call:
# ingest_documents(["./path/to/your/report.pdf"])
