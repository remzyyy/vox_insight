"""Signal extraction from transcript chunks (Q4).

Two modes:
  - heuristic (default, no keys): fast keyword/pattern rules with per-signal
    confidence. Deterministic and cheap — good for real-time and for the noisy-
    call false-positive control.
  - LLM (OPENAI_API_KEY): augments/creates signals from a rolling window; the
    heuristic still runs as a floor.

The extractor keeps light conversational state (recent topics, whether required
disclosures were spoken) so it can detect *missed* opportunities and *skipped*
disclosures, not just present keywords.
"""
from __future__ import annotations

import re

from shared.config import settings
from shared.logging_utils import get_logger
from .models import Signal, TranscriptChunk

log = get_logger("q4.signals")

# --- lexicons (business-loan / finance call domain) ---
FRUSTRATION = [
    "this is ridiculous", "waste of time", "frustrated", "annoyed", "not happy",
    "unacceptable", "third time", "again and again", "fed up", "come on",
    "seriously", "still waiting", "no one helps",
]
PAYMENT_DIFFICULTY = [
    "can't afford", "cannot afford", "too expensive", "no money", "lost my job",
    "business is down", "cash flow", "struggling to pay", "miss a payment",
    "behind on", "can't pay",
]
BUYING = [
    "how do i sign up", "how soon", "when can i get", "sounds good", "let's do it",
    "i'm interested", "what's the next step", "ready to", "go ahead", "sign me up",
]
CALLBACK = [
    "call me back", "call me later", "not a good time", "busy right now",
    "reach me at", "in a meeting", "call tomorrow",
]
# Cross-sell cues: customer reveals a second need the agent could offer for.
CROSS_SELL_CUES = {
    "second_business": ["another business", "second shop", "other store", "franchise", "expand to"],
    "equipment": ["new machine", "equipment", "machinery", "buy a truck", "vehicle for the business"],
    "invoices": ["unpaid invoices", "clients owe", "receivables", "waiting on payment from clients"],
}
# Required compliance disclosures the AGENT must say at some point.
REQUIRED_DISCLOSURES = {
    "rate_apr_disclosure": ["interest rate", "apr", "per annum", "% per"],
    "fee_disclosure": ["processing fee", "charges", "fees"],
    "recording_disclosure": ["this call is recorded", "call may be recorded", "recorded for quality"],
}
TOPIC_KEYWORDS = {
    "rate": ["rate", "interest", "apr"],
    "eligibility": ["qualify", "eligible", "revenue", "vintage", "credit score"],
    "documents": ["document", "papers", "statement", "itr", "gst"],
    "repayment": ["emi", "repay", "prepay", "installment"],
    "product": ["term loan", "working capital", "line of credit"],
}


def _match(text: str, phrases: list[str]) -> str | None:
    low = text.lower()
    for p in phrases:
        if p in low:
            return p
    return None


def _topic_of(text: str) -> str:
    low = text.lower()
    for topic, kws in TOPIC_KEYWORDS.items():
        if any(k in low for k in kws):
            return topic
    return "general"


class SignalExtractor:
    def __init__(self, *, use_llm: bool | None = None) -> None:
        self.use_llm = settings.has_openai if use_llm is None else use_llm
        # conversational state
        self.disclosures_made: set[str] = set()
        self.customer_cross_sell_cues: list[tuple[str, str, int]] = []  # (cue_type, phrase, seq)
        self.agent_offered_products: bool = False
        self.last_topic: str = "general"
        self.frustration_streak: int = 0
        # True once the call actually enters loan business (so we know a
        # disclosure is *required*). Avoids compliance false-positives on
        # small-talk/no-intent calls.
        self.loan_context_entered: bool = False

    # Cues that the call has entered ACTUAL loan business (not just the word
    # "loan" in a greeting/offer). Requires product specifics, amounts, EMIs,
    # application/processing, or a concrete borrowing question.
    _LOAN_CONTEXT = [
        "emi", "term loan", "working capital", "line of credit",
        "how much can i get", "how much can i borrow", "how much can i",
        "the application", "submit it", "50 lakh", "disburs", "monthly payment",
        "installment", "proceed with the application", "let's do it", "sign up",
        "interest rate", "processing fee",
    ]

    def update_state(self, chunk: TranscriptChunk) -> None:
        low = chunk.text.lower()
        if any(c in low for c in self._LOAN_CONTEXT):
            self.loan_context_entered = True
        if chunk.speaker == "agent":
            for disc, kws in REQUIRED_DISCLOSURES.items():
                if any(k in low for k in kws):
                    self.disclosures_made.add(disc)
            if any(p in low for p in ["we also offer", "you might also", "have you considered",
                                      "we can also help with", "another product"]):
                self.agent_offered_products = True

    def extract(self, chunk: TranscriptChunk, window: list[TranscriptChunk]) -> list[Signal]:
        signals = self._heuristic(chunk, window)
        if self.use_llm:
            try:
                signals += self._llm(chunk, window)
            except Exception as e:  # pragma: no cover
                log.warning("LLM signal extraction failed (%s); heuristic only", e)
        return signals

    # ---------------- heuristic ----------------
    def _heuristic(self, chunk: TranscriptChunk, window: list[TranscriptChunk]) -> list[Signal]:
        out: list[Signal] = []
        text = chunk.text
        topic = _topic_of(text)

        if chunk.speaker == "customer":
            # frustration (escalates with streak)
            if _match(text, FRUSTRATION):
                self.frustration_streak += 1
                conf = min(0.5 + 0.2 * self.frustration_streak, 0.95)
                out.append(Signal("rising_frustration", conf,
                                  _match(text, FRUSTRATION), chunk.speaker, chunk.seq, topic))
            else:
                # decay streak on calm customer turns
                self.frustration_streak = max(0, self.frustration_streak - 1)

            if (m := _match(text, PAYMENT_DIFFICULTY)):
                out.append(Signal("payment_difficulty", 0.8, m, chunk.speaker, chunk.seq, topic))
            if (m := _match(text, BUYING)):
                out.append(Signal("buying_signal", 0.7, m, chunk.speaker, chunk.seq, topic))
            if (m := _match(text, CALLBACK)):
                out.append(Signal("callback_needed", 0.75, m, chunk.speaker, chunk.seq, topic))

            # cross-sell cue: record it; missed only if agent never acts on it
            for cue_type, phrases in CROSS_SELL_CUES.items():
                if (m := _match(text, phrases)):
                    self.customer_cross_sell_cues.append((cue_type, m, chunk.seq))

        # topic shift
        if topic != "general" and topic != self.last_topic:
            out.append(Signal("topic_shift", 0.55, f"{self.last_topic}->{topic}",
                              chunk.speaker, chunk.seq, topic))
            self.last_topic = topic

        return out

    def missed_and_compliance_at_end(self, last_seq: int) -> list[Signal]:
        """Signals that can only be judged with call context (end-of-window checks)."""
        out: list[Signal] = []
        # Missed cross-sell: customer raised a cue, agent never offered a product after it.
        if self.customer_cross_sell_cues and not self.agent_offered_products:
            cue_type, phrase, seq = self.customer_cross_sell_cues[-1]
            out.append(Signal("missed_cross_sell", 0.72,
                              f"customer mentioned '{phrase}' ({cue_type}); no offer made",
                              "customer", seq, "cross_sell"))
        # Compliance gap: only relevant if the call actually did loan business.
        if self.loan_context_entered:
            missing = set(REQUIRED_DISCLOSURES) - self.disclosures_made
            for disc in ("rate_apr_disclosure", "recording_disclosure"):
                if disc in missing:
                    out.append(Signal("compliance_gap", 0.85,
                                      f"required disclosure missing: {disc}", "agent", last_seq, "compliance"))
        return out

    # ---------------- LLM ----------------
    def _llm(self, chunk: TranscriptChunk, window: list[TranscriptChunk]) -> list[Signal]:
        from openai import OpenAI
        import json

        client = OpenAI(api_key=settings.openai_api_key)
        convo = "\n".join(f"{c.speaker}: {c.text}" for c in window[-6:])
        prompt = (
            "You monitor a live business-loan sales call. From the recent turns, return a JSON "
            "list of signals. Each: {type, confidence (0-1), evidence, speaker}. "
            "Allowed types: missed_cross_sell, compliance_gap, rising_frustration, "
            "payment_difficulty, buying_signal, callback_needed. Return [] if none are clearly "
            f"present (avoid false positives on small talk).\n\nTurns:\n{convo}\n\nJSON:"
        )
        resp = client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1, max_tokens=300,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```(json)?|```$", "", raw).strip()
        try:
            items = json.loads(raw)
        except Exception:
            return []
        out = []
        for it in items:
            if not isinstance(it, dict) or "type" not in it:
                continue
            out.append(Signal(
                type=it["type"], confidence=float(it.get("confidence", 0.6)),
                evidence=str(it.get("evidence", ""))[:120],
                speaker=it.get("speaker", chunk.speaker), seq=chunk.seq,
                topic=_topic_of(chunk.text),
            ))
        return out
