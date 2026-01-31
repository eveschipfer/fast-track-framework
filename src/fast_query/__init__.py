"""
Fast Query - Framework-Agnostic ORM Package

A standalone, framework-agnostic database/ORM layer built on SQLAlchemy.
Provides Laravel Eloquent-inspired fluent API with Repository Pattern.

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
