"""Briefy WS default authentication helpers."""

from pyramid.httpexceptions import HTTPUnauthorized as BaseHTTPUnauthorized
from webob import Response

import json


class HTTPUnauthorized(BaseHTTPUnauthorized):
    """401 Unauthorized HTTP exception."""
    def __init__(self, msg='Unauthorized'):
        body = {'status': 401, 'message': msg}
        Response.__init__(self, json.dumps(body))
        self.status = 401
        self.content_type = 'application/json'


def validate_jwt_token(request):
    """Use pyramid JWT to validate if the user is authenticated."""
    user_id = request.authenticated_userid
    if user_id is None:
        raise HTTPUnauthorized
    fields = ['locale', 'fullname', 'first_name', 'last_name', 'email', 'groups']
    user = {key: request.jwt_claims[key] for key in fields}
    user['id'] = user_id
    request.user = user
