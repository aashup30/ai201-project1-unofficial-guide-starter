#!/usr/bin/env python3
"""
Georgia Tech Restaurant RAG — Embedding & Retrieval
====================================================
Loads chunks from chunks/all_chunks.json (produced by ingest_and_chunk.py),
embeds them with all-MiniLM-L6-v2, stores in ChromaDB with source metadata,
and runs the 5 evaluation queries from planning.md.

Dependencies (from requirements.txt):
    sentence-transformers==3.4.1
    chromadb>=0.6.0

Usage:
    # Step 1 — ingest and chunk first (if not already done):
    python ingest_and_chunk.py

    # Step 2 — embed, store, and evaluate retrieval:
    python embed_and_retrieve.py
"""

import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

# ── Configuration ─────────────────────────────────────────────────────────────

CHUNKS_FILE = Path("chunks/all_chunks.json")
CHROMA_DIR  = Path("chroma_db")
COLLECTION  = "gt_restaurants"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K       = 5
BATCH_SIZE  = 500   # ChromaDB upsert batch size

# Evaluation questions from planning.md
# (question, expected answer, keywords to check for retrieval quality)
EVAL_QUESTIONS = [
    (
        "What is the closest restaurant to the library?",
        "Blue Donkey Coffee (Odyssey article)",
        ["blue donkey", "library", "student center", "culc"],
    ),
    (
        "What is the most budget-friendly option for food near campus?",
        "Publix subs, Blue Donkey, or Halal Guys",
        ["publix", "halal guys", "blue donkey", "budget", "cheap", "affordable"],
    ),
    (
        "What are the best pizza places around campus?",
        "Antico's, Atwood's",
        ["antico", "atwood"],
    ),
    (
        "What restaurants are open late near campus?",
        "Waffle House, Taco Bell, Lucky Buddha",
        ["waffle house", "taco bell", "lucky buddha", "late", "midnight"],
    ),
    (
        "I want a sweet treat near campus, where could I go?",
        "Jeni's Ice Cream, Sweet Hut",
        ["jeni", "sweet hut", "ice cream", "dessert", "bakery"],
    ),
]

# ── Load chunks ───────────────────────────────────────────────────────────────

def load_chunks(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Chunks file not found at '{path}'.\n"
            "Run ingest_and_chunk.py first to generate it."
        )
    chunks = json.loads(path.read_text(encoding="utf-8"))
    # Drop any empty/malformed chunks defensively
    chunks = [c for c in chunks if c.get("text", "").strip()]
    print(f"✓ Loaded {len(chunks)} chunks from {path}")
    return chunks

# ── Embed & store ─────────────────────────────────────────────────────────────

def build_vector_store(
    chunks: list[dict],
) -> tuple[chromadb.Collection, SentenceTransformer]:
    """
    Embed all chunks with all-MiniLM-L6-v2 and upsert into a persistent
    ChromaDB collection. Re-running is safe — upsert by chunk_id means no
    duplicates even if you call this multiple times.

    Metadata stored per chunk:
        source_id   — integer ID matching planning.md table
        source_name — short slug (e.g. "odyssey_best_places")
        url         — original source URL (for attribution in Milestone 5)
        char_start  — approximate start offset in the cleaned document
        char_end    — approximate end offset
    """
    print(f"\nLoading embedding model '{EMBED_MODEL}' (downloads once, cached after)...")
    model = SentenceTransformer(EMBED_MODEL)

    print(f"Embedding {len(chunks)} chunks...")
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)

    print(f"\nConnecting to ChromaDB at '{CHROMA_DIR}/'")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},  # cosine similarity (best for sentence-transformers)
    )

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        batch_embeddings = embeddings[i : i + BATCH_SIZE].tolist()
        collection.upsert(
            ids=[c["chunk_id"] for c in batch],
            embeddings=batch_embeddings,
            documents=[c["text"] for c in batch],
            metadatas=[
                {
                    "source_id":   int(c["source_id"]),
                    "source_name": c["source_name"],
                    "url":         c["url"],
                    "char_start":  int(c["char_start"]),
                    "char_end":    int(c["char_end"]),
                }
                for c in batch
            ],
        )
        print(f"  Stored chunks {i + 1}–{min(i + BATCH_SIZE, len(chunks))}")

    total = collection.count()
    print(f"\n✓ ChromaDB collection '{COLLECTION}' now contains {total} chunks")
    return collection, model

# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve(
    query: str,
    collection: chromadb.Collection,
    model: SentenceTransformer,
    k: int = TOP_K,
) -> list[dict]:
    """
    Embed the query and return the top-k most similar chunks.

    Each result dict contains:
        text        — the chunk text
        source_name — short source slug
        url         — original URL (for citation)
        score       — cosine similarity 0–1 (higher = more relevant)
    """
    query_vec = model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[query_vec],
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
            "score":       round(1 - dist, 4),  # convert cosine distance → similarity
        })
    return hits

# ── Evaluation ────────────────────────────────────────────────────────────────

def _assess_retrieval(hits: list[dict], keywords: list[str]) -> str:
    """Auto-assess retrieval quality by checking if expected keywords appear in top chunks."""
    combined = " ".join(h["text"].lower() for h in hits)
    matched = sum(1 for kw in keywords if kw in combined)
    ratio = matched / len(keywords) if keywords else 0
    if ratio >= 0.5:
        return "Relevant"
    elif ratio > 0:
        return "Partially relevant"
    return "Off-target"


def run_evaluation(
    collection: chromadb.Collection,
    model: SentenceTransformer,
) -> None:
    """
    Run all 5 evaluation questions from planning.md and print results
    as a markdown table matching the project rubric format.
    """
    print(f"\nRunning {len(EVAL_QUESTIONS)} evaluation queries (top-k={TOP_K})...\n")

    rows = []
    for i, (question, expected, keywords) in enumerate(EVAL_QUESTIONS, 1):
        hits = retrieve(question, collection, model)
        # Summarize top chunk as the "system response"
        top_text = hits[0]["text"] if hits else "(no results)"
        summary = top_text[:120].strip() + ("..." if len(top_text) > 120 else "")
        retrieval_quality = _assess_retrieval(hits, keywords)
        rows.append((i, question, expected, summary, retrieval_quality))

    # Print markdown table
    print("| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |")
    print("|---|----------|-----------------|------------------------------|-------------------|-------------------|")
    for i, question, expected, summary, retrieval_quality in rows:
        # Response accuracy is left blank — no LLM generation yet (Milestone 5)
        print(f"| {i} | {question} | {expected} | {summary} | {retrieval_quality} | — |")

    print()
    print("**Retrieval quality:** Relevant / Partially relevant / Off-target")
    print("**Response accuracy:** Accurate / Partially accurate / Inaccurate")
    print("(Response accuracy will be filled in after generation is wired up in Milestone 5.)")
    print()
    print("── Detailed chunk results ──")
    for i, (question, expected, keywords) in enumerate(EVAL_QUESTIONS, 1):
        hits = retrieve(question, collection, model)
        print(f"\nQ{i}: {question}")
        for rank, hit in enumerate(hits, 1):
            snippet = hit["text"][:180] + ("..." if len(hit["text"]) > 180 else "")
            print(f"  [{rank}] score={hit['score']:.4f}  |  {hit['source_name']}")
            print(f"       {snippet}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    chunks = load_chunks(CHUNKS_FILE)
    collection, model = build_vector_store(chunks)
    run_evaluation(collection, model)


if __name__ == "__main__":
    main()