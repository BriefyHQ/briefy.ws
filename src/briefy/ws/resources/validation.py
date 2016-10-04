"""Custom common validators."""

import uuid


def validate_id(request):
    """Check if id parameter is UUID valid.

    :param request: pyramid request.
    :return:
    """
    path_id = request.matchdict.get('id')
    if path_id is None:
        return

    try:
        uuid.UUID(path_id)
    except ValueError as e:
        request.errors.add('path', 'id',
                           'The id informed is not 16 byte uuid valid.')
