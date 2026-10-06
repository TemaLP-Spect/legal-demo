# app/ingest.py
from pathlib import Path
import sys
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_chroma import Chroma
from app.rag import summarize_text, load_summaries, save_summaries

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "legal_documents"

SUPPORTED = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
    ".md": TextLoader,
}

def load_documents(folder_path):
    documents = []
    summaries = load_summaries()
    for file in Path(folder_path).iterdir():
        ext = file.suffix.lower()
        if ext not in SUPPORTED:
            continue
        print(f"Loading: {file.name}")
        try:
            docs = SUPPORTED[ext](str(file)).load()
            documents.extend(docs)
            if file.name not in summaries:
                print(f"  Generating summary for {file.name}...")
                full_text = "\n".join(d.page_content for d in docs)
                try:
                    summaries[file.name] = summarize_text(full_text)
                    print("  Summary done.")
                except Exception as e:
                    print(f"  Summary failed: {e}")
        except Exception as e:
            print(f"  Skipped {file.name}: {e}")
    save_summaries(summaries)
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
    print(f"Ingesting from: {folder_path}")
    docs = load_documents(folder_path)
    if not docs:
        print("No supported documents found.")
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
