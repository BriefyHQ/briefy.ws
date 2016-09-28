from briefy.ws.resources import RESTService
from briefy.ws.resources import events
from unittest.mock import Mock


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


class Request:
    def __init__(self):
        self.registry = RequestRegistry()

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
    u = login
    b = RESTService(u, r)

    assert b.request is r
    assert b.context is u


def test_base_resource_get(login):
    r = Request()
    u = login
    b = RESTService(u, r)
    b.model = Model()

    b.get()
    assert isinstance(r.registry.notifications[0], events.ObjectLoadedEvent)


def test_base_resource_post(login):
    r = Request()
    u = login
    b = RESTService(u, r)
    b.model = Model()

    b.collection_post()
    assert isinstance(r.registry.notifications[0], events.ObjectCreatedEvent)


def test_base_resource_put(login):
    r = Request()
    u = login
    b = RESTService(u, r)
    b.model = Model()

    b.put()

    assert isinstance(r.registry.notifications[0], events.ObjectLoadedEvent)
    assert isinstance(r.registry.notifications[1], events.ObjectUpdatedEvent)


def test_base_resource_delete(login):
    r = Request()
    u = login
    b = RESTService(u, r)
    b.model = Model()

    b.delete()

    assert isinstance(r.registry.notifications[0], events.ObjectLoadedEvent)
    assert isinstance(r.registry.notifications[1], events.ObjectDeletedEvent)