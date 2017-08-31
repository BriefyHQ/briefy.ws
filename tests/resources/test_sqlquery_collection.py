"""Test briefy.ws.resources.sqlquery module."""
from briefy.ws.resources import SQLQueryService

import pytest


@pytest.mark.usefixtures('login')
class TestSQLQueryResource:
    """Test SQLQueryResource class."""

    def test_sqlquery_resource_init(self, login, web_request, context):
        """Create new sqlquery service instance."""
        service = SQLQueryService(context, web_request)
        assert service.context == context
        assert service.request == web_request

    def test_sqlquery_resource_collection_get(self, login, web_request, context):
        """Execute collection_get method of sqlservice."""
        service = SQLQueryService(context, web_request)
        response = service.collection_get()
        assert 'data' in response
        assert 'pagination' in response
