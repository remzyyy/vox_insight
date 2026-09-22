"""Retrieval + ranking + citation (Q2).

Hybrid ranking: dense cosine similarity (embeddings) blended with a lexical
keyword-overlap boost. This makes retrieval robust when the offline embedder is
in use and keeps exact-term matches (e.g. "prepayment fee") ranking highly.

Returns grounded results with citations. A confidence gate lets callers (the
Q1 voice agent) detect "no good answer" and fall back safely instead of
hallucinating.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from shared.config import settings
from .embeddings import Embedder
from .store import KBStore, ScoredChunk

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Below this blended score, treat retrieval as "no confident answer".
CONFIDENCE_FLOOR = 0.18


@dataclass
class RetrievedAnswer:
    query: str
    results: list[ScoredChunk]
    confident: bool
    top_score: float

    def citations(self) -> list[str]:
        return [r.chunk.citation() for r in self.results]

    def context_block(self) -> str:
        """Formatted context for an LLM prompt, each chunk labeled with a cite tag."""
        lines = []
        for i, r in enumerate(self.results, 1):
            lines.append(f"[{i}] {r.chunk.content}\n    (source: {r.chunk.citation()})")
        return "\n\n".join(lines)


def _lexical_overlap(query: str, text: str) -> float:
    q = set(_TOKEN_RE.findall(query.lower()))
    t = set(_TOKEN_RE.findall(text.lower()))
    if not q:
        return 0.0
    return len(q & t) / len(q)


class Retriever:
    def __init__(self, store: KBStore | None = None) -> None:
        self.embedder = Embedder()
        self.store = store or KBStore(settings.kb_store_path)

    def retrieve(self, query: str, top_k: int = 4, category: str | None = None) -> RetrievedAnswer:
        qvec = self.embedder.embed_one(query)
        dense = self.store.search(qvec, top_k=max(top_k * 3, 8), category=category)

        # Blend dense score with lexical overlap, giving the title extra weight
        # (titles are curated topic labels, so a title match is a strong signal).
        blended: list[ScoredChunk] = []
        for sc in dense:
            lex_body = _lexical_overlap(query, sc.chunk.content)
            lex_title = _lexical_overlap(query, sc.chunk.title)
            score = 0.72 * sc.score + 0.14 * lex_body + 0.14 * lex_title
            blended.append(ScoredChunk(chunk=sc.chunk, score=score))
        blended.sort(key=lambda s: -s.score)
        top = blended[:top_k]

        top_score = top[0].score if top else 0.0
        return RetrievedAnswer(
            query=query,
            results=top,
            confident=top_score >= CONFIDENCE_FLOOR,
            top_score=top_score,
        )
