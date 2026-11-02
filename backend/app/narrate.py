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
The points change is for the whole fantasy team, not necessarily one player.
Mention no other numbers, including score, runs, over, target, or totals.
Do not call a player captain or vice-captain unless their supplied role says so.
Perspective: "aapki team", "aapka captain"."""
CACHE = {}
log = logging.getLogger("my_team_live.narration")


def configured():
    return bool(os.getenv("GROQ_API_KEY"))


def narrate(facts, fallback):
    if not configured():
        return {"text": fallback, "source": "template"}
    payload = json.dumps(facts, sort_keys=True, ensure_ascii=False)
    cache_key = hashlib.sha256(payload.encode()).hexdigest()
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
        points = str(facts["points_delta"])
        numbers = re.findall(r"(?<![\w.])[+-]?\d+(?:\.\d+)?", text)
        wrong_role = facts.get("role") == "regular" and re.search(r"\b(?:captain|kaptaan|skipper|vice)\b", text, re.IGNORECASE)
        if len(text.split()) > 25 or numbers != [points] or wrong_role:
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
