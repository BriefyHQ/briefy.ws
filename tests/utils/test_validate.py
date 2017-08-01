"""Test validate utilities."""
from briefy.ws.utils import validate

import pytest


test_data = [
    '228abe0b-f9dd-44f5-a3c6-a9a5976a3f1b',
    '868c16f0-1fcf-4057-9a5e-3ed968376b33',
    '6737474d-d9d4-4805-a0d0-be85c4dc3311',
    '339e1685-59ef-4050-b0b3-5a8060e1f4cc',
    'c986be43-2944-49d0-a094-19eb7dbab665'
]


@pytest.mark.parametrize('value', test_data)
def test_uuid_default_valid(value):
    """Test validate_uuid function without specifying a version."""
    func = validate.validate_uuid

    assert func(value) is True


@pytest.mark.parametrize('value', test_data)
def test_uuid4_valid(value):
    """Test validate_uuid function for version 4."""
    func = validate.validate_uuid

    assert func(value, version=4) is True


test_data = [
    '228abe0b',
    '',
    'foo',
    '339e1685-59ef-5050-b0b3-5a8060e1f4cc',
    '11111111-1111-1111-1111-111111111111'
]


@pytest.mark.parametrize('value', test_data)
def test_uuid_invalid(value):
    """Test validate_uuid function with invalid values."""
    func = validate.validate_uuid

    assert func(value) is False
