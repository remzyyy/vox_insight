# VoxInsight — Architecture

The **Q2 knowledge base** is the shared foundation. The **Q1 voice agent** queries
it live for grounded answers. **Q3** reuses the same voice-platform pattern for
localized markets. Recorded calls from **Q1/Q3** feed **Q4**'s real-time pipeline.

```mermaid
flowchart TB
  subgraph Sources["Mixed business content"]
    WEB[Web pages / marketing]
    POL[Policy & qualification rules]
    FAQ[FAQs / objections]
    PII[(Content with PII)]
  end

  subgraph Q2["Q2 — Knowledge Base (shared foundation)"]
    CLEAN[Clean: strip boilerplate,\nstandardize, redact PII,\nflag errors, dedupe]
    CHUNK[Chunk\nsentence-aware]
    EMB[Embed\nOpenAI or TF-IDF]
    STORE[(SQLite store\n+ vectors)]
    RET[Retriever\ndense+lexical, citations,\nconfidence gate]
    Sources --> CLEAN --> CHUNK --> EMB --> STORE --> RET
  end

  subgraph Q1["Q1 — Voice Agent (Vapi)"]
    VAPI1[Vapi assistant\nASR+LLM+TTS]
    HOOK[FastAPI webhook\n/vapi dispatcher]
    ELIG[check_eligibility]
    CRM[(mock CRM:\nlead + escalation)]
    VAPI1 -->|tool call| HOOK
    HOOK -->|query_knowledge_base| RET
    HOOK --> ELIG
    HOOK --> CRM
  end

  subgraph Q3["Q3 — Native-Language Bots"]
    PH[Philippines\nTaglish · bancassurance]
    ID[Indonesia\nBahasa+Javanese · multifinance]
  end

  subgraph Q4["Q4 — Real-time Nudges"]
    ASR2[Streaming ASR sim\nspeaker-separated]
    SIG[Signal extraction\nheuristic + LLM]
    NUDGE[Nudge engine\nthreshold/dedup/cooldown/\npriority/expiry]
    DASH[WebSocket dashboard\n+ polling API]
    ASR2 --> SIG --> NUDGE --> DASH
  end

  RET -. grounded answers .-> VAPI1
  VAPI1 -. recorded calls .-> ASR2
  PH -. recorded calls .-> ASR2
  ID -. recorded calls .-> ASR2
```

## Key design decisions

| Decision | Why |
|---|---|
| SQLite + in-memory cosine for the KB | Zero external services, durable & traceable records; swap for FAISS/pgvector at scale |
| TF-IDF offline fallback for embeddings | Whole RAG pipeline runs and is testable with **no API keys**; OpenAI is a quality upgrade, not a hard dependency |
| Grounding via a confidence floor | Below the floor the agent refuses instead of hallucinating — directly targets the "hallucinated answers" rejection condition |
| PII excluded from retrieval | PII-flagged records are stored for audit but never ground a customer answer |
| Voice tools via webhook, not prompt | FAQs/policies live in the KB (Q2), satisfying "do not hardcode all FAQs in the system prompt" |
| Localization as config objects (Q3) | Terminology, code-switching, and localization-vs-translation examples are explicit and reviewable |
| Heuristic-first signals (Q4) | Fast, deterministic, cheap for real-time; LLM augments but never blocks critical nudges |
| Nudge control layer (Q4) | Thresholds/dedup/cooldown/expiry defend against "excessive low-value alerts" |

## Shared modules (`shared/`)
- `config.py` — env-driven settings; `has_openai` gates quality vs offline.
- `pii.py` — regex PII scan/redact (email, phone, card, SSN, PAN).
- `logging_utils.py` — consistent logging.
