"""
Fast Track Framework - HTTP Module

This module provides FastAPI integration with the IoC Container.

Public API:
    FastTrackFramework: Main application kernel with DI integration
    Inject: Dependency injection parameter for FastAPI routes
    scoped_middleware: Middleware for request-scoped dependency management

Exception Handling (Sprint 3.4):
    AppException: Base exception class for framework exceptions
    AuthenticationError: 401 Unauthorized
    AuthorizationError: 403 Forbidden
    ValidationException: 422 Unprocessable Entity
    ExceptionHandler: Registry for exception handlers

Middleware (Sprint 3.4):
    configure_cors: CORS configuration
    configure_gzip: GZip compression
    configure_trusted_host: Security headers
    MiddlewareManager: Centralized middleware configuration
"""

from .app import FastTrackFramework, scoped_middleware
from .exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    ExceptionHandler,
    ValidationException,
)
from .middleware import (
    MiddlewareManager,
    configure_cors,
    configure_gzip,
    configure_trusted_host,
)
from .params import Inject

__all__ = [
    # Core
    "FastTrackFramework",
    "Inject",
    "scoped_middleware",
    # Exceptions (Sprint 3.4)
    "AppException",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationException",
    "ExceptionHandler",
    # Middleware (Sprint 3.4)
    "configure_cors",
    "configure_gzip",
    "configure_trusted_host",
    "MiddlewareManager",
]
