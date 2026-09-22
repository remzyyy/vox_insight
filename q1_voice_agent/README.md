# Q1 — Knowledge-Grounded Voice Agent (Business-Loan Qualification)

A Vapi voice agent, "Aria", that qualifies business-loan leads. Every factual
answer is grounded in the **Q2 knowledge base** via a webhook tool — nothing is
hardcoded in the system prompt.

## Architecture

```
Caller ──phone/web──▶ Vapi (ASR + LLM + TTS)
                         │  tool calls (query_knowledge_base, check_eligibility,
                         │              create_lead, escalate_to_human)
                         ▼
                POST {WEBHOOK}/vapi  (FastAPI, this repo)
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                  ▼
  Q2 KB Retriever   eligibility.py      crm.py (mock CRM)
  (grounded answer   (preliminary        (lead + escalation
   + citations)       verdict)            + call summary)
```

## Files
- `prompts.py` — system prompt + first message (behavior/flow only, no hardcoded facts)
- `grounded_answer.py` — retrieves from Q2 KB, composes a grounded spoken answer (LLM or extractive fallback), refuses when not confident
- `eligibility.py` — preliminary eligibility rules (mirror the KB rules)
- `crm.py` — mock CRM: `create_lead`, `escalate`, `call_summary` (SQLite)
- `webhook.py` — FastAPI app; direct `/tools/*` endpoints + Vapi `/vapi` dispatcher
- `vapi_assistant.json` — importable Vapi assistant config with the 4 tools
- `smoke_test.py` — offline end-to-end check of all tools

## Run locally
```bash
python -m q2_knowledge_base.build_kb          # build the KB first
uvicorn q1_voice_agent.webhook:app --port 8001
python -m q1_voice_agent.smoke_test           # verify tools offline
```

## Connect to Vapi (what you do)
1. Deploy `webhook.py` to a public URL (e.g. ngrok for testing:
   `ngrok http 8001`).
2. In `vapi_assistant.json`, replace `WEBHOOK_BASE_URL` with that URL and
   `YOUR_VAPI_WEBHOOK_SECRET` with your `VAPI_WEBHOOK_SECRET`.
3. Import the assistant into Vapi and attach a phone number or use the web-call widget.
4. Place at least 3 test calls covering the scenarios below; save transcripts to
   `docs/transcripts/`.

## Required test coverage → where it's handled
| Scenario | Handling |
|---|---|
| Cooperative customer | qualification flow → `check_eligibility` → `create_lead` |
| Objection | `query_knowledge_base(category="objection")` grounded response |
| Incomplete / conflicting details | prompt asks to clarify / restate; never assumes |
| Out-of-scope question | KB returns `grounded=false` → safe "not confirmed" + offer specialist |
| Human-assistance request | `escalate_to_human` |
| Unavailable info | `grounded=false` path — states it won't guess |

Sample transcripts demonstrating each are in `docs/transcripts/q1_*.md`.

## Grounding guarantee
- Answers come only from retrieved KB chunks.
- Below the retrieval confidence floor (0.18 blended score) the agent refuses
  and offers escalation instead of inventing.
- PII-flagged KB records are excluded from retrieval entirely.
