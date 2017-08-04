"""Webservice to return a paginate collection based in a custom query."""
from briefy.ws.resources import BaseResource
from briefy.ws.utils import paginate
from cornice.resource import view


class SQLQueryService(BaseResource):
    """Rest service based on a custom plain sql query."""

    _columns_map = ()
    """Tuple with all metadata about the fields returned in the listing set payload.

    This data will be available in the payload as "columns" attribute.
    Ex::

        _column_map = (
            {'field': 'country', 'label': 'Country', 'type': 'country', 'url': '', 'filter': ''},
            {'field': 'total', 'label': 'Total', 'type': 'integer', 'url': '', 'filter': ''},
        )

    """

    _collection_query = None
    """String with a custom plain sql query."""

    def transform(self, data: list) -> list:
        """Transform data items after query execution.

        :data: list of records to be transformed
        :returns: list of records after transformation
        """
        return data

    def query_params(self, query: str) -> str:
        """Apply query parameters based on request.

        This is supposed to be specialized by resource classes.

        :query: string with a query to be parametrized
        :returns: string with a query after adding parameters
        """
        return query

    @view(validators='_run_validators', permission='list')
    def collection_get(self) -> dict:
        """Return a list of objects.

        :returns: Payload with total records and list of objects
        """
        self.set_transaction_name('collection_get')
        db = self.request.db
        query = self._collection_query
        query = self.query_params(query)
        result = db.execute(query)

        data_set = []
        data_keys = list(enumerate(result.keys()))
        for row in result:
            item = {column: row[i] for i, column in data_keys}
            data_set.append(item)
        data_set = self.transform(data_set)

        item_count = result.rowcount
        params = {
            'collection': data_set,
            'item_count': item_count
        }

        columns_map = self._columns_map
        if columns_map:
            params['columns'] = columns_map

        headers = self.request.response.headers
        headers['Total-Records'] = str(item_count)
        pagination = paginate.SQLPage(**params)()
        return pagination
