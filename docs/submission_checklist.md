# Submission Checklist

Maps deliverables to what's in this repo and what you still need to do.

## Built & verified (in this repo)
- [x] **Q1** voice-agent config + KB-connected webhook (`q1_voice_agent/`)
- [x] **Q2** production knowledge base + RAG with retrieval tests (`q2_knowledge_base/`)
- [x] **Q3** Philippines + Indonesia localized bot configs (`q3_native_bots/`)
- [x] **Q4** real-time nudge pipeline + dashboard + latency + FP report (`q4_realtime_nudges/`)
- [x] Q1 connected to Q2 KB (webhook `query_knowledge_base` → retriever)
- [x] Grounded answers with citations; safe fallback when unavailable
- [x] Retrieval test results (5+ queries with verdicts) — `docs/test_results.md`
- [x] Localization-not-translation examples (3 per market)
- [x] Real-time nudges within seconds; measured P50/P95; FP analysis
- [x] README + per-question READMEs + `.env.example`
- [x] Architecture diagram (`docs/architecture.md`)
- [x] Limitations + 10x/noisy notes (`docs/limitations.md`)
- [x] Production-improvement plan (`docs/production_plan.md`)
- [x] Video walkthrough script (`docs/video_walkthrough.md`)
- [x] Sample transcripts for Q1 (3) and Q3 (2 per market)
- [x] No secrets committed (`.gitignore` blocks `.env`, keys, recordings, DBs)

## You must do to finalize (needs your accounts/hardware)
- [ ] Add API keys to `.env` (OpenAI optional but recommended; Vapi for calls).
- [ ] Deploy `q1_voice_agent.webhook` to a public URL; set it + secret in
      `q1_voice_agent/vapi_assistant.json`.
- [ ] Import Vapi assistants (Q1 + both Q3 configs); attach numbers/web widget.
- [ ] Record **3+ Q1 test calls** and **2 calls per Q3 market**; save audio +
      transcripts under `docs/transcripts/` and `docs/recordings/`.
- [ ] Run one live/replayed call through Q4 and record the dashboard demo.
- [ ] Record the video walkthrough (follow `docs/video_walkthrough.md`).
- [ ] Push to a GitHub repo (README + `.env.example` already included).

## Reproduce all offline results
```bash
python -m q2_knowledge_base.build_kb
python -m q2_knowledge_base.retrieval_tests
python -m q1_voice_agent.smoke_test
python -m q3_native_bots.export_configs
python -m q4_realtime_nudges.simulate --scenario all --fast
python -m q4_realtime_nudges.false_positive_report
```
