"""
Fast Track Framework - Application Kernel

This module provides the main application class that integrates FastAPI with the IoC Container.

Key Features:
- Extends FastAPI with automatic dependency injection
- Manages Container lifecycle (startup/shutdown)
- Provides request-scoped dependency management via middleware

Design Decision:
    Inheriting from FastAPI (not composition) because:
    - Cleaner API: users call app.get(), not app.fastapi.get()
    - Full FastAPI compatibility: all features work as expected
    - Transparent integration: drop-in replacement for FastAPI

Trade-offs:
    + Simpler API surface
    + Better IDE support (autocomplete works)
    - Tightly coupled to FastAPI (but that's the point of this framework)
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ftf.core import Container, clear_scoped_cache, set_scoped_cache


class FastTrackFramework(FastAPI):
    """
    Application Kernel with integrated IoC Container.

    This class extends FastAPI to provide automatic dependency injection
    using the Fast Track Framework's Container.

    Features:
    - Built-in Container instance (accessible via app.container)
    - Lifespan management for startup/shutdown events
    - Request-scoped dependency management

    Example:
        >>> app = FastTrackFramework()
        >>> app.container.register(Database, scope="singleton")
        >>> app.container.register(UserService)
        >>>
        >>> @app.get("/users/{user_id}")
        >>> def get_user(
        ...     user_id: int,
        ...     service: UserService = Inject(UserService)
        ... ):
        ...     return service.get_user(user_id)
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the Fast Track Framework application.

        Args:
            *args: Positional arguments to pass to FastAPI
            **kwargs: Keyword arguments to pass to FastAPI
                Note: If 'lifespan' is not provided, we inject our own
        """
        # Initialize IoC Container FIRST (before FastAPI)
        # This ensures container is available during route registration
        self.container = Container()

        # Register the container itself (for self-injection patterns)
        # This allows routes to inject the Container if needed
        self.container.register(Container, implementation=Container, scope="singleton")
        # Make the container instance available via singleton
        self.container._singletons[Container] = self.container

        # Inject custom lifespan if not provided
        if "lifespan" not in kwargs:
            kwargs["lifespan"] = self._lifespan

        # Initialize FastAPI with our lifespan handler
        super().__init__(*args, **kwargs)

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG002
        """
        Application lifespan handler for startup/shutdown events.

        This manages the container lifecycle:
        - Startup: Log application start, initialize resources
        - Shutdown: Cleanup resources, close connections

        Args:
            app: The FastAPI application instance

        Yields:
            None: Application runs between startup and shutdown
        """
        # Startup Phase
        print("🚀 Fast Track Framework starting up...")  # noqa: T201
        print(f"📦 Container initialized with {len(self.container._registry)} services")  # noqa: T201

        # Yield control to the application
        # Everything between startup and shutdown happens here
        yield

        # Shutdown Phase
        print("🛑 Fast Track Framework shutting down...")  # noqa: T201
        print("✅ Cleanup complete")  # noqa: T201

    def register(
        self,
        interface: type,
        implementation: type | None = None,
        scope: str = "transient",
        instance: Any = None,
    ) -> None:
        """
        Convenience method to register dependencies directly on the app.

        This is a wrapper around self.container.register() to provide
        a more Laravel-like API.

        Args:
            interface: The type to register
            implementation: Concrete implementation (None = use interface)
            scope: Lifetime scope (singleton/transient/scoped)
            instance: Pre-existing instance for singleton registration

        Example:
            >>> app = FastTrackFramework()
            >>> app.register(Database, PostgresDatabase, scope="singleton")
            >>> app.register(UserService)  # transient by default
        """
        if instance is not None:
            # Register pre-existing singleton instance
            self.container.register(
                interface, implementation or interface, scope="singleton"
            )
            self.container._singletons[interface] = instance
        else:
            self.container.register(interface, implementation, scope)  # type: ignore


def scoped_middleware(app: FastTrackFramework, call_next: Any) -> Any:  # noqa: ARG001
    """
    Middleware for managing request-scoped dependencies.

    This middleware:
    1. Creates a new scoped cache at request start
    2. Processes the request (scoped dependencies are resolved)
    3. Clears the scoped cache at request end

    Design Decision:
        Using ContextVars (not threading.local) because:
        - Async-safe: Each async task gets its own context
        - No leakage: Context is automatically isolated
        - FastAPI-compatible: Works with async route handlers

    Args:
        app: The Fast Track Framework application
        call_next: Next middleware in the chain

    Returns:
        Async middleware callable

    Example:
        >>> app = FastTrackFramework()
        >>> app.add_middleware(scoped_middleware)
        >>> app.container.register(DatabaseSession, scope="scoped")
    """

    async def middleware(request: Request, call_next: Any) -> Response:
        """
        Process request with scoped dependency management.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        # Step 1: Initialize empty scoped cache for this request
        set_scoped_cache({})

        try:
            # Step 2: Process request (scoped dependencies resolved on-demand)
            response: Response = await call_next(request)
            return response
        finally:
            # Step 3: Cleanup scoped dependencies (prevent memory leaks)
            # This runs even if the request handler raises an exception
            clear_scoped_cache()

    return middleware


# Type alias for BaseHTTPMiddleware usage
class ScopedMiddleware(BaseHTTPMiddleware):
    """
    BaseHTTPMiddleware wrapper for scoped dependency management.

    This allows using scoped_middleware with Starlette's middleware system.

    Example:
        >>> app.add_middleware(ScopedMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Dispatch request with scoped cache management."""
        middleware = scoped_middleware(self.app, call_next)  # type: ignore
        response: Response = await middleware(request, call_next)
        return response
