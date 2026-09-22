"""Real-time streaming pipeline (Q4): ASR sim -> signals -> nudges -> delivery.

`stream_call` is an async generator that replays a scenario at real-time speed,
simulating streaming ASR (with agent/customer separation), extracts signals per
chunk, runs the nudge engine, and yields nudges as they are produced. It records
component and end-to-end latency for every processed chunk.

The ASR is *simulated* (we already have speaker-labeled text) so the pipeline is
runnable offline; the timing model adds a realistic per-chunk ASR latency so the
latency report is meaningful. Swap `_simulate_asr` for a real streaming ASR
client (e.g. Deepgram live) in production.
"""
from __future__ import annotations

import asyncio
import time

from shared.logging_utils import get_logger
from .latency import LatencyTracker
from .models import Nudge, TranscriptChunk
from .nudge_engine import NudgeEngine
from .signals import SignalExtractor

log = get_logger("q4.pipeline")

# Simulated timing (seconds).
CHUNK_INTERVAL = 0.8      # gap between utterances during real-time replay
ASR_LATENCY = 0.12        # simulated ASR processing latency per chunk


async def _simulate_asr(speaker: str, text: str) -> tuple[float, float]:
    """Return (t_audio_received, t_transcribed) using a realistic ASR delay."""
    t_recv = time.monotonic()
    await asyncio.sleep(ASR_LATENCY)
    return t_recv, time.monotonic()


async def stream_call(
    turns: list[tuple[str, str]],
    *,
    use_llm: bool | None = None,
    realtime: bool = True,
    tracker: LatencyTracker | None = None,
):
    """Async generator yielding Nudge objects as the call streams."""
    tracker = tracker or LatencyTracker()
    extractor = SignalExtractor(use_llm=use_llm)
    engine = NudgeEngine()
    window: list[TranscriptChunk] = []

    for seq, (speaker, text) in enumerate(turns):
        if realtime:
            await asyncio.sleep(CHUNK_INTERVAL)

        # --- ASR ---
        t_recv, t_trans = await _simulate_asr(speaker, text)
        tracker.record("asr", (t_trans - t_recv) * 1000)
        chunk = TranscriptChunk(seq=seq, speaker=speaker, text=text,
                                t_audio_received=t_recv, t_transcribed=t_trans)
        window.append(chunk)
        extractor.update_state(chunk)

        # --- signal extraction ---
        t0 = time.monotonic()
        signals = extractor.extract(chunk, window)
        t_sig = time.monotonic()
        tracker.record("signal_extraction", (t_sig - t0) * 1000)

        # --- nudge generation + delivery ---
        for sig in signals:
            t_llm0 = time.monotonic()
            nudge = engine.consider(sig)
            t_llm = time.monotonic()
            tracker.record("llm", (t_llm - t_llm0) * 1000)  # nudge compose step
            if nudge:
                t_deliver = time.monotonic()
                tracker.record("delivery", (t_deliver - t_llm) * 1000)
                # end-to-end: audio received -> nudge ready
                e2e = (t_deliver - chunk.t_audio_received) * 1000
                tracker.record("end_to_end", e2e)
                nudge.latency_ms = {
                    "asr": round((t_trans - t_recv) * 1000, 1),
                    "signal_extraction": round((t_sig - t0) * 1000, 1),
                    "nudge": round((t_llm - t_llm0) * 1000, 1),
                    "end_to_end": round(e2e, 1),
                }
                yield nudge

    # end-of-call checks (missed cross-sell / compliance gaps)
    t0 = time.monotonic()
    for sig in extractor.missed_and_compliance_at_end(len(turns) - 1):
        tracker.record("signal_extraction", (time.monotonic() - t0) * 1000)
        nudge = engine.consider(sig)
        if nudge:
            nudge.latency_ms = {"post_call_check": True}
            yield nudge


class CallSession:
    """Stateful driver: feed one turn at a time, keep a single extractor/engine.

    Lets a web app stream a transcript turn-by-turn (showing the conversation
    live) while cross-turn signals (missed cross-sell, compliance gaps) are still
    detected correctly, because state persists across turns.
    """

    def __init__(self, *, use_llm: bool | None = None,
                 tracker: LatencyTracker | None = None) -> None:
        self.tracker = tracker or LatencyTracker()
        self.extractor = SignalExtractor(use_llm=use_llm)
        self.engine = NudgeEngine()
        self.window: list[TranscriptChunk] = []
        self._seq = 0

    async def add_turn(self, speaker: str, text: str) -> list[Nudge]:
        seq = self._seq
        self._seq += 1
        t_recv, t_trans = await _simulate_asr(speaker, text)
        self.tracker.record("asr", (t_trans - t_recv) * 1000)
        chunk = TranscriptChunk(seq=seq, speaker=speaker, text=text,
                                t_audio_received=t_recv, t_transcribed=t_trans)
        self.window.append(chunk)
        self.extractor.update_state(chunk)

        t0 = time.monotonic()
        signals = self.extractor.extract(chunk, self.window)
        t_sig = time.monotonic()
        self.tracker.record("signal_extraction", (t_sig - t0) * 1000)

        out: list[Nudge] = []
        for sig in signals:
            t_n0 = time.monotonic()
            nudge = self.engine.consider(sig)
            t_n = time.monotonic()
            self.tracker.record("llm", (t_n - t_n0) * 1000)
            if nudge:
                self.tracker.record("delivery", (time.monotonic() - t_n) * 1000)
                e2e = (time.monotonic() - chunk.t_audio_received) * 1000
                self.tracker.record("end_to_end", e2e)
                nudge.latency_ms = {
                    "asr": round((t_trans - t_recv) * 1000, 1),
                    "signal_extraction": round((t_sig - t0) * 1000, 1),
                    "end_to_end": round(e2e, 1),
                }
                out.append(nudge)
        return out

    def finalize(self) -> list[Nudge]:
        """Post-call checks (missed cross-sell / compliance gaps)."""
        out: list[Nudge] = []
        for sig in self.extractor.missed_and_compliance_at_end(max(self._seq - 1, 0)):
            nudge = self.engine.consider(sig)
            if nudge:
                nudge.latency_ms = {"post_call_check": True}
                out.append(nudge)
        return out


async def run_and_collect(
    turns: list[tuple[str, str]], *, use_llm=None, realtime=False
) -> tuple[list[Nudge], LatencyTracker]:
    """Convenience: run a scenario to completion, return (nudges, tracker)."""
    tracker = LatencyTracker()
    nudges: list[Nudge] = []
    async for n in stream_call(turns, use_llm=use_llm, realtime=realtime, tracker=tracker):
        nudges.append(n)
    return nudges, tracker
