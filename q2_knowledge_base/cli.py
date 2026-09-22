"""Simple interactive retrieval interface (Q2).

    python -m q2_knowledge_base.cli "what is the interest rate?"
    python -m q2_knowledge_base.cli          # interactive loop
"""
from __future__ import annotations

import sys

from .retriever import Retriever


def answer(query: str, r: Retriever) -> None:
    ans = r.retrieve(query, top_k=3)
    print(f"\nQ: {query}")
    if not ans.confident:
        print("  (low confidence — a voice agent would fall back / escalate here)")
    for i, sc in enumerate(ans.results, 1):
        print(f"  [{i}] {sc.score:.3f} {sc.chunk.title}")
        print(f"      {sc.chunk.content[:160]}")
        print(f"      cite: {sc.chunk.citation()}")


def main() -> None:
    r = Retriever()
    if r.store.count() == 0:
        print("KB empty. Run: python -m q2_knowledge_base.build_kb")
        return
    if len(sys.argv) > 1:
        answer(" ".join(sys.argv[1:]), r)
        return
    print("KB retrieval CLI. Type a question (blank to quit).")
    while True:
        try:
            q = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            break
        answer(q, r)


if __name__ == "__main__":
    main()
