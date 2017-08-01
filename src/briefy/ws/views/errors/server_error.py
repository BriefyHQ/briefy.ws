"""HTTP Errors 50x view for Briefy APIs using briefy.ws."""
from briefy.ws import logger
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_config

import json


@view_config(context=Exception)
def server_error(exc: Exception, request: Request) -> Response:
    """View overriding default 500 error page.

    :param exc: A 500 exception
    :param request: A request object
    :returns: A response object with a application/json formatted body
    """
    try:
        payload = request.json_body
    except json.JSONDecodeError:
        payload = {}

    logger.error(
        f'{exc.__class__.__name__} occurred on url {request.url}',
        extra={'payload': payload},
        exc_info=exc
    )
    msg = 'Something went terribly wrong and now we need to wake up a sysadmin'
    body = {'status': 'error', 'message': msg, 'url': request.url}
    response = Response(json.dumps(body))
    response.status_int = 500
    response.content_type = 'application/json'
    return response
