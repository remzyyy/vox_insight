# Q4 — Live Insights and Nudges From Call Audio

Analyzes a call **while it is happening** and produces short, actionable nudges
before the call ends. Nudges stream to a dashboard (WebSocket) and a polling API.

## Pipeline

```
audio chunk ─▶ streaming ASR ─▶ signal extraction ─▶ nudge engine ─▶ delivery
 (replayed      (speaker-        (heuristic +         (threshold,      (WebSocket +
  in real time)  separated)       optional LLM)        dedup, cooldown,  polling API +
                                                        priority, expiry) dashboard)
        └──────────────── latency measured at each stage ────────────────┘
```

- **Streaming input:** a scenario transcript (or real recording) replayed at
  real-time speed in chunks (`pipeline.stream_call`).
- **Streaming ASR:** simulated with agent/customer separation and a realistic
  per-chunk latency (`_simulate_asr`); swap for Deepgram live in production.
- **Signal extraction** (`signals.py`): intent/topic shift, compliance/risk,
  sentiment/frustration (with escalation streak), buying signals, missed
  opportunities, payment difficulty, callback needs. Heuristic by default;
  LLM-augmented when `OPENAI_API_KEY` is set.
- **Nudge engine** (`nudge_engine.py`): confidence thresholds, duplicate
  suppression, per-type cooldowns, topic grouping, priorities, and expiry.
- **Delivery** (`server.py`): live WebSocket dashboard + `/nudges` polling API.

## Files
- `models.py` — `TranscriptChunk`, `Signal`, `Nudge`, priority map
- `signals.py` — `SignalExtractor` (heuristic + LLM), conversational state
- `nudge_engine.py` — `NudgeEngine` with all control mechanisms
- `latency.py` — `LatencyTracker` with P50/P95 per component
- `pipeline.py` — `stream_call` async generator + `run_and_collect`
- `scenarios.py` — 5 sample calls (incl. the 4 required test cases)
- `simulate.py` — CLI runner
- `false_positive_report.py` — approximate FP analysis
- `server.py` — FastAPI + WebSocket + dashboard

## Run
```bash
# CLI (offline, no keys needed)
python -m q4_realtime_nudges.simulate --scenario all --fast
python -m q4_realtime_nudges.false_positive_report

# Live server + dashboard
uvicorn q4_realtime_nudges.server:app --port 8004
# open http://localhost:8004/ and click a scenario
# or: curl -X POST http://localhost:8004/simulate/frustration
```

## Signal design
| Signal | How it's detected |
|---|---|
| rising_frustration | frustration lexicon; confidence grows with a streak of frustrated turns |
| payment_difficulty | hardship lexicon ("can't afford", "cash flow", "miss a payment") |
| buying_signal | intent lexicon ("let's do it", "how soon", "sign me up") |
| callback_needed | callback lexicon ("call me back", "not a good time") |
| missed_cross_sell | customer reveals a second need (second shop, equipment, invoices) AND the agent never offers a matching product |
| compliance_gap | a required disclosure (rate/APR, recording) is never spoken — **only after the call enters real loan business** |
| topic_shift | topic keyword changes (high confidence gate → rarely nudges) |

## Nudge control (anti-spam)
- **Confidence threshold** per type (`CONF_THRESHOLD`); `topic_shift` gated at 0.9.
- **Duplicate suppression:** one active nudge per `(type, topic)`.
- **Cooldown** per type (`COOLDOWN_S`, 15–30s).
- **Priority:** compliance (1) > frustration/payment (2) > cross-sell/buying (3) > topic (4).
- **Expiry:** nudges auto-expire after 30s so stale advice disappears.

## Latency report (from `simulate --fast`, local, heuristic mode)
Measured audio-received → transcription → signal detection → nudge → display.

| Component | P50 | P95 | Notes |
|---|---|---|---|
| ASR (simulated) | ~125 ms | ~140 ms | dominates; models real streaming ASR delay |
| signal_extraction | <1 ms | ~1 ms | heuristic; LLM mode adds provider round-trip |
| nudge (compose+control) | <1 ms | <1 ms | in-memory |
| end_to_end | ~125 ms | ~140 ms | audio→nudge ready |

> With LLM signal mode, add the model round-trip (~300–900 ms) to signal
> extraction; the heuristic still runs as a fast floor so critical nudges
> (compliance, frustration) are never blocked on the LLM.

## False-positive control
`false_positive_report.py` compares fired vs expected nudges. On the test set:
**7 nudges fired, 0 false positives (precision 1.00)**. The `noisy` scenario —
small talk with no loan intent — correctly fires **zero** nudges, satisfying the
"avoid unnecessary nudges" requirement.

## Required test coverage
- Missed cross-sell → `missed_cross_sell` scenario ✓
- Skipped disclosure / risky statement → `compliance` scenario ✓
- Rising frustration → `frustration` scenario ✓
- Noisy / ambiguous (no nudges) → `noisy` scenario ✓

## Limitations
- **10x scale:** single-process, in-memory engine. At 10x concurrent calls,
  move signal extraction to workers, use a per-call engine instance keyed by
  call_id, and back delivery with a message broker (Redis/Kafka) instead of an
  in-memory client set. LLM-mode cost/latency dominates — batch or cache.
- **Noisy audio:** heuristics rely on clean ASR text; high word-error input
  will miss lexicon matches and may mis-segment speakers. Mitigate with ASR
  confidence gating, phrase-fuzzy matching, and requiring 2 weak cues before a
  low-priority nudge.
- Disclosure detection is keyword-based; a paraphrased disclosure could be
  missed. An LLM verifier per disclosure would raise recall at a latency cost.
