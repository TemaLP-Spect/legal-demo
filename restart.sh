#!/bin/bash
cd /workspaces/legal-demo
source venv/bin/activate

# Ollama
pgrep -f "ollama serve" > /dev/null || {
  export OLLAMA_KEEP_ALIVE=-1
  nohup ollama serve > /tmp/ollama.log 2>&1 &
  sleep 6
}

# Kill old
pkill -f uvicorn
pkill -f streamlit
sleep 2

# Start
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 4
nohup streamlit run ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > /tmp/streamlit.log 2>&1 &
sleep 12

# Verify
curl -s http://localhost:8000/health
echo ""
curl -s -o /dev/null -w "UI: %{http_code}\n" http://localhost:8501
