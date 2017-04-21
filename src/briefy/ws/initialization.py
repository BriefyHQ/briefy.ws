"""Briefy microservices helper."""
from pyramid.exceptions import ConfigurationError

import warnings


def initialize(config, version=None, project_name='', default_settings=None):
    """Initialize briefy.ws with the given configuration, version and project name.

    :param config: Pyramid configuration
    :type config: ~pyramid:pyramid.config.Configurator
    :param str version: Current project version (e.g. '0.0.1') if not defined in app settings.
    :param str project_name: Project name if not defined in app settings.
    :param dict default_settings: Override briefy.ws default settings values.
    """
    settings = config.get_settings()

    settings['project_name'] = project_name

    if not project_name:
        warnings.warn('No value specified for `project_name`')

    # Override project version from settings.
    project_version = settings.get('project_version') or version
    if not project_version:
        error_msg = 'Invalid project version: {version}'.format(version=project_version)
        raise ConfigurationError(error_msg)
    settings['project_version'] = project_version = str(project_version)

    # HTTP API version.
    http_api_version = settings.get('http_api_version')
    if http_api_version is None:
        # The API version is derived from the module version if not provided.
        http_api_version = '.'.join(project_version.split('.')[0:2])
    settings['http_api_version'] = http_api_version = str(http_api_version)
    # api_version = 'v%s' % http_api_version.split('.')[0]
    # config.route_prefix = api_version
