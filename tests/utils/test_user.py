"""Test user utilities."""
from briefy.ws.utils import user

import httmock
import os


@httmock.urlmatch(netloc=r'briefy-rolleiflex')
def mock_rolleiflex(url, request):
    """Mock request to briefy-rolleiflex."""
    status_code = 200
    user_id = url.path.split('/')[-1]
    headers = {
        'content-type': 'application/json',
    }
    try:
        filename = '{0}.json'.format(user_id)
        data = open(os.path.join(__file__.rsplit('/', 1)[0], filename)).read()
    except FileNotFoundError:
        status_code = 404
        data = {}
    return httmock.response(status_code, data, headers, None, 5, request)


def test__get_user_info_from_service(testapp):
    """Test _get_user_info_from_service function."""
    user_id = 'b9f1e623-775c-4607-9380-506b570ad0ee'
    with httmock.HTTMock(mock_rolleiflex):
        data = user._get_user_info_from_service(user_id)

    assert isinstance(data, dict)
    assert 'first_name' in data
    assert 'last_name' in data
    assert 'fullname' in data
    assert 'password' in data
    assert 'locale' in data
    assert 'id' in data


def test__get_user_info_from_service_not_found(testapp):
    """Test _get_user_info_from_service function for a non existing user."""

    user_id = 'fake'
    with httmock.HTTMock(mock_rolleiflex):
        data = user._get_user_info_from_service(user_id)

    assert isinstance(data, dict)
    assert 'first_name' not in data
    assert 'last_name' not in data
    assert 'fullname' not in data
    assert 'password' not in data
    assert 'locale' not in data
    assert 'id' not in data


def test_get_public_user_info(testapp):
    """Test get_public_user_info function."""
    user_id = 'b9f1e623-775c-4607-9380-506b570ad0ee'
    with httmock.HTTMock(mock_rolleiflex):
        data = user.get_public_user_info(user_id)

    assert isinstance(data, dict)
    assert 'first_name' in data
    assert 'last_name' in data
    assert 'fullname' in data
    assert 'id' in data
    assert 'password' not in data
    assert 'locale' not in data

    assert data['id'] == user_id
    assert data['first_name'] == 'Sebastião'
    assert data['last_name'] == 'Salgado'
    assert data['fullname'] == 'Sebastião Salgado'


def test_get_public_user_info_not_found(testapp):
    """Test get_public_user_info function for a non existing user."""
    user_id = 'fake'
    with httmock.HTTMock(mock_rolleiflex):
        data = user.get_public_user_info(user_id)

    assert isinstance(data, dict)
    assert 'first_name' in data
    assert 'last_name' in data
    assert 'fullname' in data
    assert 'id' in data
    assert 'password' not in data
    assert 'locale' not in data

    assert data['id'] == ''
    assert data['first_name'] == ''
    assert data['last_name'] == ''
    assert data['fullname'] == ''
