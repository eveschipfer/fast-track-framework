"""
Fast Query Exceptions

Framework-agnostic exception classes for the fast_query ORM package.

These exceptions are NOT tied to any web framework (FastAPI, Flask, etc.).
They provide a clean separation between the ORM layer and HTTP layer.

Usage:
    from fast_query import RecordNotFound, FastQueryError

    try:
        user = await repo.find_or_fail(123)
    except RecordNotFound as e:
        # Handle missing record (return 404, log, etc.)
        print(f"Record not found: {e}")

WHY FRAMEWORK-AGNOSTIC:
    - Reusable: Works with FastAPI, Flask, Django, CLI tools, background jobs
    - Testable: No HTTP dependencies in tests
    - Clean: ORM layer shouldn't know about web frameworks
    - Flexible: Each framework can map exceptions to HTTP responses

See: src/ftf/http/app.py for FastAPI exception handler example
"""


class FastQueryError(Exception):
    """
    Base exception for all fast_query errors.

    All custom exceptions in fast_query inherit from this base class.
    This allows catching any fast_query error with a single except clause.

    Example:
        >>> try:
        ...     result = await some_query_operation()
        ... except FastQueryError as e:
        ...     # Handle any fast_query error
        ...     logger.error(f"Database error: {e}")
    """

    pass


class RecordNotFound(FastQueryError):
    """
    Raised when a record is not found in the database.

    This is a framework-agnostic exception that replaces HTTPException(404).
    Web frameworks can catch this and convert it to appropriate HTTP responses.

    Attributes:
        model_name: Name of the model that wasn't found (e.g., "User")
        identifier: The ID or criteria that failed (e.g., 123)
        message: Human-readable error message

    Example:
        >>> # Raise in repository
        >>> raise RecordNotFound("User", user_id)
        >>>
        >>> # Catch in web framework
        >>> @app.exception_handler(RecordNotFound)
        >>> async def handle_not_found(request, exc):
        ...     return JSONResponse(
        ...         status_code=404,
        ...         content={"error": str(exc)}
        ...     )
    """

    def __init__(
        self,
        model_name: str,
        identifier: int | str | None = None,
        message: str | None = None,
    ) -> None:
        """
        Initialize RecordNotFound exception.

        Args:
            model_name: Name of the model (e.g., "User", "Post")
            identifier: The ID or criteria that wasn't found (optional)
            message: Custom error message (optional, auto-generated if None)

        Example:
            >>> raise RecordNotFound("User", 123)
            >>> # "User not found: 123"
            >>>
            >>> raise RecordNotFound("Post", message="Post has been deleted")
            >>> # "Post has been deleted"
        """
        self.model_name = model_name
        self.identifier = identifier

        # Generate message if not provided
        if message is None:
            if identifier is not None:
                message = f"{model_name} not found: {identifier}"
            else:
                message = f"{model_name} not found"

        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        """Return the error message."""
        return self.message
