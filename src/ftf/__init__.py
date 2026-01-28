"""
Fast Track Framework (FTF)

A Laravel-inspired micro-framework built on top of FastAPI, designed
as an educational deep-dive into modern Python architecture patterns.

Features:
- Type-safe dependency injection container
- Async-first architecture
- Laravel-inspired developer experience
- Strict type safety with MyPy

Main Components:
    core: IoC container and dependency injection
    database: SQLAlchemy async integration with Repository Pattern
    models: Database models (User, etc.)
    http: FastAPI extensions (coming soon)
    cli: Artisan-like CLI tools (coming soon)

Quick Start:
    >>> from ftf import Container
    >>> container = Container()
    >>> container.register(Database, scope="singleton")
    >>> db = container.resolve(Database)
"""

from .core import (
    CircularDependencyError,
    Container,
    DependencyResolutionError,
    Registration,
    Scope,
    UnregisteredDependencyError,
    clear_scoped_cache,
    clear_scoped_cache_async,
    get_scoped_cache,
    set_scoped_cache,
)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Core - Container
    "Container",
    "Registration",
    "Scope",
    # Core - Scoped cache
    "get_scoped_cache",
    "set_scoped_cache",
    "clear_scoped_cache",
    "clear_scoped_cache_async",
    # Core - Exceptions
    "DependencyResolutionError",
    "CircularDependencyError",
    "UnregisteredDependencyError",
    # Note: database and models modules are available but not exported here
    # Import directly: from ftf.database import Base, BaseRepository
    # Import directly: from ftf.models import User
]
