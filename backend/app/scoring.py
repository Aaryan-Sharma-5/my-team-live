"""Simplified fantasy points, independent of any language model."""

RULES = {
    "run": 1, "four_bonus": 1, "six_bonus": 2,
    "30_runs": 4, "50_runs": 8, "100_runs": 16, "duck": -2,
    "wicket": 25, "bowled_lbw_bonus": 8, "3_wickets": 4,
    "5_wickets": 16, "catch": 8, "run_out": 10,
    "captain_multiplier": 2, "vice_captain_multiplier": 1.5,
}


def score_event(event, state, xi, captain, vc):
    """Return point deltas from the event and prior state without mutating either."""
    deltas = []
    def award(player, code, text, amount):
        if player not in xi:
            return
        multiplier = 2 if player == captain else 1.5 if player == vc else 1
        final = round(amount * multiplier, 1)
        deltas.append(dict(player=player, base_points=amount, multiplier=multiplier,
                           final_points=final, reason_code=code, reason_text=text))

    batter, bowler = event["batter"], event["bowler"]
    runs = event["runs_batter"]
    before = state["runs"].get(batter, 0)
    if runs:
        award(batter, "run", f"{runs} run(s)", runs * RULES["run"])
    if event["is_four"]:
        award(batter, "four_bonus", "Four bonus", RULES["four_bonus"])
    if event["is_six"]:
        award(batter, "six_bonus", "Six bonus", RULES["six_bonus"])
    for milestone in (30, 50, 100):
        if before < milestone <= before + runs:
            award(batter, f"{milestone}_runs", f"{milestone}-run milestone", RULES[f"{milestone}_runs"])
    w = event["wicket"]
    if w and w["kind"] not in {"retired hurt", "retired not out"}:
        out, kind = w["player_out"], w["kind"]
        if (out in state["faced"] or (out == batter and event["extra_type"] != "wide")) and state["runs"].get(out, 0) + (runs if out == batter else 0) == 0:
            award(out, "duck", "Dismissed for a duck", RULES["duck"])
        if kind in {"bowled", "caught", "caught and bowled", "lbw", "stumped", "hit wicket"}:
            count = state["wickets"].get(bowler, 0) + 1
            award(bowler, "wicket", "Bowler wicket", RULES["wicket"])
            if kind in {"bowled", "lbw"}:
                award(bowler, "bowled_lbw_bonus", "Bowled/LBW bonus", RULES["bowled_lbw_bonus"])
            if count in (3, 5):
                award(bowler, f"{count}_wickets", f"{count}-wicket haul", RULES[f"{count}_wickets"])
        if kind in {"caught", "caught and bowled"}:
            for fielder in w["fielders"] or ([bowler] if kind == "caught and bowled" else []):
                award(fielder, "catch", "Catch", RULES["catch"])
        if kind == "run out":
            for fielder in w["fielders"]:
                award(fielder, "run_out", "Run out involvement", RULES["run_out"])
    return deltas
