"""Data utilities for Briefy webservices."""
import ast
import colander


class NullSchema(colander.MappingSchema):
    """Colander schema to bypass validations."""


class WorkflowTransitionSchema(colander.MappingSchema):
    """Workflow schema for transitions."""

    transition = colander.SchemaNode(
        typ=colander.String(),
        title='Transition to be executed.'
    )
    message = colander.SchemaNode(
        typ=colander.String(),
        title='Message for this transition.',
        missing=colander.drop,
        default='-'
    )


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
