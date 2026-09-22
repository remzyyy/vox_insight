"""VoxInsight unified web console — all four parts in one app.

Serves a landing page + one page per question, the unified API, and the Q4
WebSocket. This is the single entry point for the whole demo.

Run:
    uvicorn app.main:app --port 8080
Open:
    http://localhost:8080/
"""
from __future__ import annotations

import os

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import router, q4_ws, call_audio_path

app = FastAPI(title="VoxInsight Console")
app.include_router(router)

_STATIC = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=_STATIC), name="static")


def _page(name: str) -> FileResponse:
    return FileResponse(os.path.join(_STATIC, name))


@app.get("/")
def home():
    return _page("index.html")


@app.get("/q1")
def q1_page():
    return _page("q1.html")


@app.get("/q2")
def q2_page():
    return _page("q2.html")


@app.get("/q3")
def q3_page():
    return _page("q3.html")


@app.get("/q4")
def q4_page():
    return _page("q4.html")


@app.get("/calls")
def calls_page():
    return _page("calls.html")


@app.get("/api/calls/{cid}/audio")
def call_audio(cid: str):
    path = call_audio_path(cid)
    if not path:
        raise HTTPException(status_code=404, detail="audio not found")
    return FileResponse(path, media_type="audio/wav")


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await q4_ws(websocket)
