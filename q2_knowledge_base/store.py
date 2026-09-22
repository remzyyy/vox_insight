"""SQLite-backed KB store with in-memory cosine vector search.

Design choice: SQLite gives durable, traceable records (every chunk keeps its
source, version, and PII flag) with zero external services. Vectors are stored
as JSON blobs and loaded into memory for cosine ranking. For the assessment
corpus (dozens–hundreds of chunks) this is fast and fully reproducible. The
retriever interface is drop-in replaceable with FAISS/pgvector at scale.
"""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass

import numpy as np

from shared.logging_utils import get_logger
from .schema import KBChunk

log = get_logger("q2.store")


@dataclass
class ScoredChunk:
    chunk: KBChunk
    score: float


class KBStore:
    def __init__(self, path: str) -> None:
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        # check_same_thread=False so the store can serve a multi-threaded web
        # server (FastAPI/uvicorn). Reads dominate; writes happen at build time.
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id    TEXT PRIMARY KEY,
                record_id   TEXT NOT NULL,
                title       TEXT NOT NULL,
                content     TEXT NOT NULL,
                category    TEXT NOT NULL,
                subcategory TEXT NOT NULL,
                source      TEXT NOT NULL,
                version     TEXT NOT NULL,
                pii         INTEGER NOT NULL,
                seq         INTEGER NOT NULL,
                embedding   TEXT NOT NULL,
                embed_model TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_category ON chunks(category);
            """
        )
        self.conn.commit()

    def clear(self) -> None:
        self.conn.execute("DELETE FROM chunks")
        self.conn.commit()

    def add_chunks(self, chunks: list[KBChunk], embeddings: list[list[float]], model: str) -> None:
        rows = [
            (
                c.chunk_id, c.record_id, c.title, c.content, c.category, c.subcategory,
                c.source, c.version, int(c.pii), c.seq, json.dumps(emb), model,
            )
            for c, emb in zip(chunks, embeddings)
        ]
        self.conn.executemany(
            """INSERT OR REPLACE INTO chunks
               (chunk_id,record_id,title,content,category,subcategory,source,version,pii,seq,embedding,embed_model)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        self.conn.commit()
        log.info("Stored %d chunks (model=%s)", len(rows), model)

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()["n"]

    def _load_matrix(self, category: str | None = None, exclude_pii: bool = True):
        # PII-flagged chunks are stored (for traceability/audit) but excluded
        # from retrieval so they can never ground a customer-facing answer.
        clauses = []
        params: list = []
        if category:
            clauses.append("category = ?")
            params.append(category)
        if exclude_pii:
            clauses.append("pii = 0")
        q = "SELECT * FROM chunks"
        if clauses:
            q += " WHERE " + " AND ".join(clauses)
        rows = self.conn.execute(q, tuple(params)).fetchall()
        if not rows:
            return [], np.zeros((0, 0))
        vecs = np.array([json.loads(r["embedding"]) for r in rows], dtype=np.float32)
        return rows, vecs

    def search(self, query_vec: list[float], top_k: int = 4, category: str | None = None) -> list[ScoredChunk]:
        rows, mat = self._load_matrix(category)
        if len(rows) == 0:
            return []
        q = np.array(query_vec, dtype=np.float32)
        qn = np.linalg.norm(q) or 1.0
        mn = np.linalg.norm(mat, axis=1)
        mn[mn == 0] = 1.0
        sims = (mat @ q) / (mn * qn)
        order = np.argsort(-sims)[:top_k]
        results: list[ScoredChunk] = []
        for idx in order:
            r = rows[idx]
            chunk = KBChunk(
                chunk_id=r["chunk_id"], record_id=r["record_id"], title=r["title"],
                content=r["content"], category=r["category"], subcategory=r["subcategory"],
                source=r["source"], version=r["version"], pii=bool(r["pii"]), seq=r["seq"],
            )
            results.append(ScoredChunk(chunk=chunk, score=float(sims[idx])))
        return results

    def close(self) -> None:
        self.conn.close()
