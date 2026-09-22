# Production Improvement Plan

Prioritized path from this prototype to a production system.

## 1. Retrieval & knowledge base (Q2)
- Replace SQLite in-memory cosine with a vector DB (pgvector or FAISS/Qdrant)
  and keep SQLite for the source-of-truth records + versioning.
- Add a real ingestion pipeline: scheduled scraper + document parsers (PDF/DOCX),
  extraction-failure retries, and a review queue for flagged/low-quality records.
- Move to OpenAI (or a hosted open model) embeddings; add a reranker
  (cross-encoder) for the final top-k.
- Add embedding-based near-duplicate detection on top of the Jaccard pass.
- Versioning: keep record history; retrieval pins the latest active version and
  citations include the version (already modeled).

## 2. Voice agent (Q1)
- Deploy the webhook behind HTTPS with request signing (Vapi secret already
  checked) and rate limiting.
- Swap the mock CRM for a real integration (Salesforce/HubSpot) via a queue so
  the call path never blocks on CRM latency.
- Add analytics: per-call grounding rate, escalation rate, KB-miss log to drive
  KB improvements.
- Human handoff: warm transfer to a live agent, not just a queued callback.

## 3. Localization (Q3)
- Native-speaker QA loop for each market; capture real call recordings to tune
  terminology and politeness.
- Per-market ASR tuning and evaluation sets; track word-error by
  accent/register.
- Explore native regional TTS as it matures; document compromises until then.
- Compliance review with local regulators' conduct rules (insurance suitability;
  OJK collections).

## 4. Real-time nudges (Q4)
- Horizontal scale: stateless signal workers + per-call engine keyed by call_id;
  Redis/Kafka for fan-out to dashboards.
- Real streaming ASR (Deepgram live) with diarization; feed ASR word-confidence
  into signal gating for noisy audio.
- Learned signals: replace/augment lexicons with a small classifier trained on
  labeled call data; keep heuristics as a fast, explainable floor.
- Nudge quality loop: log agent accept/dismiss to tune thresholds and cooldowns;
  measure precision over time, not just on the test set.
- Observability: per-component latency dashboards with alerting on P95
  regressions.

## 5. Platform & security
- Secrets in a vault, not `.env`, in production.
- Data retention & PII handling policy; encrypt call recordings at rest.
- CI: run `retrieval_tests`, `smoke_test`, `simulate`, and
  `false_positive_report` on every commit as regression gates.
