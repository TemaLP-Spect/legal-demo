# ui/streamlit_app.py
import streamlit as st
import requests
import uuid
import html
from urllib.parse import quote
import html

API_URL = "http://127.0.0.1:8000"

USER_AVATAR = "\u2696\ufe0f"
AI_AVATAR = "\U0001F4DC"
GAVEL = "\U0001F528"

st.set_page_config(page_title="Legal Assistant", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
<style>
#MainMenu, footer {visibility: hidden !important;}
[data-testid="stDeployButton"],[data-testid="stToolbarActions"],
[data-testid="stStatusWidget"],[data-testid="stDecoration"] {display: none !important;}

html, body, [class*="css"] {font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;}
.block-container {max-width: 800px; padding-top: 2.5rem; padding-bottom: 8rem;}

section[data-testid="stSidebar"] {background-color: #0d0d0f; border-right: 1px solid #1f1f23;}
.sb-title {font-size: 13px; font-weight: 600; color: #f5f5f5; padding: 0 4px 4px 4px; margin-bottom: 12px;}
.sb-heading {font-size: 11px; font-weight: 600; color: #6b6b73; text-transform: uppercase;
             letter-spacing: 0.08em; padding: 12px 4px 6px 4px;}

section[data-testid="stSidebar"] .stButton button {
    background-color: transparent; border: 1px solid transparent; color: #c8c8cc;
    text-align: left; padding: 9px 12px; border-radius: 8px; font-size: 13.5px;
    width: 100%; box-shadow: none;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background-color: #1a1a1e; color: #ffffff; border-color: #2a2a30;
}
section[data-testid="stSidebar"] .stButton button[kind="primary"] {
    background-color: #1a1a1e; color: #ffffff; border-color: #2f2f36; font-weight: 500;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background-color: #131316; border: 1px dashed #2a2a30; border-radius: 8px; padding: 12px;
}

.msg-row {display: flex; align-items: flex-start; margin: 14px 0; gap: 12px;}
.msg-row.user {justify-content: flex-end;}
.avatar {
    flex-shrink: 0; width: 36px; height: 36px; border-radius: 50%;
    background: #000000 !important; border: 1px solid #2a2a30;
    display: flex; align-items: center; justify-content: center;
    font-size: 17px; filter: grayscale(1) brightness(1.6); color: #ffffff;
}
.bubble-user {
    background: #1a1a1e; border: 1px solid #26262c; border-radius: 16px;
    padding: 12px 16px; max-width: 75%; color: #f0f0f2;
    font-size: 14.5px; line-height: 1.55;
}
.bubble-ai {max-width: 78%; color: #f0f0f2; font-size: 14.5px; line-height: 1.55;}

.welcome {text-align: center; margin-top: 26vh; color: #e8e8ea; font-size: 26px; font-weight: 400;}
.disclaimer-banner {background: #1a1a1e; border: 1px solid #2a2a30; border-radius: 8px;
                    padding: 10px 14px; font-size: 11.5px; color: #8a8a92;
                    margin-top: 1rem; text-align: center;}

.stChatInput textarea {border-radius: 16px !important; border: 1px solid #2a2a30 !important;
                       background: #131316 !important; color: #f0f0f2 !important;}
.streamlit-expanderHeader {font-size: 12px !important; color: #8a8a92 !important;}
.doc-item {font-size: 12px; color: #b8b8bd; padding: 6px 8px; border-radius: 6px; margin: 3px 0;
           background: #131316; border: 1px solid #1f1f23; word-break: break-all;}
.legal-doc {font-size: 11.5px; color: #a0a0a8; line-height: 1.6;}

.gavel-wrap {display: flex; align-items: center; gap: 12px; padding: 8px 0;}
.gavel {font-size: 20px; display: inline-block; transform-origin: 70% 80%;
        animation: gavel-strike 1.1s ease-in-out infinite; filter: grayscale(1) brightness(1.6);}
@keyframes gavel-strike {0%,40%{transform:rotate(-22deg);} 55%{transform:rotate(6deg);}
                          65%{transform:rotate(-4deg);} 75%,100%{transform:rotate(-22deg);}}
.processing-text {color: #8a8a92; font-size: 13.5px;}
.dots::after {content: ''; animation: dots 1.4s steps(4, end) infinite;}
@keyframes dots {0%{content:'';} 25%{content:'.';} 50%{content:'..';} 75%{content:'...';} 100%{content:'';}}

/* Source expander cards */
.src-label {
    font-size: 12px;
    color: #b8b8bd;
    padding: 4px 0;
}
.src-snippet {
    background: #0f0f12;
    border: 1px solid #232329;
    border-radius: 6px;
    padding: 10px 12px;
    margin: 6px 0 0 0;
    font-size: 12px;
    color: #c8c8cc;
    line-height: 1.55;
    font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
    white-space: pre-wrap;
    word-wrap: break-word;
    max-height: 320px;
    overflow-y: auto;
}
.src-header {
    font-size: 12px;
    color: #e8e8ea;
    font-weight: 600;
    margin-bottom: 6px;
}
.src-page {
    display: inline-block;
    background: #1a1a1e;
    border: 1px solid #2a2a30;
    color: #b8b8bd;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10.5px;
    margin-left: 6px;
    font-weight: 500;
}

.doc-reader {background: #0f0f12; border: 1px solid #232329; border-radius: 6px;
    padding: 12px 14px; font-size: 12px; color: #c8c8cc; line-height: 1.6;
    font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
    white-space: pre-wrap; word-wrap: break-word;
    max-height: 400px; overflow-y: auto; margin-top: 6px;}
</style>
""", unsafe_allow_html=True)

# ---------- State ----------
if "chats" not in st.session_state: st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    cid = str(uuid.uuid4())[:8]
    st.session_state.chats[cid] = {"title": "New chat", "messages": []}
    st.session_state.current_chat_id = cid
if "processed_files" not in st.session_state: st.session_state.processed_files = set()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="sb-title">Legal Assistant</div>', unsafe_allow_html=True)

    if st.button("+  New chat", use_container_width=True, key="new_chat_btn"):
        cid = str(uuid.uuid4())[:8]
        st.session_state.chats[cid] = {"title": "New chat", "messages": []}
        st.session_state.current_chat_id = cid
        st.rerun()

        st.markdown('<div class="sb-heading">Chats</div>', unsafe_allow_html=True)
    for cid in reversed(list(st.session_state.chats.keys())):
        c = st.session_state.chats[cid]
        label = c["title"][:28] if c["title"] != "New chat" else "New chat"
        is_current = cid == st.session_state.current_chat_id
        if st.button(label, key=f"chat_{cid}", use_container_width=True,
                     type="primary" if is_current else "secondary"):
            st.session_state.current_chat_id = cid
            st.rerun()

    st.markdown('<div class="sb-heading">Documents</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Upload", type=["pdf","docx","txt","md"],
        label_visibility="collapsed", accept_multiple_files=True, key="uploader")

    if uploaded_files:
        new_uploads = 0
        for uploaded in uploaded_files:
            if uploaded.name in st.session_state.processed_files: continue
            try:
                r = requests.post(f"{API_URL}/upload",
                    files={"file": (uploaded.name, uploaded.getvalue())}, timeout=3600)
                if r.status_code == 200:
                    st.session_state.processed_files.add(uploaded.name)
                    new_uploads += 1
            except Exception as e:
                st.error(f"{uploaded.name}: {e}")
        if new_uploads > 0:
            try:
                with st.spinner(f"Processing {new_uploads} file(s)..."):
                    r2 = requests.post(f"{API_URL}/ingest", timeout=3600)
                if r2.status_code == 200: st.rerun()
                else: st.error(r2.text)
            except Exception as e:
                st.error(f"Ingest failed: {e}")

    try:
        summaries = requests.get(f"{API_URL}/summaries", timeout=5).json()
        count = len(summaries) if summaries else 0
    except Exception:
        summaries = {}
        count = 0

    with st.expander(f"Loaded documents ({count})", expanded=False):
        if not summaries:
            st.caption("No documents uploaded yet.")
        else:
            st.caption("Click a document to read it.")
            for name in summaries:
                with st.expander(name, expanded=False):
                    key = f"doc_text__{name}"
                    if key not in st.session_state:
                        try:
                            r = requests.get(f"{API_URL}/document/{quote(name)}", timeout=60)
                            if r.status_code == 200:
                                st.session_state[key] = r.json().get("text", "")
                            else:
                                st.session_state[key] = f"[Could not load: {r.text[:200]}]"
                        except Exception as e:
                            st.session_state[key] = f"[Error: {e}]"
                    text = st.session_state.get(key, "")
                    if text:
                        safe = html.escape(text[:30000])
                        st.markdown(f'<div class="doc-reader">{safe}</div>', unsafe_allow_html=True)
                        if len(text) > 30000:
                            st.caption("Showing first 30,000 characters.")
                    else:
                        st.caption("Empty document.")

    st.markdown('<div class="sb-heading">Settings</div>', unsafe_allow_html=True)
    with st.expander("Settings & Legal", expanded=False):
        st.markdown("##### Privacy Policy")
        st.markdown("""<div class="legal-doc">
<b>1. Data Controller.</b> This system runs entirely on your premises. No personal information is transmitted to third parties.
<b>2. Data Processing.</b> Documents are processed locally. Embeddings stored on your device.
<b>3. POPIA Compliance.</b> Designed for practitioners subject to the Protection of Personal Information Act, 2013.
<b>4. Data Retention.</b> All data remains on your device until deleted. No remote backup. No telemetry.
<b>5. Your Rights.</b> Full control over all data.
</div>""", unsafe_allow_html=True)

        st.markdown("##### Terms of Use")
        st.markdown("""<div class="legal-doc">
<b>1. Nature of Service.</b> Assistive research tool. Does not provide legal advice.
<b>2. No Attorney-Client Relationship.</b> Use does not create an attorney-client relationship.
<b>3. Verification Required.</b> All outputs are AI-generated and must be independently verified.
<b>4. Professional Responsibility.</b> You remain solely responsible for the final work product.
<b>5. Limitation of Liability.</b> Developers assume no liability for loss arising from use.
<b>6. Acceptable Use.</b> Not for unlawful purposes or to circumvent professional obligations.
</div>""", unsafe_allow_html=True)

        st.markdown("##### AI Disclaimer")
        st.markdown("""<div class="legal-doc">
This system is an AI assistant, not a legal practitioner. Designed to help locate information within your own documents.
Does not replace professional judgment. All outputs must be verified by a qualified legal professional.
</div>""", unsafe_allow_html=True)

# ---------- Main chat ----------
chat = st.session_state.chats[st.session_state.current_chat_id]
messages = chat["messages"]

if not messages:
    st.markdown('<div class="welcome">How may I assist you today?</div>', unsafe_allow_html=True)
    st.markdown('<div class="disclaimer-banner">This system is an AI assistant, not a legal practitioner. All outputs must be independently verified.</div>', unsafe_allow_html=True)

def render_user(text):
    safe = html.escape(text)
    st.markdown(f'<div class="msg-row user"><div class="bubble-user">{safe}</div><div class="avatar">{USER_AVATAR}</div></div>', unsafe_allow_html=True)

def render_sources(sources):
    """Render each source as an expandable card showing the actual page text."""
    if not sources:
        return
    st.markdown(f'<div style="font-size:11.5px;color:#8a8a92;margin:10px 0 4px 0;">Sources ({len(sources)})</div>', unsafe_allow_html=True)
    for i, s in enumerate(sources, 1):
        fname = s.get("filename") or s.get("source", "unknown").split("/")[-1].split("\\")[-1]
        page = s.get("page", "?")
        snippet = s.get("snippet", "")
        label = f"Source {i}  |  {fname}  |  page {page}"
        with st.expander(label, expanded=False):
            if snippet:
                safe_snippet = html.escape(snippet)
                st.markdown(f'<div class="src-snippet">{safe_snippet}</div>', unsafe_allow_html=True)
            else:
                st.caption("No excerpt available for this source.")

def render_ai(text, sources=None, used_web=False, web_sources=None):
    st.markdown(f'<div class="msg-row"><div class="avatar">{AI_AVATAR}</div><div class="bubble-ai">{text}</div></div>', unsafe_allow_html=True)
    if used_web:
        st.caption("WEB")
    elif sources:
        render_sources(sources)
    if web_sources:
        with st.expander("Web sources"):
            for w in web_sources:
                st.markdown(f"- [{w['title']}]({w['url']})")

for msg in messages:
    if msg["role"] == "user":
        render_user(msg["content"])
    else:
        render_ai(msg["content"], msg.get("sources"), msg.get("used_web"), msg.get("web_sources"))

# ---------- Input ----------
if question := st.chat_input("Ask a question about your legal documents..."):
    if chat["title"] == "New chat": chat["title"] = question[:40]
    messages.append({"role": "user", "content": question})
    render_user(question)

    ph = st.empty()
    ph.markdown(f'<div class="msg-row"><div class="avatar">{AI_AVATAR}</div><div class="gavel-wrap"><span class="gavel">{GAVEL}</span><span class="processing-text dots">Reviewing your documents</span></div></div>', unsafe_allow_html=True)

    try:
        r = requests.post(f"{API_URL}/chat",
                          json={"question": question, "language": "English"},
                          timeout=3600)
        ph.empty()
        if r.status_code == 200:
            data = r.json()
            render_ai(data["answer"], data.get("sources"), data.get("used_web"), data.get("web_sources"))
            messages.append({"role": "assistant", "content": data["answer"],
                "sources": data.get("sources", []), "web_sources": data.get("web_sources", []),
                "used_web": data.get("used_web", False)})
        else:
            st.error(f"Backend error: {r.text}")
    except requests.exceptions.ConnectionError:
        ph.empty()
        st.error("Backend is not running. Start it in another window: uvicorn app.main:app --host 127.0.0.1 --port 8000")
    except Exception as e:
        ph.empty()
        st.error(f"Error: {e}")
