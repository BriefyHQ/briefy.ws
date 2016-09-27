"""Testapp views"""
from briefy.ws import CORS_POLICY
from briefy.ws.auth import validate_jwt_token
from cornice import Service
from pyramid.view import view_config

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


protected = Service(
    name='protected',
    path='/protected',
    description="Protected view"
)


@view_config(route_name='login', renderer='json')
def login_view(request):
    user = {
        "locale": "en_GB",
        "id": "669a99c2-9bb3-443f-8891-e600a15e3c10",
        "fullname": "Person Lastname",
        "first_name": "Person",
        "email": "person@gmail.com",
        "last_name": "Lastname",
        "groups": ["g:briefy_pms", "g:briefy_qa"]
    }
    token = request.create_jwt_token(user.get('id'), **user)
    result = dict(token=token,
                  status='200',
                  message='Authentication success',
                  provider='email',
                  user=user)
    return result


@protected.get(validators=validate_jwt_token)
def get_protected(request):
    """Returns protected information when the user is authenticated."""
    return {'status': 'success',
            'message': 'Protected information.',
            'user': request.user.to_dict(),
            }
