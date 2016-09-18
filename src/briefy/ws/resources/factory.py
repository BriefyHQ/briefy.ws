"""Context base factory for cornice resources."""

from pyramid.authentication import Authenticated
from pyramid.authorization import Allow


__base_admin_acl__ = [
    (Allow, Authenticated, ['add', 'delete', 'edit', 'list', 'view'])
    ]


class BaseFactory(object):
    """Base Factory that computes acl"""

    model = None

    def __init__(self, request):
        """Initialize route factory.

        :param request: pyramid request object.
        """
        self.request = request

    @property
    def __base_acl__(self) -> list:
        """Hook to be use by subclasses to define default ACLs in context.
        :return: list of ACLs
        :rtype: list
        """
        return []

    @property
    def __acl__(self) -> list:
        """ACL for a factory
        :return: list of tuples containing the acl
        :rtype: list
        """
        permissions = []
        # ACL for admins
        permissions.extend(__base_admin_acl__)
        # ACL for each Factory
        permissions.extend(self.__base_acl__)
        # Computed acl
        permissions.extend(self.workflow_permissions)
        return permissions

    @property
    def workflow_permissions(self) -> list:
        """Compute ACLs from instance workflow.

        :return: permissions from model instance using workflow object.
        :rtype: list
        """
        result = []
        if self.model:
            context_id = self.request.matchdict.get('id')
            context = self.model.get(context_id)
            if context:
                permissions = list(context.workflow.permissions())
                result.append((Allow, self.request.user.get('id'), permissions))
        return result
