"""Base Resources for briefy.ws."""
from briefy.common.workflow.base import AttachedTransition
from briefy.common.workflow.exceptions import WorkflowPermissionException
from briefy.common.workflow.exceptions import WorkflowTransitionException
from briefy.ws.auth import validate_jwt_token
from briefy.ws.errors import ValidationError
from briefy.ws.resources import events
from briefy.ws.resources.validation import validate_id
from briefy.ws.utils import data
from briefy.ws.utils import filter
from briefy.ws.utils import paginate
from briefy.ws.utils import user
from colanderalchemy import SQLAlchemySchemaNode
from cornice.schemas import CorniceSchema
from cornice.util import json_error
from cornice.resource import view
from pyramid.httpexceptions import HTTPNotFound as NotFound
from pyramid.httpexceptions import HTTPUnauthorized as Unauthorized


import colander
import sqlalchemy as sa


class BaseResource:
    """Base class for resources."""

    model = None
    friendly_name = ''
    items_per_page = 25
    default_order_by = 'updated_at'
    default_order_direction = 1

    _default_notify_events = {}

    def __init__(self, context, request):
        """Initialize the service."""
        self.context = context
        self.request = request

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
        schema = CorniceSchema.from_colander(colander_schema)
        return schema

    def get_user_info(self, user_id: str) -> dict:
        """Get public information about an user with given user_id.

        :param user_id: Id of the user.
        :return: Public information about this user.
        """
        return user.get_public_user_info(user_id)

    @property
    def default_filters(self) -> tuple:
        """Default filters to be applied to every query.

        This is supposed to be specialized by resource classes.
        :returns: A tuple of default filters to be applied to queries.
        """
        return tuple()

    def _get_base_query(self):
        """Return the base query for this service.

        :return: Query object with default filter already applie.
        """
        model = self.model
        query = model.query()
        for filter_ in self.default_filters:
            query = query.filter(filter_)
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
        return SQLAlchemySchemaNode(self.model, unknown='ignore')

    @property
    def filter_allowed_fields(self):
        """List of fields allowed in filtering and sorting."""
        schema = self.schema_filter
        allowed_fields = [child.name for child in schema.children]
        # Allow filtering by state
        allowed_fields.append('state')
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

    def _run_validators(self, request):
        """Run all validators for the current http method.

        :param request: request object
        """
        # first #ForaTemer, second always validate jwt token on request.
        validate_jwt_token(request)

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

    def attach_request(self, obj):
        """Attach current request in one model object instance.

        :param obj: sqlalchemy model obj instance
        :return: sqlalchemy model obj instance with current request as instance attribute
        """
        obj.request = self.request
        return obj

    def notify_obj_event(self, obj, method=None):
        """Create right event object based on current request method.

        :param obj: sqlalchemy model obj instance
        """
        request = self.request
        if 'Briefy-SyncBot' in request.headers.get('User-Agent', ''):
            return
        method = method or request.method
        event_klass = self._default_notify_events.get(method)
        if event_klass:
            event = event_klass(obj, request)
            request.registry.notify(event)
            # also execute the event to dispatch to sqs if needed
            event()

    def get_one(self, id):
        """Given an id, return an instance of the model object or raise a not found exception.

        :param id: Id for the object
        :return: Category
        """
        model = self.model
        query = self._get_base_query()
        obj = query.filter(model.id == id).one_or_none()

        if not obj:
            raise NotFound(
                '{friendly_name} with id: {id} not found.'.format(
                    friendly_name=self.friendly_name,
                    id=id
                )
            )
        self.notify_obj_event(obj, 'GET')
        return self.attach_request(obj)

    def get_records(self):
        """Get all records for this resource and return a dictionary.

        :return: dict
        """
        query_params = self.request.GET
        query = self._get_base_query()

        # Apply filters
        query = self.filter_query(query, query_params)

        # Apply sorting
        query = self.sort_query(query, query_params)
        pagination = self.paginate(query, query_params)
        data = pagination['data']
        records = [self.attach_request(record) for record in data]
        pagination['data'] = records

        for record in records:
            self.notify_obj_event(record, 'GET')

        return pagination

    def filter_query(self, query, query_params=None):
        """Apply request filters to a query."""
        model = self.model
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
            column = getattr(model, key, None)
            func = sa.asc
            if direction == -1:
                func = sa.desc
            query = query.order_by(func(column))
        return query

    def paginate(self, query, query_params: dict=None):
        """Pagination."""
        if not 'items_per_page' in query_params:
            query_params['items_per_page'] = self.items_per_page
        params = paginate.extract_pagination_from_query_params(query_params)
        params['collection'] = query
        pagination = paginate.SQLPage(**params)
        return pagination()


class RESTService(BaseResource):
    """Rest service based on a model."""

    default_excludes = ['created_at', 'updated_at', 'state_history', 'state']

    _required_fields = (
        ('PUT', tuple()),
    )

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
        schema = self.schema_write
        required_fields = self.get_required_fields('PUT')
        for child in schema.children:
            if child.title not in required_fields:
                child.missing = colander.drop
                child.default = colander.null
        return schema

    @view(validators='_run_validators', permission='add')
    def collection_post(self):
        """Add a new instance.

        :returns: Newly created instance
        """
        request = self.request
        payload = request.validated
        model = self.model

        # verify if object with same ID exists
        obj_id = payload.get('id')
        if obj_id:
            obj_exists = model.get(obj_id)
            if obj_exists:
                self.raise_invalid('body', 'id', 'Duplicate object UUID: {id}'.format(id=obj_id))

        session = self.session
        obj = model(**payload)
        obj = self.attach_request(obj)
        session.add(obj)
        session.flush()
        self.notify_obj_event(obj, 'POST')
        return obj

    @view(validators='_run_validators', permission='list')
    def collection_head(self):
        """Return the header with total objects for this request."""
        headers = self.request.response.headers
        records = self.get_records()
        headers['Total-Records'] = '{total}'.format(total=records['total'])

    @view(validators='_run_validators', permission='list')
    def collection_get(self):
        """Return a list of objects.

        :returns: Payload with total records and list of objects
        """
        headers = self.request.response.headers
        pagination = self.get_records()
        total = pagination['total']
        headers['Total-Records'] = '{total}'.format(total=total)
        # Force in here to use the listing serialization.
        pagination['data'] = [o.to_listing_dict() for o in pagination['data']]
        return pagination

    @view(validators='_run_validators', permission='view')
    def get(self):
        """Get an instance of the model object."""
        id = self.request.matchdict.get('id', '')
        obj = self.get_one(id)
        return obj

    @view(validators='_run_validators', permission='edit')
    def put(self):
        """Update an existing object."""
        id = self.request.matchdict.get('id', '')
        obj = self.get_one(id)
        obj.update(self.request.validated)
        self.session.flush()
        self.notify_obj_event(obj, 'PUT')
        return obj

    @view(permission='delete')
    def delete(self):
        """Soft delete an object if there is an apropriate transition for it."""
        obj = self.get_one(id)
        # We do not delete things from the Database -
        # The delete event should be enough to trigger
        # transitions that will set a delete-like
        # state for the object, if appropriate
        self.notify_obj_event(obj, 'DELETE')
        return obj


class WorkflowAwareResource(BaseResource):
    """Workflow aware resource."""

    @property
    def workflow(self):
        """Return workflow for the model."""
        id = self.request.matchdict.get('id', '')
        obj = self.get_one(id)
        context = self.request.user
        workflow = getattr(obj, 'workflow', None)
        if workflow:
            workflow.context = context
            return workflow
        return None

    @property
    def schema_post(self):
        """Schema for write operations."""
        return data.WorkflowTransitionSchema(unknown='ignore')

    @view(validators='_run_validators')
    def collection_post(self):
        """Add a new instance.

        :returns: Newly created instance
        """
        request = self.request
        transition = self.request.validated['transition']
        message = self.request.validated.get('message', '')
        workflow = self.workflow

        # Execute transition
        try:
            transition_method = getattr(workflow, transition, None)
            if isinstance(transition_method, AttachedTransition):
                transition_method(message=message)

                wf_event = events.WorkflowTranstionEvent(workflow.document,
                                                         request,
                                                         transition_method)
                request.registry.notify(wf_event)
                # also execute the event to dispatch to sqs if needed
                wf_event()

                response = {
                    'status': True,
                    'message': 'Transition executed: {id}'.format(id=transition)
                }

                return response
            else:
                msg = 'Transition not found: {id}'.format(id=transition)
                raise NotFound(msg)
        except WorkflowPermissionException:
            msg = 'Unauthorized transition: {id}'.format(id=transition)
            raise Unauthorized(msg)
        except WorkflowTransitionException:
            valid_transitions_list = str(list(workflow.transitions))
            state = workflow.state.name
            msg = 'Invalid transition: {id} (for state: {state}). ' \
                  'Your valid transitions list are: {transitions}'
            msg = msg.format(id=transition,
                             state=state,
                             transitions=valid_transitions_list)
            self.raise_invalid('body', 'transition', msg)

    @view(validators='_run_validators')
    def collection_get(self):
        """Return the list of available transitions for this user in this object."""
        response = {
            'transitions': [],
            'total': 0
        }
        workflow = self.workflow
        if workflow:
            transitions = workflow.transitions
            transitions_ids = list(transitions)
            response['transitions'] = transitions_ids
            response['total'] = len(transitions_ids)
        return response
