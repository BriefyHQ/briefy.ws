import pytest


@pytest.mark.usefixtures('login')
class TestSecureResource:
    """Validate resource access using jWT token."""

    token = None
    user = None

    def get_auth_header(self):
        """Format the Authorization header using token"""
        return {'Authorization': 'JWT {token}'.format(token=self.token)}

    def test_get_protected_success(self):
        """Call the protected view service with Authorization token."""
        headers = self.get_auth_header()
        response = self.app.get('/protected', headers=headers, status=200)
        assert 'application/json' == response.content_type

        result = response.json
        assert 'user' in result.keys()

        for field in ['locale', 'fullname', 'first_name', 'last_name', 'email', 'id', 'groups']:
            assert result['user'].get(field) is not None

    def test_get_protected_failure(self):
        """Call the protected view service without Authorization header."""
        response = self.app.get('/protected', status=401)
        assert 'application/json' == response.content_type

        result = response.json
        assert result.get('status') == 401
        assert result.get('message') == 'Unauthorized'
