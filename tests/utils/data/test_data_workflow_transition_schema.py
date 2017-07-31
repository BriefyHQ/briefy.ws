"""Test WorkflowTransitionSchema."""
from briefy.ws.utils import data

import colander
import pytest


def test_without_message():
    """Test WorkflowTransitionSchema without providing a message."""
    schema = data.WorkflowTransitionSchema()
    payload = {'transition': 'foo', 'message': ''}
    deserialized = schema.deserialize(payload)
    assert isinstance(deserialized, dict)
    assert 'transition' in deserialized
    assert 'message' not in deserialized


def test_with_message():
    """Test WorkflowTransitionSchema providing a message."""
    schema = data.WorkflowTransitionSchema()
    payload = {'transition': 'foo', 'message': 'A message'}
    deserialized = schema.deserialize(payload)
    assert isinstance(deserialized, dict)
    assert 'transition' in deserialized
    assert 'message' in deserialized


def test_without_transition():
    """Test WorkflowTransitionSchema without a transition raises an error."""
    schema = data.WorkflowTransitionSchema()
    payload = {'transition': '', 'message': 'A message'}
    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize(payload)
    assert '\'transition\': \'Required\'' in str(exc)
