"""Briefy WS default authentication helpers."""

from pyramid.httpexceptions import HTTPUnauthorized as BaseHTTPUnauthorized
from webob import Response

import json


class AuthenticatedUser:
    """Class to represent current authenticated user.
    """
    _fields = ['locale', 'fullname', 'first_name', 'last_name', 'email', 'groups']

    def __init__(self, request):
        self.id = request.authenticated_userid
        for field in self._fields:
            setattr(self, field, request.jwt_claims[field])


class HTTPUnauthorized(BaseHTTPUnauthorized):
    """401 Unauthorized HTTP exception."""
    def __init__(self, msg='Unauthorized'):
        body = {'status': 401, 'message': msg}
        Response.__init__(self, json.dumps(body))
        self.status = 401
        self.content_type = 'application/json'


def user_factory(request):
    """Create a user map from jwt token.

    :param request:
    :return: user map from jwt claims
    """
    return AuthenticatedUser(request)


def validate_jwt_token(request):
    """Use pyramid JWT to validate if the user is authenticated."""
    user_id = request.authenticated_userid
    if user_id is None:
        raise HTTPUnauthorized
    return user_factory(request)
