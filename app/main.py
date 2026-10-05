# app/main.py
# FastAPI backend for the Legal RAG agent.

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from pathlib import Path
import shutil

from app.ingest import ingest_folder
from app.rag import ask

app = FastAPI(title="Legal RAG Agent")

DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: list

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    dest = DATA_DIR / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": f"Uploaded {file.filename}", "path": str(dest)}

@app.post("/ingest")
def ingest():
    store = ingest_folder(str(DATA_DIR))
    if store is None:
        raise HTTPException(status_code=400, detail="No PDFs found in data folder")
    return {"message": "Ingestion complete"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = ask(req.question)
    return ChatResponse(answer=result["answer"], sources=result["sources"])
