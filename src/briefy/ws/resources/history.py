"""History service."""
from briefy.ws.resources import BaseResource
from cornice.resource import view


class HistoryService(BaseResource):
    """History service for workflow aware models."""

    model = None
    """This must be provided by subclass."""

    @view(validators='_run_validators')
    def get(self):
        """Return a version for this object."""
        id_ = self.request.matchdict.get('id', '')
        obj = self.get_one(id_)
        return obj.state_history
