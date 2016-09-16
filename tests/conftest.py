"""Conftest for briefy.ws."""
from tests.testapp import main as _testapp

import pytest


@pytest.fixture('class')
def testapp():
    """WSGI app for testing purposes."""
    from webtest import TestApp

    app = _testapp({}, config=None)

    return TestApp(app)


@pytest.fixture('class')
def login(request, testapp):
    """Login and get JWT token."""
    app = testapp
    response = app.get('/login', status=200)
    assert 'application/json' == response.content_type

    result = response.json
    for item in 'message', 'provider', 'user', 'status', 'token':
        assert item in result.keys()

    cls = request.cls
    cls.token = result.get('token')
    cls.user = result.get('user')
    cls.app = testapp
