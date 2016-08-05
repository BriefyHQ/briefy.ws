"""Views for briefy.ws."""
from pyramid.response import Response
from pyramid.view import view_config

import json
import pyramid.httpexceptions as http_exc


@view_config(context=http_exc.HTTPNotFound)
def not_found(exc, request):
    """View overriding default 404 error page.

    :param exc: A 404 exception
    :type exc: :class:`pyramid.httpexceptions.HTTPNotFound`
    :param request: A request object
    :type request: request
    :returns: A response object with a application/json formatted body
    :rtype: :class:`pyramid.response.Response`
    """
    comment = exc.comment
    body = {}
    if comment:
        body.update(comment)
    body.update({
        'status': 'error',
        'message': '{0}: {1}'.format(exc.detail, request.url),
        'url': '{0}'.format(request.url)
    })
    response = Response(json.dumps(body))
    response.status_int = 404
    response.content_type = 'application/json'
    return response
