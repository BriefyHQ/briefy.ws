"""Custom common validators."""
from briefy.ws.utils.validate import validate_uuid


def validate_id(request):
    """Check if id parameter is UUID valid.

    :param request: pyramid request.
    :return:
    """
    path_id = request.matchdict.get('id')

    if path_id and not validate_uuid(path_id):
        request.errors.add('path', 'id', 'The id informed is not 16 byte uuid valid.')
