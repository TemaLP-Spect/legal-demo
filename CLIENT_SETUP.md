# Client Setup Guide

## What to customize per client

1. Documents - replace everything in data/ with the client's PDFs
2. Branding - update the sidebar title in ui/streamlit_app.py
3. Language - leave the selector; the client chooses at runtime
4. Legal docs - customize Privacy Policy and Terms in ui/streamlit_app.py

## Delivery options

### Option A - Docker (recommended)

    docker build -t client-name-assistant .
    docker save client-name-assistant | gzip > client-assistant.tar.gz

Client runs:

    docker load < client-assistant.tar.gz
    docker run -p 8501:8501 -p 8000:8000 client-name-assistant

### Option B - Clean repo (ZIP)

Strip the demo folder of everything client-specific, deliver as ZIP with a setup script.

### Option C - Portable Python bundle

Package with PyInstaller or shiv for a no-Python-install delivery.

## Minimum client machine spec

- 16 GB RAM
- 4-core CPU (modern)
- 5 GB free disk
- Windows 10+, macOS 12+, or Linux

Below 16 GB, use qwen2.5:1.5b and expect slower answers.

## Support window

30 days post-delivery for bug fixes. New features quoted separately.

## What NOT to include in the delivery

- Your demo PDFs
- summaries.json from testing
- .env files
- Any client-specific data from other clients
