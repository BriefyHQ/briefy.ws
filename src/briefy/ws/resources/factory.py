"""Context base factory for cornice resources."""
from briefy.ws.utils.validate import validate_uuid
from pyramid.authorization import Allow
from pyramid.request import Request

import typing as t


ACL = t.Tuple[str, str, t.Sequence[str]]


__base_admin_acl__ = [(Allow, 'g:briefy', ['list', 'view'])]


class BaseFactory:
    """Base Factory that computes acl."""

    model = None

    def __init__(self, request: Request):
        """Initialize route factory.

        :param request: pyramid request object.
        """
        self.request = request

    @property
    def __base_acl__(self) -> t.Sequence[ACL]:
        """Hook to be use by subclasses to define default ACLs in context.

        :return: Sequence of ACLs
        """
        return []

    @property
    def __acl__(self) -> t.Sequence[ACL]:
        """ACL for a factory.

        :return: list of tuples containing the acl
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
    def model_permissions(self) -> t.Sequence[ACL]:
        """Get permissions defined on model level."""
        model = self.model
        permissions = []
        if model:
            permissions = [(Allow, role, permissions) for role, permissions in model.__acl__()]
        return permissions

    def has_global_permissions(self, permission: str, roles: t.Sequence[str]) -> bool:
        """Return true if the permission is global in the model level."""
        model = self.model
        check = False
        if model:
            raw_acl = self.model.__raw_acl__
            for acl_permissions, acl_roles in raw_acl:
                if acl_permissions == permission:
                    for role in roles:
                        if role in acl_roles:
                            check = True
                    break
        return check

    @property
    def workflow_permissions(self) -> t.Sequence[ACL]:
        """Compute ACLs from instance workflow.

        :return: permissions from model instance using workflow object.
        """
        result = []
        context_id = self.request.matchdict.get('id')
        model = self.model
        user = self.request.user

        if validate_uuid(context_id) and model and user:
            context = model.get(context_id)
            if context and getattr(context, 'workflow', None):
                wf = context.workflow
                wf.context = user
                permissions = list(wf.permissions())
                if permissions:
                    result.append((Allow, user.id, permissions))
        return result
