"""Webservice base resource."""
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
    def schema_write(self):
        """Schema for write operations."""
        colander_config = self.model.__colanderalchemy_config__
        excludes = colander_config.get('excludes', self.default_excludes)
        return data.BriefySchemaNode(
            self.model, unknown='ignore', excludes=excludes
        )

    @property
    def schema_get(self):
        """Return the schema for GET requests."""
        return self.schema_read

    @property
    def schema_post(self):
        """Return the schema for POST requests."""
        return self.schema_write

    @property
    def schema_put(self):
        """Return the schema for PUT requests."""
        schema = self.schema_write
        required_fields = self.get_required_fields('PUT')
        for child in schema.children:
            if child.title not in required_fields:
                child.missing = colander.drop
                child.default = colander.null
        return schema

    @view(validators='_run_validators', permission='create')
    def collection_post(self, model=None):
        """Add a new instance.

        :returns: Newly created instance
        """
        self.set_transaction_name('collection_post')
        request = self.request
        payload = request.validated
        model = model if model else self.model

        # verify if object with same ID exists
        obj_id = payload.get('id')
        if obj_id:
            obj_exists = model.get(obj_id)
            if obj_exists:
                self.raise_invalid('body', 'id', 'Duplicate object UUID: {id}'.format(id=obj_id))

        try:
            obj = model.create(payload)
        except ValidationError as e:
            error_details = {
                'location': e.location,
                'description': e.message,
                'name': e.name
            }
            self.raise_invalid(**error_details)
        except Exception as exc:
            logger.exception(
                'Error creating an instance of {klass}'.format(klass=model.__name__)
            )
            raise ValueError from exc
        else:
            self.notify_obj_event(obj, 'POST')
            return obj

    @view(validators='_run_validators', permission='list')
    def collection_head(self):
        """Return the header with total objects for this request."""
        self.set_transaction_name('collection_head')
        headers = self.request.response.headers
        total_records = self.count_records()
        headers['Total-Records'] = '{total}'.format(total=total_records)

    @view(validators='_run_validators', permission='list')
    def collection_get(self):
        """Return a list of objects.

        :returns: Payload with total records and list of objects
        """
        self.set_transaction_name('collection_get')
        headers = self.request.response.headers
        pagination = self.get_records()
        total = pagination['total']
        headers['Total-Records'] = '{total}'.format(total=total)
        # Force in here to use the listing serialization.
        pagination['data'] = [o.to_listing_dict() for o in pagination['data']]
        # also append columns metadata if available
        columns_map = self._columns_map
        if columns_map:
            pagination['columns'] = columns_map
        return pagination

    @view(validators='_run_validators', permission='view')
    def get(self):
        """Get an instance of the model object."""
        self.set_transaction_name('get')
        id = self.request.matchdict.get('id', '')
        obj = self.get_one(id, permission='view')
        return obj

    @view(validators='_run_validators', permission='edit')
    def put(self):
        """Update an existing object."""
        self.set_transaction_name('put')
        id = self.request.matchdict.get('id', '')
        obj = self.get_one(id, permission='edit')
        try:
            obj.update(self.request.validated)
        except ValidationError as e:
            error_details = {
                'location': e.location,
                'description': e.message,
                'name': e.name
            }
            self.raise_invalid(**error_details)
        except Exception as e:
            logger.exception(
                'Error updating an instance {id} of {klass}'.format(
                    id=obj.id,
                    klass=obj.__class__.__name__
                )
            )
            raise ValueError from e
        else:
            self.session.flush()
            self.notify_obj_event(obj, 'PUT')
            return obj

    @view(permission='delete')
    def delete(self):
        """Soft delete an object if there is an appropriated transition for it."""
        self.set_transaction_name('delete')
        obj = self.get_one(id, permission='delete')
        # We do not delete things from the Database -
        # The delete event should be enough to trigger
        # transitions that will set a delete-like
        # state for the object, if appropriate
        self.notify_obj_event(obj, 'DELETE')
        return obj
