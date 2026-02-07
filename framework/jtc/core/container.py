"""
IoC Container - Dependency Injection for Fast Track Framework.

This module provides a type-hint based dependency injection container
with automatic dependency resolution.

Key Features:
- Type-hint based dependency injection
- Three lifetime scopes: singleton, transient, scoped
- Circular dependency detection
- Nested dependency resolution
- Thread-safe and async-safe with ContextVars

Inspired by:
- FastAPI: Uses Depends() with similar type-based resolution
- Laravel: Service Container pattern
- ASP.NET Core: Explicit lifetime scopes
"""

import inspect
from contextvars import ContextVar
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Literal, get_type_hints

from .exceptions import (
    CircularDependencyError,
    DependencyResolutionError,
)

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

# Type alias for scope literals
Scope = Literal["singleton", "transient", "scoped"]


@dataclass
class Registration:
    """
    Metadata about a registered dependency.

    Attributes:
        implementation: The concrete class to instantiate
        scope: Lifetime scope (singleton/transient/scoped)

    Design Decision:
        Using dataclass instead of dict for:
        - Type safety (MyPy can validate)
        - IDE autocomplete
        - Easier refactoring
    """

    implementation: type
    scope: Scope = "transient"


# ============================================================================
# SCOPED CONTEXT (Request-Level Instances)
# ============================================================================

# ContextVar for request-scoped instances
# This is thread-safe and async-safe, unlike threading.local
_scoped_instances: ContextVar[dict[type, Any]] = ContextVar(
    "scoped_instances", default={}
)


def get_scoped_cache() -> dict[type, Any]:
    """
    Get current request's scoped instance cache.

    Returns:
        Dictionary mapping types to their scoped instances
    """
    return _scoped_instances.get()


def set_scoped_cache(cache: dict[type, Any]) -> None:
    """
    Set scoped instance cache for current request.

    Args:
        cache: Dictionary of scoped instances for this request
    """
    _scoped_instances.set(cache)


def clear_scoped_cache() -> None:
    """
    Clear scoped instances (call at end of request).

    This should be called by middleware at the end of each request
    to prevent memory leaks.

    WARNING: This does NOT call cleanup methods on instances.
    Use clear_scoped_cache_async() for proper resource cleanup.
    """
    _scoped_instances.set({})


async def _dispose_instance(instance: Any) -> None:
    """
    Dispose a single instance by calling its cleanup method.

    Supports multiple cleanup patterns:
    1. async def close(self) - Async cleanup (preferred)
    2. def close(self) - Sync cleanup
    3. async def dispose(self) - Alternative async cleanup
    4. def dispose(self) - Alternative sync cleanup
    5. async context manager (__aexit__) - Not used here (requires __aenter__)

    Args:
        instance: Object to dispose

    Note:
        Silently ignores objects without cleanup methods.
        Logs errors but continues disposal (fail-safe).
    """
    # Try async close() first
    if hasattr(instance, "close") and inspect.iscoroutinefunction(instance.close):
        try:
            await instance.close()
            return
        except Exception:
            # TODO: Add logging when logging system exists
            pass

    # Try sync close()
    if hasattr(instance, "close") and callable(instance.close):
        try:
            instance.close()
            return
        except Exception:
            pass

    # Try async dispose()
    if hasattr(instance, "dispose") and inspect.iscoroutinefunction(
        instance.dispose
    ):
        try:
            await instance.dispose()
            return
        except Exception:
            pass

    # Try sync dispose()
    if hasattr(instance, "dispose") and callable(instance.dispose):
        try:
            instance.dispose()
            return
        except Exception:
            pass

    # No cleanup method found - this is OK (not all objects need cleanup)


async def clear_scoped_cache_async() -> None:
    """
    Clear scoped instances with proper async cleanup.

    This is the RECOMMENDED way to clear scoped cache in async applications.

    Algorithm:
    1. Get current scoped cache
    2. Dispose each instance (call close/dispose methods)
    3. Clear cache

    Example:
        # FastAPI middleware
        @app.middleware("http")
        async def scoped_lifecycle(request, call_next):
            set_scoped_cache({})
            try:
                response = await call_next(request)
                return response
            finally:
                await clear_scoped_cache_async()
    """
    cache = get_scoped_cache()

    # Dispose all instances
    for instance in cache.values():
        await _dispose_instance(instance)

    # Clear cache
    _scoped_instances.set({})


# ============================================================================
# CONTAINER
# ============================================================================


class Container:
    """
    Dependency Injection container with automatic type-based resolution.

    Features:
    - Type-hint based dependency injection
    - Three lifetime scopes: singleton, transient, scoped
    - Circular dependency detection
    - Nested dependency resolution
    - Thread-safe and async-safe

    Example:
        >>> container = Container()
        >>> container.register(Database, scope="singleton")
        >>> container.register(UserRepository)
        >>>
        >>> # UserRepository.__init__ requires Database
        >>> # Container automatically resolves and injects it
        >>> repo = container.resolve(UserRepository)
    """

    def __init__(self) -> None:
        # Registry: Type → Registration metadata
        self._registry: dict[type, Registration] = {}

        # Singleton cache: Type → Instance (lives for app lifetime)
        self._singletons: dict[type, Any] = {}

        # Resolution tracking (prevents infinite recursion)
        self._resolution_stack: set[type] = set()

        # Overrides: Type → Override registration (for testing/runtime config)
        # Priority: override > registration > fallback instantiation
        self._overrides: dict[type, Registration] = {}

        # Instance overrides: Type → Pre-constructed instance
        # Used for mocking with specific instances
        self._instance_overrides: dict[type, Any] = {}

        # Deferred providers: Type → Provider class (for JIT loading)
        # Maps service types to their DeferredServiceProvider classes
        self._deferred_map: dict[type, type] = {}

    def register(
        self,
        interface: type,
        implementation: type | None = None,
        scope: Scope = "transient",
    ) -> None:
        """
        Register a dependency with the container.

        Args:
            interface: The type to register (used as resolution key)
            implementation: Concrete implementation (None = use interface itself)
            scope: Lifetime scope
                - singleton: One instance for entire application
                - transient: New instance on every resolve
                - scoped: One instance per request (requires middleware setup)

        Examples:
            >>> # Self-registration (interface is implementation)
            >>> container.register(UserService)
            >>>
            >>> # Interface → Implementation mapping
            >>> container.register(IDatabase, PostgresDatabase, scope="singleton")
            >>>
            >>> # Scoped for request-level state
            >>> container.register(DatabaseSession, scope="scoped")
        """
        impl = implementation or interface
        self._registry[interface] = Registration(implementation=impl, scope=scope)

    def resolve(self, target: type) -> Any:
        """
        Resolve a dependency, recursively resolving its dependencies.

        Algorithm:
        0. Check instance overrides (highest priority)
        1. Check deferred providers (JIT loading if needed)
        2. Check appropriate cache (singleton or scoped)
        3. Guard against circular dependencies
        4. Find concrete implementation (override > registration > fallback)
        5. Introspect constructor parameters
        6. Recursively resolve each parameter
        7. Instantiate with resolved dependencies
        8. Cache if singleton/scoped

        Args:
            target: Type to resolve

        Returns:
            Fully instantiated object with all dependencies injected

        Raises:
            CircularDependencyError: If circular dependency detected
            DependencyResolutionError: If resolution fails

        Example:
            >>> # Resolving UserService automatically resolves:
            >>> # UserService → UserRepository → Database
            >>> service = container.resolve(UserService)
        """
        # ------------------------------------------------------------------
        # STEP 0: Check Instance Overrides (Highest Priority)
        # ------------------------------------------------------------------
        if target in self._instance_overrides:
            return self._instance_overrides[target]

        # ------------------------------------------------------------------
        # STEP 1: Check Deferred Providers (JIT Loading)
        # ------------------------------------------------------------------
        # Sprint 13: If service is deferred, load provider now
        if target in self._deferred_map:
            self._load_deferred_provider(target)

        # ------------------------------------------------------------------
        # STEP 2: Determine Registration (Override > Registry)
        # ------------------------------------------------------------------
        # Check override first, then fallback to registry
        registration = self._overrides.get(target) or self._registry.get(target)
        scope = registration.scope if registration else "transient"

        # ------------------------------------------------------------------
        # STEP 3: Check Cache (Singleton or Scoped)
        # ------------------------------------------------------------------

        # Singleton: Application-wide cache
        if scope == "singleton" and target in self._singletons:
            return self._singletons[target]

        # Scoped: Request-level cache (via ContextVar)
        if scope == "scoped":
            scoped_cache = get_scoped_cache()
            if target in scoped_cache:
                return scoped_cache[target]

        # ------------------------------------------------------------------
        # STEP 4: Circular Dependency Guard
        # ------------------------------------------------------------------
        if target in self._resolution_stack:
            # Build error message showing dependency chain
            chain = " → ".join(cls.__name__ for cls in self._resolution_stack)
            raise CircularDependencyError(
                f"Circular dependency detected: {chain} → {target.__name__}"
            )

        # Mark as "currently resolving"
        self._resolution_stack.add(target)

        try:
            # ------------------------------------------------------------------
            # STEP 5: Find Implementation
            # ------------------------------------------------------------------
            if registration:
                implementation = registration.implementation
            else:
                # Fallback: Try to instantiate target directly
                implementation = target

            # ------------------------------------------------------------------
            # STEP 6: Instantiate (with or without dependencies)
            # ------------------------------------------------------------------
            instance = self._create_instance(implementation)

            # ------------------------------------------------------------------
            # STEP 7: Cache Appropriately
            # ------------------------------------------------------------------
            if scope == "singleton":
                self._singletons[target] = instance
            elif scope == "scoped":
                scoped_cache = get_scoped_cache()
                scoped_cache[target] = instance
                set_scoped_cache(scoped_cache)

            return instance

        finally:
            # Cleanup: Always remove from stack (even if error)
            # This allows retrying resolution after fixing circular deps
            self._resolution_stack.discard(target)

    def _create_instance(self, implementation: type) -> Any:
        """
        Create instance of implementation, resolving dependencies.

        This is where the magic happens: we use get_type_hints() to
        discover what dependencies the constructor needs, then
        recursively resolve each one.

        Args:
            implementation: Class to instantiate

        Returns:
            Instance with all dependencies injected
        """
        # Get constructor
        # Type ignore: accessing __init__ on type is safe here
        init_method = implementation.__init__  # type: ignore[misc]

        # Edge case: Classes without custom __init__
        if init_method is object.__init__:
            return implementation()

        # ------------------------------------------------------------------
        # Type Introspection (The Core Technique)
        # ------------------------------------------------------------------
        try:
            # get_type_hints resolves string annotations to actual types
            # Example: 'UserRepository' → <class 'UserRepository'>
            type_hints = get_type_hints(init_method)
            signature = inspect.signature(init_method)
        except NameError as e:
            # Forward reference to undefined class
            raise DependencyResolutionError(
                f"Cannot resolve type hints for {implementation.__name__}: {e}\n"
                f"Hint: Ensure all dependencies are imported before registration."
            )

        # ------------------------------------------------------------------
        # Recursive Dependency Resolution
        # ------------------------------------------------------------------
        dependencies = {}

        for param_name, param in signature.parameters.items():
            # Skip special keys
            if param_name in ("self", "return"):
                continue

            if param_name not in type_hints:
                continue

            param_type = type_hints[param_name]
            is_registered = self.is_registered(param_type) or param_type in self._overrides

            if param.default != inspect.Parameter.empty and not is_registered:
                continue

            # Recursively resolve each parameter
            try:
                dependencies[param_name] = self.resolve(param_type)
            except DependencyResolutionError as e:
                # Wrap error with context
                raise DependencyResolutionError(
                    f"Failed to resolve '{param_name}: {param_type.__name__}' "
                    f"for {implementation.__name__}:\n{e}"
                )

        # ------------------------------------------------------------------
        # Instantiation with Kwargs Unpacking
        # ------------------------------------------------------------------
        return implementation(**dependencies)

    def reset_singletons(self) -> None:
        """
        Clear singleton cache (useful for testing).

        Warning: Use with caution in production!
        """
        self._singletons.clear()

    def is_registered(self, target: type) -> bool:
        """
        Check if a type is registered.

        Args:
            target: Type to check

        Returns:
            True if registered, False otherwise
        """
        return target in self._registry

    async def dispose_all(self) -> None:
        """
        Dispose all singleton instances.

        Call this on application shutdown to clean up resources.

        Algorithm:
        1. Iterate all singleton instances
        2. Call cleanup method on each (close/dispose)
        3. Clear singleton cache

        Example:
            # Application shutdown
            async def shutdown():
                await container.dispose_all()

        Note:
            This does NOT dispose scoped instances (use clear_scoped_cache_async).
            This does NOT dispose transient instances (they're not cached).
        """
        # Dispose all singletons
        for instance in self._singletons.values():
            await _dispose_instance(instance)

        # Clear cache
        self._singletons.clear()

    @asynccontextmanager
    async def scoped_context(self):
        """
        Async context manager for scoped lifetime.

        Recommended pattern for FastAPI middleware and request handlers.

        Algorithm:
        1. Initialize scoped cache on entry
        2. Yield control to user code
        3. Dispose all scoped instances on exit
        4. Clear scoped cache

        Example:
            @app.middleware("http")
            async def scoped_lifecycle(request, call_next):
                async with container.scoped_context():
                    response = await call_next(request)
                    return response

            # All scoped resources automatically cleaned up here

        Usage in tests:
            async with container.scoped_context():
                db = container.resolve(Database)  # scoped
                await db.query()
            # db.close() called automatically
        """
        # Initialize scope
        set_scoped_cache({})

        try:
            yield
        finally:
            # Cleanup: dispose all scoped instances
            await clear_scoped_cache_async()

    # ========================================================================
    # OVERRIDE MANAGEMENT
    # ========================================================================

    def override(
        self,
        interface: type,
        implementation: type | None = None,
        scope: Scope = "transient",
    ) -> None:
        """
        Override a dependency registration (for testing/runtime config).

        Overrides have HIGHEST priority in resolution:
            Priority: instance override > override > registration > fallback

        Use cases:
        - Testing: Mock dependencies with test doubles
        - Feature flags: Swap implementations at runtime
        - A/B testing: Use different services per request

        Args:
            interface: The type to override
            implementation: Concrete implementation (None = use interface itself)
            scope: Lifetime scope for the override

        Example:
            # Production registration
            container.register(Database, PostgresDatabase, scope="singleton")

            # Test override
            container.override(Database, FakeDatabase)

            # Resolve uses FakeDatabase
            db = container.resolve(Database)  # Uses FakeDatabase

        Important:
            - Override invalidates existing singleton cache
            - Override does NOT modify original registration
            - Call reset_override() or reset_overrides() to revert
        """
        impl = implementation or interface
        self._overrides[interface] = Registration(implementation=impl, scope=scope)

        # Invalidate cache for immediate effect
        if interface in self._singletons:
            del self._singletons[interface]

    def override_instance(self, interface: type, instance: Any) -> None:
        """
        Override with a pre-constructed instance (for mocking).

        This has HIGHEST priority (even above override()).

        Use cases:
        - Mock objects with specific state
        - Spy objects for verification
        - Test fixtures

        Args:
            interface: The type to override
            instance: Pre-constructed instance to return

        Example:
            # Create mock
            fake_db = FakeDatabase()
            fake_db.setup_test_data([...])

            # Override with instance
            container.override_instance(Database, fake_db)

            # All resolves return this specific instance
            db1 = container.resolve(Database)  # Returns fake_db
            db2 = container.resolve(Database)  # Returns same fake_db
            assert db1 is fake_db
        """
        self._instance_overrides[interface] = instance

        # Invalidate cache
        if interface in self._singletons:
            del self._singletons[interface]

    def reset_override(self, interface: type) -> None:
        """
        Reset a specific override (revert to original registration).

        Args:
            interface: The type to reset

        Example:
            container.override(Database, FakeDatabase)
            db = container.resolve(Database)  # Uses FakeDatabase

            container.reset_override(Database)
            container.reset_singletons()  # Clear cache

            db = container.resolve(Database)  # Uses original registration
        """
        # Remove from both override dicts
        self._overrides.pop(interface, None)
        self._instance_overrides.pop(interface, None)

        # Invalidate cache
        if interface in self._singletons:
            del self._singletons[interface]

    def reset_overrides(self) -> None:
        """
        Reset all overrides (revert to original registrations).

        Example:
            # Test setup
            container.override(Database, FakeDatabase)
            container.override(Cache, FakeCache)

            # Test runs...

            # Test cleanup
            container.reset_overrides()
            container.reset_singletons()

            # All back to original registrations
        """
        self._overrides.clear()
        self._instance_overrides.clear()

        # Invalidate entire singleton cache (safest approach)
        self._singletons.clear()

    # ========================================================================
    # DEFERRED SERVICE PROVIDER SUPPORT (Sprint 13)
    # ========================================================================

    def add_deferred(self, service_type: type, provider_class: type) -> None:
        """
        Register a deferred service provider for JIT loading.

        Deferred providers are not loaded at application startup.
        Instead, they are loaded the first time one of their services
        is requested via resolve().

        Args:
            service_type: The service type this provider provides
            provider_class: The DeferredServiceProvider class

        Example:
            >>> container.add_deferred(QueueService, QueueServiceProvider)
            >>> # QueueServiceProvider is NOT loaded yet
            >>> service = container.resolve(QueueService)  # JIT load now!
        """
        self._deferred_map[service_type] = provider_class

    def _load_deferred_provider(self, service_type: type) -> None:
        """
        Load a deferred service provider on-demand.

        This method is called by resolve() when a deferred service is requested.
        It instantiates the provider, calls register(), and calls boot().

        Algorithm:
        1. Get provider class from deferred_map
        2. Instantiate provider
        3. Call provider.register(self) to bind services
        4. Call provider.boot() to initialize services (async or sync)
        5. Remove ALL services from this provider from deferred_map

        Args:
            service_type: The service type being resolved

        Note:
            For v1.0, boot() is called synchronously. If boot() is async,
            it will be awaited. This works because resolve() is called from
            async route handlers in FastAPI contexts.

            For non-async contexts, async boot() will not be awaited and
            may not complete. This is a known limitation for v1.0.
        """
        # Get provider class from deferred map
        provider_class = self._deferred_map[service_type]

        # Instantiate provider
        provider = provider_class()

        # Call register() to bind services
        provider.register(self)

        # Call boot() to initialize services
        # Note: resolve() is sync, but boot() can be async
        boot_result = provider.boot()
        if hasattr(boot_result, "__await__"):
            # boot() is async - we need to await it
            # This requires an event loop, which should exist in FastAPI contexts
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a task
                # Note: This is fire-and-forget for v1.0
                asyncio.create_task(boot_result)  # type: ignore[arg-type]
            else:
                # If loop is not running, run until complete
                loop.run_until_complete(boot_result)

        # Remove ALL services from this provider from deferred map
        # This handles providers with multiple services in provides list
        services_to_remove = [
            svc for svc, provider_cls in self._deferred_map.items()
            if provider_cls is provider_class
        ]
        for svc in services_to_remove:
            del self._deferred_map[svc]

    @asynccontextmanager
    async def override_context(
        self,
        interface: type,
        implementation: type | None = None,
        scope: Scope = "transient",
    ):
        """
        Temporarily override a dependency (reverts on exit).

        Recommended pattern for test fixtures and temporary configuration.

        Algorithm:
        1. Save current override state
        2. Apply new override
        3. Yield control
        4. Restore original state

        Args:
            interface: The type to override
            implementation: Concrete implementation
            scope: Lifetime scope for override

        Example:
            container.register(Database, RealDatabase, scope="singleton")

            # Temporarily override for test
            async with container.override_context(Database, FakeDatabase):
                db = container.resolve(Database)  # Uses FakeDatabase
                # Test code...

            # Reverted to RealDatabase
            db = container.resolve(Database)  # Uses RealDatabase

        Usage in pytest:
            @pytest.fixture
            async def fake_database(container):
                async with container.override_context(Database, FakeDatabase):
                    yield container.resolve(Database)
                # Automatic cleanup
        """
        # Save current state
        had_override = interface in self._overrides
        had_instance_override = interface in self._instance_overrides
        original_override = self._overrides.get(interface)
        original_instance = self._instance_overrides.get(interface)

        # Apply new override
        self.override(interface, implementation, scope)

        try:
            yield
        finally:
            # Restore original state
            if had_override:
                self._overrides[interface] = original_override  # type: ignore
            else:
                self._overrides.pop(interface, None)

            if had_instance_override:
                self._instance_overrides[interface] = original_instance
            else:
                self._instance_overrides.pop(interface, None)

            # Invalidate cache
            if interface in self._singletons:
                del self._singletons[interface]
