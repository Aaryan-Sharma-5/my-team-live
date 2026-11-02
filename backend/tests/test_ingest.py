from backend.app.ingest import load_match, normalize


def test_final_source_totals():
    events = normalize(load_match())
    first = [e for e in events if e["innings"] == 1]
    second = [e for e in events if e["innings"] == 2]
    assert first[-1]["score_after"] == "214/4"
    assert second[-1]["score_after"] == "171/5"
    assert second[-1]["target"] == 171
    assert len(events) == 216
    assert sum(e["wicket"] is not None for e in events) == 9
    assert sum(e["is_four"] for e in events) == 31
    assert sum(e["is_six"] for e in events) == 19


def test_illegal_delivery_does_not_advance_ball():
    events = normalize(load_match())
    for a, b in zip(events, events[1:]):
        if a["extra_type"] in ("wide", "noball") and a["innings"] == b["innings"] and a["over"] == b["over"]:
            assert a["ball"] == b["ball"]


def test_completed_overs_use_legal_ball_count():
    events = normalize(load_match())
    first = [e for e in events if e['innings'] == 1]
    second = [e for e in events if e['innings'] == 2]
    assert first[-1]['overs_completed'] == '20.0'
    assert second[-1]['overs_completed'] == '15.0'
    assert first[5]['overs_completed'] == '1.0'
    for a, b in zip(events, events[1:]):
        if a['innings'] == b['innings'] and b['extra_type'] in ('wide', 'noball'):
            assert a['overs_completed'] == b['overs_completed']
