"""Test app used for py.test."""
from pyramid.config import Configurator


def includeme(config):
    """Custom routes and scan app."""
    config.add_route('login', '/login')
    config.scan('tests.testapp.views')


def main(settings=None, config=None, *args, **additional_settings):
    import briefy.ws

    if settings is None:
        settings = {}
    settings.update(additional_settings)
    if config is None:
        config = Configurator(settings=settings)
    config.include('briefy.ws')
    config.include(includeme)
    briefy.ws.initialize(config, version='1.0.0', project_name='testapp')
    app = config.make_wsgi_app()
    return app
