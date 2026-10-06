# Legal RAG Assistant

A private, local, document Q&A system for legal professionals.

## What it does
- Upload PDFs, DOCX, TXT, or MD files
- Ask questions in natural language
- Get answers with citations to the exact page and text
- Web fallback when documents don't contain the answer
- Multilingual: English, Afrikaans, isiZulu, isiXhosa, Sesotho, Setswana, Sepedi
- 100% local - nothing leaves the machine

## One-command start

    bash start.sh

This starts Ollama, loads models, builds the index if needed, and launches the backend + UI.

## First-time setup (fresh machine)

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt fastembed

    ollama pull qwen2.5:7b
    ollama pull nomic-embed-text

    python -m app.ingest data

    uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    streamlit run ui/streamlit_app.py --server.port 8501 --server.headless true &

Then open http://localhost:8501

## Directory layout

    legal-demo/
    app/
      ingest.py     load - chunk - embed - store
      rag.py        retrieve - LLM - answer with citations
      main.py       FastAPI backend
    ui/
      streamlit_app.py   chat interface
    data/             put source documents here
    chroma_db/        vector store (auto-generated)
    summaries.json    document summaries (auto-generated)
    start.sh          one-command boot
    KNOWN_ISSUES.md   troubleshooting
    requirements.txt

## Model options

| Model | Size | RAM needed | Use for |
|---|---|---|---|
| qwen2.5:7b | 4.7 GB | 16 GB | Production / client delivery |
| qwen2.5:1.5b | 1 GB | 4 GB | Development / weak machines |

Change in app/rag.py:

    LLM_MODEL = "qwen2.5:7b"

## Client delivery

For each client, clone this repo into a new folder, add their documents and branding, then deliver the folder or a Docker image.

See CLIENT_SETUP.md.
