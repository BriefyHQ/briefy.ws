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
    None,
    'foo',
    'x39e1685-59ef-5050-b0b3-5a8060e1f4cc',
    '11111111-s111-1111-1111-111111111111'
]


@pytest.mark.parametrize('value', test_data)
def test_uuid_invalid(value):
    """Test validate_uuid function with invalid values."""
    func = validate.validate_uuid

    assert func(value) is False


test_data = [
    '197587e1-eb7d-4aa0-5ea1-aef575a28ade',
    '74fdc63e-3b82-4e52-fd44-30fdf5b5c62e',
    '800b12b0-6cda-4b22-c666-f9ce0a282b6b',
    '9b13ea27-e517-4687-7aea-f17e7a10c308',
    'cc9964da-9d11-45d0-670c-4efa8e2eaaf9',
    'df454734-d6af-4b77-785f-5585900eb57d',
    '10ca7fe4-da55-40ef-1b24-679524b837ac',
    'fe055379-23f8-40bd-1a19-aca784a353f4',
    'fe5403dd-32ab-4c69-59ae-5d1db45e34ee',
    'ff086cf3-bcbb-49a2-6f46-76782330d6fb',
    'ffcff482-47c3-4224-1f7e-0e5cbfc269e7'
]


@pytest.mark.parametrize('value', test_data)
def test_uuid_valid_not_uuid4(value):
    """Test validate_uuid function without specifying a version."""
    func = validate.validate_uuid

    assert func(value) is True
