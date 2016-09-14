"""Briefy microservices errors."""


class ValidationError(Exception):
    """Validation error."""

    def __init__(self, message:str, location:str, name:str):
        """Initialize a ValidationError.

        :param message: Error message.
        :param location: Where the message occured.
        :param name: Field name.
        """
        self.message = message
        self.location = location
        self.name = name
