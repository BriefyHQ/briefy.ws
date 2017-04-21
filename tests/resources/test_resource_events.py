from briefy.ws.resources import events
from briefy.ws.resources import RESTService
from pyramid.testing import DummyRequest
from unittest.mock import Mock


class ContextMock:

    def has_global_permissions(self, permission, roles):
        """Mock global permission always true method."""
        return True


class UserMock:
    """User mock object."""

    groups = ['g:briefy']
    id = 'fbda5789-2e32-44c4-b9dc-d0d217454a2a'


class AclMock:
    """Acl mock."""

    real = 1


class AuthPolicyMock:
    """Auth policy mock."""

    def effective_principals(self, request):
        """Mock user information."""
        return self

    def permits(self, context, principals, permission):
        """Mock auth policy permits."""
        return AclMock()


class RequestRegistry(dict):
    def __init__(self):
        self.used_keys = []
        self.notifications = []

    class Session:
        def add(self, other):
            pass

        def __call__(self):
            return self

        def flush(self):
            pass

    def __missing__(self, key):
        """The missing"""
        self.used_keys.append(key)
        return self.Session()

    def notify(self, event):
        self.notifications.append(event)

    def queryUtility(self, interface):
        """Mock AuthPolice."""
        return AuthPolicyMock()


class Request(DummyRequest):

    def __init__(self):
        super().__init__()
        self.registry = RequestRegistry()
        self.user = UserMock()

    validated = {}
    matchdict = Mock()


class Model:
    def __init__(self, **kw):
        self.id = 1

    def __getattr__(self, attr):
        """The getattr"""
        return self

    def __call__(self, *args):
        return self


def test_base_resource_triggers_get_events(login):
    r = Request()
    c = ContextMock()
    b = RESTService(c, r)

    assert b.request is r
    assert b.context is c


def test_base_resource_get(login):
    r = Request()
    c = ContextMock()
    b = RESTService(c, r)
    b.model = Model()

    b.get()
    assert len(r.registry.notifications) == 0


def test_base_resource_post(login):
    r = Request()
    c = ContextMock()
    b = RESTService(c, r)
    b.model = Model()

    b.collection_post()
    assert isinstance(r.registry.notifications[0], events.ObjectCreatedEvent)


def test_base_resource_put(login):
    r = Request()
    c = ContextMock()
    b = RESTService(c, r)
    b.model = Model()

    b.put()
    assert isinstance(r.registry.notifications[0], events.ObjectUpdatedEvent)


def test_base_resource_delete(login):
    r = Request()
    c = ContextMock()
    b = RESTService(c, r)
    b.model = Model()
    b.delete()

    assert isinstance(r.registry.notifications[0], events.ObjectDeletedEvent)
