"""
Database Engine Configuration

Provides singleton AsyncEngine for connection pooling.

This module manages the global database engine instance which should be
created once at application startup and shared across all database operations.

WHY SINGLETON:
    - Connection pools are expensive to create
    - Should be shared across all requests/operations
    - Lives for entire application lifetime
    - Properly disposed on shutdown

Example:
    from fast_query import create_engine
    from sqlalchemy.ext.asyncio import AsyncEngine

    # Create engine at application startup
    engine = create_engine("postgresql+asyncpg://user:pass@localhost/db")

    # Register with your dependency injection container (if using one)
    container.register_instance(AsyncEngine, engine)

    # Or use directly
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT 1"))

    # Cleanup on shutdown
    await engine.dispose()
"""

from typing import Optional

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# Global singleton instance
_engine: Optional[AsyncEngine] = None


def create_engine(
    database_url: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
) -> AsyncEngine:
    """
    Create SQLAlchemy AsyncEngine (singleton pattern).

    This should be called once at application startup. The engine manages
    a connection pool and should be disposed on application shutdown.

    Args:
        database_url: Database connection URL
            Examples:
                - SQLite: "sqlite+aiosqlite:///./test.db"
                - PostgreSQL: "postgresql+asyncpg://user:pass@localhost/db"
                - MySQL: "mysql+aiomysql://user:pass@localhost/db"
        echo: Enable SQL query logging (default: False)
        pool_size: Number of connections to maintain (default: 5, ignored for SQLite)
        max_overflow: Max connections beyond pool_size (default: 10, ignored for SQLite)

    Returns:
        AsyncEngine: Configured database engine

    Example:
        >>> from fast_query import create_engine
        >>> engine = create_engine("sqlite+aiosqlite:///./app.db")
        >>> # Use engine for session creation
        >>> from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        >>> SessionFactory = async_sessionmaker(engine, class_=AsyncSession)
    """
    global _engine

    if _engine is None:
        # SQLite uses StaticPool and doesn't accept pool_size/max_overflow
        is_sqlite = database_url.startswith("sqlite")
        is_memory = ":memory:" in database_url

        if is_sqlite:
            # SQLite needs special configuration
            if is_memory:
                # In-memory SQLite: Use StaticPool to keep connection alive
                _engine = create_async_engine(
                    database_url,
                    echo=echo,
                    poolclass=pool.StaticPool,  # Keep single connection alive
                    connect_args={"check_same_thread": False},  # Allow multiple threads
                )
            else:
                # File-based SQLite: Use NullPool (no pooling)
                _engine = create_async_engine(
                    database_url,
                    echo=echo,
                    # NullPool is default for SQLite
                )
        else:
            # PostgreSQL, MySQL, etc: Use connection pooling
            _engine = create_async_engine(
                database_url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,  # Verify connections before use
            )

    return _engine


def get_engine() -> AsyncEngine:
    """
    Get existing engine or raise error.

    Returns:
        AsyncEngine: The singleton engine instance

    Raises:
        RuntimeError: If engine has not been initialized

    Example:
        >>> from fast_query import get_engine
        >>> engine = get_engine()
        >>> async with engine.begin() as conn:
        ...     await conn.execute(text("SELECT 1"))
    """
    if _engine is None:
        msg = (
            "Database engine not initialized. "
            "Call create_engine() first during application startup."
        )
        raise RuntimeError(msg)

    return _engine
