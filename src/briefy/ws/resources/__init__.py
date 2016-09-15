"""Base Resources for briefy.ws."""
from briefy.ws.utils import data
from briefy.ws.utils import filter
from colanderalchemy import SQLAlchemySchemaNode
from cornice.schemas import CorniceSchema
from cornice.util import json_error
from cornice.resource import view
from pyramid.httpexceptions import HTTPNotFound as NotFound


import sqlalchemy as sa
import uuid


class RESTService:
    """Rest service based on a model."""

    model = None
    friendly_name = ''
    default_order_by = 'updated_at'
    default_order_direction = 1
    default_excludes = ['created_at', 'updated_at', 'state_history', 'state']

    validators = {
        'GET': ['validate_id'],
        'PUT': ['validate_id']
    }

    def validate_id(self, request):
        """Validate id in matchdict is UUID valid.

        :param request: pyramid request.
        :return:
        """
        try:
            uuid.UUID(request.matchdict.get('id'))
        except ValueError as e:
            request.errors.add('path', 'id',
                               'The id informed is not 16 byte uuid valid.')

    def __init__(self, request):
        """Initialize the service."""
        self.request = request

    def _run_validators(self, request):
        """Run all validators for the current http method.

        :param request: request object
        """
        validators = self.validators.get(self.request.method, [])
        for item in validators:
            try:
                validator = getattr(self, item)
            except AttributeError as e:
                raise AttributeError('Validator "{name}" specified not found.'.format(name=item))
            else:
                validator(request)

    def raise_invalid(self, location='body', name=None, description=None, **kwargs):
        """Raise a 400 error.

        :param location: location in request (e.g. ``'querystring'``)
        :param name: field name
        :param description: detailed description of validation error
        """
        request = self.request
        request.errors.add(location, name, description, **kwargs)
        raise json_error(request.errors)

    @property
    def schema_filter(self):
        """Schema for filtering and ordering operations."""
        return SQLAlchemySchemaNode(self.model, unknown='ignore')

    @property
    def filter_allowed_fields(self):
        """List of fields allowed in filtering and sorting.
        """
        schema = self.schema_filter
        return [child.name for child in schema.children]

    @property
    def schema_read(self):
        """Schema for read operations."""
        return data.NullSchema(unknown='ignore')

    @property
    def schema_write(self):
        """Schema for write operations."""
        colander_config = self.model.__colanderalchemy_config__
        excludes = colander_config.get('excludes', self.default_excludes)
        return SQLAlchemySchemaNode(
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
        return self.schema_write

    @property
    def schema(self):
        """Returns the schema to validate this resource."""
        method = self.request.method
        colander_schema = getattr(
            self,
            'schema_{method}'.format(method=method.lower()),
            self.schema_read
        )
        schema = CorniceSchema.from_colander(colander_schema)
        return schema

    @property
    def session(self):
        """Return a session object from the request."""
        return self.request.registry['db_session_factory']()

    def get_one(self, id):
        """Given an id, return an instance of the model object or raise a not found exception.

        :param id: Id for the object
        :return: Category
        """
        model = self.model
        obj = model.get(id)
        if not obj:
            raise NotFound(
                '{friendly_name} with id: {id} not found.'.format(
                    friendly_name=self.friendly_name,
                    id=id
                )
            )
        return obj

    def get_records(self):
        """Get all records for this resource and return a dictionary.

        :return: dict
        """
        query_params = self.request.GET
        model = self.model
        query = model.query()

        # Apply filters
        query = self.filter_query(query, query_params)

        # Apply sorting
        query = self.sort_query(query, query_params)

        total = query.count()
        records = query.all()

        return {
            'total': total,
            'data': records
        }

    @view(validators='_run_validators')
    def collection_post(self):
        """Add a new instance.

        :returns: Newly created instance
        """
        payload = self.request.validated
        session = self.session
        model = self.model
        obj = model(**payload)
        session.add(obj)
        session.flush()
        return obj

    def collection_get(self):
        """Return a list of objects.

        :returns: Payload with total records and list of objects
        """
        headers = self.request.response.headers
        records = self.get_records()
        headers['Total-Records'] = '{total}'.format(total=records['total'])
        collection = records['data']
        return {
            'total': records['total'],
            'data': collection,
        }

    @view(validators='_run_validators')
    def get(self):
        """Get an instance of the model object."""
        id = self.request.matchdict.get('id', '')
        obj = self.get_one(id)
        return obj

    @view(validators='_run_validators')
    def put(self):
        """Update an existing object."""
        id = self.request.matchdict.get('id', '')
        obj = self.get_one(id)
        obj.update(self.request.validated)
        self.session.flush()
        return obj

    def filter_query(self, query, query_params=None):
        """Apply request filters to a query."""
        model = self.model
        raw_filters = filter.create_filter_from_query_params(
            query_params,
            self.filter_allowed_fields
        )
        for raw_filter in raw_filters:
            key = raw_filter.field
            value = raw_filter.value
            op = raw_filter.operator.value

            column = getattr(model, key, None)

            if value == 'null':
                value = None

            possible_names = [name.format(op=op) for name in ['{op}', '{op}_', '__{op}__']]
            attrs = [getattr(column, name) for name in possible_names if hasattr(column, name)]

            if not attrs:
                error_details = {
                    'location': 'querystring',
                    'description': "Invalid filter operator: '{op}'".format(op)
                }
                self.raise_invalid(**error_details)
            else:
                filt = attrs[0](value)
            query = query.filter(filt)
        return query

    def sort_query(self, query, query_params=None):
        """Apply request sorting to a query."""
        model = self.model
        raw_sorting = filter.create_sorting_from_query_params(
            query_params,
            self.filter_allowed_fields,
            self.default_order_by,
            self.default_order_direction
        )
        for sorting in raw_sorting:
            key = sorting.field
            direction = sorting.direction
            column = getattr(model, key, None)
            func = sa.asc
            if direction == -1:
                func = sa.desc
            query = query.order_by(func(column))
        return query
