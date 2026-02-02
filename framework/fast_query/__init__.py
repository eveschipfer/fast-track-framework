"""
Fast Query - Framework-Agnostic ORM Package

A standalone, framework-agnostic database/ORM layer built on SQLAlchemy.
Provides Laravel Eloquent-inspired fluent API with Repository Pattern.

STABILITY LEVEL: STABLE
    This package has a stable API contract. Breaking changes will only occur
    in major version releases (e.g., 1.0 -> 2.0). Minor/patch releases will
    maintain backward compatibility.

    Public API exports (in __all__) are guaranteed stable. Any internal
    implementation details (not in __all__) may change without notice.

FRAMEWORK RELATIONSHIP:
    This is a completely standalone ORM package with ZERO dependencies on
    any web framework (ftf, FastAPI, Flask, Django, etc.).

    The ftf web framework builds on top of fast_query, but fast_query can
    be used independently in any Python application (CLI tools, scripts,
    other web frameworks).

    Integration: ftf provides IoC Container integration for automatic
    dependency injection of repositories and sessions. This is optional -
    fast_query works perfectly with manual session management via get_session().

Key Features:
    - Framework-agnostic (works with FastAPI, Flask, Django, CLI, etc.)
    - Complete database stack (engine, session, repository, query builder)
    - Repository Pattern (NOT Active Record)
    - Fluent Query Builder (Laravel Eloquent-inspired)
    - Mixins for timestamps and soft deletes
    - Smart delete (auto-detects soft vs hard delete)
    - Full async support
    - Type-safe (MyPy strict mode)
    - Zero dependencies on web frameworks

Public API:
    # Database Engine & Session
    - create_engine: Create singleton AsyncEngine
    - get_engine: Get existing AsyncEngine
    - AsyncSessionFactory: Create session factory
    - get_session: Context manager for manual session use

    # Core ORM
    - Base: SQLAlchemy declarative base
    - BaseRepository: Generic CRUD repository
    - QueryBuilder: Fluent query builder

    # Mixins
    - TimestampMixin: Auto-managed created_at/updated_at
    - SoftDeletesMixin: Soft delete with deleted_at

    # Exceptions
    - FastQueryError: Base exception
    - RecordNotFound: Record not found exception

    # Testing & Development (Sprint 2.8)
    - Factory: Base class for model factories
    - Seeder: Base class for database seeders

Example (Complete Workflow):
    from fast_query import (
        create_engine,
        get_session,
        Base,
        BaseRepository,
        TimestampMixin,
        SoftDeletesMixin,
    )
    from sqlalchemy import String
    from sqlalchemy.orm import Mapped, mapped_column

    # 1. Create engine at startup
    engine = create_engine("sqlite+aiosqlite:///./app.db")

    # 2. Define model with mixins
    class User(Base, TimestampMixin, SoftDeletesMixin):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(100))
        email: Mapped[str] = mapped_column(String(100), unique=True)

    # 3. Create repository
    class UserRepository(BaseRepository[User]):
        async def find_by_email(self, email: str) -> User | None:
            return await (
                self.query()
                .where(User.email == email)
                .first()
            )

    # 4. Use repository with session
    async with get_session() as session:
        repo = UserRepository(session)

        # Create user (timestamps auto-set)
        user = User(name="Alice", email="alice@example.com")
        await repo.create(user)

        # Query with fluent builder
        adults = await (
            repo.query()
            .where(User.deleted_at.is_(None))  # Exclude soft-deleted
            .order_by(User.created_at, "desc")
            .limit(50)
            .get()
        )

        # Soft delete (sets deleted_at)
        await repo.delete(user)
        assert user.is_deleted  # True

    # 5. Cleanup on shutdown
    await engine.dispose()

See: https://github.com/yourusername/fast_query for documentation
"""

# Database Engine & Session
from .engine import create_engine, get_engine
from .session import AsyncSessionFactory, get_session

# Core ORM components
from .base import Base
from .repository import BaseRepository
from .query_builder import QueryBuilder

# Mixins
from .mixins import TimestampMixin, SoftDeletesMixin

# Exceptions
from .exceptions import FastQueryError, RecordNotFound

# Testing & Development (Sprint 2.8)
from .factories import Factory
from .seeding import Seeder

# Public API
__all__ = [
    # Engine & Session
    "create_engine",
    "get_engine",
    "AsyncSessionFactory",
    "get_session",
    # Core ORM
    "Base",
    "BaseRepository",
    "QueryBuilder",
    # Mixins
    "TimestampMixin",
    "SoftDeletesMixin",
    # Exceptions
    "FastQueryError",
    "RecordNotFound",
    # Testing & Development
    "Factory",
    "Seeder",
]

# Version
__version__ = "0.1.0"
