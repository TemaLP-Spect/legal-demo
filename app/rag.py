# app/rag.py
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

OLLAMA_URL = "http://127.0.0.1:11434"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
LLM_MODEL = "qwen2.5-coder-8k"
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "legal_documents"
TOP_K = 4

SYSTEM_PROMPT = """You are a legal document assistant. Answer using ONLY the context.

Rules:
- If the answer is in the context, answer and cite the source.
- If not, say: "I don't have enough information to answer that. Please consult a human."
- Never make up information.

Context:
{context}
"""

def get_vector_store():
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

def retrieve_chunks(question, vs, k=TOP_K):
    return vs.similarity_search(question, k=k)

def build_context(chunks):
    parts = []
    for i, c in enumerate(chunks, 1):
        src = c.metadata.get("source", "unknown")
        pg = c.metadata.get("page", "?")
        parts.append(f"[Source {i}: {src}, page {pg}]\n{c.page_content}")
    return "\n\n".join(parts)

def ask(question):
    vs = get_vector_store()
    chunks = retrieve_chunks(question, vs)
    if not chunks:
        return {"answer": "No relevant documents found.", "sources": []}
    context = build_context(chunks)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ])
    llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_URL, temperature=0.2)
    response = (prompt | llm).invoke({"context": context, "question": question})
    sources = [
        {"source": c.metadata.get("source", "unknown"), "page": c.metadata.get("page", "?")}
        for c in chunks
    ]
    return {"answer": response.content, "sources": sources}

if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is this document about?"
    r = ask(q)
    print("\n--- ANSWER ---")
    print(r["answer"])
    print("\n--- SOURCES ---")
    for s in r["sources"]:
        print(f"- {s['source']} (page {s['page']})")
