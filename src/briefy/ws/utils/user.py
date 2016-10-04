"""User utilities for briefy.webservice."""
from briefy.common.utils.cache import timeout_cache
from briefy.ws import logger
from briefy.ws.config import USER_SERVICE_BASE
from briefy.ws.config import USER_SERVICE_TIMEOUT

import requests
import transaction


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
    # TODO: improve this to user current user locale
    headers = {'X-Locale': 'en_GB'}
    savepoint = transaction.savepoint()
    try:
        resp = requests.get(
            endpoint,
            headers=headers
        )
    except ConnectionError as exc:
        logger.warn('Failure connecting to internal user service. Exception: {exc}'.format(exc=exc))
        savepoint.rollback()
    else:
        if resp.status_code == 200:
            raw_data = resp.json()
            data = raw_data['data'] if 'data' in raw_data else data
        else:
            msg = 'Getting user info from internal services fail. Status code: {status_code}.'
            logger.info(msg.format(status_code=resp.status_code))
    return data


@timeout_cache(USER_SERVICE_TIMEOUT, renew=False)
def get_public_user_info(user_id: str) -> dict:
    """Retrieve user information from briefy.rolleiflex.

    :param user_id: Id for the user we want to query.
    :return: Dictionary with public user information.
    """
    data = {
        'id': user_id,
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


def add_user_info_to_state_history(state_history):
    """Receive object state history and add user information.

    :param state_history: list of workflow state history.
    """
    for item in state_history:
        user = item.get('actor', None)
        if isinstance(user, str):
            user_id = user  # first call where actor is a UUID string
            new_actor = get_public_user_info(user_id)
            if new_actor:
                item['actor'] = new_actor
