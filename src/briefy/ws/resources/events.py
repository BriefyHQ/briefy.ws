"""briefy.ws.resources events."""
from briefy.common.event import BaseEvent
from briefy.common.event import IDataEvent
from briefy.ws import logger
from zope.interface import implementer


class BaseResourceObjectEvent:
    """Base class for object events: load and delete."""

    def __init__(self, obj, request, **kwargs):
        """Custom init to call parent BaseEvent if it exist."""
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
        """Custom init to call parent BaseEvent if it exist."""
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
