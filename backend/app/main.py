import json
import os
import ipaddress
import time
from threading import Lock
from functools import lru_cache
from collections import defaultdict, deque
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from .ingest import load_match
from .replay import build_replay
from .scoring import RULES
from .narrate import configured, narrate, cached_narration
from .facts import narration_facts

app = FastAPI(title="My Team Live")
origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
if origins:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
DATA = Path(__file__).resolve().parents[1] / "data"


class Team(BaseModel):
    model_config = ConfigDict(extra='forbid')
    xi: list[str] = Field(min_length=11, max_length=11)
    captain: str = Field(max_length=100)
    vice_captain: str = Field(max_length=100)


class Narration(BaseModel):
    model_config = ConfigDict(extra='forbid')
    team: Team
    seq: int = Field(ge=0, le=10000, strict=True)


@app.get("/api/match")
def match():
    info = load_match()["info"]
    return {key: info[key] for key in ("teams", "players", "dates", "venue", "event", "outcome")}


@app.get("/api/rules")
def rules():
    return RULES


@app.get("/api/default-team")
def default_team():
    return json.loads((DATA / "default_xi.json").read_text(encoding="utf-8"))


def validate_team(team: Team):
    pool = {p for players in load_match()["info"]["players"].values() for p in players}
    if len(team.xi) != 11 or len(set(team.xi)) != 11 or not set(team.xi) <= pool:
        raise HTTPException(422, "Select exactly 11 distinct players from this match.")
    if team.captain not in team.xi or team.vice_captain not in team.xi or team.captain == team.vice_captain:
        raise HTTPException(422, "Captain and vice-captain must be different players in your XI.")


@lru_cache(maxsize=32)
def cached_replay(xi, captain, vice_captain):
    return build_replay(list(xi), captain, vice_captain)


@app.post("/api/replay")
def replay(team: Team):
    validate_team(team)
    return cached_replay(tuple(team.xi), team.captain, team.vice_captain)


@app.get("/api/health")
def health():
    return {"ai_configured": configured()}


RATE = defaultdict(deque)
RATE_LOCK = Lock()
LIMIT = 120


def client_ip(request):
    # Render documents that Cloudflare overwrites this header at its edge.
    # Never trust a client-supplied forwarded chain in local deployments.
    candidate = request.headers.get("cf-connecting-ip", "") if os.getenv("RENDER") else ""
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return request.client.host if request.client else "unknown"


@app.post("/api/narrate")
def narration(body: Narration, request: Request):
    validate_team(body.team)
    timeline = cached_replay(tuple(body.team.xi), body.team.captain, body.team.vice_captain)['items']
    if body.seq >= len(timeline):
        raise HTTPException(422, "Delivery does not exist in this match.")
    item = timeline[body.seq]
    facts = narration_facts(item, body.team)
    fallback = {"text": item['template_text'], "source": "template"}
    if not configured() or not item['relevant'] or sum(d['final_points'] for d in item['deltas']) == 0 or item['tag'] not in {"boundary", "wicket", "milestone", "captain", "danger"}:
        return fallback
    cached = cached_narration(facts)
    if cached:
        return cached
    now = time.monotonic()
    ip = client_ip(request)
    with RATE_LOCK:
        timestamps = RATE[ip]
        while timestamps and now - timestamps[0] >= 60:
            timestamps.popleft()
        if len(timestamps) >= LIMIT:
            return fallback
        timestamps.append(now)
        if len(RATE) > 2000:
            for key in list(RATE):
                if not RATE[key] or now - RATE[key][-1] >= 60:
                    del RATE[key]
    return narrate(facts, item['template_text'])


DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
