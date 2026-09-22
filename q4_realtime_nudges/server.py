"""Real-time nudge server: WebSocket + polling API + live dashboard (Q4).

Run:  uvicorn q4_realtime_nudges.server:app --port 8004
Then open http://localhost:8004/ and click a scenario, or connect a WS client.

Endpoints:
  GET  /                       -> minimal live dashboard (HTML)
  WS   /ws                     -> stream nudges as JSON as they are produced
  POST /simulate/{scenario}    -> start a scenario streaming to all WS clients
  GET  /nudges                 -> polling API: nudges from the last run
  GET  /latency                -> latency report from the last run
  GET  /scenarios              -> list scenario names
"""
from __future__ import annotations

import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from shared.logging_utils import get_logger
from .latency import LatencyTracker
from .pipeline import stream_call
from .scenarios import SCENARIOS, get

log = get_logger("q4.server")
app = FastAPI(title="VoxInsight Q4 Real-time Nudges")

_clients: set[WebSocket] = set()
_last_nudges: list[dict] = []
_last_latency: dict = {}


async def _broadcast(msg: dict) -> None:
    dead = []
    for ws in _clients:
        try:
            await ws.send_text(json.dumps(msg))
        except Exception:
            dead.append(ws)
    for ws in dead:
        _clients.discard(ws)


@app.get("/scenarios")
def scenarios() -> dict:
    return {"scenarios": list(SCENARIOS)}


@app.get("/nudges")
def nudges() -> dict:
    """Polling API for the most recent run's nudges."""
    return {"nudges": _last_nudges}


@app.get("/latency")
def latency() -> dict:
    return _last_latency


@app.post("/simulate/{scenario}")
async def simulate(scenario: str, realtime: bool = True) -> dict:
    global _last_nudges, _last_latency
    try:
        turns = get(scenario)
    except KeyError as e:
        return {"error": str(e)}

    _last_nudges = []
    tracker = LatencyTracker()

    async def _run():
        global _last_latency
        await _broadcast({"event": "call_started", "scenario": scenario})
        async for nudge in stream_call(turns, realtime=realtime, tracker=tracker):
            d = nudge.to_dict()
            _last_nudges.append(d)
            await _broadcast({"event": "nudge", "nudge": d})
        _last_latency = tracker.report()
        await _broadcast({"event": "call_ended", "latency": _last_latency})

    asyncio.create_task(_run())
    return {"status": "started", "scenario": scenario}


@app.websocket("/ws")
async def ws(websocket: WebSocket) -> None:
    await websocket.accept()
    _clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # keepalive / ignore client msgs
    except WebSocketDisconnect:
        _clients.discard(websocket)


DASHBOARD = """<!doctype html><html><head><meta charset="utf-8">
<title>VoxInsight — Live Nudges</title>
<style>
 body{font-family:system-ui,Arial;margin:24px;background:#0f1420;color:#e6e9ef}
 h1{font-size:20px} .row{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
 button{background:#2b6cb0;color:#fff;border:0;padding:8px 12px;border-radius:6px;cursor:pointer}
 #nudges{margin-top:16px} .n{border-left:4px solid #888;background:#1a2233;padding:10px 12px;margin:8px 0;border-radius:4px}
 .p1{border-color:#e53e3e}.p2{border-color:#dd6b20}.p3{border-color:#38a169}.p4{border-color:#718096}
 .meta{color:#9fb0c8;font-size:12px} .status{color:#9fb0c8;font-size:13px}
</style></head><body>
<h1>VoxInsight — Live Call Nudges (Q4)</h1>
<div class="row" id="buttons"></div>
<div class="status" id="status">connecting…</div>
<div id="nudges"></div>
<script>
 const ws=new WebSocket(`ws://${location.host}/ws`);
 const st=document.getElementById('status'); const box=document.getElementById('nudges');
 ws.onopen=()=>st.textContent='connected — pick a scenario';
 ws.onmessage=(e)=>{const m=JSON.parse(e.data);
   if(m.event==='call_started'){box.innerHTML='';st.textContent='call started: '+m.scenario;}
   else if(m.event==='nudge'){const n=m.nudge;const d=document.createElement('div');
     d.className='n p'+n.priority;
     d.innerHTML=`<b>[P${n.priority}] ${n.signal_type}</b> — ${n.text}
       <div class="meta">confidence ${n.confidence} · topic ${n.topic} · latency ${JSON.stringify(n.latency_ms)}</div>`;
     box.appendChild(d);}
   else if(m.event==='call_ended'){st.textContent='call ended · latency '+JSON.stringify(m.latency);}
 };
 fetch('/scenarios').then(r=>r.json()).then(d=>{const b=document.getElementById('buttons');
   d.scenarios.forEach(s=>{const btn=document.createElement('button');btn.textContent=s;
     btn.onclick=()=>fetch('/simulate/'+s,{method:'POST'});b.appendChild(btn);});});
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD
