import io
import json
import importlib

narration = importlib.import_module("backend.app.narrate")


def test_missing_key_returns_template(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert narration.narrate({"team_points_delta": "+5"}, "fallback") == {"text":"fallback", "source":"template"}


def test_timeout_returns_template(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    def fail(*args, **kwargs):
        raise TimeoutError()
    monkeypatch.setattr(narration.urllib.request, "urlopen", fail)
    assert narration.narrate({"team_points_delta": "+6"}, "fallback")["source"] == "template"


def test_validated_ai_and_invalid_number(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    narration.CACHE.clear()
    def response(text):
        return io.BytesIO(json.dumps({"choices":[{"message":{"content":text}}]}).encode())
    monkeypatch.setattr(narration.urllib.request, "urlopen", lambda *a, **k: response("Aapki team ko +5 points!"))
    assert narration.narrate({"team_points_delta":"+5"}, "fallback")["source"] == "ai"
    monkeypatch.setattr(narration.urllib.request, "urlopen", lambda *a, **k: response("Aapki team ko +50 points!"))
    assert narration.narrate({"team_points_delta":"+7"}, "fallback")["source"] == "template"


def test_rejects_invented_role_or_extra_numbers(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    narration.CACHE.clear()
    def respond(text):
        return io.BytesIO(json.dumps({"choices":[{"message":{"content":text}}]}).encode())
    monkeypatch.setattr(narration.urllib.request, "urlopen", lambda *a, **k: respond("Aapke captain ko +5 points!"))
    assert narration.narrate({"team_points_delta":"+5", "breakdown":[{"role":"regular"}]}, "fallback")["source"] == "template"
    monkeypatch.setattr(narration.urllib.request, "urlopen", lambda *a, **k: respond("4 runs aur +5 points!"))
    assert narration.narrate({"team_points_delta":"+5", "breakdown":[{"role":"captain"}]}, "fallback")["source"] == "template"


def test_groq_request_shape(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    narration.CACHE.clear()
    def respond(request, timeout):
        payload = json.loads(request.data)
        assert request.full_url == "https://api.groq.com/openai/v1/chat/completions"
        assert request.get_header("Authorization") == "Bearer test-key"
        assert request.get_header("User-agent") == "MyTeamLive/1.0"
        assert payload["model"] == "openai/gpt-oss-20b"
        assert timeout == 3
        return io.BytesIO(json.dumps({"choices":[{"message":{"content":"Aapki team ko +12 points!"}}]}).encode())
    monkeypatch.setattr(narration.urllib.request, "urlopen", respond)
    assert narration.narrate({"team_points_delta":"+12"}, "fallback")["source"] == "ai"


def test_positive_sign_optional_but_negative_sign_required(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    narration.CACHE.clear()
    def respond(*args, **kwargs):
        return io.BytesIO(json.dumps({"choices":[{"message":{"content":"Aapki team ko 8 points!"}}]}).encode())
    monkeypatch.setattr(narration.urllib.request, "urlopen", respond)
    assert narration.narrate({"team_points_delta":"+8"}, "fallback")["source"] == "ai"
    assert narration.narrate({"team_points_delta":"-8"}, "fallback")["source"] == "template"
