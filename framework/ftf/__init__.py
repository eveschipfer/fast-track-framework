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
    models: Database models (User, etc.)
    http: FastAPI extensions
    cli: Artisan-like CLI tools (coming soon)

Database Layer:
    Fast Track Framework uses the standalone fast_query package for all
    database operations. Import from fast_query for ORM functionality:
        from fast_query import (
            create_engine, get_session,
            Base, BaseRepository, QueryBuilder,
            TimestampMixin, SoftDeletesMixin
        )

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
    # Note: Database ORM functionality is provided by the standalone fast_query package
    # Import directly: from fast_query import Base, BaseRepository, create_engine, etc.
    # Import directly: from ftf.models import User (FTF-specific models)
]
