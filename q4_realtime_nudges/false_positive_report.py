"""Approximate false-positive analysis for the nudge pipeline (Q4).

Runs every scenario and compares fired nudges against expected nudges. Reports
per-scenario precision (are fired nudges wanted?) and a global false-positive
rate. The 'noisy' scenario is the key control: it should fire zero nudges.

    python -m q4_realtime_nudges.false_positive_report
"""
from __future__ import annotations

import asyncio

from .pipeline import run_and_collect
from .scenarios import get

# Expected nudge types per scenario (what a good agent-assist SHOULD surface).
EXPECTED: dict[str, set[str]] = {
    "missed_cross_sell": {"missed_cross_sell", "compliance_gap"},
    "compliance": {"compliance_gap", "buying_signal"},
    "frustration": {"rising_frustration"},
    "payment_difficulty": {"payment_difficulty", "compliance_gap"},
    "noisy": set(),  # control: no nudges expected
}


async def main_async() -> None:
    total_fired = 0
    total_fp = 0
    print("=" * 72)
    print("Q4 FALSE-POSITIVE ANALYSIS")
    print("=" * 72)
    for name, expected in EXPECTED.items():
        nudges, _ = await run_and_collect(get(name), realtime=False)
        fired = [n.signal_type for n in nudges]
        fp = [t for t in fired if t not in expected]
        tp = [t for t in fired if t in expected]
        total_fired += len(fired)
        total_fp += len(fp)
        precision = (len(tp) / len(fired)) if fired else 1.0
        status = "OK" if not fp else "FALSE POSITIVE"
        print(f"\n[{name}] {status}")
        print(f"  expected : {sorted(expected) or '(none)'}")
        print(f"  fired    : {fired or '(none)'}")
        print(f"  false-pos: {fp or '(none)'}")
        print(f"  precision: {precision:.2f}")

    fp_rate = (total_fp / total_fired) if total_fired else 0.0
    print("\n" + "-" * 72)
    print(f"Global: {total_fired} nudges fired, {total_fp} false positives "
          f"-> approx FP rate {fp_rate:.1%}")
    print("-" * 72)


if __name__ == "__main__":
    asyncio.run(main_async())
