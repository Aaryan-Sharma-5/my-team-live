import json
import re
from backend.app.main import Team, default_team, replay
from backend.app.replay import build_replay


def test_saved_default_narrations_match_replay_points():
    team=Team(**default_team())
    result=replay(team)
    eligible={'boundary','wicket','milestone','captain','danger','mixed'}
    for item in result['items']:
        total=sum(d['final_points'] for d in item['deltas'])
        if item['relevant'] and item['tag'] in eligible:
            assert item['narration']['source']=='ai-pre-generated'
            if total:
                assert re.search(r'(?<![\d.])' + re.escape(f'{total:+g}') + r'(?!\d|\.\d)',item['narration']['text'])
    assert result['final']['team_total']==723


def test_mixed_gill_event_and_custom_team_do_not_share_narration():
    team=Team(**default_team())
    mixed=replay(team)['items'][41]
    assert mixed['tag']=='mixed'
    assert mixed['event']['wicket']['player_out']=='Shubman Gill'
    assert sum(d['final_points'] for d in mixed['deltas'])==50
    assert 'Jadeja' in mixed['narration']['text']
    rashid = replay(team)['items'][121]
    assert 'net +31' in rashid['template_text']
    assert 'Pathirana se' not in rashid['template_text']
    custom=team.model_copy(update={'captain':'Shubman Gill'})
    assert all('narration' not in item for item in replay(custom)['items'])


def test_pre_generated_wicket_credits_actual_fielding():
    data=json.loads((__import__('pathlib').Path(__file__).resolve().parents[1]/'data'/'narrations_default.json').read_text(encoding='utf-8'))['items']
    assert 'Jadeja' in data['41'] and 'stump' not in data['41'].lower()
    assert 'caught' not in data['202'].lower()
    assert 'caught-and-bowled' in data['201'].lower()


def test_stale_scoring_never_uses_pre_generated_lines(monkeypatch, tmp_path):
    from backend.app import main
    data = json.loads(main.PREGENERATED.read_text(encoding='utf-8'))
    data['metadata']['rules']['run'] = 99
    file = tmp_path / 'stale.json'
    file.write_text(json.dumps(data), encoding='utf-8')
    monkeypatch.setattr(main, 'PREGENERATED', file)
    main.pre_generated.cache_clear()
    try:
        assert main.pre_generated() == {}
    finally:
        main.pre_generated.cache_clear()
