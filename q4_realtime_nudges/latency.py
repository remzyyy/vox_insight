"""Latency tracking with P50/P95 reporting per component (Q4).

Measures the end-to-end path: audio received -> transcription -> signal
detection -> nudge generation -> display, plus per-component timings for ASR,
signal extraction, LLM, and delivery.
"""
from __future__ import annotations

from dataclasses import dataclass, field


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    frac = k - lo
    return s[lo] * (1 - frac) + s[hi] * frac


@dataclass
class LatencyTracker:
    samples: dict[str, list[float]] = field(default_factory=dict)

    def record(self, component: str, ms: float) -> None:
        self.samples.setdefault(component, []).append(ms)

    def report(self) -> dict:
        out = {}
        for comp, vals in self.samples.items():
            out[comp] = {
                "count": len(vals),
                "p50_ms": round(_percentile(vals, 0.50), 1),
                "p95_ms": round(_percentile(vals, 0.95), 1),
                "max_ms": round(max(vals), 1) if vals else 0.0,
            }
        return out

    def pretty(self) -> str:
        rep = self.report()
        lines = ["Component          count   p50(ms)  p95(ms)  max(ms)"]
        for comp in ["asr", "signal_extraction", "llm", "delivery", "end_to_end"]:
            if comp in rep:
                r = rep[comp]
                lines.append(f"{comp:<18} {r['count']:>5}  {r['p50_ms']:>8} {r['p95_ms']:>8} {r['max_ms']:>8}")
        return "\n".join(lines)
