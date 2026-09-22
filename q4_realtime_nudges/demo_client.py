"""Live demo client for the running Q4 server (talks to http://localhost:8004).

Triggers a scenario, then reads nudges + latency from the polling API. Useful
for a terminal demo without opening the browser dashboard.

    python -m q4_realtime_nudges.demo_client compliance
"""
from __future__ import annotations

import json
import sys
import time

import httpx

BASE = "http://localhost:8004"


def main() -> None:
    scenario = sys.argv[1] if len(sys.argv) > 1 else "missed_cross_sell"

    print("1) Scenarios available:")
    print("  ", httpx.get(f"{BASE}/scenarios").json())

    print(f"\n2) Triggering live call: {scenario}")
    print("  ", httpx.post(f"{BASE}/simulate/{scenario}?realtime=false").json())

    time.sleep(2)

    print("\n3) Nudges produced (polling API /nudges):")
    nudges = httpx.get(f"{BASE}/nudges").json()["nudges"]
    if not nudges:
        print("   (no nudges - correct for a noisy/ambiguous call)")
    for n in nudges:
        print(f"   [P{n['priority']}] {n['signal_type']} "
              f"(conf {n['confidence']}) -> {n['text']}")

    print("\n4) Latency report (/latency, P50/P95 per component):")
    print(json.dumps(httpx.get(f"{BASE}/latency").json(), indent=2))


if __name__ == "__main__":
    main()
