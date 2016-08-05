"""Conftest for briefy.ws."""
from tests.testapp import main as _testapp

import pytest


@pytest.fixture()
def testapp():
    """WSGI app for testing purposes."""
    from webtest import TestApp

    app = _testapp({}, config=None)

    return TestApp(app)
