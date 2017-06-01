"""Conftest for briefy.ws."""
from briefy import common
from briefy.ws.auth import AuthenticatedUser
from tests.testapp import main as _testapp
from zope.configuration.xmlconfig import XMLConfig

import pytest


XMLConfig('configure.zcml', common)()


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
    for item in ['message', 'provider', 'user', 'status', 'token']:
        assert item in result.keys()

    user = result.get('user')
    cls = request.cls
    if cls:
        cls.token = result.get('token')
        cls.user = user
        cls.app = testapp
    return AuthenticatedUser(user.get('id'), user)
