"""Convert a Cricsheet JSON match to a deterministic delivery timeline."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "match.json"
NON_DISMISSALS = {"retired hurt", "retired not out", "obstructing the field (not out)"}


def load_match(path=DATA):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize(match):
    events = []
    for innings_number, innings in enumerate((i for i in match["innings"] if not i.get("super_over")), 1):
        if innings_number > 2:
            break
        runs = wickets = 0
        for over in innings["overs"]:
            legal = 0
            for delivery in over["deliveries"]:
                extras = delivery.get("extras", {})
                ball = legal + 1
                if "wides" not in extras and "noballs" not in extras:
                    legal += 1
                runs += delivery["runs"]["total"]
                raw_wickets = delivery.get("wickets", [])
                wickets += sum(w["kind"] not in NON_DISMISSALS for w in raw_wickets)
                w = raw_wickets[0] if raw_wickets else None
                wicket = None if w is None else {"player_out": w["player_out"], "kind": w["kind"], "fielders": [f["name"] for f in w.get("fielders", [])]}
                batter_runs = delivery["runs"]["batter"]
                events.append({"seq": len(events), "innings": innings_number, "over": over["over"], "ball": ball,
                    "batter": delivery["batter"], "bowler": delivery["bowler"], "non_striker": delivery["non_striker"],
                    "runs_batter": batter_runs, "runs_extras": delivery["runs"]["extras"],
                    "extra_type": next((name for key, name in (("wides", "wide"), ("noballs", "noball"), ("byes", "bye"), ("legbyes", "legbye")) if key in extras), None),
                    "is_four": batter_runs == 4 and not delivery.get("non_boundary", False), "is_six": batter_runs == 6 and not delivery.get("non_boundary", False),
                    "wicket": wicket, "score_after": f"{runs}/{wickets}",
                    "target": innings.get("target", {}).get("runs") if innings_number == 2 else None})
    return events
