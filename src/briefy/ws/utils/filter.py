"""Filter and Sorting utilities to be used for REST Services."""
from briefy.ws.errors import ValidationError
from briefy.ws.utils import data
from collections import namedtuple
from enum import Enum

import re
import typing as t


UPDATED_AT = 'updated_at'

Filter = namedtuple('Filter', ['field', 'value', 'operator'])
"""Filtering properties."""


Sort = namedtuple('Sort', ['field', 'direction'])
"""Sorting properties."""


class COMPARISON(Enum):
    """Comparision enum.

    This is used to convert filtering params, in requests, to proper SQLAlchemy methods.
    """

    LT = 'lt'
    MIN = 'ge'
    MAX = 'le'
    NOT = 'ne'
    EQ = 'eq'
    GT = 'gt'
    IN = 'in_'
    LIKE = 'like'
    ILIKE = 'ilike'
    EXCLUDE = 'notin_'


def create_filter_from_query_params(
        query_params: dict,
        allowed_fields: t.Sequence[str]
) -> t.Sequence[Filter]:
    """Process a query parameters dictionary and return a list of Filter objects.

    :param query_params: Dictionary containing query_params for a request.
    :param allowed_fields: List of fields that support sorting.
    :return: list of Filter objects.
    """
    filters = []
    for param, param_value in query_params.items():
        param = param.strip()

        # Ignore specific fields
        if param.startswith('_') and param not in ('_since', '_to', '_before'):
            continue

        # Handle the _since specific filter.
        if param in ('_since', '_to', '_before'):
            try:
                value = int(param_value)
            except ValueError as exc:
                raise ValueError(f'Parameter "{param}" is not a valid integer.')

            operators = {
                '_since': COMPARISON.GT,
                '_to': COMPARISON.MAX,
                '_before': COMPARISON.LT,
            }

            operator = operators[param]

            filters.append(Filter(UPDATED_AT, value, operator))
            continue

        m = re.match(r'^(min|max|not|lt|gt|in|exclude|like|ilike)_([\.\w]+)$', param)
        if m:
            keyword, field = m.groups()
            operator = getattr(COMPARISON, keyword.upper())
        else:
            operator, field = COMPARISON.EQ, param

        if field not in allowed_fields:
            raise ValidationError(
                message=f'Unknown filter field \'{field}\'',
                location='querystring',
                name=field
            )

        value = data.native_value(param_value, field)
        if operator in (COMPARISON.IN, COMPARISON.EXCLUDE):
            value = set([data.native_value(v, field) for v in param_value.split(',')])
        elif operator in (COMPARISON.LIKE, COMPARISON.ILIKE, ):
            value = value.replace('%', '')
            value = f'%{value}%'
        filters.append(Filter(field, value, operator))
    return filters


def create_sorting_from_query_params(
        query_params: dict,
        allowed_fields: t.Sequence[str],
        default: str='',
        default_direction: str='') -> t.Sequence[Sort]:
    """Process a query parameters dictionary and return a list of Sort objects.

    :param query_params: Dictionary containing query_params for a request.
    :param allowed_fields: List of fields that support sorting.
    :param default: Default field for sorting.
    :param default_direction: Default direction for sorting.
    :return: list of Sort objects.
    """
    specified = query_params.get('_sort', '').split(',')
    sorting = []
    for field in specified:
        field = field.strip()
        m = re.match(r'^([\-+]?)([\.\w]+)$', field)
        if m:
            order, field = m.groups()
            if field not in allowed_fields:
                raise ValidationError(
                    message=f'Unknown sort field \'{field}\'',
                    location='querystring',
                    name=field
                )
            direction = -1 if order == '-' else 1
            sorting.append(Sort(field, direction))
    if not sorting and (default and default_direction):
        sorting.append(Sort(default, default_direction))
    return sorting
