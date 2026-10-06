# Known Issues & Fixes

## After Codespace restart
Run: `bash start.sh`
This handles everything: Ollama, models, index, backend, Streamlit.

## "Backend error: Internal Server Error"
Cause: Ollama died. Codespaces kills it under memory pressure.
Fix: `pgrep -f "ollama serve" || nohup ollama serve > /tmp/ollama.log 2>&1 &`

## "Loaded documents (0)" even though PDFs exist
Cause: summaries.json missing or empty.
Fix: `rm -f summaries.json && python -m app.ingest data`

## "Connection refused" in backend.log
Cause: Same as above — Ollama down.
Fix: Restart Ollama, then restart backend.

## Port 8501 not accessible from browser
Cause: Codespace port visibility not set.
Fix: Open Codespaces in browser → PORTS tab → right-click 8501 → Public.

## SSH session closed unexpectedly
Cause: Codespaces idle timeout (30 min).
Fix: Reconnect: `gh codespace ssh --codespace animated-giggle-qvp6r6v59r7jh997w`

## Add to requirements.txt
Always run: `echo "package-name" >> requirements.txt` after installing
anything with pip, so the next build has it.
