"""Common validators."""
import uuid


def validate_uuid(value: str, version: int=4) -> bool:
    """Check if id parameter is UUID valid.

    :param request: pyramid request.
    :return:
    """
    try:
        valid = uuid.UUID(value).version == version
    except ValueError as e:
        valid = False
    return valid
