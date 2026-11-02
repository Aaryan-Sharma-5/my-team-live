"""Optional Groq narration; deterministic replay remains the source of truth."""
import hashlib
import json
import logging
import os
import re
import urllib.request

SYSTEM = """You write one-line live updates for a cricket fan tracking their fantasy team.
Language: casual Hinglish in Roman script, like a friend texting during the match.
Use ONLY the facts provided. Never compute or change any numbers. Never invent events or players.
Mention the points change exactly as given. Max 25 words. No hashtags. At most one emoji.
team_points_delta is the combined change for the whole fantasy team, not the points earned by any individual. The breakdown lists each player's change. When more than one player is involved, avoid attributing the team total to any single player. If a batter and bowler are both in the XI, you may mention mixed feelings without inventing facts.
Mention no other numbers, including score, runs, over, target, or totals.
Do not call a player captain or vice-captain unless their role in the breakdown says so.
Do not attribute a catch or stumping to a bowler unless the facts explicitly say caught and bowled.
For wicket events involving multiple players, describe the wicket and combined team points; never attribute the combined points to an individual.
For every wicket or danger update, say only that a wicket fell and the team points change; do not describe catches or stumpings. For changes involving multiple players, do not name a player or assign the total to one person.
For example, if the team change is +5, a valid line is: "Wah, aapki team ko +5 points mile!"
Perspective: "aapki team", "aapka captain"."""
CACHE = {}
log = logging.getLogger("my_team_live.narration")


def configured():
    return bool(os.getenv("GROQ_API_KEY"))


def cache_key_for(facts):
    payload = json.dumps(facts, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def cached_narration(facts):
    return CACHE.get(cache_key_for(facts))


def narrate(facts, fallback):
    if not configured():
        return {"text": fallback, "source": "template"}
    # Omit unrelated numbers to reduce score/points confusion.
    model_facts = {key: value for key, value in facts.items() if key not in {"team_total", "score", "over", "target"}}
    payload = json.dumps(model_facts, sort_keys=True, ensure_ascii=False)
    cache_key = cache_key_for(facts)
    if cache_key in CACHE:
        return CACHE[cache_key]
    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps({"model": "openai/gpt-oss-20b", "max_completion_tokens": 512,
                         "reasoning_effort": "low",
                         "messages": [{"role": "system", "content": SYSTEM},
                                      {"role": "user", "content": payload}]}).encode(),
        headers={"content-type": "application/json", "user-agent": "MyTeamLive/1.0",
                 "authorization": "Bearer " + os.environ["GROQ_API_KEY"]}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            data = json.load(response)
        text = data["choices"][0]["message"]["content"].strip()
        points = str(facts["team_points_delta"])
        numbers = re.findall(r"(?<![\w.])[+-]?\d+(?:\.\d+)?", text)
        roles = {p.get("role") for p in facts.get("breakdown", [])}
        wrong_role = not roles.intersection({"captain", "vice-captain"}) and re.search(r"\b(?:captain|kaptaan|skipper|vice)\b", text, re.IGNORECASE)
        wicket_claim = facts.get("tag") in {"wicket", "danger"} and re.search(r"\b(?:stump\w*|catch\w*|caught|keeper|pakad\w*)\b", text, re.IGNORECASE)
        contributing = [p for p in facts.get("breakdown", []) if p.get("points")]
        multi_person = len(contributing) > 1
        named_player = multi_person and any(
            any(re.search(r"\b" + re.escape(part) + r"\b", text, re.IGNORECASE) for part in p.get("player", "").split() if len(part) > 2)
            for p in facts.get("breakdown", [])
        )
        missing_team = multi_person and not re.search(r"\bteam\b", text, re.IGNORECASE)
        # A missing plus sign is harmless; a missing minus sign is not.
        allowed = {points} | ({points.lstrip('+')} if not points.startswith('-') else set())
        if len(text.split()) > 25 or len(numbers) != 1 or numbers[0] not in allowed or wrong_role or wicket_claim or named_player or missing_team:
            raise ValueError("Narration failed validation")
        result = {"text": text, "source": "ai"}
        if len(CACHE) >= 1000:
            CACHE.clear()
        CACHE[cache_key] = result
        return result
    except Exception as exc:
        # Log only the failure category/status, never the key or model response.
        error_code = "unknown"
        if isinstance(exc, urllib.error.HTTPError):
            try:
                candidate = json.load(exc).get("error", {}).get("code", "unknown")
                if isinstance(candidate, str) and re.fullmatch(r"[a-z0-9_-]{1,80}", candidate):
                    error_code = candidate
            except (ValueError, TypeError, AttributeError):
                pass
        log.warning("Groq narration fallback: %s status=%s code=%s", type(exc).__name__, getattr(exc, "code", "n/a"), error_code)
        return {"text": fallback, "source": "template"}
