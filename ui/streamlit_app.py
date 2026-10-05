# ui/streamlit_app.py
# Streamlit chat UI for the Legal RAG agent.

import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Legal Document Assistant", page_icon="??")
st.title("?? Legal Document Assistant")
st.caption("Ask questions about your legal documents. Answers include citations.")

with st.sidebar:
    st.header("Upload Documents")
    uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded is not None:
        files = {"file": (uploaded.name, uploaded.getvalue(), "application/pdf")}
        r = requests.post(f"{API_URL}/upload", files=files)
        if r.status_code == 200:
            st.success(f"Uploaded {uploaded.name}")
            with st.spinner("Ingesting documents..."):
                r2 = requests.post(f"{API_URL}/ingest")
                if r2.status_code == 200:
                    st.success("Ingestion complete")
                else:
                    st.error(f"Ingestion failed: {r2.text}")
        else:
            st.error(f"Upload failed: {r.text}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                for s in msg["sources"]:
                    st.write(f"- {s['source']} (page {s['page']})")

if question := st.chat_input("Ask a question about your documents..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            r = requests.post(f"{API_URL}/chat", json={"question": question})
            if r.status_code == 200:
                data = r.json()
                st.markdown(data["answer"])
                if data.get("sources"):
                    with st.expander("Sources"):
                        for s in data["sources"]:
                            st.write(f"- {s['source']} (page {s['page']})")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data["answer"],
                    "sources": data.get("sources", []),
                })
            else:
                st.error(f"Error: {r.text}")
