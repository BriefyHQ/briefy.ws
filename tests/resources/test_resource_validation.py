"""Test resource validation."""
from briefy.ws.resources import validation


class Errors(list):
    """Mock."""

    items = None

    def __init__(self, *args, **kwargs):
        """Initialize Errors object."""
        super().__init__(*args, **kwargs)
        self.items = []

    def add(self, *args):
        """Add a new error."""
        self.items.append(args)

    def __len__(self):
        """Size of the list."""
        return len(self.items)


class DummyRequest:
    """Dummy request object."""

    matchdict = None
    errors = None

    def __init__(self, id: str):
        """Initialize matchdict with an id."""
        self.matchdict = {
            'id': id
        }
        self.errors = Errors()


def test_validate_id():
    """Test validate_id function."""
    func = validation.validate_id

    request = DummyRequest(id='b833ae9a-387c-4c76-a48f-c4d71b251561')
    assert func(request) is None
    assert len(request.errors) == 0


def test_validate_id_empty_id():
    """Test validate_id function."""
    func = validation.validate_id

    request = DummyRequest(id=None)
    assert func(request) is None
    assert len(request.errors) == 0


def test_validate_id_invalid_data():
    """Test validate_id function."""
    func = validation.validate_id

    # Invalid uuid
    request = DummyRequest(id='foo')
    assert func(request) is None
    assert len(request.errors) == 1
