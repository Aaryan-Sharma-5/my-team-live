"""Optional Anthropic narration; deterministic replay remains the source of truth."""
import hashlib
import json
import os
import re
import urllib.request

SYSTEM = """You write one-line live updates for a cricket fan tracking their fantasy team.
Language: casual Hinglish in Roman script, like a friend texting during the match.
Use ONLY the facts provided. Never compute or change any numbers. Never invent events or players.
Mention the points change exactly as given. Max 25 words. No hashtags. At most one emoji.
Perspective: "aapki team", "aapka captain"."""
CACHE = {}


def configured():
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def narrate(facts, fallback):
    if not configured():
        return {"text": fallback, "source": "template"}
    payload = json.dumps(facts, sort_keys=True, ensure_ascii=False)
    cache_key = hashlib.sha256(payload.encode()).hexdigest()
    if cache_key in CACHE:
        return CACHE[cache_key]
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({"model": "claude-haiku-5-5", "max_tokens": 100, "system": SYSTEM,
                         "messages": [{"role": "user", "content": payload}]}).encode(),
        headers={"content-type": "application/json", "anthropic-version": "2023-06-01",
                 "x-api-key": os.environ["ANTHROPIC_API_KEY"]}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            data = json.load(response)
        text = " ".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text").strip()
        points = str(facts["points_delta"])
        if len(text.split()) > 25 or not re.search(r"(?<![\d.])" + re.escape(points) + r"(?![\d.])", text):
            raise ValueError("Narration failed validation")
        result = {"text": text, "source": "ai"}
        if len(CACHE) >= 1000:
            CACHE.clear()
        CACHE[cache_key] = result
        return result
    except Exception:
        return {"text": fallback, "source": "template"}
