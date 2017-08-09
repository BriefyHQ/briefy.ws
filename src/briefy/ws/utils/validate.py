"""Common validators."""
import typing as t
import uuid


def validate_uuid(value: str, version: t.Optional[int]=None) -> bool:
    """Check if id parameter is UUID valid.

    :param value: A string that should represent an uuid.
    :param version: Version of the uuid to check against.
    :return: Check if value is a valid uuid or not.
    """
    try:
        value = uuid.UUID(value)
    except (TypeError, ValueError) as e:
        valid = False
    else:
        valid = True
        if version:
            valid = value.version == version
    return valid
