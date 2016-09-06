"""Testapp views"""
from briefy.ws import CORS_POLICY
from cornice import Service

import pyramid.httpexceptions as http_exc

dummy = Service(
    name='Dummy service',
    path='/dummy',
    cors_policy=CORS_POLICY
)


@dummy.get()
def error_500(request):
    """Return a 500 error."""
    raise ValueError('Error')


@dummy.post()
def error_403(request):
    """Return a 403 error."""
    raise http_exc.HTTPForbidden('You shall not pass')


success = Service(
    name='success',
    path='/success',
    description="Simplest app"
)


@success.get()
def get_info(request):
    """Returns Hello in JSON."""
    return {'Hello': 'World'}
