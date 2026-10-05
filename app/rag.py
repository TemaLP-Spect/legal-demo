# app/rag.py
# RAG Query Pipeline
# Searches ChromaDB, sends context + question to Ollama, returns answer with citations.

from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

OLLAMA_URL = "http://127.0.0.1:11434"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5-coder-8k"
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "legal_documents"
TOP_K = 4

SYSTEM_PROMPT = """You are a legal document assistant. Answer the user's question using ONLY the provided context.

Rules:
- If the answer is in the context, answer clearly and cite the source.
- If the answer is NOT in the context, say exactly: "I don't have enough information to answer that. Please consult a human."
- Never make up information.
- Always include the source filename and page number when citing.

Context:
{context}
"""

def get_vector_store():
    """Connect to the existing ChromaDB collection."""
    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_URL,
    )
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

def retrieve_chunks(question, vector_store, k=TOP_K):
    """Search the vector store for the most relevant chunks."""
    return vector_store.similarity_search(question, k=k)

def build_context(chunks):
    """Format retrieved chunks into a context string with source labels."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.metadata.get("source", "unknown")
        page = chunk.metadata.get("page", "?")
        parts.append(f"[Source {i}: {source}, page {page}]\n{chunk.page_content}")
    return "\n\n".join(parts)

def ask(question):
    """Full RAG pipeline: retrieve, build prompt, ask LLM, return answer + sources."""
    vector_store = get_vector_store()
    chunks = retrieve_chunks(question, vector_store)
    if not chunks:
        return {"answer": "No relevant documents found.", "sources": []}

    context = build_context(chunks)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ])
    llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_URL, temperature=0.2)
    chain = prompt | llm
    response = chain.invoke({"context": context, "question": question})

    sources = [
        {
            "source": c.metadata.get("source", "unknown"),
            "page": c.metadata.get("page", "?"),
        }
        for c in chunks
    ]
    return {"answer": response.content, "sources": sources}

if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is this document about?"
    result = ask(question)
    print("\n--- ANSWER ---")
    print(result["answer"])
    print("\n--- SOURCES ---")
    for s in result["sources"]:
        print(f"- {s['source']} (page {s['page']})")
