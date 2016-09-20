"""Briefy WS default authentication helpers."""

from pyramid.httpexceptions import HTTPUnauthorized as BaseHTTPUnauthorized
from webob import Response

import json


class AuthenticatedUser:
    """Class to represent current authenticated user.
    """
    _fields = ['locale', 'fullname', 'first_name', 'last_name', 'email', 'groups']

    def __init__(self, user_id, data):
        """Initialize object from JWT token using pyramid jwt claims."""
        self.id = user_id
        for field in self._fields:
            setattr(self, field, data.get(field))

    def to_dict(self):
        """Create a dict representation of current user.

        :return: dict serializable user data
        """
        fields = self._fields
        fields.append('id')
        return {field: getattr(self, field, None) for field in self._fields}


class HTTPUnauthorized(BaseHTTPUnauthorized):
    """401 Unauthorized HTTP exception."""
    def __init__(self, msg='Unauthorized'):
        body = {'status': 401, 'message': msg}
        Response.__init__(self, json.dumps(body))
        self.status = 401
        self.content_type = 'application/json'


def user_factory(request) -> AuthenticatedUser:
    """Create a user map from jwt token.

    :param request: pyramid request object.
    :return: Authenticated user instance or None
    """
    user_id = request.authenticated_userid
    if user_id:
        used_data = request.jwt_claims
        return AuthenticatedUser(user_id, used_data)


def groupfinder(userid, request):
    """Callback to the authentication policy to return the list of users.

    :param userid: authenticatded userid.
    :param request: pyramid request object.
    :return: list of user groups
    :rtype: list
    """
    return request.jwt_claims.get('groups', [])


def validate_jwt_token(request):
    """Use pyramid JWT to validate if the user is authenticated."""
    user_id = request.authenticated_userid
    if user_id is None:
        raise HTTPUnauthorized
    return user_factory(request)
