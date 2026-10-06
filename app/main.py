# app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from pathlib import Path
import shutil
from app.ingest import ingest_folder
from app.rag import ask, load_summaries

app = FastAPI(title="Legal RAG Agent")
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)
ALLOWED_EXTS = {".pdf", ".docx", ".txt", ".md"}

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: list
    used_web: bool = False
    web_sources: list = []

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    dest = DATA_DIR / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": f"Uploaded {file.filename}"}

@app.post("/ingest")
def ingest():
    store = ingest_folder(str(DATA_DIR))
    if store is None:
        raise HTTPException(status_code=400, detail="No supported documents found")
    return {"message": "Ingestion complete"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    r = ask(req.question)
    return ChatResponse(
        answer=r["answer"],
        sources=r["sources"],
        used_web=r.get("used_web", False),
        web_sources=r.get("web_sources", []),
    )

@app.get("/document/{filename}")
def get_document(filename: str):
    from app.rag import get_vector_store
    vs = get_vector_store()
    try:
        data = vs.get()
        metas = data.get("metadatas", []) or []
        docs = data.get("documents", []) or []
        matched = []
        for meta, text in zip(metas, docs):
            src = (meta or {}).get("source", "") or ""
            if src.replace("\\", "/").lower().endswith(filename.lower()):
                matched.append((meta, text))
        if not matched:
            raise HTTPException(status_code=404, detail="Document not found")
        full = "\n\n".join(t for _, t in matched)
        return {"filename": filename, "text": full, "chunks": len(matched)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summaries")
def summaries():
    return load_summaries()
