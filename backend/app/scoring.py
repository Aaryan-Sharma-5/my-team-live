"""Simplified fantasy points, independent of any language model."""

RULES = {
    "run": 1, "four_bonus": 1, "six_bonus": 2,
    "30_runs": 4, "50_runs": 8, "100_runs": 16, "duck": -2,
    "wicket": 25, "bowled_lbw_bonus": 8, "3_wickets": 4,
    "5_wickets": 16, "catch": 8, "run_out": 10,
    "captain_multiplier": 2, "vice_captain_multiplier": 1.5,
}
