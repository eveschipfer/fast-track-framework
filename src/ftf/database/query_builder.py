"""
Fluent Query Builder

Laravel Eloquent-inspired query builder with type safety and async support.

This implements a fluent interface for building SQLAlchemy queries with:
    - Method chaining (returns Self for type safety)
    - Lazy execution (builds query, executes on terminal methods)
    - Explicit session dependency (no ContextVar magic)
    - Full MyPy support with Generic[T]

WHY QUERY BUILDER:
    - Laravel-like DX: Familiar fluent API for Laravel developers
    - Type Safe: Generic[T] preserves model type through chain
    - Lazy Execution: Build query step-by-step, execute once
    - Explicit: Session passed in constructor (testable, no globals)
    - Async First: All terminal methods are async

Example:
    from ftf.database import BaseRepository, QueryBuilder
    from ftf.models import User

    class UserRepository(BaseRepository[User]):
        async def find_active_adults(self) -> list[User]:
            return await (
                self.query()
                .where(User.age >= 18)
                .where(User.status == "active")
                .order_by(User.created_at, "desc")
                .limit(50)
                .get()
            )

COMPARISON TO ELOQUENT:
    Laravel (Active Record):
        $users = User::where('age', '>=', 18)
                    ->where('status', 'active')
                    ->orderBy('created_at', 'desc')
                    ->limit(50)
                    ->get();

    FastTrack (Repository + Query Builder):
        users = await (
            repo.query()
            .where(User.age >= 18)
            .where(User.status == "active")
            .order_by(User.created_at, "desc")
            .limit(50)
            .get()
        )

    Trade-off: Slightly more verbose (async, repo), but explicit and type-safe.

LAZY EXECUTION:
    query = repo.query().where(User.age >= 18)  # No SQL executed yet
    users = await query.get()                    # NOW executes SELECT

TERMINAL METHODS (execute query):
    - get() -> list[T]
    - first() -> T | None
    - first_or_fail() -> T
    - count() -> int
    - exists() -> bool
    - pluck(column) -> list[Any]

BUILDER METHODS (return Self for chaining):
    - where(), or_where(), where_in(), etc.
    - order_by(), latest(), oldest()
    - limit(), offset(), paginate()
    - with_(), with_joined() (eager loading)
"""

from typing import Any, Generic, Literal, TypeVar

from sqlalchemy import Select, and_, between, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, joinedload, selectinload
from sqlalchemy.sql import ColumnElement

from .base import Base

T = TypeVar("T", bound=Base)


class QueryBuilder(Generic[T]):
    """
    Fluent query builder for SQLAlchemy models.

    Provides Laravel Eloquent-inspired API for building database queries
    with method chaining and lazy execution.

    Type Parameters:
        T: Model type (must inherit from Base)

    Usage:
        >>> # Create via repository
        >>> query = repo.query()
        >>>
        >>> # Build query with method chaining
        >>> query = (
        ...     query
        ...     .where(User.age >= 18)
        ...     .where(User.status == "active")
        ...     .order_by(User.created_at, "desc")
        ...     .limit(10)
        ... )
        >>>
        >>> # Execute with terminal method
        >>> users = await query.get()
        >>>
        >>> # Or chain everything
        >>> users = await (
        ...     repo.query()
        ...     .where(User.age >= 18)
        ...     .latest()
        ...     .get()
        ... )

    See: docs/query-builder.md for complete API reference
    """

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        """
        Initialize query builder.

        Args:
            session: AsyncSession for executing queries
            model: Model class (e.g., User, Post)

        Note:
            Typically created via BaseRepository.query() rather than directly.

        Example:
            >>> # Via repository (recommended)
            >>> query = user_repo.query()
            >>>
            >>> # Direct instantiation (advanced)
            >>> query = QueryBuilder(session, User)
        """
        self.session = session
        self.model = model
        self._stmt: Select[tuple[T]] = select(model)
        self._eager_loads: list[Any] = []

    # ===========================
    # FILTERING METHODS
    # ===========================

    def where(self, *conditions: ColumnElement[bool]) -> "QueryBuilder[T]":
        """
        Add WHERE clause with AND logic.

        Multiple conditions are combined with AND. Can be called multiple
        times to add more conditions.

        Args:
            *conditions: SQLAlchemy filter expressions

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Single condition
            >>> query = repo.query().where(User.age >= 18)
            >>>
            >>> # Multiple conditions (AND)
            >>> query = repo.query().where(
            ...     User.age >= 18,
            ...     User.status == "active"
            ... )
            >>>
            >>> # Chained calls (also AND)
            >>> query = (
            ...     repo.query()
            ...     .where(User.age >= 18)
            ...     .where(User.status == "active")
            ... )
            >>>
            >>> # Complex conditions
            >>> query = repo.query().where(
            ...     (User.age >= 18) & (User.age <= 65)
            ... )
        """
        if conditions:
            self._stmt = self._stmt.where(and_(*conditions))
        return self

    def or_where(self, *conditions: ColumnElement[bool]) -> "QueryBuilder[T]":
        """
        Add WHERE clause with OR logic.

        Combines conditions with OR. Use in conjunction with where() for
        complex AND/OR logic.

        Args:
            *conditions: SQLAlchemy filter expressions

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Simple OR
            >>> query = repo.query().or_where(
            ...     User.email == "alice@test.com",
            ...     User.email == "bob@test.com"
            ... )
            >>>
            >>> # Combining AND with OR
            >>> query = (
            ...     repo.query()
            ...     .where(User.status == "active")
            ...     .or_where(
            ...         User.role == "admin",
            ...         User.role == "moderator"
            ...     )
            ... )
            >>> # SQL: WHERE status = 'active' AND (role = 'admin' OR role = 'moderator')
        """
        if conditions:
            # Get existing WHERE clause if any
            if self._stmt.whereclause is not None:
                # Combine existing conditions with OR conditions
                self._stmt = self._stmt.where(or_(*conditions))
            else:
                # No existing WHERE, just add OR conditions
                self._stmt = self._stmt.where(or_(*conditions))
        return self

    def where_in(
        self, column: InstrumentedAttribute[Any], values: list[Any]
    ) -> "QueryBuilder[T]":
        """
        Add WHERE IN clause.

        Args:
            column: Model column attribute (e.g., User.id)
            values: List of values to match

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Find users by IDs
            >>> query = repo.query().where_in(User.id, [1, 2, 3, 4, 5])
            >>>
            >>> # Find users by status
            >>> query = repo.query().where_in(
            ...     User.status,
            ...     ["active", "pending"]
            ... )
        """
        if values:
            self._stmt = self._stmt.where(column.in_(values))
        return self

    def where_not_in(
        self, column: InstrumentedAttribute[Any], values: list[Any]
    ) -> "QueryBuilder[T]":
        """
        Add WHERE NOT IN clause.

        Args:
            column: Model column attribute
            values: List of values to exclude

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Exclude specific users
            >>> query = repo.query().where_not_in(User.id, [1, 2, 3])
            >>>
            >>> # Exclude statuses
            >>> query = repo.query().where_not_in(
            ...     User.status,
            ...     ["banned", "deleted"]
            ... )
        """
        if values:
            self._stmt = self._stmt.where(not_(column.in_(values)))
        return self

    def where_null(self, column: InstrumentedAttribute[Any]) -> "QueryBuilder[T]":
        """
        Add WHERE IS NULL clause.

        Args:
            column: Model column attribute

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Find users without email verification
            >>> query = repo.query().where_null(User.email_verified_at)
            >>>
            >>> # Find posts without published date
            >>> query = repo.query().where_null(Post.published_at)
        """
        self._stmt = self._stmt.where(column.is_(None))
        return self

    def where_not_null(self, column: InstrumentedAttribute[Any]) -> "QueryBuilder[T]":
        """
        Add WHERE IS NOT NULL clause.

        Args:
            column: Model column attribute

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Find verified users
            >>> query = repo.query().where_not_null(User.email_verified_at)
            >>>
            >>> # Find published posts
            >>> query = repo.query().where_not_null(Post.published_at)
        """
        self._stmt = self._stmt.where(column.isnot(None))
        return self

    def where_like(
        self, column: InstrumentedAttribute[Any], pattern: str
    ) -> "QueryBuilder[T]":
        """
        Add WHERE LIKE clause for pattern matching.

        Args:
            column: Model column attribute (typically string column)
            pattern: SQL LIKE pattern (% for wildcard)

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Find users with name containing "alice"
            >>> query = repo.query().where_like(User.name, "%alice%")
            >>>
            >>> # Find users with email ending in "@gmail.com"
            >>> query = repo.query().where_like(User.email, "%@gmail.com")
            >>>
            >>> # Case-insensitive search (use ilike for PostgreSQL)
            >>> query = repo.query().where(User.name.ilike("%alice%"))
        """
        self._stmt = self._stmt.where(column.like(pattern))
        return self

    def where_between(
        self,
        column: InstrumentedAttribute[Any],
        start: Any,
        end: Any,
    ) -> "QueryBuilder[T]":
        """
        Add WHERE BETWEEN clause.

        Args:
            column: Model column attribute
            start: Lower bound (inclusive)
            end: Upper bound (inclusive)

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Find users aged 18-65
            >>> query = repo.query().where_between(User.age, 18, 65)
            >>>
            >>> # Find posts created in date range
            >>> from datetime import datetime, timedelta
            >>> start = datetime.utcnow() - timedelta(days=7)
            >>> end = datetime.utcnow()
            >>> query = repo.query().where_between(
            ...     Post.created_at, start, end
            ... )
        """
        self._stmt = self._stmt.where(between(column, start, end))
        return self

    # ===========================
    # ORDERING METHODS
    # ===========================

    def order_by(
        self,
        column: InstrumentedAttribute[Any],
        direction: Literal["asc", "desc"] = "asc",
    ) -> "QueryBuilder[T]":
        """
        Add ORDER BY clause.

        Args:
            column: Model column attribute to sort by
            direction: Sort direction ("asc" or "desc", default: "asc")

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Ascending order (default)
            >>> query = repo.query().order_by(User.name)
            >>>
            >>> # Descending order
            >>> query = repo.query().order_by(User.created_at, "desc")
            >>>
            >>> # Multiple ORDER BY clauses
            >>> query = (
            ...     repo.query()
            ...     .order_by(User.status, "asc")
            ...     .order_by(User.created_at, "desc")
            ... )
        """
        if direction == "desc":
            self._stmt = self._stmt.order_by(column.desc())
        else:
            self._stmt = self._stmt.order_by(column.asc())
        return self

    def latest(
        self, column: InstrumentedAttribute[Any] | None = None
    ) -> "QueryBuilder[T]":
        """
        Order by column descending (newest first).

        Convenience method for order_by(column, "desc"). Defaults to
        created_at column if available.

        Args:
            column: Column to sort by (default: created_at if exists)

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Latest posts (by created_at)
            >>> query = repo.query().latest()
            >>>
            >>> # Latest posts (by custom column)
            >>> query = repo.query().latest(Post.published_at)
        """
        if column is None:
            # Try to use created_at column
            if hasattr(self.model, "created_at"):
                column = self.model.created_at
            else:
                # Fallback to primary key
                column = self.model.id

        return self.order_by(column, "desc")

    def oldest(
        self, column: InstrumentedAttribute[Any] | None = None
    ) -> "QueryBuilder[T]":
        """
        Order by column ascending (oldest first).

        Convenience method for order_by(column, "asc"). Defaults to
        created_at column if available.

        Args:
            column: Column to sort by (default: created_at if exists)

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Oldest posts (by created_at)
            >>> query = repo.query().oldest()
            >>>
            >>> # Oldest posts (by custom column)
            >>> query = repo.query().oldest(Post.published_at)
        """
        if column is None:
            # Try to use created_at column
            if hasattr(self.model, "created_at"):
                column = self.model.created_at
            else:
                # Fallback to primary key
                column = self.model.id

        return self.order_by(column, "asc")

    # ===========================
    # PAGINATION METHODS
    # ===========================

    def limit(self, count: int) -> "QueryBuilder[T]":
        """
        Add LIMIT clause.

        Args:
            count: Maximum number of records to return

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Get first 10 users
            >>> query = repo.query().limit(10)
            >>>
            >>> # Get top 5 active users
            >>> query = (
            ...     repo.query()
            ...     .where(User.status == "active")
            ...     .order_by(User.created_at, "desc")
            ...     .limit(5)
            ... )
        """
        self._stmt = self._stmt.limit(count)
        return self

    def offset(self, count: int) -> "QueryBuilder[T]":
        """
        Add OFFSET clause.

        Args:
            count: Number of records to skip

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Skip first 10 users
            >>> query = repo.query().offset(10)
            >>>
            >>> # Pagination: page 2 (skip 10, take 10)
            >>> query = repo.query().offset(10).limit(10)
        """
        self._stmt = self._stmt.offset(count)
        return self

    def paginate(self, page: int = 1, per_page: int = 20) -> "QueryBuilder[T]":
        """
        Paginate results.

        Convenience method that sets both LIMIT and OFFSET based on page
        number and items per page.

        Args:
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 20)

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # First page (items 1-20)
            >>> query = repo.query().paginate(page=1, per_page=20)
            >>>
            >>> # Second page (items 21-40)
            >>> query = repo.query().paginate(page=2, per_page=20)
            >>>
            >>> # With filtering
            >>> query = (
            ...     repo.query()
            ...     .where(User.status == "active")
            ...     .paginate(page=page, per_page=50)
            ... )
        """
        offset_count = (page - 1) * per_page
        return self.offset(offset_count).limit(per_page)

    # ===========================
    # RELATIONSHIP LOADING
    # ===========================

    def with_(self, *relationships: InstrumentedAttribute[Any]) -> "QueryBuilder[T]":
        """
        Eager load relationships using selectinload (N+1 prevention).

        Uses SQLAlchemy's selectinload strategy, which issues a separate
        SELECT for each relationship. More efficient for one-to-many
        relationships than joinedload.

        Args:
            *relationships: Relationship attributes to eager load

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Load posts with authors (prevents N+1)
            >>> posts = await (
            ...     post_repo.query()
            ...     .with_(Post.author)
            ...     .get()
            ... )
            >>>
            >>> # Access author without additional query
            >>> for post in posts:
            ...     print(post.author.name)  # Already loaded!
            >>>
            >>> # Multiple relationships
            >>> posts = await (
            ...     post_repo.query()
            ...     .with_(Post.author, Post.comments)
            ...     .get()
            ... )

        See: docs/relationships.md for N+1 prevention guide
        """
        for rel in relationships:
            self._eager_loads.append(selectinload(rel))
        return self

    def with_joined(
        self, *relationships: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[T]":
        """
        Eager load relationships using joinedload (single query).

        Uses SQLAlchemy's joinedload strategy, which uses JOINs to fetch
        relationships in a single query. Can be more efficient for
        many-to-one relationships, but may be slower for one-to-many.

        Args:
            *relationships: Relationship attributes to eager load

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Load posts with authors using JOIN
            >>> posts = await (
            ...     post_repo.query()
            ...     .with_joined(Post.author)
            ...     .get()
            ... )
            >>>
            >>> # Multiple relationships
            >>> users = await (
            ...     user_repo.query()
            ...     .with_joined(User.posts, User.roles)
            ...     .get()
            ... )

        Note:
            For one-to-many relationships, with_() (selectinload) is
            typically more efficient. Use with_joined() for many-to-one
            or when you need a single query.

        See: docs/relationships.md for loading strategy comparison
        """
        for rel in relationships:
            self._eager_loads.append(joinedload(rel))
        return self

    # ===========================
    # TERMINAL METHODS (Execute Query)
    # ===========================

    async def get(self) -> list[T]:
        """
        Execute query and return all results.

        Terminal method that executes the query and returns all matching
        records as a list.

        Returns:
            list[T]: List of model instances (may be empty)

        Example:
            >>> # Get all active users
            >>> users = await (
            ...     repo.query()
            ...     .where(User.status == "active")
            ...     .get()
            ... )
            >>>
            >>> # Get all (use with caution on large tables)
            >>> all_users = await repo.query().get()
        """
        # Apply eager loading
        stmt = self._stmt
        for load_option in self._eager_loads:
            stmt = stmt.options(load_option)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def first(self) -> T | None:
        """
        Execute query and return first result or None.

        Terminal method that executes the query and returns the first
        matching record, or None if no records found.

        Returns:
            Optional[T]: First model instance or None

        Example:
            >>> # Get first active user
            >>> user = await (
            ...     repo.query()
            ...     .where(User.status == "active")
            ...     .first()
            ... )
            >>>
            >>> if user:
            ...     print(user.name)
            ... else:
            ...     print("No active users found")
        """
        stmt = self._stmt.limit(1)

        # Apply eager loading
        for load_option in self._eager_loads:
            stmt = stmt.options(load_option)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def first_or_fail(self) -> T:
        """
        Execute query and return first result or raise 404.

        Terminal method that executes the query and returns the first
        matching record. Raises HTTPException with 404 status if no
        record found.

        Returns:
            T: First model instance (guaranteed to exist)

        Raises:
            HTTPException: 404 if no record found

        Example:
            >>> # Get first active user or fail
            >>> user = await (
            ...     repo.query()
            ...     .where(User.status == "active")
            ...     .first_or_fail()
            ... )
            >>> # No None check needed - either returns user or raises 404
            >>> print(user.name)
        """
        result = await self.first()

        if result is None:
            # Import here to avoid circular dependency
            from fastapi import HTTPException

            msg = f"{self.model.__name__} not found"
            raise HTTPException(status_code=404, detail=msg)

        return result

    async def count(self) -> int:
        """
        Execute query and return count of matching records.

        Terminal method that executes a COUNT query and returns the
        number of matching records.

        Returns:
            int: Number of matching records

        Example:
            >>> # Count active users
            >>> total = await (
            ...     repo.query()
            ...     .where(User.status == "active")
            ...     .count()
            ... )
            >>> print(f"Found {total} active users")
            >>>
            >>> # Count all
            >>> total_users = await repo.query().count()
        """
        # Build COUNT query from current statement
        subquery = self._stmt.subquery()
        count_stmt = select(func.count()).select_from(subquery)

        result = await self.session.execute(count_stmt)
        count = result.scalar_one()
        return int(count)

    async def exists(self) -> bool:
        """
        Check if any records match the query.

        Terminal method that checks if at least one record matches the
        query without fetching all results.

        Returns:
            bool: True if at least one record exists, False otherwise

        Example:
            >>> # Check if active users exist
            >>> has_active = await (
            ...     repo.query()
            ...     .where(User.status == "active")
            ...     .exists()
            ... )
            >>>
            >>> if has_active:
            ...     print("Active users found")
        """
        count = await self.count()
        return count > 0

    async def pluck(self, column: InstrumentedAttribute[Any]) -> list[Any]:
        """
        Execute query and extract values from a single column.

        Terminal method that executes the query and returns a list of
        values from the specified column only.

        Args:
            column: Column attribute to extract values from

        Returns:
            list[Any]: List of column values (may be empty)

        Example:
            >>> # Get all user emails
            >>> emails = await repo.query().pluck(User.email)
            >>> # ['alice@test.com', 'bob@test.com', ...]
            >>>
            >>> # Get IDs of active users
            >>> active_ids = await (
            ...     repo.query()
            ...     .where(User.status == "active")
            ...     .pluck(User.id)
            ... )
            >>> # [1, 3, 5, 7, ...]
        """
        stmt = select(column)
        # Copy WHERE clause from main statement
        if self._stmt.whereclause is not None:
            stmt = stmt.where(self._stmt.whereclause)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ===========================
    # DEBUG METHODS
    # ===========================

    def to_sql(self) -> str:
        """
        Get compiled SQL query string (for debugging).

        Returns the SQL string that would be executed by this query.
        Useful for debugging and understanding what SQLAlchemy generates.

        Returns:
            str: Compiled SQL query string

        Example:
            >>> query = (
            ...     repo.query()
            ...     .where(User.age >= 18)
            ...     .order_by(User.name)
            ...     .limit(10)
            ... )
            >>> print(query.to_sql())
            >>> # SELECT users.id, users.name, users.email
            >>> # FROM users
            >>> # WHERE users.age >= :age_1
            >>> # ORDER BY users.name ASC
            >>> # LIMIT :param_1

        Note:
            Parameters are shown as placeholders (:age_1, :param_1).
            This is for debugging only - actual values are bound securely
            during execution.
        """
        # Apply eager loading to statement
        stmt = self._stmt
        for load_option in self._eager_loads:
            stmt = stmt.options(load_option)

        return str(stmt.compile(compile_kwargs={"literal_binds": False}))
