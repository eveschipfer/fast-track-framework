"""
Fast Track Framework - Core Module

This module provides the core dependency injection container
and related utilities.

Public API:
    Container: Main IoC container for dependency injection
    Registration: Dependency registration metadata
    Scope: Type alias for lifetime scopes
    get_scoped_cache: Get current request's scoped cache
    set_scoped_cache: Set scoped cache for current request
    clear_scoped_cache: Clear scoped cache (end of request)
    clear_scoped_cache_async: Clear scoped cache with async cleanup

Exceptions:
    DependencyResolutionError: Base exception for DI errors
    CircularDependencyError: Circular dependency detected
    UnregisteredDependencyError: Unregistered dependency requested
"""

from .container import (
    Container,
    Registration,
    Scope,
    clear_scoped_cache,
    clear_scoped_cache_async,
    get_scoped_cache,
    set_scoped_cache,
)
from .exceptions import (
    CircularDependencyError,
    DependencyResolutionError,
    UnregisteredDependencyError,
)

__all__ = [
    # Container
    "Container",
    "Registration",
    "Scope",
    # Scoped cache management
    "get_scoped_cache",
    "set_scoped_cache",
    "clear_scoped_cache",
    "clear_scoped_cache_async",
    # Exceptions
    "DependencyResolutionError",
    "CircularDependencyError",
    "UnregisteredDependencyError",
]
