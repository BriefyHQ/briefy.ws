"""Briefy microservices helper."""
from .initialization import initialize  # noqa
from .renderer import JSONRenderer
from briefy.ws.config import JWT_EXPIRATION
from briefy.ws.config import JWT_SECRET
from pyramid.authorization import ACLAuthorizationPolicy

import os
import logging


CORS_POLICY = {
    'origins': ('*', ),
    'headers': ('X-Locale', )
}

logger = logging.getLogger(__name__)


def expandvars_dict(settings):
    """Expand all environment variables in a settings dictionary.

    http://stackoverflow.com/a/16446566
    :returns: Dictionary with settings
    :rtype: dict
    """
    return {key: os.path.expandvars(value) for key, value in settings.items()}


def includeme(config):
    """Configuration to be included by other services."""

    # Setup cornice.
    config.include("cornice")

    # add default renderer
    config.add_renderer('json', JSONRenderer())

    # Per-request transaction.
    config.include("pyramid_tm")

    # config jwt
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.include('pyramid_jwt')
    config.set_jwt_authentication_policy(private_key=JWT_SECRET,
                                         expiration=int(JWT_EXPIRATION))
    # Scan views.
    config.scan("briefy.ws.views")
