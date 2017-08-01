"""HTTP Error 403 view for Briefy APIs using briefy.ws."""
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_config

import json
import pyramid.httpexceptions as http_exc


@view_config(context=http_exc.HTTPForbidden)
def forbidden(exc: http_exc.HTTPForbidden, request: Request) -> Response:
    """View overriding default 403 error page.

    :param exc: A 403 exception
    :param request: A request object
    :returns: A response object with a application/json formatted body
    """
    body = {}
    body.update({'status': 'error', 'message': 'Unauthorized', 'url': f'{request.url}'})
    response = Response(json.dumps(body))
    response.status_int = 403
    response.content_type = 'application/json'
    return response
