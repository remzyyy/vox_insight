"""FastAPI webhook that Vapi calls for tool/function execution (Q1).

Vapi's assistant is configured (see vapi_assistant.json) with custom tools that
POST here. This backend is the bridge between the voice platform and the Q2
knowledge base, so answers are grounded and never hardcoded in the prompt.

Run:  uvicorn q1_voice_agent.webhook:app --port 8001

Exposed tools:
  - query_knowledge_base : grounded answer from the Q2 KB (+ citations)
  - check_eligibility    : preliminary business-loan eligibility
  - create_lead          : mock CRM lead creation
  - escalate_to_human    : queue a human callback

Also supports a generic /vapi endpoint that dispatches Vapi tool-call payloads,
and a /health check.
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from shared.config import settings
from shared.logging_utils import get_logger
from .crm import Lead, create_lead, escalate, call_summary
from .eligibility import check_eligibility
from .grounded_answer import GroundedAnswerer

log = get_logger("q1.webhook")
app = FastAPI(title="VoxInsight Q1 Voice Agent Webhook")

_answerer: GroundedAnswerer | None = None


def answerer() -> GroundedAnswerer:
    global _answerer
    if _answerer is None:
        _answerer = GroundedAnswerer()
    return _answerer


# ---------- request models ----------
class KBQuery(BaseModel):
    question: str
    category: str | None = None


class EligibilityInput(BaseModel):
    annual_revenue_lakh: float | None = None
    vintage_months: int | None = None
    credit_score: int | None = None
    applicant_age: int | None = None


class LeadInput(BaseModel):
    name: str
    phone: str = ""
    business_type: str = ""
    purpose: str = ""
    revenue_lakh: float | None = None
    vintage_months: int | None = None
    credit_band: str = ""
    eligibility: str = ""


class EscalateInput(BaseModel):
    reason: str
    call_id: str = ""
    notes: str = ""


# ---------- direct tool endpoints (easy to unit-test) ----------
@app.get("/health")
def health() -> dict:
    return {"ok": True, "openai": settings.has_openai}


@app.post("/tools/query_knowledge_base")
def tool_kb(q: KBQuery) -> dict:
    return answerer().answer(q.question, category=q.category)


@app.post("/tools/check_eligibility")
def tool_eligibility(e: EligibilityInput) -> dict:
    r = check_eligibility(
        annual_revenue_lakh=e.annual_revenue_lakh,
        vintage_months=e.vintage_months,
        credit_score=e.credit_score,
        applicant_age=e.applicant_age,
    )
    return {
        "verdict": r.verdict,
        "reasons": r.reasons,
        "suggested_products": r.suggested_products,
        "disclaimer": r.disclaimer,
    }


@app.post("/tools/create_lead")
def tool_lead(inp: LeadInput) -> dict:
    return create_lead(Lead(**inp.model_dump()))


@app.post("/tools/escalate_to_human")
def tool_escalate(inp: EscalateInput) -> dict:
    return escalate(inp.reason, call_id=inp.call_id, notes=inp.notes)


# ---------- Vapi-style dispatcher ----------
def _dispatch(name: str, args: dict[str, Any]) -> dict:
    if name == "query_knowledge_base":
        return answerer().answer(args.get("question", ""), category=args.get("category"))
    if name == "check_eligibility":
        r = check_eligibility(
            annual_revenue_lakh=args.get("annual_revenue_lakh"),
            vintage_months=args.get("vintage_months"),
            credit_score=args.get("credit_score"),
            applicant_age=args.get("applicant_age"),
        )
        return {"verdict": r.verdict, "reasons": r.reasons,
                "suggested_products": r.suggested_products, "disclaimer": r.disclaimer}
    if name == "create_lead":
        return create_lead(Lead(**{k: v for k, v in args.items() if k in Lead.__annotations__}))
    if name == "escalate_to_human":
        return escalate(args.get("reason", "unspecified"),
                        call_id=args.get("call_id", ""), notes=args.get("notes", ""))
    raise HTTPException(status_code=400, detail=f"unknown tool {name}")


@app.post("/vapi")
async def vapi_webhook(payload: dict, x_vapi_secret: str | None = Header(default=None)) -> dict:
    """Handle Vapi tool-call messages.

    Verifies the shared secret and dispatches each tool call. Returns results in
    Vapi's expected {"results": [{"toolCallId", "result"}]} shape.
    """
    if settings.vapi_webhook_secret and x_vapi_secret != settings.vapi_webhook_secret:
        raise HTTPException(status_code=401, detail="bad secret")

    msg = payload.get("message", payload)
    tool_calls = msg.get("toolCalls") or msg.get("tool_calls") or []
    results = []
    for call in tool_calls:
        fn = call.get("function", {})
        name = fn.get("name")
        args = fn.get("arguments", {})
        if isinstance(args, str):
            import json
            try:
                args = json.loads(args)
            except Exception:
                args = {}
        try:
            result = _dispatch(name, args)
        except HTTPException:
            raise
        except Exception as e:  # pragma: no cover
            log.exception("tool %s failed", name)
            result = {"error": str(e)}
        results.append({"toolCallId": call.get("id"), "result": result})
    return {"results": results}
