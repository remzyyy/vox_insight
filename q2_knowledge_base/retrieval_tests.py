"""Retrieval testing harness (Q2 requirement: >=5 queries with verdicts).

For each query it prints: user question, top retrieved chunk/record, source
reference, relevance explanation, and a verdict (correct / partially correct /
incorrect) derived from an expected-category/keyword check.

Covers the five required question types: product, policy, qualification, FAQ,
and objection.

    python -m q2_knowledge_base.retrieval_tests
"""
from __future__ import annotations

from dataclasses import dataclass

from .retriever import Retriever


@dataclass
class TestCase:
    kind: str            # product/policy/qualification/faq/objection
    question: str
    expect_category: str
    expect_keywords: list[str]


TEST_CASES: list[TestCase] = [
    TestCase("product", "What is a working capital loan and how much can I borrow?",
             "product", ["working capital", "25 lakh", "operating"]),
    TestCase("policy", "What is the prepayment fee and when can I prepay?",
             "policy", ["prepayment", "6 emis", "3%"]),
    TestCase("qualification", "Do I qualify if my business is 1 year old with 15 lakh revenue?",
             "qualification", ["24 months", "20 lakh", "vintage"]),
    TestCase("faq", "How many days until the loan is disbursed?",
             "faq", ["3 business days", "disbursal", "approval"]),
    TestCase("objection", "Your interest rate seems too high, why should I proceed?",
             "objection", ["risk-based", "credit score", "soft check"]),
    TestCase("policy", "What documents do I need to apply?",
             "policy", ["bank statements", "itr", "gst"]),
]


def _verdict(tc: TestCase, top) -> str:
    if top is None:
        return "incorrect"
    text = (top.chunk.title + " " + top.chunk.content).lower()
    hits = sum(1 for kw in tc.expect_keywords if kw.lower() in text)
    cat_ok = top.chunk.category == tc.expect_category
    if cat_ok and hits >= 2:
        return "correct"
    if cat_ok or hits >= 1:
        return "partially correct"
    return "incorrect"


def run() -> list[tuple[TestCase, str]]:
    r = Retriever()
    if r.store.count() == 0:
        print("KB is empty. Run:  python -m q2_knowledge_base.build_kb")
        return []

    results = []
    print("=" * 78)
    print("Q2 RETRIEVAL TESTS")
    print("=" * 78)
    for i, tc in enumerate(TEST_CASES, 1):
        ans = r.retrieve(tc.question, top_k=3)
        top = ans.results[0] if ans.results else None
        verdict = _verdict(tc, top)
        results.append((tc, verdict))

        print(f"\n[{i}] ({tc.kind}) Q: {tc.question}")
        if top:
            print(f"    Retrieved : {top.chunk.record_id} — {top.chunk.title}")
            print(f"    Source    : {top.chunk.source} (v{top.chunk.version})")
            print(f"    Score     : {top.score:.3f}  confident={ans.confident}")
            print(f"    Snippet   : {top.chunk.content[:140]}...")
            print(f"    Relevance : matched category={top.chunk.category==tc.expect_category}, "
                  f"keyword hits={sum(1 for kw in tc.expect_keywords if kw.lower() in (top.chunk.title+' '+top.chunk.content).lower())}/{len(tc.expect_keywords)}")
        else:
            print("    Retrieved : <none>")
        print(f"    VERDICT   : {verdict.upper()}")

    ok = sum(1 for _, v in results if v == "correct")
    partial = sum(1 for _, v in results if v == "partially correct")
    print("\n" + "-" * 78)
    print(f"Summary: {ok} correct, {partial} partially correct, "
          f"{len(results)-ok-partial} incorrect (of {len(results)})")
    print("-" * 78)
    return results


if __name__ == "__main__":
    run()
