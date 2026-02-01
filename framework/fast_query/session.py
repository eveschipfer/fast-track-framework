"""
Database Session Factory

Provides AsyncSession factory for database access with proper lifecycle management.

This module creates session factories that can be used with any dependency injection
framework or manually in scripts, CLI tools, and background jobs.

WHY SESSION FACTORY:
    - Proper transaction management (commit/rollback)
    - Connection pooling via engine
    - Configurable for different use cases
    - Works with or without dependency injection

Example (Manual Use):
    from fast_query import get_session, Base

    class User(Base):
        __tablename__ = "users"
        # ... columns

    async with get_session() as session:
        user = User(name="Alice", email="alice@example.com")
        session.add(user)
        # Auto-commits on success, auto-rolls back on exception

Example (With Dependency Injection):
    from fast_query import AsyncSessionFactory
    from sqlalchemy.ext.asyncio import AsyncSession

    # Create factory
    factory = AsyncSessionFactory()

    # Register with your DI container (e.g., FastAPI, Flask-Injector)
    def session_provider() -> AsyncSession:
        return factory()

    # Use in routes/handlers via injection
    async def get_users(session: AsyncSession):
        result = await session.execute(select(User))
        return result.scalars().all()
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .engine import get_engine


def AsyncSessionFactory() -> async_sessionmaker[AsyncSession]:
    """
    Create session factory from engine.

    This factory creates new AsyncSession instances with proper configuration
    for async applications. Sessions should be managed either by a dependency
    injection container or manually using context managers.

    Returns:
        async_sessionmaker: Factory that creates AsyncSession instances

    Configuration:
        - expire_on_commit=False: Keep objects accessible after commit
        - autoflush=False: Manual control over flush operations
        - autocommit=False: Explicit transaction control (manual commit/rollback)

    Example:
        >>> from fast_query import AsyncSessionFactory
        >>> factory = AsyncSessionFactory()
        >>> async with factory() as session:
        ...     user = User(name="Alice")
        ...     session.add(user)
        ...     await session.commit()
    """
    engine = get_engine()

    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Important: Keep objects accessible after commit
        autoflush=False,  # Manual control over flush
        autocommit=False,  # Manual control over commit/rollback
    )


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for session (for manual use outside of dependency injection).

    This is useful for scripts, CLI commands, background jobs, or any code
    outside of a web request lifecycle where you need manual session management.

    Yields:
        AsyncSession: Database session with automatic commit/rollback

    Example:
        >>> from fast_query import get_session, Base
        >>>
        >>> async with get_session() as session:
        ...     user = User(name="Alice", email="alice@example.com")
        ...     session.add(user)
        ...     # Auto-commits on success
        ...
        >>> # If exception occurs, auto-rollback happens

    Note:
        For web frameworks with dependency injection (FastAPI, Flask, etc.),
        use AsyncSessionFactory() and register it with your DI container instead.
        The container will manage session lifecycle automatically.
    """
    factory = AsyncSessionFactory()

    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
