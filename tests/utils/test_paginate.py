"""Test pagination."""
from briefy.ws.utils import paginate


def test_page_default_values():
    """Test paginate.Page default values."""
    func = paginate.Page

    data = range(0, 100)

    page = func(data)

    assert page.items_per_page == 20
    assert page.page == 1
    assert page.page_count == 5
    assert page.previous_page is None
    assert page.next_page == 2


def test_page_pagination_second_page():
    """Test paginate.Page second page."""
    func = paginate.Page

    data = range(0, 100)

    # Second page
    page = func(data, page=2)
    assert page.page == 2
    assert page.previous_page == 1
    assert page.next_page == 3


def test_page_pagination_last_page():
    """Test paginate.Page last page."""
    func = paginate.Page

    data = range(0, 100)

    # Last page
    page = func(data, page=5)
    assert page.page == 5
    assert page.previous_page == 4
    assert page.next_page is None


def test_page_pagination_page_number_is_zero():
    """Test paginate.Page with page = 0."""
    func = paginate.Page

    data = range(0, 100)

    # Page number is 0, should return first page
    page = func(data, page=0)
    assert page.page == 1
    assert page.previous_page is None
    assert page.next_page == 2


def test_page_pagination_page_number_bigger_than_number_of_pages():
    """Test paginate.Page with page = 6."""
    func = paginate.Page

    data = range(0, 100)

    # Page number bigger than number of pages
    page = func(data, page=6)
    assert page.page == 5
    assert page.previous_page == 4
    assert page.next_page is None


def test_page_number_items_per_page():
    """Test paginate.Page default values."""
    func = paginate.Page

    data = range(0, 100)

    page = func(data, items_per_page=50)

    assert page.items_per_page == 50
    assert page.page == 1
    assert page.page_count == 2
    assert page.previous_page is None
    assert page.next_page == 2


def test_page_page_info():
    """Test paginate.Page info"""
    func = paginate.Page

    data = range(0, 100)

    page = func(data)
    page_info = page.page_info()

    assert isinstance(page_info, dict) is True
    assert page_info['items_per_page'] == 20
    assert page_info['page'] == 1
    assert page_info['page_count'] == 5
    assert page_info['previous_page'] is None
    assert page_info['next_page'] == 2
    assert page_info['total'] == 100


def test_page_call():
    """Test paginate.Page execution"""
    func = paginate.Page

    data = range(0, 100)

    page = func(data)

    resp = page()

    assert isinstance(resp, dict) is True
    assert resp['pagination']['items_per_page'] == 20
    assert resp['pagination']['page'] == 1
    assert resp['pagination']['page_count'] == 5
    assert resp['pagination']['previous_page'] is None
    assert resp['pagination']['next_page'] == 2
    assert resp['pagination']['total'] == 100
    assert resp['total'] == 100
    assert 1 in resp['data']
    assert 100 not in resp['data']


def test_extract_pagination_from_query_params_empty():
    """Test paginate.extract_pagination_from_query_params with empty query_params."""
    func = paginate.extract_pagination_from_query_params
    query_params = {}

    params = func(query_params)
    assert isinstance(params, dict) is True
    assert params['page'] == 1
    assert params['items_per_page'] == 25


def test_extract_pagination_from_query_params_invalid():
    """Test paginate.extract_pagination_from_query_params with invalid query_params."""
    func = paginate.extract_pagination_from_query_params
    query_params = {
        '_page': 'page 1',
        '_items_per_page': -1
    }

    params = func(query_params)
    assert isinstance(params, dict) is True
    assert params['page'] == 1
    assert params['items_per_page'] == 25


def test_extract_pagination_from_query_params():
    """Test paginate.extract_pagination_from_query_params with valid query_params."""
    func = paginate.extract_pagination_from_query_params
    query_params = {
        '_page': '2',
        '_items_per_page': 50
    }

    params = func(query_params)
    assert isinstance(params, dict) is True
    assert params['page'] == 2
    assert params['items_per_page'] == 50
