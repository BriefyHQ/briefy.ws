"""Conftest for briefy.ws."""
from briefy import common
from briefy.common.db import Base
from briefy.ws.auth import AuthenticatedUser
from pyramid.testing import DummyRequest
from sqlalchemy import create_engine
from sqlalchemy import orm
from tests.testapp import main as _testapp
from unittest.mock import Mock
from zope.configuration.xmlconfig import XMLConfig
from zope.sqlalchemy import ZopeTransactionExtension

import collections
import pytest
import uuid


XMLConfig('configure.zcml', common)()

DBSession = orm.scoped_session(
    orm.sessionmaker(extension=ZopeTransactionExtension())
)


class UserMock:
    """User mock object."""

    groups = ['g:briefy']
    id = 'fbda5789-2e32-44c4-b9dc-d0d217454a2a'


class ContextMock:
    """Context mock class."""

    def has_global_permissions(self, permission, roles):
        """Mock global permission always true method."""
        return True


class SQLResultMock(collections.UserList):
    """Mock plain sql query result."""

    def __init__(self, *args, **kwargs):
        """Initilize result set mock."""
        self._keys = kwargs.pop('keys')
        super().__init__(*args, **kwargs)

    @property
    def rowcount(self):
        """Return the number of items."""
        return len(self)

    def keys(self):
        """Mock keys method."""
        return self._keys


class SessionMock:
    """Session mock class."""

    def add(self, other):
        """Mock add method."""
        pass

    def __call__(self):
        """Call return always itself."""
        return self

    def flush(self):
        """Mock flush method."""
        pass

    def execute(self, query):
        """Mock execute method."""
        item = dict(
            id=uuid.uuid4(),
            first='Ruda',
            last='Filgueirs',
            age=43
        )
        values = [i for i in item.values()]
        keys = [i for i in item.keys()]
        return SQLResultMock([values], keys=keys)


class AclMock:
    """Acl mock."""

    real = 1


class AuthPolicyMock:
    """Auth policy mock."""

    def __init__(self, *args, **kwargs):
        """Mock init method."""
        self.headers = dict()

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

    def __missing__(self, key):
        """The missing"""
        self.used_keys.append(key)
        return SessionMock()

    def notify(self, event):
        self.notifications.append(event)

    def queryUtility(self, interface, default=None):
        """Mock AuthPolice."""
        return AuthPolicyMock


class Request(DummyRequest):
    """Web request mock."""

    def __init__(self, user, registry):
        super().__init__()
        self.registry = registry
        self.user = user
        self.validated = {}
        self.matchdict = Mock()


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
    """Mock model."""

    _default_notify_events = None
    _class_id = uuid.uuid4()

    def __init__(self, **kw):
        """Initialize model."""
        self._id = uuid.uuid4()

    def __getattr__(self, attr):
        """The getattr"""
        return self

    def __call__(self, *args):
        return self

    @classmethod
    def id(cls):
        """Return cls id attribute to be used in the obj query."""
        return cls._class_id

    @classmethod
    def create(cls, payload):
        """Create new model using payload."""
        return Model(**payload)

    @classmethod
    def query(cls, principal_id=None, permission='view'):
        """Mock query."""
        return QueryMock(model=cls)


@pytest.fixture('function')
def context():
    """Return a context mock instance."""
    return ContextMock()


@pytest.fixture('function')
def model_class():
    """Return a model class."""
    return Model


@pytest.fixture('function')
def obj_instance():
    """Return a model instance."""
    return Model()


@pytest.fixture('function')
def registry():
    """Create new request registry."""
    return RequestRegistry()


@pytest.fixture('function')
def user():
    """Create new mock user."""
    return UserMock()


@pytest.fixture('function')
def web_request(user, registry):
    """Create new dummy request."""
    req = Request(user, registry)
    req.db = SessionMock()
    return req


@pytest.fixture('class')
def testapp():
    """WSGI app for testing purposes."""
    from webtest import TestApp

    app = _testapp({}, config=None)

    return TestApp(app)


@pytest.fixture()
def database(request):
    """Create new engine based on db_settings fixture.
    :param request: pytest request
    :return: sqlalcheny engine instance.
    """
    database_url = 'sqlite://'
    engine = create_engine(database_url, echo=False)
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    def teardown():
        Base.metadata.drop_all(engine)

    request.addfinalizer(teardown)
    return DBSession()


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
