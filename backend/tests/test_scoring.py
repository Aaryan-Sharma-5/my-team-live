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


def test_vice_captain_six_and_50_100_milestones():
    s = state()
    for before, expected in ((49, 8), (99, 16)):
        s["runs"]["B"] = before
        ds = score_event(event(batter="B", bowler="A", runs_batter=6, is_six=True), s, ["A", "B", "C"], "A", "B")
        assert sum(d["final_points"] for d in ds) == (6 + 2 + expected) * 1.5


@pytest.mark.parametrize("kind,bonus", [("bowled", 8), ("lbw", 8), ("caught", 0)])
def test_bowler_wicket_and_haul(kind, bonus):
    s = state()
    s["wickets"]["B"] = 2
    ds = score(event(wicket={"kind": kind, "player_out": "A", "fielders": ["C"] if kind == "caught" else []}), s)
    bowler = sum(d["final_points"] for d in ds if d["player"] == "B")
    assert bowler == (25 + bonus + 4) * 1.5
    if kind == "caught":
        assert any(d["reason_code"] == "catch" and d["player"] == "C" for d in ds)
    s["wickets"]["B"] = 4
    ds = score(event(wicket={"kind": kind, "player_out": "A", "fielders": []}), s)
    assert any(d["reason_code"] == "5_wickets" for d in ds)


def test_wide_and_retired_hurt_do_not_create_duck():
    s = state()
    assert not score(event(extra_type="wide", wicket={"kind":"run out", "player_out":"A", "fielders":[]}), s)
    assert not score(event(wicket={"kind":"retired hurt", "player_out":"A", "fielders":[]}), s)


def test_switching_captain_changes_only_affected_multipliers():
    t = default_team()
    original = build_replay(**t)["final"]["player_totals"]
    other = dict(t, captain="DP Conway")
    changed = build_replay(**other)["final"]["player_totals"]
    for player in t["xi"]:
        if player not in {t["captain"], "DP Conway"}:
            assert original[player] == changed[player]
    assert changed[t["captain"]] * 2 == original[t["captain"]]
    assert changed["DP Conway"] == original["DP Conway"] * 2
