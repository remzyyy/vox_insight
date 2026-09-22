"""Local VOICE demo for the Q3 native-language bots (offline, no keys).

Speaks each market's greeting, a scripted flow turn, an objection response, and
the in-language fallback + escalation lines, so you can HEAR the localization.

    python -m q3_native_bots.voice_demo             # both markets
    python -m q3_native_bots.voice_demo philippines
    python -m q3_native_bots.voice_demo indonesia

Note: Windows TTS has no native Filipino/Javanese voice, so pronunciation is
approximate — this is a local preview of the SCRIPTS. Production uses Azure
Filipino/Indonesian neural voices (see q3_native_bots/generated/*.json).
"""
from __future__ import annotations

import sys

from shared.tts_local import speak
from .philippines_bot import PH_BOT
from .indonesia_bot import ID_BOT

VOICE = {"philippines": "Zira", "indonesia": "David"}


def demo_market(cfg, voice_hint: str) -> None:
    print("\n" + "=" * 70)
    print(f"MARKET: {cfg.market.upper()} | {cfg.sector} | {', '.join(cfg.languages)}")
    print("=" * 70)

    def say(label, text):
        print(f"\n[{label}]")
        speak(text, voice_hint=voice_hint, rate=0)

    say("Greeting", cfg.greeting)
    if cfg.flow:
        say("Flow: " + cfg.flow[1].intent if len(cfg.flow) > 1 else cfg.flow[0].intent,
            (cfg.flow[1] if len(cfg.flow) > 1 else cfg.flow[0]).bot)
    if cfg.objections:
        o = cfg.objections[0]
        print(f"\n[Objection trigger] Caller: {o.trigger}")
        speak(o.response, voice_hint=voice_hint, rate=0)
    say("Fallback (unavailable info, stays in-language)", cfg.fallback_line)
    say("Escalation (stays in-language)", cfg.escalation_line)


def main() -> None:
    which = sys.argv[1].lower() if len(sys.argv) > 1 else "both"
    if which in ("philippines", "both"):
        demo_market(PH_BOT, VOICE["philippines"])
    if which in ("indonesia", "both"):
        demo_market(ID_BOT, VOICE["indonesia"])


if __name__ == "__main__":
    main()
