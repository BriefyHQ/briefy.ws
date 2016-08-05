"""Briefy microservices helper."""
from .initialization import initialize
from pyramid.renderers import JSONP

import os


CORS_POLICY = {
    'origins': ('*', ),
    'headers': ('X-Locale', )
}


def expandvars_dict(settings):
    """Expand all environment variables in a settings dictionary.

    http://stackoverflow.com/a/16446566
    :returns: Dictionary with settings
    :rtype: dict
    """
    return {key: os.path.expandvars(value) for key, value in settings.items()}


def includeme(config):
    """Configuration to be included by other services."""
    settings = config.get_settings()

    # add default renderer
    config.add_renderer('jsonp', JSONP(param_name='callback'))

    # Setup cornice.
    config.include("cornice")

    # Per-request transaction.
    config.include("pyramid_tm")

    # Scan views.
    config.scan("briefy.ws.views")

