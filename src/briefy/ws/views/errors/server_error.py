"""Views for briefy.ws."""
from briefy.ws import logger
from pyramid.response import Response
from pyramid.view import view_config

import json


@view_config(context=Exception)
def server_error(exc, request):
    """View overriding default 500 error page.

    :param exc: A 500 exception
    :type exc: :class:`pyramid.httpexceptions.HTTPNotFound`
    :param request: A request object
    :type request: request
    :returns: A response object with a application/json formatted body
    :rtype: :class:`pyramid.response.Response`
    """
    logger.warning('Exception raised: \n {}'.format(exc))
    msg = 'Something went terribly wrong and now we need to wake up a sysadmin'
    body = {'status': 'error', 'message': msg, 'url': request.url}
    response = Response(json.dumps(body))
    response.status_int = 500
    response.content_type = 'application/json'
    return response
