from briefy.ws.resources import events
from briefy.ws.resources import RESTService


def test_base_resource_init(login, web_request, context):
    """Test initialization of a resource."""
    service = RESTService(context, web_request)
    assert service.request is web_request
    assert service.context is context


def test_base_resource_get(login, web_request, context, model_class):
    """Test get method of rest resource."""
    service = RESTService(context, web_request)
    service.model = model_class
    service.get()
    assert len(web_request.registry.notifications) == 0


def test_base_resource_post(login, web_request, context, model_class):
    """Test collection_post method of rest resource."""
    service = RESTService(context, web_request)
    service.model = model_class
    service.collection_post()
    assert isinstance(web_request.registry.notifications[0], events.ObjectCreatedEvent)


def test_base_resource_put(login, web_request, context, model_class):
    service = RESTService(context, web_request)
    service.model = model_class
    service.put()
    assert isinstance(web_request.registry.notifications[0], events.ObjectUpdatedEvent)


def test_base_resource_delete(login, web_request, context, model_class):
    service = RESTService(context, web_request)
    service.model = model_class
    service.delete()
    assert isinstance(web_request.registry.notifications[0], events.ObjectDeletedEvent)
