"""User utilities for briefy.webservice."""
from briefy.common.utils.cache import timeout_cache
from briefy.ws.config import USER_SERVICE_BASE
from briefy.ws.config import USER_SERVICE_TIMEOUT

import requests


def _get_user_info_from_service(user_id: str) -> dict:
    """Retrieve user information from briefy.rolleiflex.

    :param user_id: Id for the user we want to query.
    :return: Dictionary with user information.
    """
    data = {}
    endpoint = '{base_url}/users/{user_id}'.format(
        base_url=USER_SERVICE_BASE,
        user_id=user_id
    )
    resp = requests.get(
        endpoint
    )
    if resp.status_code == 200:
        raw_data = resp.json()
        data = raw_data['data'] if 'data' in raw_data else data
    return data


@timeout_cache(USER_SERVICE_TIMEOUT, renew=False)
def get_public_user_info(user_id: str) -> dict:
    """Retrieve user information from briefy.rolleiflex.

    :param user_id: Id for the user we want to query.
    :return: Dictionary with public user information.
    """
    data = {
        'id': '',
        'first_name': '',
        'last_name': '',
        'fullname': '',
    }
    raw_data = _get_user_info_from_service(user_id)
    if raw_data:
        data['id'] = raw_data['id']
        data['first_name'] = raw_data['first_name']
        data['last_name'] = raw_data['last_name']
        data['fullname'] = raw_data.get('fullname')
    return data