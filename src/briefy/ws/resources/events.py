"""briefy.ws.resources events."""


class ResourceObjectEvent:
    """Base class for object events"""
    def __init__(self, obj, request):
        self.obj = obj
        self.request = request


class ObjectCreatedEvent(ResourceObjectEvent):
    """Event to notify database object creation."""
    pass


class ObjectLoadedEvent(ResourceObjectEvent):
    """Event to notify database object load."""
    pass


class ObjectUpdatedEvent(ResourceObjectEvent):
    """Event to notify database object updated."""
    pass


class ObjectDeletedEvent(ResourceObjectEvent):
    """Event to notify database object deleted."""
    pass
