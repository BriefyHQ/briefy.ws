"""HTTP Error 404 view for Briefy APIs using briefy.ws."""
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_config

import json
import pyramid.httpexceptions as http_exc


@view_config(context=http_exc.HTTPNotFound)
def not_found(exc: http_exc.HTTPNotFound, request: Request) -> Response:
    """View overriding default 404 error page.

    :param exc: A 404 exception
    :param request: A request object
    :returns: A response object with a application/json formatted body
    """
    comment = exc.comment
    body = {}
    if comment:
        body.update(comment)
    body.update({
        'status': 'error',
        'message': f'{exc.detail}: {request.url}',
        'url': f'{request.url}'
    })
    response = Response(json.dumps(body))
    response.status_int = 404
    response.content_type = 'application/json'
    return response
