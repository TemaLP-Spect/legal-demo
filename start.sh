#!/bin/bash
# start.sh — one command to boot the whole stack
cd /workspaces/legal-demo

# Activate env
source venv/bin/activate 2>/dev/null || {
  python3 -m venv venv
  source venv/bin/activate
  pip install -q -r requirements.txt fastembed
}

# Ensure fastembed
pip install -q fastembed 2>/dev/null

# Ollama up?
if ! pgrep -f "ollama serve" > /dev/null; then
  echo "→ Starting Ollama..."
  export OLLAMA_KEEP_ALIVE=-1
  nohup ollama serve > /tmp/ollama.log 2>&1 &
  sleep 6
fi

# Models present?
if ! ollama list 2>/dev/null | grep -q "qwen2.5:7b"; then
  echo "→ Pulling models (one-time)..."
  ollama pull qwen2.5:7b
  ollama pull nomic-embed-text
fi

# Index built?
if [ ! -d "chroma_db" ] || [ ! -f "summaries.json" ]; then
  echo "→ Building index..."
  rm -rf chroma_db summaries.json
  python -m app.ingest data
fi

# Kill old servers
pkill -f uvicorn 2>/dev/null
pkill -f streamlit 2>/dev/null
sleep 2

# Start backend
echo "→ Starting backend..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 3

# Start Streamlit
echo "→ Starting Streamlit..."
nohup streamlit run ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > /tmp/streamlit.log 2>&1 &
sleep 5

# Status
echo ""
echo "=== STATUS ==="
curl -s http://localhost:8000/health && echo ""
echo ""
echo "✓ Ready. Open browser to port 8501."
