"""Test error views."""


def test_403(testapp):
    """Test 403 error page."""
    app = testapp

    r = app.post_json('/dummy', {}, status=403)
    assert 'application/json' == r.content_type
    assert 'Unauthorized' in r.json['message']
    assert 'error' in r.json['status']


def test_404(testapp):
    """Test 404 error page."""
    app = testapp

    r = app.get('/foobar', status=404)
    assert 'application/json' == r.content_type
    assert '/foobar' in r.json['url']
    assert 'error' in r.json['status']


def test_500(testapp):
    """Test 500 error page."""
    app = testapp

    r = app.get('/dummy', status=500)
    assert 'application/json' == r.content_type
    assert 'Something went terribly wrong' in r.json['message']
    assert 'error' in r.json['status']
