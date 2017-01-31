"""briefy.ws sqlalchemy event handlers for model classes."""
from pyramid.threadlocal import get_current_request
from sqlalchemy import event as sa_event


def base_receive_init_workflow_context(target, args, kwargs):
    """Listener to insert request.user as workflow_context and request.

    Both are passed as init parameters of all models that have these attributes.

    :param target: model instance
    :param args: list of model init arguments
    :param kwargs: dict of model keyword arguments
    """
    request = get_current_request()
    if request:
        kwargs['request'] = request
        auth_user = request.user
        if auth_user and hasattr(target, 'workflow_context'):
            kwargs['workflow_context'] = auth_user


def base_receive_load_workflow_context(target, context):
    """Listener to set request.user as workflow_context and request in all models.

    Both are set for all models that have these attributes.

    :param target: model instance
    :param context: sqlalchemy query context
    """
    request = get_current_request()
    if request:
        if hasattr(target, 'request'):
            target.request = request
        auth_user = request.user
        if auth_user and hasattr(target, 'workflow_context'):
            target.workflow_context = auth_user


def register_workflow_context_listeners(models) -> list:
    """For all models in the list register the workflow context handlers.

    :param models: list of model classes
    :type models: list
    """
    for model_klass in models:
        sa_event.listen(model_klass, 'init', base_receive_init_workflow_context)
        sa_event.listen(model_klass, 'load', base_receive_load_workflow_context)
