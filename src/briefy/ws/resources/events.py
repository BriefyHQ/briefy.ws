"""briefy.ws.resources events."""


class ResourceObjectEvent:
    """Base class for object events"""
    def __init__(self, obj, request):
        self.obj = obj
        self.request = request


class ObjectCreatedEvent(ResourceObjectEvent):
    """Event to notify database object creation."""


class ObjectLoadedEvent(ResourceObjectEvent):
    """Event to notify database object load."""


class ObjectUpdatedEvent(ResourceObjectEvent):
    """Event to notify database object updated."""


class ObjectDeletedEvent(ResourceObjectEvent):
    """Event to notify database object deleted."""
