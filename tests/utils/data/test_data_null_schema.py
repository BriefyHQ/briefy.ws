"""Test NullSchema."""
from briefy.ws.utils import data


def test_schema():
    """Test NullSchema."""
    schema = data.NullSchema()
    payload = {'foo': 'bar', 'bar': 'foo'}
    deserialized = schema.deserialize(payload)
    assert isinstance(deserialized, dict)
    assert 'foo' not in deserialized
    assert 'bar' not in deserialized
