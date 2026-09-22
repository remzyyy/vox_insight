"""Sample call scenarios for the Q4 pipeline (simulated transcripts).

Each scenario is a list of (speaker, text) turns replayed in real time. They map
to the required test coverage:
  - missed_cross_sell : customer reveals a second need; agent never offers
  - compliance        : agent skips the required rate/recording disclosure
  - frustration       : customer frustration rises turn over turn
  - noisy             : ambiguous small-talk; NO nudges should fire (FP control)
"""
from __future__ import annotations

SCENARIOS: dict[str, list[tuple[str, str]]] = {
    "missed_cross_sell": [
        ("agent", "Hi, this is Aria from business lending. How can I help today?"),
        ("customer", "I run a bakery and I want a working capital loan for ingredients."),
        ("agent", "Great, we can help with working capital. What's your annual revenue?"),
        ("customer", "About 40 lakh. Oh, and I'm also planning to expand to a second shop next year."),
        ("agent", "Nice. For working capital, disbursal takes about three business days."),
        ("customer", "Okay that works for the bakery."),
        ("agent", "I'll set up your application for the working capital loan then."),
    ],
    "compliance": [
        ("agent", "Hi, this is the lending team. Let's get you a term loan quickly."),
        ("customer", "Great, how much can I get?"),
        ("agent", "Up to 50 lakh depending on your profile."),
        ("customer", "And the monthly payment?"),
        ("agent", "We'll fix an EMI over 12 to 48 months. Let's proceed with the application."),
        ("customer", "Sounds good, let's do it."),
        ("agent", "Perfect, I'll submit it now."),
    ],
    "frustration": [
        ("agent", "Hello, thanks for calling business lending."),
        ("customer", "Finally. I've been transferred around, this is the third time I'm explaining."),
        ("agent", "I understand, let me pull up your details."),
        ("customer", "This is ridiculous, I've been waiting and no one helps me."),
        ("agent", "Let me check that for you."),
        ("customer", "Seriously, I'm really frustrated, this is a waste of time."),
        ("agent", "I hear you, let me fix this right now."),
    ],
    "noisy": [
        ("agent", "Hi, good morning!"),
        ("customer", "Morning. Bit of rain here today huh."),
        ("agent", "Yeah, drive safe. So how can I help?"),
        ("customer", "Just wanted to say hi, my friend mentioned you guys."),
        ("agent", "Appreciate it. Anything about a loan I can answer?"),
        ("customer", "Not really, maybe some other time. Nice talking though."),
        ("agent", "Of course, have a great day!"),
    ],
    "payment_difficulty": [
        ("agent", "Hi, calling about your upcoming installment."),
        ("customer", "Yeah... honestly business is down and I can't afford the payment this month."),
        ("agent", "I understand."),
        ("customer", "I might miss a payment, cash flow is really tight."),
        ("agent", "Let me see what options we have."),
    ],
}


def get(name: str) -> list[tuple[str, str]]:
    if name not in SCENARIOS:
        raise KeyError(f"unknown scenario '{name}'. Options: {list(SCENARIOS)}")
    return SCENARIOS[name]
