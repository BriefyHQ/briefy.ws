from briefy.ws.resources import events
from briefy.ws.resources import RESTService
from pyramid.testing import DummyRequest
from unittest.mock import Mock

import uuid


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


class QueryMock:
    """Mock sqlalchemy query."""

    def __init__(self, model):
        """Initilize query."""
        self.obj = model()

    def filter(self, *args, **kwargs):
        """Filter always return same query instance."""
        return self

    def one_or_none(self, *args, **kwargs):
        """Return model for one or none."""
        return self.obj


class Model:

    _default_notify_events = None
    id = uuid.uuid4()

    def __init__(self, **kw):
        self.id = 1

    def __getattr__(self, attr):
        """The getattr"""
        return self

    def __call__(self, *args):
        return self

    @classmethod
    def create(cls, payload):
        """Create new model using payload."""
        return Model(**payload)

    @classmethod
    def query(cls, principal_id=None, permission='view'):
        """Mock query."""
        return QueryMock(model=cls)


def test_base_resource_triggers_get_events(login):
    req = Request()
    c = ContextMock()
    b = RESTService(c, req)

    assert b.request is req
    assert b.context is c


def test_base_resource_get(login):
    req = Request()
    c = ContextMock()
    b = RESTService(c, req)
    b.model = Model

    b.get()
    assert len(req.registry.notifications) == 0


def test_base_resource_post(login):
    req = Request()
    c = ContextMock()
    b = RESTService(c, req)
    b.model = Model

    b.collection_post()
    assert isinstance(req.registry.notifications[0], events.ObjectCreatedEvent)


def test_base_resource_put(login):
    req = Request()
    c = ContextMock()
    b = RESTService(c, req)
    b.model = Model

    b.put()
    assert isinstance(req.registry.notifications[0], events.ObjectUpdatedEvent)


def test_base_resource_delete(login):
    req = Request()
    c = ContextMock()
    b = RESTService(c, req)
    b.model = Model
    b.delete()

    assert isinstance(req.registry.notifications[0], events.ObjectDeletedEvent)
