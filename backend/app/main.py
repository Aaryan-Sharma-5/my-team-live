import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .ingest import load_match
from .replay import build_replay
from .scoring import RULES

app = FastAPI(title="My Team Live")
DATA = Path(__file__).resolve().parents[1] / "data"


class Team(BaseModel):
    xi: list[str]
    captain: str
    vice_captain: str


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


DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
