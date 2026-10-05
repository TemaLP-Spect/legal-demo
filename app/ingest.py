# app/ingest.py
# RAG Document Ingestion Pipeline

from pathlib import Path
import os
import sys
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma

OLLAMA_URL = "http://127.0.0.1:11434"
EMBEDDING_MODEL = "nomic-embed-text"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "legal_documents"

def load_pdfs(folder_path):
    """Read all .pdf files in folder_path. Return a list of Document objects."""
    documents = []
    folder = Path(folder_path)
    pdf_files = list(folder.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return documents
    for pdf_file in pdf_files:
        print(f"Loading: {pdf_file.name}")
        loader = PyPDFLoader(str(pdf_file))
        documents.extend(loader.load())
    return documents

def chunk_documents(documents):
    """Split documents into chunks. Return a list of chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(documents)

def store_chunks(chunks):
    """Embed chunks with Ollama and store in ChromaDB. Return the vector store."""
    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_URL,
    )
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
    )
    return vector_store

def ingest_folder(folder_path):
    """Full pipeline: load -> chunk -> embed -> store. Return vector store."""
    print(f"Ingesting PDFs from: {folder_path}")
    documents = load_pdfs(folder_path)
    if not documents:
        print("No documents to ingest.")
        return None
    print(f"Loaded {len(documents)} pages")
    chunks = chunk_documents(documents)
    print(f"Created {len(chunks)} chunks")
    vector_store = store_chunks(chunks)
    print(f"Stored chunks in ChromaDB at {CHROMA_DIR}")
    return vector_store

if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "./data"
    ingest_folder(folder)
    print("Ingestion complete.")
