"""Data utilities for Briefy webservices."""
from colander import MappingSchema

import ast


class NullSchema(MappingSchema):
    """Colander schema to bypass validations."""


def native_value(value: str, field: str=None):
    """Convert string value to native python values.

    :param value: value to convert.
    :param field: Name of the field this value relates to.
    :returns: the value coerced to python type
    """
    if isinstance(value, str):
        if value.lower() in ['on', 'true', 'yes']:
            value = True
        elif value.lower() in ['off', 'false', 'no']:
            value = False

        # HACK: Some fields should be coerced here.
        if field == 'id':
            return value

        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            pass

    return value
