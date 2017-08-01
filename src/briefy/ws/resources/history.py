"""History service."""
from briefy.common.utilities.interfaces import IUserProfileQuery
from briefy.ws.resources import BaseResource
from cornice.resource import view
from zope.component import getUtility


class HistoryService(BaseResource):
    """History service for workflow aware models."""

    model = None
    """This must be provided by subclass."""

    @view(validators='_run_validators', permission='list')
    def collection_get(self) -> dict:
        """Return the workflow history for this object."""
        self.set_transaction_name('collection_get')
        headers = self.request.response.headers
        id_ = self.request.matchdict.get('id', '')
        obj = self.get_one(id_)
        profile_service = getUtility(IUserProfileQuery)
        state_history = profile_service.update_wf_history(obj.state_history)
        total = len(state_history)
        payload = {
            'data': state_history,
            'pagination': {
                'items_per_page': total,
                'next_page': None,
                'page': 1,
                'previous_page': None,
                'page_count': 1,
                'total': total
            },
            'total': total
        }
        headers['Total-Records'] = f'{total}'
        return payload
