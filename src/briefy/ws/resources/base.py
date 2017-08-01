"""Webservice base resource."""
from briefy.common.db.mixins import LocalRolesMixin
from briefy.common.db.model import Base
from briefy.ws import logger
from briefy.ws.auth import validate_jwt_token
from briefy.ws.errors import ValidationError
from briefy.ws.resources.factory import BaseFactory
from briefy.ws.resources.validation import validate_id
from briefy.ws.utils import data
from briefy.ws.utils import filter
from briefy.ws.utils import paginate
from briefy.ws.utils import user
from cornice.util import json_error
from cornice.validators import colander_body_validator
from pyramid.httpexceptions import HTTPNotFound as NotFound
from pyramid.httpexceptions import HTTPUnauthorized as Unauthorized
from pyramid.request import Request
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.orm import ColumnProperty
from sqlalchemy.orm import Query
from sqlalchemy.orm import Session

import colander
import newrelic.agent
import sqlalchemy as sa
import typing as t


class BaseResource:
    """Base class for resources."""

    model = None
    items_per_page = 25
    default_order_by = 'updated_at'
    default_order_direction = 1
    filter_related_fields = ()
    enable_security = True

    _required_fields = ()
    _default_notify_events = None
    _item_count = None
    _query = None
    _query_params = None

    def __init__(self, context: BaseFactory, request: Request):
        """Initialize the service."""
        self.context = context
        self.request = request
        cls_ = self.__class__
        self._transaction_name = f'{cls_.__module__}:{cls_.__name__}'

    @property
    def friendly_name(self) -> str:
        """Return friendly name from the model class."""
        return self.model.__name__

    def set_transaction_name(self, suffix) -> None:
        """Set newrelic transaction name."""
        newrelic.agent.set_transaction_name(f'{self._transaction_name}.{suffix}', 'WebService')

    @property
    def session(self) -> Session:
        """Return a session object from the request."""
        return self.request.registry['db_session_factory']()

    @property
    def schema_read(self) -> colander.SchemaNode:
        """Schema for read operations."""
        return data.NullSchema(unknown='ignore')

    @property
    def schema(self) -> colander.SchemaNode:
        """Return the schema to validate this resource."""
        method_name = self.request.method.lower()
        return getattr(self, f'schema_{method_name}', self.schema_read)

    def get_user_info(self, user_id: str) -> dict:
        """Get public information about an user with given user_id.

        :param user_id: Id of the user.
        :return: Public information about this user.
        """
        return user.get_public_user_info(user_id)

    def default_filters(self, query: Query) -> Query:
        """Apply default filters to every query.

        This is supposed to be specialized by resource classes.
        :returns: Updated query.
        """
        return query

    def get_notify_event_class(self, method: str, obj: Base) -> t.Optional[t.Callable]:
        """Return a callable to be used to notify events."""
        notify_events = self._default_notify_events or {}
        event_klass = notify_events.get(method)
        obj_attr = getattr(obj, '_default_notify_events', None)
        if obj_attr:
            event_klass = obj_attr.get(method)
        return event_klass

    def _get_base_query(self, permission: str='view') -> Query:
        """Return the base query for this service.

        :return: Query object with default filter already applied.
        """
        context = self.context
        model = self.model
        user = self.request.user
        principal_id = self.request.user.id
        has_global_permission = context.has_global_permissions(permission, user.groups)
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
    def schema_filter(self) -> data.BriefySchemaNode:
        """Schema for filtering and ordering operations."""
        return data.BriefySchemaNode(self.model, unknown='ignore')

    @property
    def filter_allowed_fields(self) -> t.Sequence[str]:
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

    def validate_id(self, request: Request) -> None:
        """Check if id parameter is a valid UUID4.

        If it is not, we add an error to self.request.errors and Cornice will take care of it.
        :param request: pyramid request.
        """
        validate_id(request)

    def _run_validators(self, request: Request, **kwargs):
        """Run all validators for the current http method.

        :param request: request object
        """
        # first #ForaTemer, second always validate jwt token on request.
        validate_jwt_token(request)

        validators = self.validators.get(self.request.method, [])
        for item in validators:
            try:
                validator = item
                if isinstance(item, str):
                    validator = getattr(self, item)
            except AttributeError as e:
                raise AttributeError(f'Validator "{item}" specified not found.')
            else:
                validator(request)
        colander_body_validator(request, self.schema)

    def raise_invalid(self, location: str='body', name: str='', description: str='', **kwargs):
        """Raise a 400 error.

        :param location: location in request (e.g. ``'querystring'``)
        :param name: field name
        :param description: detailed description of validation error
        """
        request = self.request
        request.errors.add(location, name, description, **kwargs)
        raise json_error(request)

    def notify_obj_event(self, obj: Base, method: str='') -> None:
        """Create right event object based on current request method.

        :param obj: sqlalchemy model obj instance
        :param method: HTTP Method, if not provided it will be get from the current request.
        """
        request = self.request
        method = method or request.method
        is_bot = 'Briefy-SyncBot' in request.headers.get('User-Agent', '')
        if not is_bot:
            event_klass = self.get_notify_event_class(method, obj)

            if event_klass:
                event = event_klass(obj, request)
                request.registry.notify(event)
                # also execute the event to dispatch to sqs if needed
                event()

    def get_one(self, id: str, permission: str='view') -> Base:
        """Given an id, return an instance of the model object or raise a not found exception.

        :param id: Id for the object
        :return: Object
        """
        model = self.model
        query = self._get_base_query(permission=permission)
        obj = query.filter(model.id == id).one_or_none()

        if not obj:
            raise NotFound(f'{self.friendly_name} with id: {id} not found.')

        return obj

    def _get_records_query(self, permission: str='view') -> t.Tuple[Query, dict]:
        """Return a base query for records.

        :return: Tuple with Query and query parameters
        """
        if not (self._query and self._query_params):
            _query_params = self.request.GET
            _query = self._get_base_query(permission=permission)

            # Apply filters
            _query = self.filter_query(_query, _query_params)

            # Apply sorting
            _query = self.sort_query(_query, _query_params)
            self._query = _query
            self._query_params = _query_params

        return self._query, self._query_params

    def get_records(self) -> dict:
        """Get all records for this resource and return a dictionary.

        :return: Dictionary with records already paginated.
        """
        query, query_params = self._get_records_query()
        item_count = self.count_records(query)
        pagination = self.paginate(query, query_params, item_count)
        return pagination

    def count_records(self, query: t.Optional[Query]=None) -> int:
        """Count records for a request.

        :return: Count of records to be returned
        """
        if not query:
            query, query_params = self._get_records_query()

        if not self._item_count:
            self._item_count = query.count()

        return self._item_count

    def get_column_from_key(self, query, key) -> t.Tuple[Query, ColumnProperty, str]:
        """Get a column and join based on a key.

        :return: A new query with a join with necessary,
                 A column in the own model or from a related one
                 The field name,
        """
        field = key
        if '.' in key:
            relationship_column_name, field = key.split('.')
            column = getattr(self.model, relationship_column_name, None)
            if not isinstance(column, AssociationProxy):
                query = query.join(relationship_column_name)
                column = getattr(column.property.mapper.c, field, None)
        else:
            column = getattr(self.model, key, None)

        return query, column, field

    def filter_query(self, query: Query, query_params: t.Optional[dict]=None) -> Query:
        """Apply request filters to a query."""
        raw_filters = ()
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
            query, column, sub_key = self.get_column_from_key(query, key)

            if value == 'null':
                value = None

            possible_names = [name.format(op=op) for name in ['{op}', '{op}_', '__{op}__']]

            if isinstance(column, AssociationProxy) and '.' in key:
                remote_class = column.remote_attr.prop.mapper.class_
                dest_column = getattr(remote_class, sub_key)
                attrs = [
                    getattr(dest_column, name)
                    for name in possible_names if hasattr(dest_column, name)
                ]
                filt = column.has(attrs[0](value))
            else:
                attrs = [getattr(column, name) for name in possible_names if hasattr(column, name)]
                filt = attrs[0](value)

            if not attrs:
                error_details = {
                    'location': 'querystring',
                    'description': f'Invalid filter operator: \'{op}\''
                }
                self.raise_invalid(**error_details)

            query = query.filter(filt)

        return query

    def sort_query(self, query: Query, query_params: t.Optional[dict]=None) -> Query:
        """Apply request sorting to a query."""
        raw_sorting = ()
        try:
            raw_sorting = filter.create_sorting_from_query_params(
                query_params,
                self.filter_allowed_fields,
                self.default_order_by,
                self.default_order_direction
            )
        except ValidationError as e:
            error_details = {'location': e.location, 'description': e.message, 'name': e.name}
            self.raise_invalid(**error_details)

        for sorting in raw_sorting:
            key = sorting.field
            direction = sorting.direction
            func = sa.asc
            if direction == -1:
                func = sa.desc
            query, column, key = self.get_column_from_key(query, key)
            query = query.order_by(func(column))
        return query

    def paginate(
            self,
            query: Query,
            query_params: t.Optional[dict]=None,
            item_count: t.Optional[int]=None
    ) -> dict:
        """Execute the Query, return the paginated results."""
        if '_items_per_page' not in query_params:
            query_params['_items_per_page'] = str(self.items_per_page)
        params = paginate.extract_pagination_from_query_params(query_params)
        params['collection'] = query
        params['item_count'] = item_count if item_count else self.count_records(query)
        pagination = paginate.SQLPage(**params)
        return pagination()
