"""
Auth Domain Exceptions

Pure domain exceptions raised by the auth and user service layers.
They are intentionally free of any HTTP / FastAPI concerns.

The controller layer translates these into the appropriate HTTP responses:
    InvalidCredentials  → 401 Unauthorized
    UserNotFound        → 404 Not Found (or 401 to avoid user enumeration)
    EmailAlreadyTaken   → 422 Unprocessable Entity
    TokenExpired        → 401 Unauthorized
    InvalidToken        → 401 Unauthorized
    ForbiddenToken      → 403 Forbidden  (signature tampered)
"""


class InvalidCredentials(Exception):
    """Raised when login email/password do not match any active user."""

    def __init__(self, message: str = "Invalid email or password") -> None:
        super().__init__(message)


class UserNotFound(Exception):
    """Raised when a user cannot be located by any identifier."""

    def __init__(self, identifier: str | int) -> None:
        self.identifier = identifier
        super().__init__(f"User '{identifier}' not found")


class EmailAlreadyTaken(Exception):
    """Raised when a create/update would produce a duplicate email."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"The email '{email}' is already registered")


class TokenExpired(Exception):
    """Raised when a JWT has passed its expiration time (exp < now)."""

    def __init__(self, message: str = "Token has expired") -> None:
        super().__init__(message)


class InvalidToken(Exception):
    """Raised when a JWT is malformed, has an unsupported algorithm, etc."""

    def __init__(self, message: str = "Token is invalid") -> None:
        super().__init__(message)


class ForbiddenToken(Exception):
    """
    Raised when JWT signature verification fails — the token was tampered with.

    Maps to HTTP 403 Forbidden (not 401 Unauthorized) because the client
    is identified (has a token) but the token has been compromised.
    """

    def __init__(self, message: str = "Token signature is invalid") -> None:
        super().__init__(message)
