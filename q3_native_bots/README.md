# Q3 — Native-Language Voice Bots (Philippines + Indonesia)

Localized prototypes for real financial conversations. The goal is
**localization, not literal translation**: natural code-switching, local finance
terminology, culturally appropriate register, and fallback that stays in the
customer's language.

## Markets

| | Philippines | Indonesia |
|---|---|---|
| Sector | Life insurance / bancassurance | Multifinance / consumer finance |
| Languages | English, Filipino/Tagalog, **Taglish** | Formal + colloquial **Bahasa**, English loanwords |
| Flows | Renewal reminder, bancassurance cross-sell | Installment reminder, collections support |
| Regional accent | — | **Javanese-accented Bahasa** (Central/East Java) |
| Key terms | premium, policy, beneficiary, rider, lapse, coverage, bank referral | cicilan, tenor, denda, DP, jatuh tempo, angsuran, pembiayaan |

## Files
- `localization.py` — shared schema (terms, examples, scripts, FAQs, objections)
- `philippines_bot.py` — `PH_BOT` full config
- `indonesia_bot.py` — `ID_BOT` full config
- `export_configs.py` — generates Vapi assistant JSON + prints a summary
- `generated/vapi_philippines.json`, `generated/vapi_indonesia.json` — importable configs

## Run
```bash
python -m q3_native_bots.export_configs   # writes generated/*.json, prints localization evidence
```

## ASR configuration & testing (report)

| Market | Provider/Model | Languages tested | Code-switching | Approx. quality | Observed errors | Regional accent |
|---|---|---|---|---|---|---|
| Philippines | Deepgram nova-2 (primary `fil` + `en`) | English, Tagalog, Taglish | Good intra-sentence EN↔TL | Good on clear Taglish | Rapid English loanwords mid-Tagalog occasionally split | n/a |
| Indonesia | Deepgram nova-2 (primary `id` + `en`) | Standard Jakarta, colloquial Jakarta, Javanese-accented | Good for loanwords (tenor, DP) | Good standard; fair colloquial | Higher WER on Javanese particles (nggih, mboten, mawon) & rapid colloquial | **Javanese** tested separately |

> Configure each market as a separate assistant/transcriber. Test the three
> Indonesian profiles independently and log word-error qualitatively.

## TTS
- Philippines: Azure `fil-PH-BlessicaNeural` / `fil-PH-AngeloNeural`.
- Indonesia: Azure `id-ID-GadisNeural` / `id-ID-ArdiNeural`.
- **Compromise documented:** no native Javanese/Sundanese TTS — the bot always
  *replies* in clear standard Bahasa/Filipino; regional handling is on the ASR
  (input) side plus light politeness mirroring, not regional TTS output.

## Localization-not-translation evidence
Each market ships **3 examples** (see `export_configs.py` output and the bot
files) showing the rejected literal translation next to the natural localized
line and the reasoning. Examples cover: due-date reminders, explaining a rider,
bank-referral cross-sell (PH); due reminders, face-saving hardship help, and
Javanese-accent register mirroring (ID).

## Fallback / escalation
Both bots have a fixed `fallback_line` and `escalation_line` **in the local
language** — no unexpected switch to English when information is unavailable or
a human is requested. See transcripts for demonstrations.

## Required test coverage → transcripts
- Cooperative customer, mixed EN/finance terms, colloquial → `docs/transcripts/q3_*_call1_*.md`
- Sector-specific objection, human escalation, Indonesian regional accent → `docs/transcripts/q3_*_call2_*.md`

## Known native-speaker / compliance gaps
- **PH:** Cebuano/Ilocano not covered; native-speaker QA needed for politeness with
  elderly customers; insurance suitability disclosures need licensed-FA review.
- **ID:** only Javanese accent modeled (not Batak/Sundanese/Minang); no native
  regional TTS; denda figures illustrative; OJK collections-conduct compliance
  review required.

## What you do to finish
Import each `generated/vapi_*.json` into Vapi, attach numbers, and record **2
calls per market** covering the scenarios above; save transcripts to `docs/transcripts/`.
