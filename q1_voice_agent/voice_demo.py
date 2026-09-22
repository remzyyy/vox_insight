"""Local VOICE demo for the Q1 business-loan agent (offline, no keys).

Speaks the bot's turns aloud using Windows TTS and uses the SAME backend as the
real Vapi webhook: grounded KB answers, eligibility, escalation. This lets you
*hear* the agent without a Vapi account.

Modes:
    python -m q1_voice_agent.voice_demo            # scripted auto demo (speaks)
    python -m q1_voice_agent.voice_demo --chat     # you type, bot speaks answers

This is a local demo of the voice EXPERIENCE. Real phone/web calls use Vapi
(q1_voice_agent/vapi_assistant.json).
"""
from __future__ import annotations

import sys

from shared.tts_local import speak
from .grounded_answer import GroundedAnswerer
from .eligibility import check_eligibility
from .prompts import FIRST_MESSAGE

BOT_VOICE = "Zira"  # female US voice for "Aria"


def _bot(text: str) -> None:
    speak(text, voice_hint=BOT_VOICE, rate=1)


def _user(text: str) -> None:
    print(f"🗣  Caller: {text}")


def scripted_demo() -> None:
    ans = GroundedAnswerer()
    _bot(FIRST_MESSAGE)

    _user("What is a working capital loan and how much can I borrow?")
    r = ans.answer("What is a working capital loan and how much can I borrow?")
    _bot(r["answer"])

    _user("My interest rate seems high, why should I proceed?")
    r = ans.answer("interest rate too high why proceed", category="objection")
    _bot(r["answer"])

    _user("My revenue is 40 lakh, business is 3 years old, credit score 760.")
    e = check_eligibility(annual_revenue_lakh=40, vintage_months=36, credit_score=760)
    _bot(f"Good news. Based on that you look {e.verdict.replace('_',' ')}. "
         f"This is preliminary, not a final approval.")

    _user("Do you offer loans in US dollars?")
    r = ans.answer("do you offer loans in US dollars foreign currency")
    _bot(r["answer"])  # should be the safe 'not confirmed' fallback

    _user("Just connect me to a person please.")
    _bot("Absolutely, I'll connect you to a specialist now. One moment please.")


def chat_demo() -> None:
    ans = GroundedAnswerer()
    _bot(FIRST_MESSAGE)
    print("\n(Type your question, blank line to quit.)")
    while True:
        try:
            q = input("🗣  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            break
        low = q.lower()
        if any(w in low for w in ["human", "person", "agent", "representative"]):
            _bot("Sure, I'll connect you to a specialist now. One moment please.")
            continue
        r = ans.answer(q)
        _bot(r["answer"])


def main() -> None:
    if "--chat" in sys.argv:
        chat_demo()
    else:
        scripted_demo()


if __name__ == "__main__":
    main()
