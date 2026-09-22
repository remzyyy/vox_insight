"""Run a scenario through the Q4 pipeline and print nudges + latency (CLI).

    python -m q4_realtime_nudges.simulate --scenario missed_cross_sell
    python -m q4_realtime_nudges.simulate --scenario all --fast
"""
from __future__ import annotations

import argparse
import asyncio

from .latency import LatencyTracker
from .pipeline import stream_call
from .scenarios import SCENARIOS, get


async def run_one(name: str, *, realtime: bool) -> None:
    turns = get(name)
    tracker = LatencyTracker()
    print("\n" + "=" * 70)
    print(f"SCENARIO: {name}  ({len(turns)} turns, realtime={realtime})")
    print("=" * 70)
    count = 0
    async for nudge in stream_call(turns, realtime=realtime, tracker=tracker):
        count += 1
        d = nudge.to_dict()
        print(f"  -> [P{d['priority']}] {d['signal_type']} (conf {d['confidence']}): {d['text']}")
    if count == 0:
        print("  (no nudges - correct for a noisy/ambiguous call)")
    print(f"\nTotal nudges: {count}")
    print(tracker.pretty())


async def main_async(args) -> None:
    names = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    for n in names:
        await run_one(n, realtime=not args.fast)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="missed_cross_sell",
                    help="scenario name or 'all'")
    ap.add_argument("--fast", action="store_true",
                    help="skip real-time delays (faster for testing)")
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
