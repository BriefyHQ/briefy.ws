"""Test data utilities."""
from briefy.ws.utils import data


def test_native_value(testapp):
    """Test native_value function."""
    func = data.native_value

    assert func('360', 'id') == '360'
    assert func('360', 'other_field') == 360

    assert func('on', 'other_field') is True
    assert func('true', 'other_field') is True
    assert func('yes', 'other_field') is True

    assert func('off', 'other_field') is False
    assert func('false', 'other_field') is False
    assert func('no', 'other_field') is False