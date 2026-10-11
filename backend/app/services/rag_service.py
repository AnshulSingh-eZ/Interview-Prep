"""
workflow :-
1. Split resume, jd, and company profile into chunks.
2. Embed each chunk (Gemini embeddings).
3. Store chunks in Postgres.
4. Retrieve the closest chunks for a query and pass that text to Gemini.
"""
import hashlib
import logging
import math
import re
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk

logger = logging.getLogger(__name__)

from app.config.gemini_config import gemini_embed

HASH_DIM = 256
CHUNK_SIZE = 700
CHUNK_OVERLAP = 120


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return []
    if len(cleaned) <= size:
        return [cleaned]
    chunks: List[str] = []
    start = 0
    while start < len(cleaned) and len(chunks) < 40:
        chunks.append(cleaned[start : start + size])
        start += max(size - overlap, 1)
    return chunks


def _hash_embed(text: str) -> List[float]:
    vec = [0.0] * HASH_DIM
    for token in re.findall(r"[a-z0-9]+", (text or "").lower()):
        bucket = int(hashlib.md5(token.encode()).hexdigest(), 16) % HASH_DIM
        vec[bucket] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _gemini_embed(texts: List[str], task_type: str) -> Optional[List[List[float]]]:
    return gemini_embed(texts, task_type)


def embed_texts(texts: List[str], *, task_type: str, prefer: str = "auto") -> tuple[List[List[float]], str]:
    if prefer != "hash":
        vectors = _gemini_embed(texts, task_type)
        if vectors and len(vectors) == len(texts):
            return vectors, "gemini"
    return [_hash_embed(text) for text in texts], "hash"


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return -1.0
    return sum(x * y for x, y in zip(a, b))


def index_source(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    source: str,
    text: str,
) -> int:
    chunks = chunk_text(text)
    if not chunks:
        return 0
    vectors, model_name = embed_texts(chunks, task_type="retrieval_document")
    for content, vector in zip(chunks, vectors):
        db.add(
            KnowledgeChunk(
                user_id=user_id,
                session_id=session_id,
                source=source,
                content=content,
                embedding=vector,
                embed_model=model_name,
            )
        )
    return len(chunks)


def retrieve(
    db: Session,
    *,
    session_id: uuid.UUID,
    query: str,
    k: int = 5,
) -> str:
    rows = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.session_id == session_id)
        .all()
    )
    if not rows or not query.strip():
        return ""
    prefer = "hash" if any(row.embed_model == "hash" for row in rows) else "auto"
    query_vectors, _ = embed_texts([query], task_type="retrieval_query", prefer=prefer)
    query_vector = query_vectors[0]
    ranked = sorted(rows, key=lambda row: _cosine(query_vector, row.embedding or []), reverse=True)
    parts = []
    for row in ranked[:k]:
        parts.append(f"[{row.source}] {row.content}")
    return "\n\n".join(parts)[:4500]
