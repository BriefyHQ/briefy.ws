from briefy.common.db import Base
from briefy.ws.resources import events
from briefy.ws.resources import RESTService

import sqlalchemy as sa


class TestModel(Base):
    """A Model."""

    __tablename__ = 'test_model'

    __raw_acl__ = (
        ('create', ('g:briefy',)),
        ('list', ('g:briefy',)),
        ('view', ('g:briefy',)),
        ('edit', ('g:briefy',)),
        ('delete', ('g:briefy',)),
    )

    id = sa.Column(sa.String, nullable=False, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    guid = sa.Column(sa.String, nullable=True)


def test_base_resource_init(login, web_request, context):
    """Test initialization of a resource."""
    service = RESTService(context, web_request)
    assert service.request is web_request
    assert service.context is context


def test_base_resource_get(login, web_request, context, model_class):
    """Test get method of rest resource."""
    service = RESTService(context, web_request)
    service.model = model_class
    response = service.get()
    assert isinstance(response, model_class) is True
    assert len(web_request.registry.notifications) == 0


def test_base_resource_collection_post(login, web_request, context, model_class):
    """Test collection_post method of rest resource."""
    service = RESTService(context, web_request)
    service.model = model_class
    response = service.collection_post()
    assert isinstance(response, model_class) is True
    assert isinstance(web_request.registry.notifications[0], events.ObjectCreatedEvent)


def test_base_resource_collection_get(login, web_request, context, model_class, database):
    """Test collection_get method of rest resource."""
    service = RESTService(context, web_request)
    TestModel.__session__ = database
    service.model = TestModel
    service.enable_security = False
    response = service.collection_get()
    assert 'data' in response
    assert 'pagination' in response


def test_base_resource_put(login, web_request, context, model_class):
    service = RESTService(context, web_request)
    service.model = model_class
    response = service.put()
    assert isinstance(response, model_class) is True
    assert isinstance(web_request.registry.notifications[0], events.ObjectUpdatedEvent)


def test_base_resource_delete(login, web_request, context, model_class):
    service = RESTService(context, web_request)
    service.model = model_class
    response = service.delete()
    assert isinstance(response, model_class) is True
    assert isinstance(web_request.registry.notifications[0], events.ObjectDeletedEvent)
