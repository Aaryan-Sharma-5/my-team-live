from types import SimpleNamespace
from backend.app import main


def request(ip, headers=None):
    return SimpleNamespace(client=SimpleNamespace(host=ip), headers=headers or {})


def test_cache_is_checked_before_limiter(monkeypatch):
    main.RATE.clear()
    monkeypatch.setattr(main, 'configured', lambda: True)
    monkeypatch.setattr(main, 'cached_narration', lambda facts: {'text':'cached','source':'ai'})
    main.RATE['1.2.3.4'].extend([1] * main.LIMIT)
    body = main.Narration(facts={'tag':'wicket'},template_text='fallback')
    assert main.narration(body, request('1.2.3.4'))['text'] == 'cached'
    assert len(main.RATE['1.2.3.4']) == main.LIMIT


def test_per_ip_limit_and_expiry(monkeypatch):
    main.RATE.clear()
    monkeypatch.setattr(main, 'configured', lambda: True)
    monkeypatch.setattr(main, 'cached_narration', lambda facts: None)
    monkeypatch.setattr(main, 'narrate', lambda facts, fallback: {'text':'ai','source':'ai'})
    monkeypatch.setattr(main.time, 'monotonic', lambda: 100.0)
    body = main.Narration(facts={'tag':'wicket'},template_text='fallback')
    for _ in range(main.LIMIT):
        assert main.narration(body, request('1.2.3.4'))['source'] == 'ai'
    assert main.narration(body, request('1.2.3.4'))['source'] == 'template'
    assert main.narration(body, request('5.6.7.8'))['source'] == 'ai'
    monkeypatch.setattr(main.time, 'monotonic', lambda: 160.0)
    assert main.narration(body, request('1.2.3.4'))['source'] == 'ai'


def test_render_client_ip_and_local_untrusted_header(monkeypatch):
    req = request('10.0.0.1', {'cf-connecting-ip':'1.2.3.4', 'x-forwarded-for':'9.9.9.9'})
    monkeypatch.delenv('RENDER', raising=False)
    assert main.client_ip(req) == '10.0.0.1'
    monkeypatch.setenv('RENDER', 'true')
    assert main.client_ip(req) == '1.2.3.4'
