"""Manage model workflow lifecycle via REST."""
from briefy.common.workflow import Workflow
from briefy.common.workflow import WorkflowPermissionException
from briefy.common.workflow import WorkflowTransition
from briefy.common.workflow import WorkflowTransitionException
from briefy.common.workflow.transition import AttachedTransition
from briefy.ws.errors import ValidationError
from briefy.ws.resources import BaseResource
from briefy.ws.utils import data
from cornice.resource import view
from pyramid.httpexceptions import HTTPNotFound as NotFound
from pyramid.httpexceptions import HTTPUnauthorized as Unauthorized

import colander
import typing as t


BriefySchemaOrNone = t.Union[data.BriefySchemaNode, None]


class WorkflowAwareResource(BaseResource):
    """Workflow aware resource."""

    @property
    def workflow(self) -> Workflow:
        """Return workflow for the model."""
        id = self.request.matchdict.get('id', '')
        obj = self.get_one(id)
        context = self.request.user
        workflow = getattr(obj, 'workflow', None)
        if workflow:
            workflow.context = context
        return workflow

    def _fields_schema(self, transition: WorkflowTransition) -> BriefySchemaOrNone:
        """Return a schema to handle fields payload."""
        schema = None
        required_fields = transition.required_fields
        optional_fields = transition.optional_fields
        includes = required_fields + optional_fields
        if includes:
            schema = data.BriefySchemaNode(
                self.model, unknown='ignore', includes=includes
            )
            schema.name = 'fields'
        return schema

    @property
    def schema_post(self) -> colander.SchemaNode:
        """Schema for write operations."""
        body = self.request.json_body
        payload = body if body else self.request.POST
        transition_id = payload.get('transition')
        workflow = self.workflow
        transition = workflow.transitions.get(transition_id)
        schema = data.WorkflowTransitionSchema(unknown='ignore')
        fields = self._fields_schema(transition)
        if fields:
            schema.children.append(fields)
        return schema

    @view(validators='_run_validators')
    def collection_post(self) -> dict:
        """Add a new instance.

        :returns: Information about the transition.
        """
        self.set_transaction_name('collection_post')
        transition = self.request.validated['transition']
        message = self.request.validated.get('message', '')
        fields = self.request.validated.get('fields', {})
        workflow = self.workflow
        valid_transitions_list = str(list(workflow.transitions))
        if transition in valid_transitions_list:
            # Execute transition
            try:
                transition_method = getattr(workflow, transition, None)
                if isinstance(transition_method, AttachedTransition):
                    transition_method(message=message, fields=fields)

                    response = {
                        'status': True,
                        'message': f'Transition executed: {transition}'
                    }
                    return response
                else:
                    raise NotFound(f'Transition not found: {transition}')
            except ValidationError as e:
                error_details = {'location': e.location, 'description': e.message, 'name': e.name}
                self.raise_invalid(**error_details)
            except WorkflowPermissionException:
                raise Unauthorized(f'Unauthorized transition: {transition}')
            except WorkflowTransitionException as exc:
                msg = str(exc)
                field = 'fields'
                if 'Message' in str(exc):
                    field = 'message'
                self.raise_invalid('body', field, msg)
        else:
            state = workflow.state.name
            msg = f'Invalid transition: {transition} (for state: {state}). ' \
                  'Your valid transitions list are: {valid_transitions_list}'
            self.raise_invalid('body', 'transition', msg)

    @view(validators='_run_validators')
    def collection_get(self) -> dict:
        """Return the list of available transitions for this user in this object."""
        self.set_transaction_name('collection_get')
        response = {'transitions': [], 'total': 0}
        workflow = self.workflow
        if workflow:
            transitions = workflow.transitions
            transitions_ids = list(transitions)
            response['transitions'] = transitions_ids
            response['total'] = len(transitions_ids)
        return response
