from .ingest import load_match, normalize
from .scoring import score_event


def build_replay(xi, captain, vice_captain):
    state = {"totals": {p: 0.0 for p in xi}, "runs": {}, "wickets": {}, "faced": set()}
    items = []
    quiet = 0
    for event in normalize(load_match()):
        deltas = score_event(event, state, xi, captain, vice_captain)
        for delta in deltas:
            state["totals"][delta["player"]] += delta["final_points"]
        batter = event["batter"]
        state["runs"][batter] = state["runs"].get(batter, 0) + event["runs_batter"]
        if event["extra_type"] != "wide":
            state["faced"].add(batter)
        wicket = event["wicket"]
        if wicket and wicket["kind"] in {"bowled", "caught", "caught and bowled", "lbw", "stumped", "hit wicket"}:
            bowler = event["bowler"]
            state["wickets"][bowler] = state["wickets"].get(bowler, 0) + 1
        relevant = bool(deltas) or bool(event["wicket"] and event["wicket"]["player_out"] in xi)
        quiet = 0 if relevant else quiet + 1
        if quiet >= 12:
            relevant, quiet = True, 0
            tag = "quiet"
        elif event["wicket"] and event["wicket"]["player_out"] in xi and any(d['final_points'] > 0 and d['player'] != event['wicket']['player_out'] for d in deltas):
            tag = "mixed"
        elif event["wicket"] and (event["wicket"]["player_out"] in (captain, vice_captain) or state["totals"].get(event["wicket"]["player_out"], 0) >= 20):
            tag = "danger"
        elif any(d["reason_code"].endswith("runs") or d["reason_code"].endswith("wickets") for d in deltas):
            tag = "milestone"
        elif event["wicket"] and relevant:
            tag = "wicket"
        elif (event["is_four"] or event["is_six"]) and relevant:
            tag = "boundary"
        elif any(d["player"] == captain for d in deltas):
            tag = "captain"
        elif deltas:
            tag = "run"
        else:
            tag = "quiet"
        delta = round(sum(d["final_points"] for d in deltas), 1)
        total = round(sum(state["totals"].values()), 1)
        if tag == "quiet":
            text = f"Kuch khaas nahi hua. Aapki team ka total {total:g} points."
        elif tag == "mixed":
            outgoing = event['wicket']['player_out'].split()[-1]
            gainers = {}
            for d in deltas:
                if d['final_points'] > 0 and d['player'] != event['wicket']['player_out']:
                    gainers[d['player']] = gainers.get(d['player'], 0) + d['final_points']
            leader = max(gainers, key=gainers.get).split()[-1]
            if len(gainers) == 1 and delta == next(iter(gainers.values())):
                text = f"{outgoing} out, par {leader} ke points se team {delta:+g}."
            else:
                text = f"{outgoing} out, par doosre contributions ke baad team ka net {delta:+g}."
        elif tag == "danger":
            text = f"Dhyaan do: {event['wicket']['player_out']} out ho gaye."
            if delta:
                text += f" Aapki team ko {delta:+g} points."
        else:
            text = f"{event['batter']} vs {event['bowler']}: aapki team ko {delta:+g} points. Total {total:g}."
        items.append({"seq": event["seq"], "match_state": {"innings": event["innings"], "over": event["overs_completed"], "score": event["score_after"], "target": event["target"]},
            "event": event, "deltas": deltas, "team_total_after": total, "player_totals_after": state["totals"].copy(), "relevant": relevant, "tag": tag, "template_text": text})
    return {"items": items, "final": {"team_total": total, "player_totals": state["totals"], "top_mover": max(xi, key=lambda p: state["totals"][p])}}
