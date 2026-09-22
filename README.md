# VoxInsight 

A single, runnable repository covering all four assessment questions. The
**Question 2 knowledge base** is the shared RAG foundation that the
**Question 1 voice agent** queries live (no hardcoded FAQs). Recorded calls from
Q1/Q3 feed **Question 4**'s real-time nudge pipeline.

**Chosen use case (Q1):** Business-loan qualification
**Chosen voice platform:** [Vapi](https://vapi.ai) (callable web + phone agent, webhook tool integration)

---

## ⭐ One website for everything (recommended)

A single unified web console serves all four parts — landing page + one page per
question, with in-browser voice for Q1/Q3 and a live WebSocket dashboard for Q4.

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
python -m q2_knowledge_base.build_kb   # build the KB once
uvicorn app.main:app --port 8080
```
Then open **http://localhost:8080/** and use the nav to reach each demo:
- **Q1** — chat with Aria; grounded KB answers spoken aloud + eligibility calculator
- **Q2** — search the knowledge base with ranked results + citations
- **Q3** — play Philippines (Taglish) & Indonesia (Bahasa) lines with localization examples
- **Q4** — stream a call live and watch nudges appear with latency

Everything runs offline (no keys). For real phone/web calls see
[`docs/vapi_setup.md`](docs/vapi_setup.md).

## Repository layout

```
vox-insight/
├── app/                     # ⭐ Unified web console (all 4 parts in one site)
├── shared/                  # Config, logging, PII, local TTS reused across parts
├── q2_knowledge_base/       # Production KB + RAG (scrape → clean → chunk → embed → retrieve → cite)
├── q1_voice_agent/          # Vapi assistant config + FastAPI webhook that calls the Q2 KB
├── q3_native_bots/          # Philippines (Taglish) + Indonesia (Bahasa) localized bot configs
├── q4_realtime_nudges/      # Streaming ASR sim → signal extraction → nudge engine → WS dashboard
├── docs/                    # Architecture diagram, test results, limitations, video script
├── data/                    # Sample source content + generated KB store
├── .env.example             # Copy to .env and fill your keys
└── requirements.txt
```

## Quick start

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env   # then edit .env

# Q2: build the KB and run retrieval tests (works offline with local embeddings)
python -m q2_knowledge_base.build_kb
python -m q2_knowledge_base.retrieval_tests

# Q1: run the KB-connected voice webhook (connect Vapi to this URL)
uvicorn q1_voice_agent.webhook:app --port 8001

# Q4: run the real-time nudge pipeline + dashboard
uvicorn q4_realtime_nudges.server:app --port 8004
python -m q4_realtime_nudges.simulate --scenario missed_cross_sell

# To see demo of live project -
 uvicorn app.main:app --port 8080
then open this link - http://127.0.0.1:8080
```

## Runs offline vs needs keys

| Capability | Offline (no keys) | Needs a key |
|---|---|---|
| Q2 embeddings + retrieval | ✅ local hash/`sentence-transformers` fallback | Better quality with `OPENAI_API_KEY` |
| Q1 grounded answers (LLM) | ⚠️ rule-based stub | `OPENAI_API_KEY` for full answers |
| Q1/Q3 actual phone calls | ❌ | Vapi + phone number |
| Q4 signal extraction | ✅ heuristic mode | `OPENAI_API_KEY` for LLM signals |
| Q4 streaming ASR from mic | ⚠️ replays transcript files | ASR provider for live audio |

## What you (the candidate) must do to finish the submission

These require accounts/hardware I cannot provision:

1. Add your API keys to `.env`.
2. Create a Vapi assistant by importing `q1_voice_agent/vapi_assistant.json` and point its
   custom tool/webhook at your deployed `q1_voice_agent.webhook` URL.
3. Place & record at least **3 test calls** (Q1) and **2 calls per market** (Q3);
   save transcripts under `docs/transcripts/`.
4. Run one live call through the Q4 pipeline and record the demo.
5. Record the video walkthrough (outline in `docs/video_walkthrough.md`).

> **Security:** never commit `.env`, keys, or real customer data. `.gitignore` blocks them.

## Documentation
- [`docs/architecture.md`](docs/architecture.md) — diagram + key design decisions
- [`docs/test_results.md`](docs/test_results.md) — Q2 retrieval, Q1 tools, Q4 latency + false-positive analysis
- [`docs/limitations.md`](docs/limitations.md) — known limits, 10x scale, noisy audio
- [`docs/production_plan.md`](docs/production_plan.md) — path to production
- [`docs/video_walkthrough.md`](docs/video_walkthrough.md) — recording script
- [`docs/submission_checklist.md`](docs/submission_checklist.md) — deliverables map
- Per-question details: [`q1_voice_agent/README.md`](q1_voice_agent/README.md),
  [`q3_native_bots/README.md`](q3_native_bots/README.md),
  [`q4_realtime_nudges/README.md`](q4_realtime_nudges/README.md)

## Reproduce all offline results (no keys needed)
```bash
python -m q2_knowledge_base.build_kb
python -m q2_knowledge_base.retrieval_tests
python -m q1_voice_agent.smoke_test
python -m q3_native_bots.export_configs
python -m q4_realtime_nudges.simulate --scenario all --fast
python -m q4_realtime_nudges.false_positive_report
```

## Hear the voice locally (offline, Windows TTS — no keys)
A local preview so you can *hear* the Q1/Q3 agents speak on this machine. This is
a demo of the voice experience; real phone/web calls use Vapi (see below).
```bash
python -m q1_voice_agent.voice_demo          # Aria speaks a scripted loan call
python -m q1_voice_agent.voice_demo --chat   # you type, Aria speaks answers
python -m q3_native_bots.voice_demo          # Taglish + Bahasa lines spoken
python -m q3_native_bots.voice_demo philippines
```

## Real voice calls with Vapi (needs your keys)
See [`docs/vapi_setup.md`](docs/vapi_setup.md) for step-by-step connection of the
Q1 and Q3 assistants to actual phone/web calls.


## Completed by-
```bash
Rameez Siddiqui
Gmail - rameezsid1234@gmail.com
PHONE - 7428842647
IIIT BHUBANESWAR
```

