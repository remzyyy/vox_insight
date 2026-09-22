"""Build the knowledge base from sample sources (Q2 entrypoint).

Pipeline: parse -> clean (strip boilerplate, standardize, redact PII, flag
errors) -> dedupe -> chunk -> embed -> store. Run with:

    python -m q2_knowledge_base.build_kb
"""
from __future__ import annotations

from shared.config import settings
from shared.logging_utils import get_logger
from .chunking import chunk_record
from .cleaning import clean_text, dedupe_records, html_to_text
from .embeddings import Embedder
from .schema import KBRecord
from .seed_sources import RAW_SOURCES
from .store import KBStore

log = get_logger("q2.build")


def build() -> None:
    records: list[KBRecord] = []
    skipped = 0
    idx = 1
    for source_ref, category, subcat, title, raw in RAW_SOURCES:
        text = html_to_text(raw) if "<" in raw else raw
        cleaned = clean_text(text, redact_pii=True)
        if not cleaned.text:
            log.warning("SKIP %s: %s", source_ref, cleaned.warnings)
            skipped += 1
            continue
        if "suspected_source_error" in cleaned.warnings:
            log.warning("FLAG source error, skipping %s", source_ref)
            skipped += 1
            continue
        if cleaned.had_pii:
            log.warning("PII flagged & redacted in %s: %s", source_ref, cleaned.pii_types)

        rec = KBRecord(
            record_id=f"kb_{category}_{idx:03d}",
            title=title,
            content=cleaned.text,
            category=category,
            subcategory=subcat,
            source=source_ref,
            version="1.0",
            pii=cleaned.had_pii,
            tags=[category, subcat],
            updated="2026-01-01",
        )
        records.append(rec)
        idx += 1

    before = len(records)
    records = dedupe_records(records)
    log.info("Records: %d kept, %d duplicates removed, %d skipped",
             len(records), before - len(records), skipped)

    # Chunk
    chunks = []
    for rec in records:
        chunks.extend(chunk_record(rec))
    log.info("Produced %d chunks from %d records", len(chunks), len(records))

    # Embed + store. Fit the offline TF-IDF model on the corpus first
    # (title + content so query terms like the record title also match).
    embedder = Embedder(load_tfidf=False)
    corpus = [f"{c.title}. {c.content}" for c in chunks]
    embedder.fit(corpus)
    embeddings = embedder.embed(corpus)
    store = KBStore(settings.kb_store_path)
    store.clear()
    store.add_chunks(chunks, embeddings, embedder.model)
    log.info("KB built at %s with %d chunks (embed_model=%s)",
             settings.kb_store_path, store.count(), embedder.model)
    store.close()


if __name__ == "__main__":
    build()
