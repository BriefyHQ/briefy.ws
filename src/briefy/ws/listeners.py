"""briefy.ws SQLAlchemy listener to events for Base model."""

from briefy.common.db import model
from pyramid.threadlocal import get_current_request
from sqlalchemy import event


@event.listens_for(model.Base, 'init')
def base_receive_init(target, args, kwargs):
    """Listener to insert request.user as workflow_context init parameter of all models.

    :param target: model instance
    :param args: list of model init arguments
    :param kwargs: dict of model keyword arguments
    """
    request = get_current_request()
    if request:
        auth_user = request.user
        if auth_user and hasattr(target, 'workflow_context'):
            kwargs['workflow_context'] = auth_user


@event.listens_for(model.Base, 'load')
def base_receive_load(target, context):
    """Listener to set request.user as workflow_context in all models.

    :param target: model instance
    :param context: sqlalchemy query context
    """
    request = get_current_request()
    if request:
        auth_user = request.user
        if auth_user and hasattr(target, 'workflow_context'):
            target.workflow_context = auth_user
