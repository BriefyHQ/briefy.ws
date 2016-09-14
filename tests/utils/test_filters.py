"""Test filtering utils."""
from briefy.ws.utils import filter
from briefy.ws.errors import ValidationError

import pytest


class TestSortingFromQueryParams:
    """Test create_sorting_from_query_params. """

    allowed_fields = ['id', 'name', 'updated_at', 'created_at']

    def test_no_params(self):
        """No parameters passed."""
        query_params = {}
        func = filter.create_sorting_from_query_params
        result = func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_no_params_with_defaults(self):
        """No parameters passed, but set a default ordering."""
        query_params = {}
        func = filter.create_sorting_from_query_params
        result = func(
            query_params=query_params,
            allowed_fields=self.allowed_fields,
            default='updated_at',
            default_direction=1
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].field == 'updated_at'
        assert result[0].direction == 1

    def test_one_field_ascending(self):
        """Passing id, ascending."""
        query_params = {'_sort': 'id'}
        func = filter.create_sorting_from_query_params
        result = func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].field == 'id'
        assert result[0].direction == 1

    def test_one_field_descending(self):
        """Passing id, descending."""
        query_params = {'_sort': '-id'}
        func = filter.create_sorting_from_query_params
        result = func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].field == 'id'
        assert result[0].direction == -1

    def test_multiple_valid_fields(self):
        """Passing id, name and descending updated_at."""
        query_params = {'_sort': 'id,name,-updated_at'}
        func = filter.create_sorting_from_query_params
        result = func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0].field == 'id'
        assert result[0].direction == 1
        assert result[1].field == 'name'
        assert result[1].direction == 1
        assert result[2].field == 'updated_at'
        assert result[2].direction == -1

    def test_one_invalid_field(self):
        """Passing foobar, an invalid field."""
        query_params = {'_sort': 'foobar'}
        func = filter.create_sorting_from_query_params

        with pytest.raises(ValidationError) as excinfo:
            func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert  """Unknown sort field 'foobar'""" in str(excinfo.value.message)

    def test_multiple_fields_one_invalid_field(self):
        """Passing id, name and foobar, an invalid field."""
        query_params = {'_sort': 'id,name,foobar'}
        func = filter.create_sorting_from_query_params

        with pytest.raises(ValidationError) as excinfo:
            func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert  """Unknown sort field 'foobar'""" in str(excinfo.value.message)


class TestFilterFromQueryParams:
    """Test create_filter_from_query_params. """

    allowed_fields = ['id', 'name', 'updated_at', 'created_at']

    def test_no_params(self):
        """No parameters passed."""
        query_params = {}
        func = filter.create_filter_from_query_params
        result = func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_one_field_equal(self):
        """Passing id, value '360'."""
        query_params = {'id': '360'}
        func = filter.create_filter_from_query_params
        result = func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].field == 'id'
        assert result[0].operator.value == 'eq'
        assert result[0].value == '360'

    def test_one_field_in(self):
        """Passing id, value in '360'."""
        query_params = {'in_id': '360'}
        func = filter.create_filter_from_query_params
        result = func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].field == 'id'
        assert result[0].operator.value == 'in_'
        assert '360' in result[0].value

        # More values
        query_params = {'in_id': '360,wedding'}
        result = func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].field == 'id'
        assert result[0].operator.value == 'in_'
        assert '360' in result[0].value
        assert 'wedding' in result[0].value

    def test_one_field_exclude(self):
        """Passing id, value '360'."""
        query_params = {'exclude_id': '360'}
        func = filter.create_filter_from_query_params
        result = func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].field == 'id'
        assert result[0].operator.value == 'notin_'
        assert '360' in result[0].value

    def test_one_field_exclude(self):
        """Passing id, value '360'."""
        query_params = {'exclude_id': '360'}
        func = filter.create_filter_from_query_params
        result = func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].field == 'id'
        assert result[0].operator.value == 'notin_'
        assert '360' in result[0].value

    def test_since(self):
        """Passing id, value '360'."""
        query_params = {'_since': '1481544732'}
        func = filter.create_filter_from_query_params
        result = func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].field == 'updated_at'
        assert result[0].operator.value == 'gt'
        assert result[0].value == 1481544732

    def test_one_invalid_field(self):
        """Passing foobar, an invalid field."""
        query_params = {'foobar': '42'}
        func = filter.create_filter_from_query_params

        with pytest.raises(ValidationError) as excinfo:
            func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert """Unknown filter field 'foobar'""" in str(excinfo.value.message)

    def test_multiple_fields_one_invalid_field(self):
        """Passing id, name and foobar, an invalid field."""
        query_params = {'id': '360', 'name': '360', 'foobar': '42'}
        func = filter.create_filter_from_query_params

        with pytest.raises(ValidationError) as excinfo:
            func(query_params=query_params, allowed_fields=self.allowed_fields)

        assert """Unknown filter field 'foobar'""" in str(excinfo.value.message)