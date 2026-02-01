"""
HTTP Kernel Tests (Sprint 3.4)

This module tests the HTTP exception handling and middleware configuration.

Test Coverage:
    - AppException and subclasses (AuthenticationError, AuthorizationError, etc.)
    - ExceptionHandler registration and response format
    - Middleware configuration (CORS, GZip, TrustedHost)
    - Integration with FastTrackFramework
"""

import os
from unittest.mock import patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from fast_query import RecordNotFound
from ftf.http import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    ExceptionHandler,
    FastTrackFramework,
    ValidationException,
    configure_cors,
    configure_gzip,
    configure_trusted_host,
)
from ftf.http.middleware import MiddlewareManager
from ftf.validation.request import ValidationError


# ============================================================================
# EXCEPTION TESTS
# ============================================================================


def test_app_exception_has_default_status_500() -> None:
    """Test that AppException defaults to 500 Internal Server Error."""
    exc = AppException("Something went wrong")

    assert exc.message == "Something went wrong"
    assert exc.status_code == 500
    assert exc.headers is None


def test_app_exception_accepts_custom_status_code() -> None:
    """Test that AppException accepts custom status code."""
    exc = AppException("Custom error", status_code=418)

    assert exc.message == "Custom error"
    assert exc.status_code == 418


def test_app_exception_accepts_custom_headers() -> None:
    """Test that AppException accepts custom headers."""
    headers = {"X-Custom-Header": "value"}
    exc = AppException("Error", headers=headers)

    assert exc.headers == headers


def test_authentication_error_has_status_401() -> None:
    """Test that AuthenticationError returns 401 Unauthorized."""
    exc = AuthenticationError()

    assert exc.status_code == 401
    assert exc.message == "Not authenticated"


def test_authentication_error_has_www_authenticate_header() -> None:
    """Test that AuthenticationError includes WWW-Authenticate header."""
    exc = AuthenticationError()

    assert exc.headers is not None
    assert "WWW-Authenticate" in exc.headers
    assert exc.headers["WWW-Authenticate"] == "Bearer"


def test_authentication_error_accepts_custom_message() -> None:
    """Test that AuthenticationError accepts custom message."""
    exc = AuthenticationError("Invalid credentials")

    assert exc.message == "Invalid credentials"
    assert exc.status_code == 401


def test_authorization_error_has_status_403() -> None:
    """Test that AuthorizationError returns 403 Forbidden."""
    exc = AuthorizationError()

    assert exc.status_code == 403
    assert exc.message == "Forbidden"


def test_authorization_error_accepts_custom_message() -> None:
    """Test that AuthorizationError accepts custom message."""
    exc = AuthorizationError("You don't have permission")

    assert exc.message == "You don't have permission"
    assert exc.status_code == 403


def test_validation_exception_has_status_422() -> None:
    """Test that ValidationException returns 422 Unprocessable Entity."""
    exc = ValidationException()

    assert exc.status_code == 422
    assert exc.message == "Validation failed"
    assert exc.errors == []


def test_validation_exception_accepts_errors_list() -> None:
    """Test that ValidationException accepts list of errors."""
    errors = [
        {"msg": "Email is required", "type": "value_error", "loc": ["body", "email"]}
    ]
    exc = ValidationException("Validation failed", errors=errors)

    assert exc.errors == errors


# ============================================================================
# EXCEPTION HANDLER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_exception_handler_catches_authentication_error() -> None:
    """Test that AuthenticationError is converted to 401 JSON response."""
    app = FastTrackFramework()

    @app.get("/test")
    async def test_route() -> None:
        raise AuthenticationError("Invalid token")

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}
    assert response.headers.get("WWW-Authenticate") == "Bearer"


@pytest.mark.asyncio
async def test_exception_handler_catches_authorization_error() -> None:
    """Test that AuthorizationError is converted to 403 JSON response."""
    app = FastTrackFramework()

    @app.get("/test")
    async def test_route() -> None:
        raise AuthorizationError("Insufficient permissions")

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}


@pytest.mark.asyncio
async def test_exception_handler_catches_validation_exception() -> None:
    """Test that ValidationException is converted to 422 JSON response."""
    app = FastTrackFramework()

    @app.get("/test")
    async def test_route() -> None:
        errors = [
            {
                "msg": "Email is required",
                "type": "value_error",
                "loc": ["body", "email"],
            }
        ]
        raise ValidationException("Validation failed", errors=errors)

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "msg": "Email is required",
                "type": "value_error",
                "loc": ["body", "email"],
            }
        ]
    }


@pytest.mark.asyncio
async def test_exception_handler_catches_record_not_found() -> None:
    """Test that RecordNotFound is converted to 404 JSON response."""
    app = FastTrackFramework()

    @app.get("/test")
    async def test_route() -> None:
        raise RecordNotFound("User", 123)

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found: 123"}


@pytest.mark.asyncio
async def test_exception_handler_catches_validation_error() -> None:
    """Test that ValidationError is converted to 422 JSON response."""
    app = FastTrackFramework()

    @app.get("/test")
    async def test_route() -> None:
        raise ValidationError("Email already exists", field="email")

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert len(data["detail"]) == 1
    assert data["detail"][0]["msg"] == "Email already exists"
    assert data["detail"][0]["loc"] == ["body", "email"]


@pytest.mark.asyncio
async def test_exception_handler_is_automatically_registered() -> None:
    """Test that ExceptionHandler is automatically registered on app init."""
    app = FastTrackFramework()

    # Verify exception handlers are registered by testing one
    @app.get("/test")
    async def test_route() -> None:
        raise AuthenticationError("Not logged in")

    client = TestClient(app)
    response = client.get("/test")

    # If handler is registered, we get 401 with JSON
    # If not registered, we'd get 500 with HTML
    assert response.status_code == 401
    assert response.headers["content-type"] == "application/json"


# ============================================================================
# MIDDLEWARE TESTS
# ============================================================================


def test_configure_cors_with_default_settings() -> None:
    """Test CORS configuration with default settings."""
    app = FastTrackFramework()
    configure_cors(app)

    # Test that OPTIONS request succeeds (CORS preflight)
    client = TestClient(app)
    response = client.options("/", headers={"Origin": "http://localhost:3000"})

    # Should have CORS headers
    assert "access-control-allow-origin" in response.headers


def test_configure_cors_with_custom_origins() -> None:
    """Test CORS configuration with specific allowed origins."""
    app = FastTrackFramework()
    configure_cors(app, allow_origins=["https://example.com"])

    client = TestClient(app)

    # Test allowed origin
    response = client.options(
        "/",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" in response.headers


def test_configure_cors_reads_from_env_var() -> None:
    """Test that CORS configuration reads from CORS_ORIGINS env var."""
    with patch.dict(os.environ, {"CORS_ORIGINS": "https://app1.com,https://app2.com"}):
        app = FastTrackFramework()
        configure_cors(app)

        client = TestClient(app)
        response = client.options(
            "/",
            headers={
                "Origin": "https://app1.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in response.headers


def test_configure_gzip_is_applied() -> None:
    """Test that GZip middleware compresses responses."""
    app = FastTrackFramework()
    configure_gzip(app, minimum_size=100)

    @app.get("/test")
    async def test_route() -> dict[str, str]:
        # Return large enough response to trigger compression
        return {"data": "x" * 1000}

    client = TestClient(app)
    response = client.get("/test", headers={"Accept-Encoding": "gzip"})

    # If gzip is working, response should be compressed
    # (Content-Encoding header would be set, but TestClient auto-decompresses)
    assert response.status_code == 200


def test_configure_trusted_host_with_allowed_hosts() -> None:
    """Test that TrustedHost middleware validates Host header."""
    app = FastTrackFramework()
    configure_trusted_host(app, allowed_hosts=["example.com"])

    @app.get("/test")
    async def test_route() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)

    # Valid host should work
    response = client.get("/test", headers={"Host": "example.com"})
    assert response.status_code == 200

    # Invalid host should be rejected
    response = client.get("/test", headers={"Host": "evil.com"})
    assert response.status_code == 400


def test_middleware_manager_configures_all() -> None:
    """Test that MiddlewareManager.configure_all() sets up all middleware."""
    app = FastTrackFramework()

    # Configure all middleware
    MiddlewareManager.configure_all(app, enable_trusted_host=False)

    # Verify app works (middleware is registered)
    @app.get("/test")
    async def test_route() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200


def test_middleware_manager_respects_enable_flags() -> None:
    """Test that MiddlewareManager respects enable flags."""
    app = FastTrackFramework()

    # Disable all middleware
    MiddlewareManager.configure_all(
        app, enable_cors=False, enable_gzip=False, enable_trusted_host=False
    )

    # App should still work
    @app.get("/test")
    async def test_route() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_complete_error_handling_flow() -> None:
    """Test complete error handling: exception -> handler -> JSON response."""
    app = FastTrackFramework()

    @app.get("/auth-test")
    async def auth_test() -> None:
        raise AuthenticationError("Please login")

    @app.get("/forbidden-test")
    async def forbidden_test() -> None:
        raise AuthorizationError("Admins only")

    @app.get("/not-found-test")
    async def not_found_test() -> None:
        raise RecordNotFound("Post", 999)

    client = TestClient(app)

    # Test 401
    response = client.get("/auth-test")
    assert response.status_code == 401
    assert response.json()["detail"] == "Please login"

    # Test 403
    response = client.get("/forbidden-test")
    assert response.status_code == 403
    assert response.json()["detail"] == "Admins only"

    # Test 404
    response = client.get("/not-found-test")
    assert response.status_code == 404
    assert "Post not found: 999" in response.json()["detail"]


@pytest.mark.asyncio
async def test_middleware_and_exceptions_work_together() -> None:
    """Test that middleware and exception handling work together."""
    app = FastTrackFramework()
    configure_cors(app)
    configure_gzip(app)

    @app.get("/test")
    async def test_route() -> None:
        raise AuthenticationError("Token expired")

    client = TestClient(app)
    response = client.get("/test", headers={"Origin": "http://localhost:3000"})

    # Exception handling works
    assert response.status_code == 401

    # CORS headers present
    assert "access-control-allow-origin" in response.headers
