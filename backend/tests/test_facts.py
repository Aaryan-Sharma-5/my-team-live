import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from backend.app.main import Narration, Team, default_team, replay, narration
from backend.app.facts import narration_facts
from types import SimpleNamespace


def test_multi_player_facts_are_server_derived():
    team = Team(**default_team())
    item = replay(team)['items'][121]
    facts = narration_facts(item, team)
    assert facts['team_points_delta'] == '+31'
    assert [(p['player'], p['points']) for p in facts['breakdown']] == [
        ('Rashid Khan', -2), ('M Pathirana', 25), ('RD Gaikwad', 8)]


def test_arbitrary_facts_and_invalid_delivery_rejected():
    team = Team(**default_team())
    with pytest.raises(ValidationError):
        Narration(team=team, seq=121, facts={'event':'arbitrary prompt'})
    with pytest.raises(HTTPException) as exc:
        narration(Narration(team=team, seq=999), SimpleNamespace(client=None, headers={}))
    assert exc.value.status_code == 422


def test_no_key_uses_server_template(monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    team = Team(**default_team())
    result = narration(Narration(team=team, seq=121), SimpleNamespace(client=None, headers={}))
    assert result == {'text': replay(team)['items'][121]['template_text'], 'source':'template'}


def test_zero_delta_danger_omits_points():
    team = Team(**default_team())
    event = next(x for x in replay(team)['items'] if x['event']['wicket'] and x['event']['wicket']['player_out'] == 'WP Saha')
    assert event['tag'] == 'danger'
    assert 'points' not in event['template_text']


def test_zero_delta_does_not_request_ai(monkeypatch):
    from backend.app import main
    monkeypatch.setattr(main, 'configured', lambda: True)
    monkeypatch.setattr(main, 'narrate', lambda *args: pytest.fail('zero-point event called AI'))
    team = Team(**default_team())
    event = next(x for x in replay(team)['items'] if x['event']['wicket'] and x['event']['wicket']['player_out'] == 'WP Saha')
    result = narration(Narration(team=team, seq=event['seq']), SimpleNamespace(client=None, headers={}))
    assert result['source'] == 'template'
    assert 'points' not in result['text']
