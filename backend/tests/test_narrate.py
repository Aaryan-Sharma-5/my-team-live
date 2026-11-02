import io
import json
import importlib

narration = importlib.import_module("backend.app.narrate")


def test_missing_key_returns_template(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert narration.narrate({"points_delta": "+5"}, "fallback") == {"text":"fallback", "source":"template"}


def test_timeout_returns_template(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    def fail(*args, **kwargs):
        raise TimeoutError()
    monkeypatch.setattr(narration.urllib.request, "urlopen", fail)
    assert narration.narrate({"points_delta": "+6"}, "fallback")["source"] == "template"


def test_validated_ai_and_invalid_number(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    narration.CACHE.clear()
    def response(text):
        return io.BytesIO(json.dumps({"content":[{"type":"text", "text":text}]}).encode())
    monkeypatch.setattr(narration.urllib.request, "urlopen", lambda *a, **k: response("Aapki team ko +5 points!"))
    assert narration.narrate({"points_delta":"+5"}, "fallback")["source"] == "ai"
    monkeypatch.setattr(narration.urllib.request, "urlopen", lambda *a, **k: response("Aapki team ko +50 points!"))
    assert narration.narrate({"points_delta":"+7"}, "fallback")["source"] == "template"
