"""briefy.ws.resources events."""
from briefy.common.event import BaseEvent
from briefy.common.event import IDataEvent
from briefy.ws import logger
from zope.interface import implementer


class BaseResourceObjectEvent(BaseEvent):
    """Base class for object events: load and delete."""

    def __init__(self, obj, request):
        self.request = request
        self.obj = obj


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
        self.request = request
        user = getattr(request, 'user', None)
        if user:
            user_id = user.id
        else:
            user_id=None
        super().__init__(obj, user_id)


class ObjectCreatedEvent(ResourceObjectEvent):
    """Event to notify database object creation."""

    event_name = 'resource_obj.created'


class ObjectUpdatedEvent(ResourceObjectEvent):
    """Event to notify database object updated."""

    event_name = 'resource_obj.updated'


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
        return name.format(model_name=model_name, transiton_name=transition_name)

    def __init__(self, obj, request, transition):
        self.request = request
        self.transition = transition
        user = getattr(request, 'user', None)
        if user:
            user_id = user.id
        else:
            user_id=None
        super().__init__(obj, user_id)
