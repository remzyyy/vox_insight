# Known Limitations

Honest account of what is and isn't production-ready.

## Cross-cutting
- **Offline mode uses TF-IDF + heuristics.** Good for a keyless demo, but
  semantic quality (Q2 retrieval, Q4 signals) improves materially with
  `OPENAI_API_KEY`. Both paths are wired; only quality differs.
- **Live calls & recordings require your accounts.** Vapi assistant configs and
  the KB-connected webhook are built and tested, but placing/recording actual
  phone calls needs a Vapi account + number. Transcripts provided are
  representative and match the backend's real outputs.

## Q2 — Knowledge base
- Sample sources are inline blobs simulating scraped content; a live scraper is
  described but not run (no network dependency in the demo).
- PII detection is regex-based (email/phone/card/SSN/PAN). It flags & redacts
  conservatively; it is not a full DLP classifier.
- Near-duplicate detection uses token Jaccard; semantically-paraphrased
  duplicates could slip through (an embedding-similarity pass would catch more).

## Q1 — Voice agent
- Eligibility is a preliminary rule engine, not a real underwriting decision.
- The mock CRM is local SQLite; production would call a real CRM/webhook.
- Grounding depends on KB coverage — a well-formed question with no matching KB
  record correctly returns "not confirmed" rather than a guess.

## Q3 — Native-language bots
- **Philippines:** Tagalog/Taglish only (no Cebuano/Ilocano). Needs
  native-speaker QA for politeness with elderly customers. Insurance suitability
  disclosures need licensed-FA review.
- **Indonesia:** only the Javanese accent is modeled (not Batak/Sundanese/Minang).
  No native regional TTS — replies use standard Indonesian voice. Denda figures
  are illustrative; OJK collections-conduct compliance review required.
- Localization examples and terminology were authored for realism but warrant
  native-speaker validation before production.

## Q4 — Real-time nudges
- **10x scale:** single-process, in-memory engine and an in-memory WebSocket
  client set. At 10x concurrency: run signal extraction in workers, key a
  `NudgeEngine` per `call_id`, and back delivery with Redis/Kafka. LLM-mode cost
  and latency dominate — batch/cache or keep heuristics primary.
- **Noisy audio:** heuristics rely on clean ASR text. High word-error input
  misses lexicon matches and can mis-segment speakers. Mitigations: ASR
  confidence gating, fuzzy phrase matching, and requiring two weak cues before a
  low-priority nudge.
- Disclosure detection is keyword-based; a paraphrased disclosure could be
  missed without an LLM verifier.
- ASR is simulated (speaker labels already known). Real streaming ASR
  (Deepgram live) adds diarization error and variable latency.
