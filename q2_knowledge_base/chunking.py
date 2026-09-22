"""Chunking strategy (Q2).

Strategy: sentence-aware, ~budgeted chunks with overlap. KB records here are
short and self-contained (one policy/FAQ/objection each), so most records
become a single chunk. Longer records split on sentence boundaries with a
small token budget and overlap to preserve context across boundaries.

Rationale: for a voice agent, retrieved chunks are read/paraphrased aloud, so
chunks must be self-contained and short. One-record-one-topic keeps citations
precise and avoids mixing policies.
"""
from __future__ import annotations

import re

from .schema import KBChunk, KBRecord

_SENT_RE = re.compile(r"(?<=[.!?])\s+")
TARGET_WORDS = 90
OVERLAP_WORDS = 20


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_RE.split(text) if s.strip()]


def chunk_record(record: KBRecord) -> list[KBChunk]:
    sentences = _split_sentences(record.content)
    chunks: list[str] = []
    current: list[str] = []
    count = 0
    for sent in sentences:
        w = len(sent.split())
        if count + w > TARGET_WORDS and current:
            chunks.append(" ".join(current))
            # start new chunk with overlap tail
            tail = " ".join(current).split()[-OVERLAP_WORDS:]
            current = [" ".join(tail)] if tail else []
            count = len(tail)
        current.append(sent)
        count += w
    if current:
        chunks.append(" ".join(current))
    if not chunks:
        chunks = [record.content]

    out: list[KBChunk] = []
    for i, body in enumerate(chunks):
        out.append(
            KBChunk(
                chunk_id=f"{record.record_id}#{i}",
                record_id=record.record_id,
                title=record.title,
                content=body.strip(),
                category=record.category,
                subcategory=record.subcategory,
                source=record.source,
                version=record.version,
                pii=record.pii,
                seq=i,
            )
        )
    return out
