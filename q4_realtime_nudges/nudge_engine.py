"""Nudge generation + control (Q4).

Turns signals into short actionable nudges and applies quality controls so the
agent is not spammed:

  - confidence threshold : drop low-confidence signals
  - duplicate suppression: same signal_type+topic not repeated while active
  - cooldown             : per signal_type minimum gap between nudges
  - topic grouping       : nudges tagged with topic; dedup is topic-aware
  - priority             : compliance > frustration/payment > cross-sell > topic
  - expiry               : nudges auto-expire so stale advice disappears

These controls are the main defense against the "excessive low-value alerts"
rejection condition.
"""
from __future__ import annotations

import time

from shared.logging_utils import get_logger
from .models import Nudge, PRIORITY, Signal

log = get_logger("q4.nudge")

# Short, actionable templates keyed by signal type.
TEMPLATES = {
    "missed_cross_sell": "Missed opportunity: {evidence}. Offer a matching product now.",
    "compliance_gap": "Compliance: {evidence}. State it before proceeding.",
    "rising_frustration": "Customer frustration rising. Acknowledge the concern before continuing.",
    "payment_difficulty": "Payment difficulty signaled. Offer an approved payment-support or callback path.",
    "buying_signal": "Buying signal. Move to next step and confirm details.",
    "callback_needed": "Customer wants a callback. Offer to schedule one now.",
    "topic_shift": "Topic shifted to {topic}. Make sure the previous point was resolved.",
}

# Per-type minimum seconds between nudges of the same type.
COOLDOWN_S = {
    "compliance_gap": 20.0,
    "rising_frustration": 15.0,
    "payment_difficulty": 20.0,
    "missed_cross_sell": 25.0,
    "buying_signal": 15.0,
    "callback_needed": 20.0,
    "topic_shift": 30.0,
}

# Confidence gate per type (compliance is important, so lower gate).
CONF_THRESHOLD = {
    "compliance_gap": 0.6,
    "rising_frustration": 0.65,
    "payment_difficulty": 0.6,
    "missed_cross_sell": 0.6,
    "buying_signal": 0.6,
    "callback_needed": 0.6,
    "topic_shift": 0.9,   # high gate: topic shifts rarely need a nudge (noise control)
}

DEFAULT_EXPIRY_S = 30.0


class NudgeEngine:
    def __init__(self, *, clock=time.monotonic) -> None:
        self._clock = clock
        self._last_emit: dict[str, float] = {}          # type -> last emit time
        self._active: dict[tuple[str, str], Nudge] = {}  # (type, topic) -> nudge

    def _expire(self) -> None:
        now = self._clock()
        dead = [k for k, n in self._active.items() if n.expires_at and n.expires_at <= now]
        for k in dead:
            del self._active[k]

    def consider(self, signal: Signal) -> Nudge | None:
        self._expire()
        now = self._clock()

        # 1. confidence threshold
        gate = CONF_THRESHOLD.get(signal.type, 0.6)
        if signal.confidence < gate:
            return None

        key = (signal.type, signal.topic)

        # 2. duplicate suppression (same type+topic still active)
        if key in self._active:
            return None

        # 3. cooldown
        cd = COOLDOWN_S.get(signal.type, 20.0)
        last = self._last_emit.get(signal.type)
        if last is not None and (now - last) < cd:
            return None

        # build nudge
        text = TEMPLATES.get(signal.type, "{evidence}").format(
            evidence=signal.evidence, topic=signal.topic
        )
        nudge = Nudge(
            signal_type=signal.type,
            text=text,
            priority=PRIORITY.get(signal.type, 5),
            confidence=signal.confidence,
            topic=signal.topic,
        )
        nudge.expires_at = now + DEFAULT_EXPIRY_S
        self._active[key] = nudge
        self._last_emit[signal.type] = now
        log.info("NUDGE[p%d] %s: %s", nudge.priority, nudge.signal_type, nudge.text)
        return nudge
