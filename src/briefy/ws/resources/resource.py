"""Webservice base resource."""
from briefy.common.db.model import Base
from briefy.ws import logger
from briefy.ws.errors import ValidationError
from briefy.ws.resources import BaseResource
from briefy.ws.resources import events
from briefy.ws.utils import data
from cornice.resource import view

import colander


class RESTService(BaseResource):
    """Rest service based on a model."""

    default_excludes = ['created_at', 'updated_at', 'state_history', 'state']

    _required_fields = (
        ('PUT', tuple()),
    )

    _columns_map = ()
    """Tuple with all metadata about the fields returned in the listing set payload.

    This data will be available in the payload as "columns" attribute.
    Ex::

        _column_map = (
            {'field': 'country', 'label': 'Country', 'type': 'country', 'url': '', 'filter': ''},
            {'field': 'total', 'label': 'Total', 'type': 'integer', 'url': '', 'filter': ''},
        )

    """

    _default_notify_events = {
        'POST': events.ObjectCreatedEvent,
        'PUT': events.ObjectUpdatedEvent,
        'GET': events.ObjectLoadedEvent,
        'DELETE': events.ObjectDeletedEvent,
    }

    @property
    def schema_write(self) -> colander.SchemaNode:
        """Schema for write operations."""
        colander_config = self.model.__colanderalchemy_config__
        excludes = colander_config.get('excludes', self.default_excludes)
        return data.BriefySchemaNode(self.model, unknown='ignore', excludes=excludes)

    @property
    def schema_get(self) -> colander.SchemaNode:
        """Return the schema for GET requests."""
        return self.schema_read

    @property
    def schema_post(self) -> colander.SchemaNode:
        """Return the schema for POST requests."""
        return self.schema_write

    @property
    def schema_put(self) -> colander.SchemaNode:
        """Return the schema for PUT requests."""
        schema = self.schema_write
        required_fields = self.get_required_fields('PUT')
        for child in schema.children:
            if child.title not in required_fields:
                child.missing = colander.drop
                child.default = colander.null
        return schema

    @view(validators='_run_validators', permission='create')
    def collection_post(self, model: Base=None) -> dict:
        """Add a new instance.

        :returns: Newly created instance
        """
        self.set_transaction_name('collection_post')
        request = self.request
        payload = request.validated
        model = model if model else self.model

        # verify if object with same ID exists
        obj_id = payload.get('id')
        if obj_id and model.get(obj_id):
            return self.raise_invalid('body', 'id', f'Duplicate object UUID: {obj_id}')

        try:
            obj = model.create(payload)
        except ValidationError as e:
            error_details = {'location': e.location, 'description': e.message, 'name': e.name}
            return self.raise_invalid(**error_details)
        except Exception as exc:
            logger.exception(f'Error creating an instance of {model.__name__}')
            raise ValueError from exc

        self.notify_obj_event(obj, 'POST')
        return obj.to_dict()

    @view(validators='_run_validators', permission='list')
    def collection_head(self) -> None:
        """Return the header with total objects for this request."""
        self.set_transaction_name('collection_head')
        headers = self.request.response.headers
        total_records = self.count_records()
        headers['Total-Records'] = '{total}'.format(total=total_records)

    @view(validators='_run_validators', permission='list')
    def collection_get(self) -> dict:
        """Return a list of objects.

        :returns: Payload with total records and list of objects
        """
        self.set_transaction_name('collection_get')
        headers = self.request.response.headers
        try:
            pagination = self.get_records()
        except ValidationError as e:
            error_details = {'location': e.location, 'description': e.message, 'name': e.name}
            return self.raise_invalid(**error_details)

        headers['Total-Records'] = str(self.count_records())
        # Force in here to use the listing serialization.
        pagination['data'] = [o.to_listing_dict() for o in pagination['data']]
        # also append columns metadata if available
        columns_map = self._columns_map
        if columns_map:
            pagination['columns'] = columns_map
        return pagination

    @view(validators='_run_validators', permission='view')
    def get(self) -> Base:
        """Get an instance of the model object."""
        self.set_transaction_name('get')
        id = self.request.matchdict.get('id', '')
        obj = self.get_one(id, permission='view')
        return obj

    @view(validators='_run_validators', permission='edit')
    def put(self) -> Base:
        """Update an existing object."""
        self.set_transaction_name('put')
        id = self.request.matchdict.get('id', '')
        obj = self.get_one(id, permission='edit')
        try:
            obj.update(self.request.validated)
        except ValidationError as e:
            error_details = {'location': e.location, 'description': e.message, 'name': e.name}
            return self.raise_invalid(**error_details)
        except Exception as e:
            logger.exception(f'Error updating an instance {obj.id} of {obj.__class__.__name__}')
            raise ValueError from e
        else:
            self.session.flush()
            self.notify_obj_event(obj, 'PUT')
            return obj

    @view(permission='delete')
    def delete(self) -> Base:
        """Soft delete an object if there is an appropriated transition for it."""
        self.set_transaction_name('delete')
        id = self.request.matchdict.get('id', '')
        obj = self.get_one(id, permission='delete')
        # We do not delete things from the Database -
        # The delete event should be enough to trigger
        # transitions that will set a delete-like
        # state for the object, if appropriate
        self.notify_obj_event(obj, 'DELETE')
        return obj
