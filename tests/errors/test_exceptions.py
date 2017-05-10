"""Test exceptions."""
from briefy.ws.errors import ValidationError

import pytest


def raise_validation_exception(message: str, key: str):
    """Raise a ValidationException."""
    raise ValidationError(message, key)


def test_validation_exception():
    """Test ValidationError."""
    func = raise_validation_exception

    with pytest.raises(ValidationError) as excinfo:
        func('Invalid date', 'date')
        assert excinfo.message == 'Invalid date'
        assert excinfo.key == 'date'


def test_validation_exception_inheritance():
    """Test ValidationError inherits from ValueError."""
    func = raise_validation_exception

    with pytest.raises(ValueError) as excinfo:
        func('Invalid date', 'date')
        assert excinfo.message == 'Invalid date'
        assert excinfo.key == 'date'
