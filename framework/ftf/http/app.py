"""
Fast Track Framework - Application Kernel

This module provides the main application class that integrates FastAPI with the IoC Container.

ARCHITECTURE BOUNDARY: FastAPI Adapter
    FastTrackFramework is a STRICT ADAPTER over FastAPI. It adds dependency
    injection capabilities while preserving full FastAPI functionality.

    Direct FastAPI Usage:
        - All FastAPI features (routing, middleware, dependencies) work as-is
        - You CAN import from fastapi directly and use standard FastAPI patterns
        - Standard FastAPI dependencies (@Depends) work alongside ftf.Inject()

    Framework Conventions (Preferred):
        - Use ftf.Inject() instead of FastAPI's Depends() for better DI
        - Use app.register() for service registration
        - Use Service Providers for organized application bootstrapping
        - These conventions provide forward compatibility if internal
          implementation changes

    Forward Compatibility:
        Framework conventions (Inject, Service Providers, Container) are
        guaranteed stable across minor versions. Direct FastAPI imports
        follow FastAPI's own compatibility guarantees.

    When to use FastAPI directly:
        - Adding standard FastAPI middleware
        - Using FastAPI's background tasks
        - Advanced FastAPI features not yet wrapped by ftf

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
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ftf.config import get_config_repository
from ftf.core import Container, clear_scoped_cache_async, set_scoped_cache

if TYPE_CHECKING:
    from ftf.core.service_provider import ServiceProvider


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

    def __init__(
        self, *args: Any, config_path: str | None = None, **kwargs: Any
    ) -> None:
        """
        Initialize the Fast Track Framework application.

        Args:
            *args: Positional arguments to pass to FastAPI
            config_path: Path to config directory (default: "workbench/config")
            **kwargs: Keyword arguments to pass to FastAPI
                Note: If 'lifespan' is not provided, we inject our own

        Sprint 5.3: Auto-loads configuration and registers providers from config.
        """
        # Initialize IoC Container FIRST (before FastAPI)
        # This ensures container is available during route registration
        self.container = Container()

        # Initialize provider tracking lists (Sprint 5.2)
        self._providers: list["ServiceProvider"] = []
        self._booted: bool = False

        # Register the container itself (for self-injection patterns)
        # This allows routes to inject the Container if needed
        self.container.register(Container, implementation=Container, scope="singleton")
        # Make the container instance available via singleton
        self.container._singletons[Container] = self.container

        # Register FastTrackFramework itself in the container
        # This allows providers to resolve the app instance
        self.container.register(
            FastTrackFramework, implementation=FastTrackFramework, scope="singleton"
        )
        self.container._singletons[FastTrackFramework] = self

        # Sprint 5.3: Load configuration from files
        if config_path is None:
            # Default to workbench/config
            config_path = self._detect_config_path()

        self._load_configuration(config_path)

        # Sprint 5.3: Auto-register providers from config
        self._register_configured_providers()

        # Inject custom lifespan if not provided
        if "lifespan" not in kwargs:
            kwargs["lifespan"] = self._lifespan

        # Initialize FastAPI with our lifespan handler
        super().__init__(*args, **kwargs)

        # Register all global exception handlers (Sprint 3.4)
        # This includes: RecordNotFound -> 404, AuthenticationError -> 401,
        # AuthorizationError -> 403, ValidationException -> 422
        from ftf.http.exceptions import ExceptionHandler

        ExceptionHandler.register_all(self)

    def _detect_config_path(self) -> str:
        """
        Auto-detect the config directory path.

        Looks for workbench/config/ relative to the current working directory.

        Returns:
            str: Path to config directory

        Raises:
            FileNotFoundError: If config directory cannot be found
        """
        # Try workbench/config (standard location)
        workbench_config = Path("workbench/config")
        if workbench_config.exists():
            return str(workbench_config)

        # Try config in current directory (alternative)
        config_dir = Path("config")
        if config_dir.exists():
            return str(config_dir)

        # Config directory not found - will be created or cause error in load
        return "workbench/config"

    def _load_configuration(self, config_path: str) -> None:
        """
        Load all configuration files from the config directory.

        This method loads all .py files from the config directory into
        the ConfigRepository singleton.

        Args:
            config_path: Path to the config directory

        Note:
            If the config directory doesn't exist, this method silently
            continues to allow the app to work without config files.
        """
        config_repo = get_config_repository()

        try:
            config_repo.load_from_directory(config_path)
            print(f"📝 Loaded configuration from: {config_path}")  # noqa: T201
        except FileNotFoundError:
            # Config directory doesn't exist - continue without config
            print(f"⚠️  Config directory not found: {config_path}")  # noqa: T201
            print("   Continuing without configuration files...")  # noqa: T201

    def _register_configured_providers(self) -> None:
        """
        Auto-register service providers from app.providers config.

        This method reads the config.get("app.providers") list and
        automatically registers each provider class.

        This eliminates the need for manual provider registration in main.py:

        Before (Sprint 5.2):
            app.register_provider(AppServiceProvider)
            app.register_provider(RouteServiceProvider)

        After (Sprint 5.3):
            # Automatic! Reads from config/app.py
        """
        from ftf.config import config

        # Get providers list from config
        providers = config("app.providers", [])

        if not providers:
            print("⚠️  No providers configured in config/app.py")  # noqa: T201
            return

        # Register each provider
        for provider_class in providers:
            self.register_provider(provider_class)

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG002
        """
        Application lifespan handler for startup/shutdown events.

        This manages the container lifecycle:
        - Startup: Log application start, initialize resources, boot providers
        - Shutdown: Cleanup resources, close connections

        Args:
            app: The FastAPI application instance

        Yields:
            None: Application runs between startup and shutdown
        """
        # Startup Phase
        print("🚀 Fast Track Framework starting up...")  # noqa: T201
        print(f"📦 Container initialized with {len(self.container._registry)} services")  # noqa: T201

        # Boot all registered service providers (Sprint 5.2)
        if self._providers and not self._booted:
            print(f"🔧 Booting {len(self._providers)} service provider(s)...")  # noqa: T201
            self.boot_providers()

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

    def register_provider(self, provider_class: type["ServiceProvider"]) -> None:
        """
        Register a service provider with the application.

        Service providers follow a two-phase initialization:
        1. Register phase: All providers' register() methods are called
        2. Boot phase: All providers' boot() methods are called

        This ensures all services are registered before bootstrapping begins.

        Args:
            provider_class: The service provider class to register

        Example:
            >>> from app.providers import AppServiceProvider, RouteServiceProvider
            >>> app = FastTrackFramework()
            >>> app.register_provider(AppServiceProvider)
            >>> app.register_provider(RouteServiceProvider)
            >>> app.boot_providers()  # Called automatically during startup
        """
        # Instantiate the provider
        provider = provider_class()

        # Store the provider instance
        self._providers.append(provider)

        # Immediately call register() to bind services
        provider.register(self.container)

    def boot_providers(self) -> None:
        """
        Boot all registered service providers.

        This calls the boot() method on all registered providers.
        Should be called after all providers are registered, typically
        during application startup.

        The boot phase happens AFTER all register() methods have completed,
        ensuring all services are available for bootstrapping logic.

        Example:
            >>> app = FastTrackFramework()
            >>> app.register_provider(DatabaseServiceProvider)
            >>> app.register_provider(RouteServiceProvider)
            >>> app.boot_providers()  # Bootstraps all providers
        """
        if self._booted:
            return  # Already booted, skip

        # Call boot() on all providers
        for provider in self._providers:
            provider.boot(self.container)

        # Mark as booted
        self._booted = True


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
            # Step 3: Cleanup scoped dependencies with async disposal
            # This calls close() on database sessions and other resources
            # Runs even if the request handler raises an exception
            await clear_scoped_cache_async()

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
