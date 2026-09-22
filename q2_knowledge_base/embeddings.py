"""Embedding provider with graceful offline fallback.

Priority:
  1. OpenAI embeddings if OPENAI_API_KEY is set (best semantic quality).
  2. Corpus-fitted TF-IDF vectors otherwise (scikit-learn). These are genuinely
     good for lexical retrieval over a fixed KB and need no keys.

The TF-IDF model is *fit at build time* over the whole corpus and persisted
next to the KB store, then reused to transform queries at retrieval time so
query and document vectors share the same vocabulary/IDF space.
"""
from __future__ import annotations

import os
import pickle

from shared.config import settings
from shared.logging_utils import get_logger

log = get_logger("q2.embeddings")

_TFIDF_PATH_SUFFIX = ".tfidf.pkl"


def _tfidf_model_path() -> str:
    return settings.kb_store_path + _TFIDF_PATH_SUFFIX


class Embedder:
    """Two modes: 'openai' (per-text API) or 'tfidf' (corpus-fitted, offline)."""

    def __init__(self, *, load_tfidf: bool = True) -> None:
        self.use_openai = settings.has_openai
        self._client = None
        self._tfidf = None

        if self.use_openai:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=settings.openai_api_key)
                self.model = settings.openai_embed_model
                log.info("Using OpenAI embeddings: %s", self.model)
                return
            except Exception as e:  # pragma: no cover
                log.warning("OpenAI unavailable (%s); using TF-IDF fallback", e)
                self.use_openai = False

        self.model = "tfidf-offline"
        if load_tfidf and os.path.exists(_tfidf_model_path()):
            with open(_tfidf_model_path(), "rb") as f:
                self._tfidf = pickle.load(f)
            log.info("Loaded TF-IDF model (%d terms)", len(self._tfidf.vocabulary_))

    # ---- build-time ----
    def fit(self, corpus: list[str]) -> None:
        """Fit the offline TF-IDF vocabulary. No-op when using OpenAI."""
        if self.use_openai:
            return
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._tfidf = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )
        self._tfidf.fit(corpus)
        with open(_tfidf_model_path(), "wb") as f:
            pickle.dump(self._tfidf, f)
        log.info("Fitted TF-IDF model with %d terms", len(self._tfidf.vocabulary_))

    # ---- embedding ----
    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.use_openai and self._client is not None:
            try:
                resp = self._client.embeddings.create(model=self.model, input=texts)
                return [d.embedding for d in resp.data]
            except Exception as e:  # pragma: no cover
                log.warning("OpenAI embed failed (%s); TF-IDF fallback", e)
                self.use_openai = False
        if self._tfidf is None:
            raise RuntimeError(
                "TF-IDF model not fitted/loaded. Run build_kb first, or set OPENAI_API_KEY."
            )
        return self._tfidf.transform(texts).toarray().tolist()

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]
