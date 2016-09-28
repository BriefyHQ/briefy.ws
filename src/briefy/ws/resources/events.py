"""briefy.ws.resources events."""
from briefy.common.event import BaseEvent
from briefy.common.event import IDataEvent
from briefy.ws import logger
from zope.interface import implementer

import json


class BaseResourceObjectEvent:
    """Base class for object events: load and delete."""

    def __init__(self, obj, request, **kwargs):
        self.request = request
        self.obj = obj
        try:
            super().__init__(obj, **kwargs)
        except TypeError:
            pass  # TODO: fix this to look to __mro__ and use different call

    def __call__(self):
        """Notify about the event, need to be implemented by subclass.

        :returns: Id from message in the queue
        :rtype: str
        """
        try:
            super().__call__()
        except AttributeError:
            pass  # TODO: fix this to look to __mro__ and use different call
        return ''


class ObjectLoadedEvent(BaseResourceObjectEvent):
    """Event to notify database object load."""


class ObjectDeletedEvent(BaseResourceObjectEvent):
    """Event to notify database object deleted."""


class IResourceObjectEvent(IDataEvent):
    """IDataEvent interface for a model object in a resource service."""


@implementer(IResourceObjectEvent)
class ResourceObjectEvent(BaseResourceObjectEvent, BaseEvent):
    """Base class for object events that will be queued on sqs: create and update."""

    logger = logger

    def __init__(self, obj, request):
        user = getattr(request, 'user', None)
        if user:
            user_id = user.id
        else:
            user_id = None
        kwargs = dict(actor=user_id, request_id=None)
        super().__init__(obj, request, **kwargs)


class ObjectCreatedEvent(ResourceObjectEvent):
    """Event to notify database object creation."""

    event_name = 'obj.created'


class ObjectUpdatedEvent(ResourceObjectEvent):
    """Event to notify database object updated."""

    event_name = 'obj.updated'


class IWorkflowTransitionEvent(IDataEvent):
    """IDataEvent interface for a workflow transition in a workflow."""


@implementer(IWorkflowTransitionEvent)
class WorkflowTranstionEvent(BaseEvent):
    """Base class for workflow transition events that will be queued on sqs."""

    logger = logger

    @property
    def event_name(self):
        model_name = self.obj.__class__.__name__.lower()
        transition_name = self.transition.name
        name = '{model_name}.workflow.{transition_name}'
        return name.format(model_name=model_name, transition_name=transition_name)

    def __init__(self, obj, request, transition):
        self.transition = transition
        self.request = request
        self.obj = obj
        user = getattr(request, 'user', None)
        if user:
            user_id = user.id
        else:
            user_id = None
        kwargs = dict(actor=user_id, request_id=None)
        super().__init__(obj, **kwargs)

    def __call__(self):
        """Notify about the event.

        :returns: Id from message in the queue
        :rtype: str
        """
        logger = self.logger
        queue = self.queue
        payload = {
            'event_name': self.event_name,
            'actor': self.actor,
            'guid': self.guid,
            'created_at': self.created_at,
            'request_id': self.request_id,
            'data': json.loads(self.data),
            'transition': self.transition.name,
        }
        message_id = ''
        try:
            message_id = queue.write_message(payload)
        except Exception as e:
            logger.error('Event {} not fired. Exception: {}'.format(self.event_name, e),
                         extra={'payload': payload})
        else:
            logger.debug('Event {} fired with message {}'.format(self.event_name, message_id))

        return message_id
