"""
Database Session Factory

Provides scoped AsyncSession for per-request database access.

This module creates session factories that should be registered in the
IoC container with scope="scoped" to ensure one session per HTTP request.

WHY SCOPED:
    - One session per HTTP request
    - Automatic cleanup when request ends
    - Isolated transactions between requests
    - Works with container.scoped_context() middleware

Example:
    from ftf.database import AsyncSessionFactory
    from ftf.http import FastTrackFramework
    from sqlalchemy.ext.asyncio import AsyncSession

    app = FastTrackFramework()

    # Register session factory (scoped)
    def session_factory() -> AsyncSession:
        factory = AsyncSessionFactory()
        return factory()

    app.register(
        AsyncSession,
        implementation=session_factory,
        scope="scoped"
    )

    # Use in routes via dependency injection
    @app.get("/users")
    async def get_users(session: AsyncSession = Inject(AsyncSession)):
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
    for FastAPI usage. Sessions should be managed by the IoC container with
    scoped lifetime.

    Returns:
        async_sessionmaker: Factory that creates AsyncSession instances

    Configuration:
        - expire_on_commit=False: Keep objects accessible after commit (FastAPI pattern)
        - autoflush=False: Manual control over flush operations
        - autocommit=False: Explicit transaction control (manual commit/rollback)

    Example:
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
    Context manager for session (for manual use outside of DI).

    This is useful for scripts, CLI commands, or background jobs where
    you need manual session management outside of the HTTP request lifecycle.

    Yields:
        AsyncSession: Database session with automatic commit/rollback

    Example:
        >>> from ftf.database import get_session
        >>>
        >>> async with get_session() as session:
        ...     user = User(name="Alice", email="alice@example.com")
        ...     session.add(user)
        ...     await session.commit()  # Auto-committed on success
        ...
        >>> # If exception occurs, auto-rollback happens

    Note:
        For HTTP routes, use Inject(AsyncSession) instead - the container
        manages session lifecycle automatically via middleware.
    """
    factory = AsyncSessionFactory()

    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
