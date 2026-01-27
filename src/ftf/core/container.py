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

from contextvars import ContextVar
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
    """
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
        1. Check appropriate cache (singleton or scoped)
        2. Guard against circular dependencies
        3. Find concrete implementation
        4. Introspect constructor parameters
        5. Recursively resolve each parameter
        6. Instantiate with resolved dependencies
        7. Cache if singleton/scoped

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
        # STEP 1: Check Cache (Singleton or Scoped)
        # ------------------------------------------------------------------
        registration = self._registry.get(target)
        scope = registration.scope if registration else "transient"

        # Singleton: Application-wide cache
        if scope == "singleton" and target in self._singletons:
            return self._singletons[target]

        # Scoped: Request-level cache (via ContextVar)
        if scope == "scoped":
            scoped_cache = get_scoped_cache()
            if target in scoped_cache:
                return scoped_cache[target]

        # ------------------------------------------------------------------
        # STEP 2: Circular Dependency Guard
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
            # STEP 3: Find Implementation
            # ------------------------------------------------------------------
            if registration:
                implementation = registration.implementation
            else:
                # Fallback: Try to instantiate target directly
                implementation = target

            # ------------------------------------------------------------------
            # STEP 4: Instantiate (with or without dependencies)
            # ------------------------------------------------------------------
            instance = self._create_instance(implementation)

            # ------------------------------------------------------------------
            # STEP 5: Cache Appropriately
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

        for param_name, param_type in type_hints.items():
            # Skip special keys
            if param_name in ("self", "return"):
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
