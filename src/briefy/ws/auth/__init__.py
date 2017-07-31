"""Briefy WS default authentication helpers."""
from briefy.common.types import BaseUser
from briefy.common.utils.transformers import to_serializable
from pyramid.httpexceptions import HTTPUnauthorized as BaseHTTPUnauthorized
from pyramid.request import Request
from webob import Response

import json
import newrelic.agent
import typing as t


class AuthenticatedUser(BaseUser):
    """Class to represent current authenticated user."""


UserOrNone = t.Union[AuthenticatedUser, None]


@to_serializable.register(AuthenticatedUser)
def ts_authenticated_user(val: AuthenticatedUser) -> dict:
    """Serializer for AuthenticatedUser.

    :param val: AuthenticatedUser instance.
    :return: Dictionary with AuthenticatedUser serialization.
    """
    return val.to_dict()


class HTTPUnauthorized(BaseHTTPUnauthorized):
    """401 Unauthorized HTTP exception."""

    def __init__(self, msg='Unauthorized'):
        """Customize init to create a json response object and body."""
        body = {'status': 401, 'message': msg}
        Response.__init__(self, json.dumps(body))
        self.status = 401
        self.content_type = 'application/json'


def user_factory(request: Request) -> UserOrNone:
    """Create a user map from jwt token.

    :param request: pyramid request object.
    :return: The AuthenticatedUser, if exists, or None (representing an AnonymousUser).
    """
    user_id = request.authenticated_userid
    authenticated_user = None
    if user_id:
        data = request.jwt_claims
        # add all user data to the newrelic custom attributes
        newrelic.agent.add_custom_parameter('user_id', user_id)
        for key, value in data.items():
            newrelic.agent.add_custom_parameter(key, str(value))
            authenticated_user = AuthenticatedUser(user_id, data)
    return authenticated_user


def groupfinder(userid: str, request: Request) -> t.Sequence[str]:
    """Callback to the authentication policy to return the list of users.

    :param userid: authenticatded userid.
    :param request: pyramid request object.
    :return: list of user groups
    """
    return request.jwt_claims.get('groups', [])


def validate_jwt_token(request: Request, **kwargs) -> UserOrNone:
    """Use pyramid JWT to validate if the user is authenticated.

    :param request: Pyramid request object.
    :param kwargs: Additional keyword arguments.
    :return: The AuthenticatedUser, if exists, or None (representing an AnonymousUser).
    """
    user_id = request.authenticated_userid
    if user_id is None:
        raise HTTPUnauthorized
    return user_factory(request)
