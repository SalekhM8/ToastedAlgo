"""
Toasted RAG Pipeline — Paper Ingestion

Loads PDFs from backend/data/papers/, chunks them with metadata from
paper_metadata.json, and stores embeddings in a local ChromaDB instance
using sentence-transformers/all-MiniLM-L6-v2.

Usage:
    python -m backend.rag.ingest          # from project root
    python backend/rag/ingest.py          # direct invocation
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import chromadb
import pdfplumber
from chromadb.utils import embedding_functions


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _THIS_DIR.parent
_DATA_DIR = _BACKEND_DIR / "data"
_PAPERS_DIR = _BACKEND_DIR.parent / "assets" / "pdf"
_METADATA_PATH = _THIS_DIR / "paper_metadata.json"
_CHROMA_DB_PATH = str(_THIS_DIR / "toasted_rag_db")

# ChromaDB collection name
COLLECTION_NAME = "toasted_papers"

# Chunking parameters (word-level)
CHUNK_SIZE_WORDS = 800
CHUNK_OVERLAP_WORDS = 100


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_metadata() -> dict[str, dict[str, Any]]:
    """Load paper_metadata.json and return a dict keyed by filename."""
    with open(_METADATA_PATH, "r", encoding="utf-8") as f:
        papers = json.load(f)
    return {p["filename"]: p for p in papers}


def _extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF using pdfplumber."""
    pages_text: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
    return "\n\n".join(pages_text)


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS,
                overlap: int = CHUNK_OVERLAP_WORDS) -> list[str]:
    """
    Split *text* into chunks of approximately *chunk_size* words with
    *overlap* words of overlap between consecutive chunks.

    Returns a list of chunk strings.  Very short trailing chunks (< 50 words)
    are merged into the previous chunk.
    """
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    step = chunk_size - overlap  # how far to advance the window each time

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        start += step

    # Merge a tiny trailing chunk into the previous one
    if len(chunks) > 1:
        last_chunk_words = chunks[-1].split()
        if len(last_chunk_words) < 50:
            chunks[-2] = chunks[-2] + " " + chunks[-1]
            chunks.pop()

    return chunks


def _build_chunk_metadata(paper_meta: dict[str, Any], chunk_index: int,
                          total_chunks: int) -> dict[str, Any]:
    """
    Build a flat metadata dict for a single chunk, suitable for ChromaDB
    (which only accepts str | int | float | bool values).
    """
    return {
        "paper_id": paper_meta["paper_id"],
        "filename": paper_meta["filename"],
        "title": paper_meta["title"],
        "authors": ", ".join(paper_meta["authors"]),
        "year": paper_meta["year"],
        "conditions": "|".join(paper_meta["conditions"]),
        "topics": "|".join(paper_meta["topics"]),
        "body_regions": "|".join(paper_meta["body_regions"]),
        "content_type": paper_meta["content_type"],
        "priority": paper_meta["priority"],
        "chunk_index": chunk_index,
        "total_chunks": total_chunks,
    }


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------

def ingest_papers(
    papers_dir: Path = _PAPERS_DIR,
    chroma_db_path: str = _CHROMA_DB_PATH,
    collection_name: str = COLLECTION_NAME,
) -> None:
    """
    End-to-end ingestion pipeline:
      1. Load metadata
      2. Scan papers_dir for PDFs that appear in metadata
      3. Extract text, chunk, tag with metadata
      4. Upsert into a ChromaDB persistent collection
    """

    # ------------------------------------------------------------------
    # 1.  Load metadata
    # ------------------------------------------------------------------
    metadata_by_filename = _load_metadata()
    print(f"[ingest] Loaded metadata for {len(metadata_by_filename)} papers.")

    # ------------------------------------------------------------------
    # 2.  Discover PDFs
    # ------------------------------------------------------------------
    if not papers_dir.exists():
        print(f"[ingest] Papers directory does not exist: {papers_dir}")
        print("[ingest] Nothing to ingest. Place PDFs in backend/data/papers/ and re-run.")
        return

    pdf_files = sorted(papers_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[ingest] No PDF files found in {papers_dir}")
        print("[ingest] Nothing to ingest. Place PDFs in backend/data/papers/ and re-run.")
        return

    print(f"[ingest] Found {len(pdf_files)} PDF file(s) in {papers_dir}")

    # ------------------------------------------------------------------
    # 3.  Initialise ChromaDB
    # ------------------------------------------------------------------
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    client = chromadb.PersistentClient(path=chroma_db_path)
    # Delete existing collection to allow clean re-ingestion
    try:
        client.delete_collection(name=collection_name)
        print(f"[ingest] Cleared existing collection '{collection_name}'.")
    except (ValueError, Exception):
        pass  # collection did not exist yet

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # ------------------------------------------------------------------
    # 4.  Process each PDF
    # ------------------------------------------------------------------
    total_chunks_ingested = 0
    papers_processed = 0
    papers_skipped_no_meta = 0

    for pdf_path in pdf_files:
        filename = pdf_path.name
        paper_meta = metadata_by_filename.get(filename)

        if paper_meta is None:
            print(f"  [skip] No metadata entry for '{filename}' — skipping.")
            papers_skipped_no_meta += 1
            continue

        # Extract text
        try:
            raw_text = _extract_text_from_pdf(pdf_path)
        except Exception as exc:
            print(f"  [error] Could not extract text from '{filename}': {exc}")
            continue

        if not raw_text.strip():
            print(f"  [warn] '{filename}' produced no extractable text — skipping.")
            continue

        # Chunk
        chunks = _chunk_text(raw_text)
        if not chunks:
            print(f"  [warn] '{filename}' produced no chunks — skipping.")
            continue

        # Prepare batch lists
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for idx, chunk_text in enumerate(chunks):
            chunk_id = f"paper_{paper_meta['paper_id']}_chunk_{idx}"
            ids.append(chunk_id)
            documents.append(chunk_text)
            metadatas.append(
                _build_chunk_metadata(paper_meta, chunk_index=idx, total_chunks=len(chunks))
            )

        # Upsert into ChromaDB (batch-safe up to ~41 000 items per call)
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

        total_chunks_ingested += len(chunks)
        papers_processed += 1
        print(
            f"  [ok] {filename}  →  {len(chunks)} chunk(s)  "
            f"(paper_id={paper_meta['paper_id']})"
        )

    # ------------------------------------------------------------------
    # 5.  Summary
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print(f"[ingest] Done.  Papers processed: {papers_processed}")
    print(f"[ingest] Total chunks ingested : {total_chunks_ingested}")
    if papers_skipped_no_meta:
        print(f"[ingest] Papers skipped (no metadata): {papers_skipped_no_meta}")
    print(f"[ingest] ChromaDB persisted at : {chroma_db_path}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ingest_papers()
