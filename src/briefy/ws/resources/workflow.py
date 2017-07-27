"""Manage model workflow lifecycle via REST."""
from briefy.common.workflow.base import AttachedTransition
from briefy.common.workflow.exceptions import WorkflowPermissionException
from briefy.common.workflow.exceptions import WorkflowTransitionException
from briefy.ws.resources import BaseResource
from briefy.ws.utils import data
from cornice.resource import view
from pyramid.httpexceptions import HTTPNotFound as NotFound
from pyramid.httpexceptions import HTTPUnauthorized as Unauthorized


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

    def _fields_schema(self, transition):
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
    def schema_post(self):
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
    def collection_post(self):
        """Add a new instance.

        :returns: Newly created instance
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
                        'message': 'Transition executed: {id}'.format(id=transition)
                    }

                    return response
                else:
                    msg = 'Transition not found: {id}'.format(id=transition)
                    raise NotFound(msg)
            except WorkflowPermissionException:
                msg = 'Unauthorized transition: {id}'.format(id=transition)
                raise Unauthorized(msg)
            except WorkflowTransitionException as exc:
                msg = str(exc)
                field = 'fields'
                if 'Message' in str(exc):
                    field = 'message'
                self.raise_invalid('body', field, msg)
        else:
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
        self.set_transaction_name('collection_get')
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
