"""Test resource Factory."""
from briefy.ws.resources.factory import BaseFactory
from pyramid.testing import DummyRequest as BaseRequest

import pytest


class DummyUser:
    """User mock object."""

    id = 'fbda5789-2e32-44c4-b9dc-d0d217454a2a'
    groups = ['g:briefy']


class DummyWorkflow:
    """A Workflow."""

    context = None

    def permissions(self):
        """Return a list of permissions on a context."""
        context = self.context
        check = context.id == 'fbda5789-2e32-44c4-b9dc-d0d217454a2a' if context else False
        permissions = []
        if check:
            permissions = ['create', 'list', 'view', 'edit', 'delete']
        return permissions


class DummyModel:
    """Model."""

    workflow = DummyWorkflow()

    __raw_acl__ = (
        ('create', ('g:briefy_pm', 'g:system')),
        ('list', ('g:briefy_pm', 'g:system')),
        ('view', ('g:briefy_pm', 'g:system')),
        ('edit', ('g:briefy_pm', 'g:system')),
        ('delete', ('g:briefy_finance', 'g:system')),
    )

    @classmethod
    def __acl__(cls) -> tuple:
        """Return a tuple of pyramid ACLs based on __raw_acl__ attribute."""
        result = dict()
        for permission, roles in cls.__raw_acl__:
            for role_id in roles:
                if role_id not in result:
                    result[role_id] = [permission]
                else:
                    result[role_id].append(permission)
        return tuple([(key, value) for key, value in result.items()])

    @classmethod
    def get(cls, id: str):
        """Return an instance of this object.

        :param id: id of the instance
        :return: Instance of cls
        """
        return cls()


class DummyRequest(BaseRequest):
    """A Request."""

    def __init__(self, user_id='', user_groups=[]):
        super().__init__()
        user = DummyUser()
        if user_id:
            user.id = user_id
        if user_groups:
            user.groups = user_groups
        self.user = user
        self.matchdict = {'id': '228abe0b-f9dd-44f5-a3c6-a9a5976a3f1b'}


@pytest.fixture
def factory():
    """Return a BaseFactory instance."""
    request = DummyRequest()
    factory = BaseFactory(request)
    factory.model = DummyModel
    return factory


def test_factory_acl(factory):
    """Test factory permission."""
    permissions = factory.__acl__
    assert len(permissions) == 5
    # Base permission
    assert permissions[0] == ('Allow', 'g:briefy', ['list', 'view'])
    # Workflow permission
    assert permissions[-1][1] == DummyUser.id


def test_factory_acl_user_without_wf_permission(factory):
    """Test factory permission."""
    factory.request.user.id = 'gbda5789-2e32-44c4-b9dc-d0d217454a2a'
    permissions = factory.__acl__
    assert len(permissions) == 4


test_data = [
    ('create', ['g:briefy'], False),
    ('list', ['g:briefy'], False),
    ('view', ['g:briefy'], False),
    ('edit', ['g:briefy'], False),
    ('delete', ['g:briefy'], False),
    ('create', ['g:briefy_pm'], True),
    ('list', ['g:briefy_pm'], True),
    ('view', ['g:briefy_pm'], True),
    ('edit', ['g:briefy_pm'], True),
    ('delete', ['g:briefy_pm'], False),
    ('delete', ['g:briefy_finance'], True),
    ('view', ['g:briefy_finance', 'g:briefy_pm'], True),
]


@pytest.mark.parametrize('permission,roles,check', test_data)
def test_has_global_permissions(factory, permission, roles, check):
    """Test has_global_permissions."""
    assert factory.has_global_permissions(permission, roles) is check
