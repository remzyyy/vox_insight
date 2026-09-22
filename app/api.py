"""Unified backend API for the VoxInsight web console.

Exposes all four assessment parts under one FastAPI app:
  Q1  /api/q1/*   business-loan agent (grounded KB answers, eligibility, escalate)
  Q2  /api/q2/*   knowledge-base retrieval + stats
  Q3  /api/q3/*   native-language bot lines
  Q4  /api/q4/*   real-time nudge simulation (+ WebSocket in server.py)

Kept separate from server.py so the app assembly (routers, static, WS) stays clean.
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from shared.config import settings
from q1_voice_agent.grounded_answer import GroundedAnswerer
from q1_voice_agent.eligibility import check_eligibility
from q2_knowledge_base.retriever import Retriever
from q3_native_bots.philippines_bot import PH_BOT
from q3_native_bots.indonesia_bot import ID_BOT
from q4_realtime_nudges.pipeline import CallSession
from q4_realtime_nudges.scenarios import SCENARIOS, get as get_scenario

router = APIRouter(prefix="/api")

# ---- lazy singletons ----
_answerer: GroundedAnswerer | None = None
_retriever: Retriever | None = None


def answerer() -> GroundedAnswerer:
    global _answerer
    if _answerer is None:
        _answerer = GroundedAnswerer()
    return _answerer


def retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


# ===================== Q1 =====================
class Ask(BaseModel):
    question: str


@router.post("/q1/ask")
def q1_ask(a: Ask) -> dict:
    low = a.question.lower()
    if any(w in low for w in ["human", "person", "agent", "representative", "someone"]):
        return {"answer": "Sure, I'll connect you to a specialist now. One moment please.",
                "grounded": True, "citations": [], "kind": "escalation", "confidence": 1.0}
    r = answerer().answer(a.question)
    r["kind"] = "grounded" if r["grounded"] else "fallback"
    return r


@router.get("/q1/eligibility")
def q1_eligibility(revenue: float, vintage: int, score: int) -> dict:
    e = check_eligibility(annual_revenue_lakh=revenue, vintage_months=vintage, credit_score=score)
    return {"verdict": e.verdict, "reasons": e.reasons,
            "products": e.suggested_products, "disclaimer": e.disclaimer}


# ===================== Q2 =====================
@router.get("/q2/stats")
def q2_stats() -> dict:
    r = retriever()
    return {"chunks": r.store.count(), "embed_model": r.embedder.model,
            "openai": settings.has_openai}


@router.get("/q2/search")
def q2_search(q: str, k: int = 3) -> dict:
    ans = retriever().retrieve(q, top_k=k)
    return {
        "query": q,
        "confident": ans.confident,
        "top_score": round(ans.top_score, 3),
        "results": [
            {"score": round(s.score, 3), "title": s.chunk.title,
             "category": s.chunk.category, "source": s.chunk.source,
             "citation": s.chunk.citation(), "snippet": s.chunk.content[:200]}
            for s in ans.results
        ],
    }


# ===================== Q3 =====================
def _market_lines(cfg) -> list[dict]:
    lines = [{"label": "Greeting", "text": cfg.greeting}]
    if len(cfg.flow) > 1:
        lines.append({"label": cfg.flow[1].intent, "text": cfg.flow[1].bot})
    if cfg.objections:
        lines.append({"label": "Objection: " + cfg.objections[0].trigger,
                      "text": cfg.objections[0].response})
    lines.append({"label": "Fallback (in-language)", "text": cfg.fallback_line})
    lines.append({"label": "Escalation (in-language)", "text": cfg.escalation_line})
    return lines


_Q3_LANG = {"philippines": "fil-PH", "indonesia": "id-ID"}


def _q3_cfg(market: str):
    return {"philippines": PH_BOT, "indonesia": ID_BOT}.get(market)


@router.get("/q3/{market}")
def q3(market: str) -> dict:
    cfg = _q3_cfg(market)
    if not cfg:
        return {"error": "unknown market"}
    return {
        "market": market, "lang": _Q3_LANG[market], "sector": cfg.sector,
        "languages": cfg.languages, "lines": _market_lines(cfg),
        "localization_examples": [
            {"situation": e.situation, "literal": e.literal_translation,
             "localized": e.localized, "why": e.why}
            for e in cfg.localization_examples
        ],
    }


def _tokset(s: str) -> set[str]:
    import re
    return set(re.findall(r"[a-z0-9]+", s.lower()))


@router.post("/q3/{market}/ask")
def q3_ask(market: str, a: Ask) -> dict:
    """Match a caller question to this market's FAQs/objections and reply
    in-language. Escalation & unknown questions stay in the local language
    (no unexpected English switch)."""
    cfg = _q3_cfg(market)
    if not cfg:
        return {"error": "unknown market"}
    lang = _Q3_LANG[market]
    q = a.question.strip()
    qtok = _tokset(q)
    low = q.lower()

    # human escalation (multi-lingual triggers)
    esc_triggers = ["human", "person", "agent", "tao", "advisor",
                    "orang", "petugas", "manusia", "wong"]
    if any(w in low for w in esc_triggers):
        return {"answer": cfg.escalation_line, "lang": lang, "kind": "escalation", "matched": None}

    # score FAQs and objections by token overlap
    best = None
    best_score = 0.0
    best_kind = None
    best_label = None
    for f in cfg.faqs:
        s = len(qtok & _tokset(f.question)) / (len(qtok) or 1)
        if s > best_score:
            best, best_score, best_kind, best_label = f.answer, s, "faq", f.question
    for o in cfg.objections:
        s = len(qtok & _tokset(o.trigger)) / (len(qtok) or 1)
        if s > best_score:
            best, best_score, best_kind, best_label = o.response, s, "objection", o.trigger

    if best and best_score >= 0.2:
        return {"answer": best, "lang": lang, "kind": best_kind,
                "matched": best_label, "score": round(best_score, 2)}

    # nothing matched -> in-language fallback (does not invent)
    return {"answer": cfg.fallback_line, "lang": lang, "kind": "fallback",
            "matched": None, "score": round(best_score, 2)}


# ===================== Q4 =====================
_clients: set[WebSocket] = set()
_last_nudges: list[dict] = []
_last_latency: dict = {}


async def _broadcast(msg: dict) -> None:
    import json
    dead = []
    for ws in _clients:
        try:
            await ws.send_text(json.dumps(msg))
        except Exception:
            dead.append(ws)
    for ws in dead:
        _clients.discard(ws)


@router.get("/q4/scenarios")
def q4_scenarios() -> dict:
    return {"scenarios": list(SCENARIOS)}


@router.get("/q4/nudges")
def q4_nudges() -> dict:
    return {"nudges": _last_nudges, "latency": _last_latency}


@router.post("/q4/simulate/{scenario}")
async def q4_simulate(scenario: str, realtime: bool = True) -> dict:
    global _last_nudges, _last_latency
    try:
        turns = get_scenario(scenario)
    except KeyError as e:
        return {"error": str(e)}
    _last_nudges = []
    session = CallSession()

    async def _run():
        global _last_latency
        await _broadcast({"event": "call_started", "scenario": scenario})
        for seq, (speaker, text) in enumerate(turns):
            await _broadcast({"event": "transcript", "speaker": speaker, "text": text, "seq": seq})
            for nudge in await session.add_turn(speaker, text):
                d = nudge.to_dict()
                _last_nudges.append(d)
                await _broadcast({"event": "nudge", "nudge": d})
            if realtime:
                await asyncio.sleep(0.7)
        # post-call checks (missed cross-sell / compliance) with persisted state
        for nudge in session.finalize():
            d = nudge.to_dict()
            _last_nudges.append(d)
            await _broadcast({"event": "nudge", "nudge": d})
        _last_latency = session.tracker.report()
        await _broadcast({"event": "call_ended", "latency": _last_latency})

    asyncio.create_task(_run())
    return {"status": "started", "scenario": scenario}


async def q4_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    _clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _clients.discard(websocket)


# ===================== Recorded Calls (real Vapi calls) =====================
import os as _os

_REC_DIR = "docs/recordings"
_TX_DIR = "docs/transcripts"

# Ordered list of the real recorded calls with their metadata.
_CALLS = [
    ("q1_call1", "Q1 · Cooperative customer", "q1_call1_cooperative.wav", "q1_call1_real.md"),
    ("q1_call2", "Q1 · Objection + conflicting details", "q1_call2_objection.wav", "q1_call2_real.md"),
    ("q1_call3", "Q1 · Out-of-scope + human escalation", "q1_call3_escalation.wav", "q1_call3_real.md"),
    ("q3_ph1", "Q3 PH · Bancassurance cross-sell (Taglish)", "q3_philippines_call1.wav", "q3_philippines_call1_real.md"),
    ("q3_ph2", "Q3 PH · Objection + escalation (Taglish)", "q3_philippines_call2.wav", "q3_philippines_call2_real.md"),
    ("q3_id1", "Q3 ID · Installment reminder (Bahasa)", "q3_indonesia_call1.wav", "q3_indonesia_call1_real.md"),
    ("q3_id2", "Q3 ID · Payment difficulty + escalation (Bahasa)", "q3_indonesia_call2.wav", "q3_indonesia_call2_real.md"),
]


@router.get("/calls")
def calls_list() -> dict:
    out = []
    for cid, title, wav, md in _CALLS:
        out.append({
            "id": cid, "title": title,
            "has_audio": _os.path.exists(_os.path.join(_REC_DIR, wav)),
            "has_transcript": _os.path.exists(_os.path.join(_TX_DIR, md)),
        })
    return {"calls": out}


@router.get("/calls/{cid}/transcript")
def call_transcript(cid: str) -> dict:
    for c in _CALLS:
        if c[0] == cid:
            path = _os.path.join(_TX_DIR, c[3])
            if _os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    return {"id": cid, "title": c[1], "markdown": f.read()}
            return {"error": "transcript not found"}
    return {"error": "unknown call"}


def call_audio_path(cid: str) -> str | None:
    for c in _CALLS:
        if c[0] == cid:
            p = _os.path.join(_REC_DIR, c[2])
            return p if _os.path.exists(p) else None
    return None
