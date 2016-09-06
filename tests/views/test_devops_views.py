"""Test devops views."""


def test_lb_heartbeat(testapp):
    """Test loadbalancer heartbeat view."""
    app = testapp

    r = app.get('/__lbheartbeat__', status=200)
    assert 'application/json' == r.content_type
    assert r.json == {}
