"""Test main view and routes."""


def test_hello(testapp):
    """Test main view for this service."""
    app = testapp

    r = app.get('/', status=200)
    assert 'application/json' == r.content_type

    assert r.json['http_api_version'] == '1.0'
    assert r.json['project_docs'] is None
    assert r.json['project_name'] == 'testapp'
    assert r.json['project_version'] == '1.0.0'
    assert r.json['url'] == 'http://localhost/'
