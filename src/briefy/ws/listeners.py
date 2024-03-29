"""briefy.ws sqlalchemy event handlers for model classes."""
from briefy.common.db.mixins.workflow import WorkflowBase
from briefy.common.db.model import Base
from pyramid.threadlocal import get_current_request
from sqlalchemy import event as sa_event

import typing as t


def base_receive_init_workflow_context(
        target: Base,
        args: t.List,
        kwargs: dict
):
    """Listener to insert request.user as workflow_context and request.

    Both are passed as init parameters of all models that have these attributes.

    :param target: model instance
    :param args: list of model init arguments
    :param kwargs: dict of model keyword arguments
    """
    request = get_current_request()
    if request:
        if isinstance(target, WorkflowBase):
            kwargs['request'] = request
        auth_user = request.user
        if auth_user and hasattr(target, 'workflow_context'):
            kwargs['workflow_context'] = auth_user


def base_receive_load_workflow_context(
        target: Base,
        context
):
    """Listener to set request.user as workflow_context and request in all models.

    Both are set for all models that have these attributes.

    :param target: model instance
    :param context: sqlalchemy query context
    """
    request = get_current_request()
    if request:
        if 'request' in target.__dir__() and not getattr(target, 'request', None):
            target.request = request
        auth_user = request.user
        set_user = hasattr(target, 'workflow_context') and not target.workflow_context
        if auth_user and set_user:
            target.workflow_context = auth_user


def register_workflow_context_listeners(models: t.Sequence[Base]):
    """For all models in the list register the workflow context handlers.

    :param models: list of model classes
    """
    for model_klass in models:
        sa_event.listen(model_klass, 'init', base_receive_init_workflow_context)
        sa_event.listen(model_klass, 'load', base_receive_load_workflow_context)
