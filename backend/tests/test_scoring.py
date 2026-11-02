from backend.app.scoring import score_event
import pytest
from fastapi import HTTPException
from backend.app.main import default_team, replay, Team
from backend.app.replay import build_replay


def event(**changes):
    base = dict(batter="A", bowler="B", runs_batter=0, extra_type=None, is_four=False, is_six=False, wicket=None)
    return {**base, **changes}


def state():
    return {"runs": {}, "wickets": {}, "faced": set(), "totals": {"A": 0, "B": 0, "C": 0}}


def score(e, s):
    return score_event(e, s, ["A", "B", "C"], "A", "B")


def test_multipliers_and_milestone():
    s = state()
    assert sum(d["final_points"] for d in score(event(runs_batter=4, is_four=True), s)) == 10
    s["runs"]["A"] = 29
    result = score(event(runs_batter=2), s)
    assert sum(d["final_points"] for d in result) == 12
    s["runs"]["A"] = 31
    assert not any(d["reason_code"] == "30_runs" for d in score(event(runs_batter=1), s))


def test_runout_no_bowler_wicket_and_duck():
    s = state()
    ds = score(event(wicket={"kind": "run out", "player_out": "A", "fielders": ["C"]}), s)
    assert [(d["player"], d["final_points"]) for d in ds] == [("A", -4), ("C", 10)]
    assert not s["wickets"]


def test_full_replay_deterministic_and_sums():
    t = default_team()
    one = build_replay(**t)
    assert one == build_replay(**t)
    assert one["final"]["team_total"] == sum(d["final_points"] for item in one["items"] for d in item["deltas"])
    # Hand checks from the scorecard: Jadeja 15 runs, one four, one six,
    # one wicket; Sudharsan 96, eight fours, six sixes; Conway 47, four
    # fours, two sixes. The first two have C/VC multipliers.
    assert one["final"]["player_totals"]["RA Jadeja"] == (15 + 1 + 2 + 25) * 2
    assert one["final"]["player_totals"]["B Sai Sudharsan"] == (96 + 8 + 12 + 4 + 8) * 1.5
    assert one["final"]["player_totals"]["DP Conway"] == 47 + 4 + 4 + 4


def test_invalid_team():
    t = default_team()
    t["xi"] = t["xi"][:10]
    with pytest.raises(HTTPException) as exc:
        replay(Team(**t))
    assert exc.value.status_code == 422
