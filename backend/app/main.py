import json
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .ingest import load_match
from .replay import build_replay
from .scoring import RULES
from .narrate import configured, narrate

app = FastAPI(title="My Team Live")
origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
if origins:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
DATA = Path(__file__).resolve().parents[1] / "data"


class Team(BaseModel):
    xi: list[str]
    captain: str
    vice_captain: str


class Narration(BaseModel):
    facts: dict
    template_text: str


@app.get("/api/match")
def match():
    info = load_match()["info"]
    return {key: info[key] for key in ("teams", "players", "dates", "venue", "event")}


@app.get("/api/rules")
def rules():
    return RULES


@app.get("/api/default-team")
def default_team():
    return json.loads((DATA / "default_xi.json").read_text(encoding="utf-8"))


@app.post("/api/replay")
def replay(team: Team):
    pool = {p for players in load_match()["info"]["players"].values() for p in players}
    if len(team.xi) != 11 or len(set(team.xi)) != 11 or not set(team.xi) <= pool:
        raise HTTPException(422, "Select exactly 11 distinct players from this match.")
    if team.captain not in team.xi or team.vice_captain not in team.xi or team.captain == team.vice_captain:
        raise HTTPException(422, "Captain and vice-captain must be different players in your XI.")
    return build_replay(team.xi, team.captain, team.vice_captain)


@app.get("/api/health")
def health():
    return {"ai_configured": configured()}


RATE = defaultdict(deque)
@app.post("/api/narrate")
def narration(body: Narration, request: Request):
    fallback = {"text": body.template_text, "source": "template"}
    if not configured() or body.facts.get("tag") not in {"boundary", "wicket", "milestone", "captain", "danger"}:
        return fallback
    now = time.monotonic()
    ip = request.client.host if request.client else "unknown"
    timestamps = RATE[ip]
    while timestamps and now - timestamps[0] > 60:
        timestamps.popleft()
    if len(timestamps) >= 30:
        return fallback
    timestamps.append(now)
    return narrate(body.facts, body.template_text)


DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
