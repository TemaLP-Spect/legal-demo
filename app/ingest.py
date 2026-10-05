# app/ingest.py
from pathlib import Path
import sys
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_chroma import Chroma

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "legal_documents"

def load_pdfs(folder_path):
    documents = []
    for pdf_file in Path(folder_path).glob("*.pdf"):
        print(f"Loading: {pdf_file.name}")
        documents.extend(PyPDFLoader(str(pdf_file)).load())
    return documents

def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_documents(documents)

def store_chunks(chunks):
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
    )

def ingest_folder(folder_path):
    print(f"Ingesting PDFs from: {folder_path}")
    docs = load_pdfs(folder_path)
    if not docs:
        print("No documents found.")
        return None
    print(f"Loaded {len(docs)} pages")
    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks")
    vs = store_chunks(chunks)
    print(f"Stored in ChromaDB at {CHROMA_DIR}")
    return vs

if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "./data"
    ingest_folder(folder)
    print("Ingestion complete.")
