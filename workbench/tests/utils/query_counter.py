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


# ============================================================================
# DECORATOR FOR DX (Sprint 2.7)
# ============================================================================


def assert_query_count(expected_count: int):
    """
    Decorator to assert exact query count for a test function.

    This decorator wraps QueryCounter to reduce boilerplate in test files.
    It automatically counts queries and asserts they match the expected count.

    Args:
        expected_count: Exact number of queries expected

    Usage:
        >>> @assert_query_count(2)
        >>> async def test_eager_loading(engine, session):
        ...     repo = UserRepository(session)
        ...     users = await repo.query().with_("posts").get()
        ...     # Decorator automatically asserts count == 2

    Educational Note:
        This is "Performance as Correctness" DX. Instead of writing:
            async with QueryCounter(engine) as counter:
                users = await repo.query().with_("posts").get()
            assert counter.count == 2

        You write:
            @assert_query_count(2)
            async def test_eager_loading(engine, session):
                users = await repo.query().with_("posts").get()

        Shorter, clearer, and enforces the contract in the decorator.
    """
    import functools
    from typing import Callable

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract engine from test fixtures
            # Convention: engine fixture should be first or named 'engine'
            engine = None

            # Try to find engine in args (positional)
            for arg in args:
                if isinstance(arg, AsyncEngine):
                    engine = arg
                    break

            # Try to find engine in kwargs
            if engine is None and "engine" in kwargs:
                engine = kwargs["engine"]

            if engine is None:
                raise ValueError(
                    "@assert_query_count decorator requires 'engine' fixture. "
                    "Ensure your test has an 'engine' parameter."
                )

            # Run test with query counter
            async with QueryCounter(engine) as counter:
                result = await func(*args, **kwargs)

            # Assert query count matches expected
            assert counter.count == expected_count, (
                f"Query count mismatch! Expected {expected_count} queries, "
                f"got {counter.count}. Queries executed:\n"
                + "\n".join(f"  {i+1}. {q}" for i, q in enumerate(counter.get_queries()))
            )

            return result

        return wrapper

    return decorator


def assert_query_count_range(min_count: int, max_count: int):
    """
    Decorator to assert query count is within a range.

    Useful when exact count is hard to predict but you want to ensure
    it's bounded (e.g., "between 1 and 3 queries, not 50").

    Args:
        min_count: Minimum acceptable query count
        max_count: Maximum acceptable query count

    Usage:
        >>> @assert_query_count_range(1, 3)
        >>> async def test_complex_query(engine, session):
        ...     # Allow some flexibility but prevent N+1
        ...     users = await repo.query().with_("posts", "comments").get()
    """
    import functools
    from typing import Callable

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract engine
            engine = None
            for arg in args:
                if isinstance(arg, AsyncEngine):
                    engine = arg
                    break
            if engine is None and "engine" in kwargs:
                engine = kwargs["engine"]

            if engine is None:
                raise ValueError(
                    "@assert_query_count_range decorator requires 'engine' fixture."
                )

            # Run test with query counter
            async with QueryCounter(engine) as counter:
                result = await func(*args, **kwargs)

            # Assert query count is in range
            assert min_count <= counter.count <= max_count, (
                f"Query count out of range! Expected {min_count}-{max_count} queries, "
                f"got {counter.count}. Queries executed:\n"
                + "\n".join(f"  {i+1}. {q}" for i, q in enumerate(counter.get_queries()))
            )

            return result

        return wrapper

    return decorator
