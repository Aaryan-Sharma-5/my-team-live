"""Create Groq narration candidates for human review, never overwrite approved lines.

Set GROQ_API_KEY in the environment, then run `python -m scripts.precompute`.
The candidate file is local and ignored by Git; check each line against match
facts before adding it to narrations_default.json and updating its provenance.
"""
import json
import time
from pathlib import Path
from backend.app.facts import narration_facts
from backend.app.main import Team, default_team
from backend.app.narrate import configured, narrate
from backend.app.replay import build_replay

if not configured():
    raise SystemExit('Set GROQ_API_KEY in the environment to generate candidates.')

out = Path(__file__).resolve().parents[1] / 'backend/data/narrations_candidates.json'
saved = json.loads(out.read_text(encoding='utf-8')) if out.exists() else {}
team = Team(**default_team())
items = build_replay(**default_team())['items']
eligible = [i for i in items if i['relevant'] and i['tag'] in {'boundary', 'wicket', 'milestone', 'captain', 'danger', 'mixed'} and sum(d['final_points'] for d in i['deltas'])]
for item in eligible:
    seq = str(item['seq'])
    if seq in saved:
        continue
    result = narrate(narration_facts(item, team), item['template_text'])
    if result['source'] == 'ai':
        saved[seq] = result['text']
        out.write_text(json.dumps(saved, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f"{len(saved)}/{len(eligible)} candidates; delivery {seq}", flush=True)
    time.sleep(4)
