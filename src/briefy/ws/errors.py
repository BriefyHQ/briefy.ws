"""Briefy microservices errors."""


class ValidationError(ValueError):
    """Validation error."""

    def __init__(self, message: str = '', location: str = 'body', name: str = ''):
        """Initialize a ValidationError.

        :param message: Error message.
        :param location: Where the message occurred.
        :param name: Field name.
        """
        super().__init__(message)
        self.message = message
        self.location = location
        self.name = name
