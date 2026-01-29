"""
Query Counter Utility

Counts exact number of SQL queries executed using SQLAlchemy event listeners.

This is CRITICAL for validating N+1 prevention. We need to prove that:
- Without eager loading: 1 query for posts + N queries for authors (N+1 problem)
- With eager loading: EXACTLY 2 queries (1 for posts + 1 for all authors)

Usage:
    from tests.utils.query_counter import QueryCounter

    async with QueryCounter(engine) as counter:
        posts = await repo.query().with_(Post.author).get()

    assert counter.count == 2  # EXACTLY 2 queries, not 51!

Educational Note:
    This utility is inspired by Django Debug Toolbar's query counter.
    We use SQLAlchemy's event system to intercept EVERY query before
    it hits the database cursor, giving us precise query counts.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine


class QueryCounter:
    """
    Context manager that counts SQL queries executed.

    Attaches to SQLAlchemy engine's before_cursor_execute event
    to count every query sent to the database.

    Attributes:
        count: Number of SQL queries executed
        queries: List of SQL query strings (for debugging)
        engine: AsyncEngine to monitor

    Example:
        >>> async with QueryCounter(engine) as counter:
        ...     users = await session.execute(select(User))
        >>> print(f"Executed {counter.count} queries")
        >>> print(counter.queries)  # See actual SQL

    Educational Note:
        This is how we PROVE N+1 prevention works. Without this,
        we'd just be hoping our eager loading is correct.
    """

    def __init__(self, engine: AsyncEngine):
        """
        Initialize query counter.

        Args:
            engine: AsyncEngine to monitor for queries
        """
        self.engine = engine
        self.count = 0
        self.queries: list[str] = []
        self._listener_registered = False

    def _before_cursor_execute(
        self,
        conn: Connection,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        """
        Event listener called before each SQL query.

        This is the magic that lets us count queries. SQLAlchemy
        calls this function BEFORE sending query to database.

        Args:
            conn: Database connection
            cursor: Database cursor
            statement: SQL query string
            parameters: Query parameters (bound values)
            context: SQLAlchemy execution context
            executemany: Whether this is an executemany call
        """
        self.count += 1
        # Store query for debugging (strip whitespace for readability)
        clean_query = " ".join(statement.split())
        self.queries.append(clean_query)

    async def __aenter__(self) -> "QueryCounter":
        """
        Enter context manager - start counting queries.

        Registers event listener on the sync engine (wrapped by AsyncEngine).

        Returns:
            QueryCounter: Self for use in 'as' clause
        """
        # Reset counter
        self.count = 0
        self.queries = []

        # Register event listener on SYNC engine (AsyncEngine wraps it)
        # We use sync_engine because before_cursor_execute is a sync event
        sync_engine = self.engine.sync_engine
        event.listen(
            sync_engine, "before_cursor_execute", self._before_cursor_execute
        )
        self._listener_registered = True

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit context manager - stop counting queries.

        Removes event listener to avoid counting queries outside context.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        if self._listener_registered:
            sync_engine = self.engine.sync_engine
            event.remove(
                sync_engine, "before_cursor_execute", self._before_cursor_execute
            )
            self._listener_registered = False

    def reset(self) -> None:
        """
        Reset counter to zero.

        Useful for testing multiple scenarios in same context.

        Example:
            >>> async with QueryCounter(engine) as counter:
            ...     # First query
            ...     await session.execute(select(User))
            ...     assert counter.count == 1
            ...
            ...     counter.reset()
            ...
            ...     # Second query
            ...     await session.execute(select(Post))
            ...     assert counter.count == 1  # Reset to 0, now 1 again
        """
        self.count = 0
        self.queries = []

    def get_queries(self) -> list[str]:
        """
        Get list of executed SQL queries.

        Returns:
            list[str]: SQL query strings

        Example:
            >>> async with QueryCounter(engine) as counter:
            ...     await repo.query().with_(Post.author).get()
            >>> for query in counter.get_queries():
            ...     print(query)
            SELECT posts.id, posts.title FROM posts
            SELECT users.id, users.name FROM users WHERE users.id IN (?, ?, ?)
        """
        return self.queries.copy()


@asynccontextmanager
async def count_queries(engine: AsyncEngine) -> AsyncGenerator[QueryCounter, None]:
    """
    Async context manager factory for QueryCounter.

    Convenience function for cleaner syntax.

    Args:
        engine: AsyncEngine to monitor

    Yields:
        QueryCounter: Query counter instance

    Example:
        >>> async with count_queries(engine) as counter:
        ...     posts = await repo.query().with_(Post.author).get()
        >>> assert counter.count == 2
    """
    counter = QueryCounter(engine)
    async with counter:
        yield counter
