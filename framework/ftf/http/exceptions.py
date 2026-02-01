"""
HTTP Exception Handler (Sprint 3.4)

This module provides a global exception handling system inspired by Laravel's
app/Exceptions/Handler.php. It maps Python exceptions to standardized HTTP
JSON responses.

Key Features:
    - AppException base class for all framework exceptions
    - ExceptionHandler registry that maps exceptions to HTTP responses
    - Automatic 404, 401, 403, 422 error handling
    - Integration with fast_query (RecordNotFound)
    - JSON-only responses (no HTML)

Educational Note:
    Laravel uses app/Exceptions/Handler.php to convert exceptions to HTTP responses.
    We do the same here but in a more Pythonic way using FastAPI's exception_handler
    decorator pattern combined with a centralized registry.

Architecture Decision:
    - We keep fast_query exceptions framework-agnostic (they don't know about HTTP)
    - The HTTP layer (this module) knows how to convert them to HTTP responses
    - This maintains clean separation: ORM doesn't depend on web framework

Usage:
    # In app initialization
    app = FastTrackFramework()
    ExceptionHandler.register_all(app)

    # In your code
    raise AuthenticationError("Invalid credentials")
    # Automatically becomes: {"detail": "Invalid credentials"} with status 401

Comparison with Laravel:
    Laravel:
        throw new AuthenticationException('Unauthenticated');
        // Handled by app/Exceptions/Handler.php

    Fast Track:
        raise AuthenticationError("Unauthenticated")
        # Handled by ExceptionHandler.register_all()
"""

from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Import fast_query exceptions (framework-agnostic)
from fast_query import RecordNotFound

# Import validation exception
from ftf.validation.request import ValidationError


# ============================================================================
# BASE EXCEPTION CLASS
# ============================================================================


class AppException(Exception):
    """
    Base class for all framework exceptions.

    All custom exceptions in Fast Track Framework inherit from this class.
    This allows catching any framework error with a single except clause.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code (default: 500)
        headers: Optional HTTP headers to include in response

    Example:
        >>> class CustomError(AppException):
        ...     def __init__(self, message: str):
        ...         super().__init__(message, status_code=418)
        ...
        >>> raise CustomError("I'm a teapot")
        >>> # Returns: {"detail": "I'm a teapot"} with status 418

    Educational Note:
        This is similar to Laravel's base Exception class, but we add
        status_code and headers to make HTTP integration seamless.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize AppException.

        Args:
            message: Error message
            status_code: HTTP status code (default: 500 Internal Server Error)
            headers: Optional HTTP headers (e.g., WWW-Authenticate for 401)

        Example:
            >>> raise AppException("Something went wrong")
            >>> # Returns: {"detail": "Something went wrong"} with status 500
            >>>
            >>> raise AppException(
            ...     "Token expired",
            ...     status_code=401,
            ...     headers={"WWW-Authenticate": "Bearer"}
            ... )
        """
        self.message = message
        self.status_code = status_code
        self.headers = headers
        super().__init__(message)

    def __str__(self) -> str:
        """Return the error message."""
        return self.message


# ============================================================================
# SPECIFIC EXCEPTION TYPES
# ============================================================================


class AuthenticationError(AppException):
    """
    Raised when user is not authenticated.

    Returns HTTP 401 Unauthorized with optional WWW-Authenticate header.

    Example:
        >>> raise AuthenticationError("Invalid credentials")
        >>> # Returns: {"detail": "Invalid credentials"} with status 401

    Educational Note:
        401 means "not authenticated" (no valid credentials provided)
        403 means "not authorized" (valid credentials but insufficient permissions)
    """

    def __init__(
        self,
        message: str = "Not authenticated",
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize AuthenticationError.

        Args:
            message: Error message (default: "Not authenticated")
            headers: Optional headers (e.g., WWW-Authenticate)

        Example:
            >>> raise AuthenticationError()
            >>> # Returns: {"detail": "Not authenticated"} with status 401
            >>>
            >>> raise AuthenticationError(
            ...     "Token expired",
            ...     headers={"WWW-Authenticate": 'Bearer realm="api"'}
            ... )
        """
        # Set WWW-Authenticate header by default (RFC 7235)
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}

        super().__init__(message, status_code=401, headers=headers)


class AuthorizationError(AppException):
    """
    Raised when user is authenticated but not authorized.

    Returns HTTP 403 Forbidden.

    Example:
        >>> raise AuthorizationError("You don't have permission to delete this post")
        >>> # Returns: {"detail": "You don't have permission..."} with status 403

    Educational Note:
        Use 401 when: No credentials or invalid credentials (login required)
        Use 403 when: Valid credentials but insufficient permissions (e.g., not admin)

    Comparison with Laravel:
        Laravel:
            abort(403, 'Forbidden');
            // or
            throw new AuthorizationException('Forbidden');

        Fast Track:
            raise AuthorizationError("Forbidden")
    """

    def __init__(self, message: str = "Forbidden") -> None:
        """
        Initialize AuthorizationError.

        Args:
            message: Error message (default: "Forbidden")

        Example:
            >>> raise AuthorizationError()
            >>> # Returns: {"detail": "Forbidden"} with status 403
            >>>
            >>> raise AuthorizationError("Only admins can delete users")
        """
        super().__init__(message, status_code=403)


class ValidationException(AppException):
    """
    Raised when request validation fails.

    Returns HTTP 422 Unprocessable Entity with validation errors.

    This is used by FormRequest and custom validation logic to return
    structured validation errors in FastAPI's standard format.

    Attributes:
        errors: List of validation errors (FastAPI format)

    Example:
        >>> raise ValidationException(
        ...     "Validation failed",
        ...     errors=[
        ...         {"msg": "Email already exists", "type": "value_error", "loc": ["body", "email"]},
        ...         {"msg": "Password too short", "type": "value_error", "loc": ["body", "password"]}
        ...     ]
        ... )
        >>> # Returns: {"detail": [...]} with status 422

    Educational Note:
        422 Unprocessable Entity is the standard HTTP status for validation errors.
        It means "the request was well-formed but contains semantic errors".
        This is different from 400 Bad Request which means the request syntax is invalid.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Initialize ValidationException.

        Args:
            message: Error message (default: "Validation failed")
            errors: List of validation errors in FastAPI format

        Example:
            >>> raise ValidationException(
            ...     "Email is required",
            ...     errors=[
            ...         {"msg": "Email is required", "type": "value_error", "loc": ["body", "email"]}
            ...     ]
            ... )
        """
        super().__init__(message, status_code=422)
        self.errors = errors or []


# ============================================================================
# EXCEPTION HANDLERS (Convert exceptions to HTTP responses)
# ============================================================================


async def handle_app_exception(
    request: Request, exc: AppException  # noqa: ARG001
) -> JSONResponse:
    """
    Global handler for AppException and subclasses.

    Converts any AppException into a JSON response with appropriate
    status code and headers.

    Args:
        request: The incoming HTTP request (unused)
        exc: The AppException instance

    Returns:
        JSONResponse: HTTP response with error details

    Example:
        >>> raise AuthenticationError("Token expired")
        >>> # Returns: {"detail": "Token expired"} with status 401
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
        headers=exc.headers,
    )


async def handle_validation_exception(
    request: Request, exc: ValidationException  # noqa: ARG001
) -> JSONResponse:
    """
    Handler for ValidationException.

    Returns validation errors in FastAPI's standard format.

    Args:
        request: The incoming HTTP request (unused)
        exc: The ValidationException instance

    Returns:
        JSONResponse: 422 response with validation errors

    Example:
        >>> raise ValidationException(
        ...     "Email already exists",
        ...     errors=[{"msg": "Email already exists", "type": "value_error", "loc": ["body", "email"]}]
        ... )
        >>> # Returns: {"detail": [{"msg": "...", "type": "...", "loc": [...]}]}
    """
    # If errors are provided, use them; otherwise create single error from message
    if exc.errors:
        content = {"detail": exc.errors}
    else:
        content = {"detail": exc.message}

    return JSONResponse(
        status_code=422,
        content=content,
    )


async def handle_record_not_found(
    request: Request, exc: RecordNotFound  # noqa: ARG001
) -> JSONResponse:
    """
    Handler for fast_query RecordNotFound exception.

    Converts framework-agnostic RecordNotFound into HTTP 404.

    Args:
        request: The incoming HTTP request (unused)
        exc: The RecordNotFound exception

    Returns:
        JSONResponse: 404 response with error details

    Example:
        >>> raise RecordNotFound("User", 123)
        >>> # Returns: {"detail": "User not found: 123"} with status 404

    Educational Note:
        This demonstrates clean separation between ORM and HTTP layers.
        fast_query doesn't know about HTTP, but this handler converts
        its exceptions into proper HTTP responses.
    """
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


async def handle_validation_error(
    request: Request, exc: ValidationError  # noqa: ARG001
) -> JSONResponse:
    """
    Handler for FormRequest ValidationError.

    Converts ValidationError from FormRequest.rules() into HTTP 422.

    Args:
        request: The incoming HTTP request (unused)
        exc: The ValidationError instance

    Returns:
        JSONResponse: 422 response with validation error

    Example:
        >>> raise ValidationError("Email already exists", field="email")
        >>> # Returns: {"detail": [{"msg": "...", "loc": ["body", "email"]}]}
    """
    # Create FastAPI-style validation error
    detail: list[dict[str, Any]] = [
        {
            "msg": exc.message,
            "type": "value_error",
            "loc": ["body", exc.field] if exc.field else ["body"],
        }
    ]

    return JSONResponse(
        status_code=422,
        content={"detail": detail},
    )


# ============================================================================
# EXCEPTION HANDLER REGISTRY
# ============================================================================


class ExceptionHandler:
    """
    Central registry for exception handlers.

    This class provides a clean way to register all exception handlers
    with the FastAPI application. It's inspired by Laravel's Handler class
    but adapted for FastAPI's exception_handler decorator pattern.

    Example:
        >>> app = FastTrackFramework()
        >>> ExceptionHandler.register_all(app)
        >>> # All exceptions are now handled globally

    Educational Note:
        Laravel uses a single Handler class with render() method.
        FastAPI uses multiple exception_handler decorators.
        We combine the best of both: a registry class that registers
        all handlers in one call.

    Comparison with Laravel:
        Laravel (app/Exceptions/Handler.php):
            public function register() {
                $this->renderable(function (NotFoundHttpException $e) {
                    return response()->json(['message' => 'Not found'], 404);
                });
            }

        Fast Track:
            ExceptionHandler.register_all(app)
            # Automatically registers all exception handlers
    """

    @staticmethod
    def register_all(app: FastAPI) -> None:
        """
        Register all exception handlers with the FastAPI app.

        This should be called during app initialization, typically in
        the FastTrackFramework.__init__() method.

        Args:
            app: The FastAPI application instance

        Example:
            >>> app = FastTrackFramework()
            >>> ExceptionHandler.register_all(app)
            >>> # All exceptions are now handled

        Handler Priority:
            1. Most specific exceptions first (ValidationException)
            2. Then broader exceptions (AppException catches all subclasses)
            3. Finally framework-agnostic exceptions (RecordNotFound, ValidationError)

        Educational Note:
            FastAPI checks exception handlers in REVERSE registration order.
            So we register AppException BEFORE its subclasses to ensure
            subclasses are checked first.
        """
        # Register framework-agnostic exceptions (from other packages)
        app.add_exception_handler(RecordNotFound, handle_record_not_found)
        app.add_exception_handler(ValidationError, handle_validation_error)

        # Register ValidationException BEFORE AppException (more specific)
        app.add_exception_handler(ValidationException, handle_validation_exception)

        # Register base AppException (catches all subclasses)
        # This MUST be registered AFTER subclasses so subclasses are checked first
        app.add_exception_handler(AppException, handle_app_exception)

    @staticmethod
    def register(
        app: FastAPI,
        exception_class: type[Exception],
        handler: Callable[[Request, Exception], JSONResponse],
    ) -> None:
        """
        Register a custom exception handler.

        Use this to add your own exception handlers beyond the built-in ones.

        Args:
            app: The FastAPI application
            exception_class: The exception class to handle
            handler: Async function that converts exception to JSONResponse

        Example:
            >>> class CustomError(AppException):
            ...     pass
            ...
            >>> async def handle_custom(request, exc):
            ...     return JSONResponse(
            ...         status_code=418,
            ...         content={"detail": "I'm a teapot"}
            ...     )
            ...
            >>> ExceptionHandler.register(app, CustomError, handle_custom)

        Educational Note:
            This provides an escape hatch for custom exception types
            that don't fit the standard patterns. In Laravel, you'd
            add this to the Handler::register() method.
        """
        app.add_exception_handler(exception_class, handler)  # type: ignore
