# Connecting Q1 & Q3 to Real Voice Calls (Vapi)

The local voice demos (`*.voice_demo`) let you *hear* the agents offline. For
**real phone/web calls** — which the assessment needs for recorded-call
evidence — connect the assistants to Vapi. This requires your own accounts; the
code and configs are ready.

## Prerequisites
- A [Vapi](https://vapi.ai) account (free tier works for testing).
- An OpenAI API key (for the assistant's LLM + grounded answers).
- `ngrok` (or any tunnel) to expose your local webhook publicly.

## Step 1 — Put keys in `.env`
```
OPENAI_API_KEY=sk-...
VAPI_WEBHOOK_SECRET=pick-a-strong-secret
```

## Step 2 — Build the KB and run the Q1 webhook
```bash
python -m q2_knowledge_base.build_kb
uvicorn q1_voice_agent.webhook:app --port 8001
```

## Step 3 — Expose the webhook publicly
```bash
ngrok http 8001
```
Copy the HTTPS URL it prints, e.g. `https://ab12cd34.ngrok.io`.

## Step 4 — Point the assistant at your webhook
In `q1_voice_agent/vapi_assistant.json` replace:
- every `WEBHOOK_BASE_URL` → your ngrok URL (so tool URL becomes
  `https://ab12cd34.ngrok.io/vapi`)
- every `YOUR_VAPI_WEBHOOK_SECRET` → the same value as `VAPI_WEBHOOK_SECRET`

For Q3, use `q3_native_bots/generated/vapi_philippines.json` and
`vapi_indonesia.json` (generate them with `python -m q3_native_bots.export_configs`).

## Step 5 — Create the assistant in Vapi
Either:
- **Dashboard:** Assistants → Create → paste the JSON, or
- **API:**
  ```bash
  curl -X POST https://api.vapi.ai/assistant \
    -H "Authorization: Bearer $VAPI_PRIVATE_KEY" \
    -H "Content-Type: application/json" \
    -d @q1_voice_agent/vapi_assistant.json
  ```

## Step 6 — Talk to it
- **Web call:** use Vapi's web-call widget/playground with the assistant — you'll
  speak and hear it in the browser.
- **Phone:** buy/attach a Vapi phone number to the assistant and call it.

When a factual question comes up, Vapi calls your `/vapi` webhook, which queries
the Q2 KB and returns a grounded answer with citations — same behavior you saw in
`smoke_test` and the local voice demo, now over real audio.

## Step 7 — Record for submission
- Enable recording (already `recordingEnabled: true` in the config).
- Place the required calls: **Q1 ≥ 3** (cooperative, objection, out-of-scope /
  human-assistance) and **Q3 = 2 per market**.
- Download recordings + transcripts; save under `docs/recordings/` and
  `docs/transcripts/` (recordings are gitignored — don't commit customer audio).

## Troubleshooting
- **401 from webhook:** the `x-vapi-secret` header must equal `VAPI_WEBHOOK_SECRET`.
- **Tool never called:** confirm the tool `server.url` is your public ngrok URL + `/vapi`.
- **Answers sound generic:** rebuild the KB and set `OPENAI_API_KEY` for the best
  grounded phrasing.
