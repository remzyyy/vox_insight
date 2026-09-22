"""Smoke test the Q1 webhook + tools end-to-end (offline).

    python -m q1_voice_agent.smoke_test
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from shared.config import settings
from .webhook import app

client = TestClient(app)
SECRET = settings.vapi_webhook_secret


def _vapi_call(name: str, args: dict) -> dict:
    payload = {"message": {"toolCalls": [{"id": "t1", "function": {"name": name, "arguments": args}}]}}
    r = client.post("/vapi", json=payload, headers={"x-vapi-secret": SECRET})
    r.raise_for_status()
    return r.json()["results"][0]["result"]


def main() -> None:
    print("health:", client.get("/health").json())

    print("\n[KB] products:", _vapi_call("query_knowledge_base",
          {"question": "How much can I borrow with a working capital loan?"}))
    print("\n[KB] out-of-scope:", _vapi_call("query_knowledge_base",
          {"question": "What's the weather in Paris tomorrow?"}))
    print("\n[KB] objection:", _vapi_call("query_knowledge_base",
          {"question": "Your interest rate is too high", "category": "objection"}))

    print("\n[ELIG] good:", _vapi_call("check_eligibility",
          {"annual_revenue_lakh": 40, "vintage_months": 36, "credit_score": 760}))
    print("\n[ELIG] fail:", _vapi_call("check_eligibility",
          {"annual_revenue_lakh": 15, "vintage_months": 12, "credit_score": 620}))

    print("\n[LEAD]:", _vapi_call("create_lead",
          {"name": "Test Business", "phone": "9990001111", "business_type": "retail",
           "purpose": "inventory", "revenue_lakh": 40, "vintage_months": 36,
           "credit_band": "760+", "eligibility": "likely_eligible"}))

    print("\n[ESCALATE]:", _vapi_call("escalate_to_human",
          {"reason": "caller requested a human", "call_id": "call_demo_1"}))

    # bad secret should 401
    bad = client.post("/vapi", json={"message": {"toolCalls": []}},
                      headers={"x-vapi-secret": "wrong"})
    print("\nbad-secret status:", bad.status_code)
    print("\nALL SMOKE CHECKS DONE")


if __name__ == "__main__":
    main()
