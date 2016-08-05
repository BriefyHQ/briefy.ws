"""Views for briefy.ws."""
from pyramid.response import Response
from pyramid.view import view_config

import json
import pyramid.httpexceptions as http_exc


@view_config(context=http_exc.HTTPForbidden)
def forbidden(exc, request):
    """View overriding default 403 error page.

    :param exc: A 403 exception
    :type exc: :class:`pyramid.httpexceptions.HTTPForbidden`
    :param request: A request object
    :type request: request
    :returns: A response object with a application/json formatted body
    :rtype: :class:`pyramid.response.Response`
    """
    body = {}
    body.update({
        'status': 'error',
        'message': 'Unauthorized',
        'url': '{0}'.format(request.url)
    })
    response = Response(json.dumps(body))
    response.status_int = 403
    response.content_type = 'application/json'
    return response
