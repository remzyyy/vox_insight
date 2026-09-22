"""Generate Vapi assistant JSON + a human-readable summary for each market (Q3).

    python -m q3_native_bots.export_configs        # writes JSON + prints summary
"""
from __future__ import annotations

import json
import os

from .indonesia_bot import ID_BOT
from .philippines_bot import PH_BOT
from .localization import BotConfig

OUT_DIR = "q3_native_bots/generated"


def _system_prompt(cfg: BotConfig) -> str:
    terms = "; ".join(f"{t.term} ({t.meaning_en})" for t in cfg.terminology)
    faqs = " | ".join(f"Q:{f.question} A:{f.answer}" for f in cfg.faqs)
    objs = " | ".join(f"IF '{o.trigger}' THEN '{o.response}'" for o in cfg.objections)
    return (
        f"You are a {cfg.sector} voice agent for the {cfg.market} market. "
        f"Languages: {', '.join(cfg.languages)}. Register: {cfg.register_notes} "
        f"Code-switching: {cfg.code_switching_notes} "
        f"Use these local terms naturally: {terms}. "
        f"Handle FAQs from this grounded set only: {faqs}. "
        f"Handle objections: {objs}. "
        f"If you do not know something, say EXACTLY: '{cfg.fallback_line}' and do NOT switch "
        f"to English unexpectedly. If the customer asks for a human or is upset, say: "
        f"'{cfg.escalation_line}' and escalate. Always stay in the customer's language and register."
    )


def to_vapi_assistant(cfg: BotConfig) -> dict:
    return {
        "name": f"{cfg.market.title()} - {cfg.sector}",
        "firstMessage": cfg.greeting,
        "transcriber": {
            "provider": cfg.asr["provider"],
            "model": cfg.asr["model"],
            "language": cfg.asr["primary_language"],
        },
        "voice": {
            "provider": cfg.tts["provider"],
            "voiceId": cfg.tts["voice"],
        },
        "model": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.4,
            "messages": [{"role": "system", "content": _system_prompt(cfg)}],
        },
        "recordingEnabled": True,
        "_localization_meta": {
            "languages": cfg.languages,
            "asr_notes": cfg.asr["notes"],
            "tts_notes": cfg.tts["notes"],
            "accent_notes": cfg.accent_notes,
            "known_gaps": cfg.known_gaps,
        },
    }


def _print_summary(cfg: BotConfig) -> None:
    print("=" * 78)
    print(f"MARKET: {cfg.market.upper()}  |  sector: {cfg.sector}")
    print(f"Languages: {', '.join(cfg.languages)}")
    print(f"ASR: {cfg.asr['provider']}/{cfg.asr['model']} (primary={cfg.asr['primary_language']})")
    print(f"TTS: {cfg.tts['provider']} voice={cfg.tts['voice']}")
    if cfg.accent_notes:
        print(f"Accent: {cfg.accent_notes[:100]}...")
    print(f"\nLocalization (NOT translation) examples: {len(cfg.localization_examples)}")
    for i, ex in enumerate(cfg.localization_examples, 1):
        print(f"  [{i}] {ex.situation}")
        print(f"       literal : {ex.literal_translation}")
        print(f"       localized: {ex.localized}")
        print(f"       why     : {ex.why}")
    print(f"\nKnown gaps: {len(cfg.known_gaps)}")
    for g in cfg.known_gaps:
        print(f"  - {g}")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    for cfg in (PH_BOT, ID_BOT):
        path = os.path.join(OUT_DIR, f"vapi_{cfg.market}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(to_vapi_assistant(cfg), f, ensure_ascii=False, indent=2)
        _print_summary(cfg)
        print(f"\nWrote {path}\n")


if __name__ == "__main__":
    main()
