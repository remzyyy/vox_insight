"""Core data models for the real-time nudge pipeline (Q4)."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


@dataclass
class TranscriptChunk:
    """One transcribed utterance from streaming ASR."""
    seq: int
    speaker: str            # "agent" | "customer"
    text: str
    t_audio_received: float  # monotonic time the audio chunk arrived
    t_transcribed: float     # monotonic time ASR produced text


@dataclass
class Signal:
    """A detected signal from the conversation."""
    type: str               # missed_cross_sell | compliance_gap | rising_frustration | payment_difficulty | buying_signal | callback_needed | topic_shift
    confidence: float       # 0..1
    evidence: str           # the phrase/reason
    speaker: str
    seq: int
    topic: str = "general"


PRIORITY = {
    "compliance_gap": 1,        # highest — regulatory
    "rising_frustration": 2,
    "payment_difficulty": 2,
    "missed_cross_sell": 3,
    "buying_signal": 3,
    "callback_needed": 3,
    "topic_shift": 4,
}


@dataclass
class Nudge:
    """An actionable recommendation shown to the agent."""
    signal_type: str
    text: str
    priority: int
    confidence: float
    topic: str
    nudge_id: str = field(default_factory=lambda: "n_" + uuid.uuid4().hex[:8])
    created_at: float = field(default_factory=time.monotonic)
    expires_at: float = 0.0
    latency_ms: dict = field(default_factory=dict)  # component -> ms

    def to_dict(self) -> dict:
        return {
            "nudge_id": self.nudge_id,
            "signal_type": self.signal_type,
            "text": self.text,
            "priority": self.priority,
            "confidence": round(self.confidence, 2),
            "topic": self.topic,
            "latency_ms": self.latency_ms,
        }
