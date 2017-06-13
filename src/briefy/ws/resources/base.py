"""Webservice base resource."""
from briefy.common.db.mixins import LocalRolesMixin
from briefy.ws import logger
from briefy.ws.auth import validate_jwt_token
from briefy.ws.errors import ValidationError
from briefy.ws.resources.validation import validate_id
from briefy.ws.utils import data
from briefy.ws.utils import filter
from briefy.ws.utils import paginate
from briefy.ws.utils import user
from cornice.util import json_error
from cornice.validators import colander_body_validator
from pyramid.httpexceptions import HTTPNotFound as NotFound
from pyramid.httpexceptions import HTTPUnauthorized as Unauthorized

import newrelic.agent
import sqlalchemy as sa


class BaseResource:
    """Base class for resources."""

    model = None
    items_per_page = 25
    default_order_by = 'updated_at'
    default_order_direction = 1
    filter_related_fields = []
    enable_security = True

    _default_notify_events = {}

    def __init__(self, context, request):
        """Initialize the service."""
        self.context = context
        self.request = request
        cls_ = self.__class__
        self._transaction_name = '{0}:{1}'.format(cls_.__module__, cls_.__name__)

    @property
    def friendly_name(self):
        """Return friendly name from the model class."""
        return self.model.__name__

    def set_transaction_name(self, suffix):
        """Set newrelic transaction name."""
        name = '{0}.{1}'.format(self._transaction_name, suffix)
        newrelic.agent.set_transaction_name(name, 'WebService')

    @property
    def session(self):
        """Return a session object from the request."""
        return self.request.registry['db_session_factory']()

    @property
    def schema_read(self):
        """Schema for read operations."""
        return data.NullSchema(unknown='ignore')

    @property
    def schema(self):
        """Return the schema to validate this resource."""
        method = self.request.method
        colander_schema = getattr(
            self,
            'schema_{method}'.format(method=method.lower()),
            self.schema_read
        )
        return colander_schema

    def get_user_info(self, user_id: str) -> dict:
        """Get public information about an user with given user_id.

        :param user_id: Id of the user.
        :return: Public information about this user.
        """
        return user.get_public_user_info(user_id)

    def default_filters(self, query) -> object:
        """Default filters to be applied to every query.

        This is supposed to be specialized by resource classes.
        :returns: A tuple of default filters to be applied to queries.
        """
        return query

    def _get_base_query(self, permission='view'):
        """Return the base query for this service.

        :return: Query object with default filter already applie.
        """
        context = self.context
        model = self.model
        user = self.request.user
        principal_id = self.request.user.id
        has_global_permission = context.has_global_permissions(
            permission, user.groups
        )
        kwargs = {}
        lr_subclass = issubclass(self.model, LocalRolesMixin)
        if self.enable_security and not has_global_permission and lr_subclass:
            kwargs['principal_id'] = principal_id
            kwargs['permission'] = f'can_{permission}'
        try:
            query = model.query(**kwargs)
        except AttributeError:
            msg = f'Permission attribute do not exists in model ' \
                  f'{self.friendly_name} user: {principal_id} Parms: {kwargs}'
            logger.error(msg)
            raise Unauthorized(msg)
        query = self.default_filters(query)
        return query

    def get_required_fields(self, method: str) -> tuple:
        """Get required fields for a method.

        :param method: HTTP verb to filter fields for.
        :return: tuple with required fields.
        """
        mapping = dict(self._required_fields)
        return mapping.get(method, tuple())

    _validators = (
        ('GET', ('validate_id', )),
        ('PUT', ('validate_id', ))
    )

    @property
    def schema_filter(self):
        """Schema for filtering and ordering operations."""
        return data.BriefySchemaNode(self.model, unknown='ignore')

    @property
    def filter_allowed_fields(self):
        """List of fields allowed in filtering and sorting."""
        schema = self.schema_filter
        allowed_fields = [child.name for child in schema.children]
        # Allow filtering by state
        allowed_fields.append('state')
        for field in self.filter_related_fields:
            allowed_fields.append(field)
        return allowed_fields

    @property
    def validators(self) -> dict:
        """Return mapping of validators.

        :return: Dictionary containing validators per HTTP verb.
        """
        mapping = dict(self._validators)
        return mapping

    def validate_id(self, request):
        """Check if id parameter is UUID valid.

        :param request: pyramid request.
        :return:
        """
        validate_id(request)

    def _run_validators(self, request, **kwargs):
        """Run all validators for the current http method.

        :param request: request object
        """
        # first #ForaTemer, second always validate jwt token on request.
        validate_jwt_token(request)

        validators = self.validators.get(self.request.method, [])
        for item in validators:
            try:
                if type(item) == str:
                    validator = getattr(self, item)
                else:
                    validator = item
            except AttributeError as e:
                raise AttributeError('Validator "{name}" specified not found.'.format(name=item))
            else:
                validator(request)
        colander_body_validator(request, self.schema)

    def raise_invalid(self, location='body', name=None, description=None, **kwargs):
        """Raise a 400 error.

        :param location: location in request (e.g. ``'querystring'``)
        :param name: field name
        :param description: detailed description of validation error
        """
        request = self.request
        request.errors.add(location, name, description, **kwargs)
        raise json_error(request)

    def notify_obj_event(self, obj, method=None):
        """Create right event object based on current request method.

        :param obj: sqlalchemy model obj instance
        """
        request = self.request
        if 'Briefy-SyncBot' in request.headers.get('User-Agent', ''):
            return
        method = method or request.method
        # if the model defines the events it takes precedence from the service definition
        if getattr(obj, '_default_notify_events', None):
            event_klass = obj._default_notify_events.get(method)
        else:
            event_klass = self._default_notify_events.get(method)
        if event_klass:
            event = event_klass(obj, request)
            request.registry.notify(event)
            # also execute the event to dispatch to sqs if needed
            event()

    def get_one(self, id, permission='view'):
        """Given an id, return an instance of the model object or raise a not found exception.

        :param id: Id for the object
        :return: Object
        """
        model = self.model
        query = self._get_base_query(permission=permission)
        obj = query.filter(model.id == id).one_or_none()

        if not obj:
            raise NotFound(
                '{friendly_name} with id: {id} not found.'.format(
                    friendly_name=self.friendly_name,
                    id=id
                )
            )
        return obj

    def _get_records_query(self, permission='view'):
        """Return a base query for records.

        :return: tuple
        """
        query_params = self.request.GET
        query = self._get_base_query(permission=permission)

        # Apply filters
        query = self.filter_query(query, query_params)

        # Apply sorting
        query = self.sort_query(query, query_params)
        return query, query_params

    def get_records(self):
        """Get all records for this resource and return a dictionary.

        :return: dict
        """
        query, query_params = self._get_records_query()
        pagination = self.paginate(query, query_params)
        return pagination

    def count_records(self) -> int:
        """Count records for a request.

        :return: Count of records to be returned
        """
        query, query_params = self._get_records_query()
        return query.count()

    def get_column_from_key(self, query, key):
        """Get a column and join based on a key.

        :return: A new query with a join with necessary,
                 A column in the own model or from a related one
        """
        if '.' in key:
            relationship_column_name, field = key.split('.')
            query = query.join(relationship_column_name)
            column = getattr(self.model, relationship_column_name, None)
            column = getattr(column.property.mapper.c, field, None)
        else:
            column = getattr(self.model, key, None)

        return query, column

    def filter_query(self, query, query_params=None):
        """Apply request filters to a query."""
        try:
            raw_filters = filter.create_filter_from_query_params(
                query_params,
                self.filter_allowed_fields
            )
        except ValidationError as e:
            error_details = {
                'location': e.location,
                'description': e.message,
                'name': e.name
            }
            self.raise_invalid(**error_details)

        for raw_filter in raw_filters:
            key = raw_filter.field
            value = raw_filter.value
            op = raw_filter.operator.value
            query, column = self.get_column_from_key(query, key)

            if value == 'null':
                value = None

            possible_names = [name.format(op=op) for name in ['{op}', '{op}_', '__{op}__']]
            attrs = [getattr(column, name) for name in possible_names if hasattr(column, name)]

            if not attrs:
                error_details = {
                    'location': 'querystring',
                    'description': "Invalid filter operator: '{op}'".format(op=op)
                }
                self.raise_invalid(**error_details)
            else:
                filt = attrs[0](value)

            query = query.filter(filt)

        return query

    def sort_query(self, query, query_params=None):
        """Apply request sorting to a query."""
        try:
            raw_sorting = filter.create_sorting_from_query_params(
                query_params,
                self.filter_allowed_fields,
                self.default_order_by,
                self.default_order_direction
            )
        except ValidationError as e:
            error_details = {
                'location': e.location,
                'description': e.message,
                'name': e.name
            }
            self.raise_invalid(**error_details)

        for sorting in raw_sorting:
            key = sorting.field
            direction = sorting.direction
            func = sa.asc
            if direction == -1:
                func = sa.desc
            query, column = self.get_column_from_key(query, key)
            query = query.order_by(func(column))
        return query

    def paginate(self, query, query_params: dict=None):
        """Pagination."""
        if '_items_per_page' not in query_params:
            query_params['_items_per_page'] = str(self.items_per_page)
        params = paginate.extract_pagination_from_query_params(query_params)
        params['collection'] = query
        pagination = paginate.SQLPage(**params)
        return pagination()
