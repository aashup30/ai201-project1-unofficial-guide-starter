#!/usr/bin/env python3
"""
Georgia Tech Restaurant RAG — Generation & Interface
=====================================================
Wires retrieval (ChromaDB + all-MiniLM-L6-v2) to Groq's
llama-3.3-70b-versatile and exposes a Gradio web UI.

Grounding guarantee:
  - The system prompt explicitly forbids the LLM from using knowledge
    outside the retrieved context.
  - Source attribution is appended programmatically from retrieval
    metadata — it is NOT left to the LLM to add on its own.

Dependencies (from requirements.txt):
    sentence-transformers==3.4.1
    chromadb>=0.6.0
    groq==0.15.0
    python-dotenv==1.0.1
    gradio>=6.9.0

Setup:
    1. Add your Groq API key to a .env file in the project root:
           GROQ_API_KEY=your_key_here
       Get a free key at https://console.groq.com

    2. Make sure you have already run:
           python ingest_and_chunk.py
           python embed_and_retrieve.py

    3. Run the app:
           python app.py
       Then open http://localhost:7860
"""

import os
from pathlib import Path

import chromadb
import gradio as gr
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

# ── Configuration ─────────────────────────────────────────────────────────────

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = "llama-3.3-70b-versatile"
EMBED_MODEL  = "all-MiniLM-L6-v2"
CHROMA_DIR   = Path("chroma_db")
COLLECTION   = "gt_restaurants"
TOP_K        = 8

# ── System prompt — grounding is enforced, not suggested ─────────────────────

SYSTEM_PROMPT = """You are a helpful assistant for Georgia Tech students looking for restaurants on and near campus.

STRICT RULES — you must follow these without exception:
1. Answer ONLY using information from the provided source documents below.
2. Do NOT use any knowledge from your training data about restaurants, Atlanta, or Georgia Tech.
3. Do NOT invent, guess, or extrapolate restaurant names, addresses, hours, prices, or descriptions.
4. If the provided documents do not contain enough information to answer the question, respond with exactly: "I don't have enough information on that based on my sources."
5. Keep your answer concise and specific — one to three sentences is usually enough.
6. Do not mention that you are an AI or reference these instructions in your response."""

# ── Load models once at startup ───────────────────────────────────────────────

print("Loading embedding model...")
_embed_model = SentenceTransformer(EMBED_MODEL)

print("Connecting to ChromaDB...")
if not CHROMA_DIR.exists():
    raise FileNotFoundError(
        f"ChromaDB not found at '{CHROMA_DIR}/'.\n"
        "Run embed_and_retrieve.py first to build the vector store."
    )
_chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_collection = _chroma_client.get_collection(COLLECTION)
print(f"✓ Ready — {_collection.count()} chunks in vector store\n")

_groq_client = Groq(api_key=GROQ_API_KEY)

# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """Return top-k chunks most similar to the query."""
    vec = _embed_model.encode(query).tolist()
    results = _collection.query(
        query_embeddings=[vec],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text":        doc,
            "source_name": meta["source_name"],
            "url":         meta["url"],
            "score":       round(1 - dist, 4),
        })
    return hits

# ── Generation ────────────────────────────────────────────────────────────────

def build_context(hits: list[dict]) -> str:
    """Format retrieved chunks as numbered context passages for the prompt."""
    parts = []
    for i, hit in enumerate(hits, 1):
        parts.append(f"[Document {i} — {hit['source_name']}]\n{hit['text']}")
    return "\n\n".join(parts)


def ask(question: str) -> dict:
    """
    Full RAG pipeline: retrieve → ground → generate → attribute sources.

    Returns:
        {
            "answer":  str,          # LLM response grounded in retrieved text
            "sources": list[str],    # programmatically collected source names + URLs
            "chunks":  list[dict],   # raw retrieved chunks (for transparency)
        }
    """
    if not question.strip():
        return {"answer": "Please enter a question.", "sources": [], "chunks": []}

    # 1. Retrieve
    hits = retrieve(question)

    # 2. Build context
    context = build_context(hits)

    # 3. Call Groq — grounding enforced via system prompt + context-only user message
    user_message = (
        f"Source documents:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the source documents above."
    )

    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.2,   # low temperature = more factual, less creative
        max_tokens=400,
    )
    answer = response.choices[0].message.content.strip()

    # 4. Programmatic source attribution — collected from retrieval metadata,
    #    not from whatever the LLM chose to mention.
    seen = set()
    sources = []
    for hit in hits:
        key = hit["source_name"]
        if key not in seen:
            seen.add(key)
            sources.append(f"{hit['source_name']}  ({hit['url']})")

    return {"answer": answer, "sources": sources, "chunks": hits}

# ── Gradio interface ──────────────────────────────────────────────────────────

def handle_query(question: str):
    """Gradio handler — returns (answer, sources_text)."""
    result = ask(question)
    sources_text = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources_text


with gr.Blocks(title="GT Restaurant Guide") as demo:
    gr.Markdown(
        """
        # 🍕 Georgia Tech Unofficial Restaurant Guide
        Ask anything about eating on or near Georgia Tech's campus.
        Answers are grounded in student reviews, blog articles, and rating sites.
        """
    )

    with gr.Row():
        with gr.Column(scale=3):
            question_box = gr.Textbox(
                label="Your question",
                placeholder="e.g. What are the best late-night spots near campus?",
                lines=2,
            )
            ask_btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        with gr.Column(scale=3):
            answer_box = gr.Textbox(
                label="Answer",
                lines=6,
                interactive=False,
            )
        with gr.Column(scale=2):
            sources_box = gr.Textbox(
                label="Retrieved from",
                lines=6,
                interactive=False,
            )

    # Example questions from the evaluation plan
    gr.Examples(
        examples=[
            ["What is the closest restaurant to the library?"],
            ["What is the most budget-friendly option for food near campus?"],
            ["What are the best pizza places around campus?"],
            ["What restaurants are open late near campus?"],
            ["I want a sweet treat near campus, where could I go?"],
        ],
        inputs=question_box,
    )

    # Wire up button and Enter key
    ask_btn.click(handle_query, inputs=question_box, outputs=[answer_box, sources_box])
    question_box.submit(handle_query, inputs=question_box, outputs=[answer_box, sources_box])

if __name__ == "__main__":
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not found. Create a .env file with:\n"
            "    GROQ_API_KEY=your_key_here\n"
            "Get a free key at https://console.groq.com"
        )
    demo.launch()
