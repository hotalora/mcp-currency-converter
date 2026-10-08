class EmailAlreadyRegisteredError(Exception):
    """Raised when a user attempts to register an existing email."""


class InvalidCredentialsError(Exception):
    """Raised when the email and password do not match a user."""


class InvalidTokenError(Exception):
    """Raised when a token is invalid, expired, revoked, or of the wrong type."""
