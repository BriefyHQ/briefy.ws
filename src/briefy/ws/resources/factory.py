"""Context base factory for cornice resources."""
from pyramid.authorization import Allow

import uuid


__base_admin_acl__ = [
    (Allow, 'g:briefy', ['list', 'view'])
    ]


class BaseFactory(object):
    """Base Factory that computes acl."""

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
        """ACL for a factory.

        :return: list of tuples containing the acl
        :rtype: list
        """
        permissions = []
        # ACL for admins
        permissions.extend(__base_admin_acl__)
        # ACL for each Factory
        permissions.extend(self.__base_acl__)
        # Computed acl from model
        permissions.extend(self.model_permissions)
        # Computed acl from workflow
        permissions.extend(self.workflow_permissions)
        return permissions

    @property
    def model_permissions(self) -> list:
        """Get permissions defined on model level."""
        model = self.model
        if model:
            return [(Allow, role, permissions) for role, permissions in model.__acl__()]
        else:
            return []

    def has_global_permissions(self, permission, roles) -> bool:
        """Return true if the permission is global in the model level."""
        model = self.model
        if not model:
            return False
        raw_acl = self.model.__raw_acl__
        for acl_permissions, acl_roles in raw_acl:
            if acl_permissions == permission:
                for role in roles:
                    if role in acl_roles:
                        return True
                break

    @property
    def workflow_permissions(self) -> list:
        """Compute ACLs from instance workflow.

        :return: permissions from model instance using workflow object.
        :rtype: list
        """
        result = []
        context_id = self.request.matchdict.get('id')

        if context_id:
            # make sure id is uid valid at this point
            # request validators only run after permission checks
            try:
                uuid.UUID(context_id)
            except ValueError:
                return result
        else:
            return result

        model = self.model
        user = self.request.user
        if model and user:
            context = model.get(context_id)
            if context:
                wf = context.workflow
                wf.context = user
                permissions = list(wf.permissions())
                if permissions:
                    result.append((Allow, user.id, permissions))
        return result
