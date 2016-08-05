"""Main view for the service."""

from cornice import Service
from pyramid.security import Authenticated
from pyramid.security import NO_PERMISSION_REQUIRED

hello = Service(
    name="hello",
    path='/',
    description="Welcome"
)


@hello.get(permission=NO_PERMISSION_REQUIRED)
def get_hello(request):
    """Return information regarding the current instance."""
    settings = request.registry.settings
    project_name = settings['project_name']
    project_version = settings['project_version']
    data = dict(
        project_name=project_name,
        project_version=project_version,
        http_api_version=settings['http_api_version'],
        project_docs=settings.get('project_docs'),
        url=request.route_url(hello.name)
    )

    # If current user is authenticated, add user info:
    # (Note: this will call authenticated_userid() with multiauth+groupfinder)
    if Authenticated in request.effective_principals:
        data['user'] = request.get_user_info()


    return data