"""Test BriefySchemaNode."""
from briefy.ws.utils import data
from sqlalchemy import create_engine
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from zope.sqlalchemy import ZopeTransactionExtension

import colander
import pytest
import sqlalchemy as sa


DBSession = orm.scoped_session(orm.sessionmaker(extension=ZopeTransactionExtension()))

Base = declarative_base()


class Company(Base):
    """A Company."""

    __tablename__ = 'companies'

    __colanderalchemy_config__ = {
        'excludes': ['users'],
        'overrides': {
            'guid': {
                'title': 'ID',
                'validator': colander.uuid,
                'missing': colander.drop,
                'typ': colander.String()
            },
            'dummy': {
                'title': 'Customer message',
                'default': '',
                'missing': colander.drop,
                'typ': colander.String()
            }
        }

    }

    id = sa.Column(sa.String, nullable=False, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    users = orm.relationship('User', back_populates='company')
    departments = orm.relationship(
        'Department', back_populates='company',
        uselist=True,
        info={'colanderalchemy': {'children': ()}}
    )
    guid = sa.Column(sa.String, nullable=True)


class Department(Base):
    """A Department."""

    __tablename__ = 'departments'

    id = sa.Column(sa.String, nullable=False, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    company_id = sa.Column(sa.String, sa.ForeignKey('companies.id'), nullable=False)
    company = orm.relationship(
        'Company', back_populates='departments', lazy='joined', innerjoin=True
    )
    users = orm.relationship(
        'User', back_populates='department', info={'colanderalchemy': {'exclude': True}}
    )


class User(Base):
    """A User."""

    __tablename__ = 'users'

    id = sa.Column(sa.String, nullable=False, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    last_name = sa.Column(sa.String, nullable=False)
    fullname = orm.column_property(name + ' ' + last_name)
    _email = sa.Column(sa.String, nullable=False)
    age = sa.Column(sa.Integer, default=0)
    company_id = sa.Column(sa.String, sa.ForeignKey('companies.id'), nullable=False)
    company = orm.relationship(
        'Company', back_populates='users', info={'colanderalchemy': {'children': ()}}
    )
    department_id = sa.Column(sa.String, sa.ForeignKey('departments.id'), nullable=False)
    department = orm.relationship('Department', back_populates='users')

    @hybrid_property
    def email(self):
        """Return the email."""
        return self._email

    @property
    def masked_email(self):
        """Return the email, masked."""
        return self.email.replace('@', ' at ')


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
    return engine


def test_schema_base(database):
    """Test BriefySchemaNode."""
    model = User
    schema = data.BriefySchemaNode(model, unknown='ignore')
    payload = {
        'id': 'unique_key',
        'name': 'User',
        'last_name': 'Foo',
        'email': 'user@email.com',
        'age': '18',
        'company_id': 'another_key',
        'department_id': 'unique_dept_key'
    }
    deserialized = schema.deserialize(payload)
    assert isinstance(deserialized, dict)
    assert 'company_id' in deserialized
    assert deserialized['age'] == 18


def test_schema_excludes(database):
    """Test BriefySchemaNode."""
    model = User
    excludes = ['email', ]
    schema = data.BriefySchemaNode(model, unknown='ignore', excludes=excludes)
    payload = {
        'id': 'unique_key',
        'name': 'User',
        'last_name': 'Foo',
        'email': 'user@email.com',
        'age': '18',
        'company_id': 'another_key',
        'department_id': 'unique_dept_key'
    }
    deserialized = schema.deserialize(payload)
    assert isinstance(deserialized, dict)
    assert 'email' not in deserialized


def test_schema_excludes_relationship_imperatively(database):
    """Test BriefySchemaNode."""
    model = Company
    schema = data.BriefySchemaNode(model, unknown='ignore')
    payload = {'id': 'another_key', 'name': 'Company', 'dummy': 'Foobar'}
    deserialized = schema.deserialize(payload)
    assert isinstance(deserialized, dict)
    assert 'users' not in deserialized
    assert 'dummy' in deserialized


def test_schema_excludes_relationship_declaratively(database):
    """Test BriefySchemaNode."""
    model = Department
    schema = data.BriefySchemaNode(model, unknown='ignore')
    payload = {
        'id': 'unique_dept_key',
        'name': 'Department',
        'company_id': 'another_key',
        'company': {
            'id': 'another_key',
            'name': 'Company',
        }
    }
    deserialized = schema.deserialize(payload)
    assert isinstance(deserialized, dict)
    assert 'users' not in deserialized


def test_schema_includes_known_attributes(database):
    """Test BriefySchemaNode."""
    model = User
    includes = ['email', 'company']
    schema = data.BriefySchemaNode(model, unknown='ignore', includes=includes)
    assert len(schema.children) == 2


def test_schema_includes_unknown_attributes(database):
    """Test BriefySchemaNode."""
    model = User
    includes = ['email', 'another_crazy_attr']
    schema = data.BriefySchemaNode(model, unknown='ignore', includes=includes)
    assert len(schema.children) == 1


def test_schema_includes_and_excludes(database):
    """Test BriefySchemaNode."""
    model = User
    includes = ['email', ]
    excludes = ['email', ]
    with pytest.raises(ValueError) as exc:
        data.BriefySchemaNode(model, unknown='ignore', includes=includes, excludes=excludes)
    assert 'excludes and includes are mutually exclusive' in str(exc)
