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
    from fast_query import BaseRepository, QueryBuilder
    from myapp.models import User

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

    FastQuery (Repository + Query Builder):
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
    - paginate() -> LengthAwarePaginator[T]  # NEW Sprint 5.6
    - cursor_paginate() -> CursorPaginator[T]  # NEW Sprint 5.6

BUILDER METHODS (return Self for chaining):
    - where(), or_where(), where_in(), etc.
    - order_by(), latest(), oldest()
    - limit(), offset()
    - with_(), with_joined() (eager loading)
"""

from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, TypeVar

from sqlalchemy import Select, and_, between, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, joinedload, selectinload
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql import ColumnElement

from .base import Base
from .exceptions import RecordNotFound

# Forward reference to avoid circular imports
if TYPE_CHECKING:
    from .pagination import CursorPaginator, LengthAwarePaginator

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

        # Global scope flags for soft deletes (Sprint 2.6)
        self._include_trashed = False  # If True, include soft-deleted records
        self._only_trashed = False     # If True, only show soft-deleted records

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
            >>> from datetime import datetime, timedelta, timezone
            >>> start = datetime.now(timezone.utc) - timedelta(days=7)
            >>> end = datetime.now(timezone.utc)
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

    async def paginate(self, page: int = 1, per_page: int = 15) -> "LengthAwarePaginator[T]":
        """
        Execute paginated query and return LengthAwarePaginator.

        **NEW Sprint 5.6**: This is now a TERMINAL METHOD that executes
        TWO queries: COUNT (for total) and SELECT (for data). Replaced
        the old builder-style paginate() that just set LIMIT/OFFSET.

        The COUNT query intelligently clones the current query, removing
        ORDER BY and LIMIT/OFFSET clauses to ensure accurate count while
        preserving all WHERE conditions and JOINs.

        This enables pagination on FILTERED queries:
            await repo.query().where(...).paginate(...)

        Args:
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 15)

        Returns:
            LengthAwarePaginator[T]: Pagination container with items and metadata

        Example:
            >>> # Paginate all users
            >>> result = await user_repo.query().paginate(page=1, per_page=20)
            >>> print(result.total)       # Total users across all pages
            >>> print(result.items)       # Users on current page
            >>> print(result.last_page)   # Total number of pages
            >>>
            >>> # Paginate filtered query (Sprint 5.6!)
            >>> result = await (
            ...     user_repo.query()
            ...     .where(User.status == "active")
            ...     .where(User.age >= 18)
            ...     .paginate(page=2, per_page=50)
            ... )
            >>> # COUNT and SELECT both include WHERE clauses
            >>>
            >>> # With eager loading
            >>> result = await (
            ...     user_repo.query()
            ...     .with_("posts")
            ...     .paginate(page=1, per_page=10)
            ... )

        Technical Details:
            Query 1 (COUNT): Clones _stmt, removes ORDER BY/LIMIT/OFFSET
            Query 2 (SELECT): Applies LIMIT/OFFSET to original query
            Both queries share WHERE clauses and JOINs for accuracy
        """
        from .pagination import LengthAwarePaginator

        # Normalize inputs
        page = max(page, 1)
        per_page = max(per_page, 1)

        # Apply global scope for soft deletes (Sprint 2.6)
        self._apply_global_scope()

        # ========================================
        # Query 1: COUNT (total across all pages)
        # ========================================
        # We need to COUNT the filtered results WITHOUT ORDER BY or LIMIT
        # SQLAlchemy challenge: Clone the statement and strip ordering/limits

        # Build count query by wrapping current statement in subquery
        # This preserves WHERE clauses and JOINs while removing ORDER BY/LIMIT
        count_stmt = select(func.count()).select_from(
            self._stmt.order_by(None).limit(None).offset(None).subquery()
        )

        count_result = await self.session.execute(count_stmt)
        total = int(count_result.scalar_one())

        # ========================================
        # Query 2: SELECT (items for current page)
        # ========================================
        offset_count = (page - 1) * per_page
        select_stmt = self._stmt.limit(per_page).offset(offset_count)

        # Apply eager loading
        for load_option in self._eager_loads:
            select_stmt = select_stmt.options(load_option)

        select_result = await self.session.execute(select_stmt)
        items = list(select_result.scalars().all())

        # Return LengthAwarePaginator with results
        return LengthAwarePaginator(
            items=items,
            total=total,
            per_page=per_page,
            current_page=page,
        )

    async def cursor_paginate(
        self,
        per_page: int = 15,
        cursor: int | str | None = None,
        cursor_column: str = "id",
        ascending: bool = True,
    ) -> "CursorPaginator[T]":
        """
        Execute cursor-based pagination for high-performance infinite scroll.

        **NEW Sprint 5.6**: Uses WHERE clauses instead of OFFSET for O(1)
        performance. Perfect for infinite scroll, real-time feeds, and large
        datasets where traditional offset pagination becomes slow.

        HOW IT WORKS:
            - First page: SELECT * FROM table ORDER BY id LIMIT 15
            - Next page: SELECT * FROM table WHERE id > :cursor ORDER BY id LIMIT 15
            - Database uses index on cursor_column for O(1) seek (no scanning)

        PERFORMANCE COMPARISON:
            Offset Pagination:  O(n) - OFFSET 1000000 scans 1M rows
            Cursor Pagination:  O(1) - WHERE id > X uses index seek

        Args:
            per_page: Items per page (default: 15)
            cursor: Last cursor value from previous page (None for first page)
            cursor_column: Column to use for cursoring (default: "id")
                Must be sequential and indexed (id, created_at)
            ascending: Sort direction (True for ASC, False for DESC)

        Returns:
            CursorPaginator[T]: Pagination container with items and next_cursor

        Example:
            >>> # First page (no cursor)
            >>> result = await (
            ...     post_repo.query()
            ...     .where(Post.status == "published")
            ...     .cursor_paginate(per_page=20)
            ... )
            >>> print(len(result.items))      # 20 posts
            >>> print(result.next_cursor)     # 1045 (ID of last post)
            >>> print(result.has_more_pages)  # True
            >>>
            >>> # Next page (use cursor from previous result)
            >>> result2 = await (
            ...     post_repo.query()
            ...     .where(Post.status == "published")
            ...     .cursor_paginate(
            ...         per_page=20,
            ...         cursor=result.next_cursor
            ...     )
            ... )
            >>> # Fetches: WHERE status = 'published' AND id > 1045
            >>>
            >>> # Descending order (newest first, common for feeds)
            >>> result = await (
            ...     post_repo.query()
            ...     .cursor_paginate(
            ...         per_page=50,
            ...         cursor_column="created_at",
            ...         ascending=False
            ...     )
            ... )
            >>>
            >>> # With filtering and relationships
            >>> result = await (
            ...     user_repo.query()
            ...     .where(User.status == "active")
            ...     .with_("posts")
            ...     .cursor_paginate(per_page=10)
            ... )

        Use Cases:
            ✅ Mobile apps with "Load More" button
            ✅ Infinite scroll feeds (Twitter, Instagram)
            ✅ Real-time data streams
            ✅ Large datasets (millions of rows)
            ❌ Traditional page numbers (use paginate() instead)
            ❌ Random access to pages (use paginate() instead)

        Technical Notes:
            - Fetches per_page + 1 items to determine if more pages exist
            - Cursor is the value of cursor_column from the last item
            - Requires indexed column for optimal performance
            - Automatically applies global scopes (soft deletes)
        """
        from .pagination import CursorPaginator

        # Normalize inputs
        per_page = max(per_page, 1)

        # Apply global scope for soft deletes (Sprint 2.6)
        self._apply_global_scope()

        # Get the cursor column attribute from model
        if not hasattr(self.model, cursor_column):
            raise AttributeError(
                f"Model {self.model.__name__} has no column '{cursor_column}'"
            )

        cursor_attr = getattr(self.model, cursor_column)

        # ========================================
        # Build cursor query
        # ========================================
        stmt = self._stmt

        # Add WHERE clause for cursor (if provided)
        if cursor is not None:
            if ascending:
                # For ascending: get items AFTER cursor
                stmt = stmt.where(cursor_attr > cursor)
            else:
                # For descending: get items BEFORE cursor
                stmt = stmt.where(cursor_attr < cursor)

        # Order by cursor column
        if ascending:
            stmt = stmt.order_by(cursor_attr.asc())
        else:
            stmt = stmt.order_by(cursor_attr.desc())

        # Fetch per_page + 1 to determine if more pages exist
        # (Similar to Laravel's simplePaginate() strategy)
        stmt = stmt.limit(per_page + 1)

        # Apply eager loading
        for load_option in self._eager_loads:
            stmt = stmt.options(load_option)

        # ========================================
        # Execute query
        # ========================================
        result = await self.session.execute(stmt)
        all_items = list(result.scalars().all())

        # ========================================
        # Determine next cursor
        # ========================================
        has_more = len(all_items) > per_page

        if has_more:
            # Remove the extra item (we only fetched it to check if more exist)
            items = all_items[:per_page]
            # Next cursor is the value of cursor_column from the last item
            last_item = items[-1]
            next_cursor = getattr(last_item, cursor_column)
        else:
            # No more pages
            items = all_items
            next_cursor = None

        # Return CursorPaginator with results
        return CursorPaginator(
            items=items,
            next_cursor=next_cursor,
            per_page=per_page,
            cursor_column=cursor_column,
        )

    # ===========================
    # RELATIONSHIP LOADING
    # ===========================

    def with_(
        self, *relationships: InstrumentedAttribute[Any] | str
    ) -> "QueryBuilder[T]":
        """
        Eager load relationships using selectinload (N+1 prevention).

        Uses SQLAlchemy's selectinload strategy, which issues a separate
        SELECT for each relationship. More efficient for one-to-many
        relationships than joinedload.

        **NEW in Sprint 2.6:** Supports dot notation for nested relationships!

        Args:
            *relationships: Relationship attributes to eager load (objects or strings)

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
            >>>
            >>> # NEW: Nested relationships with dot notation (Sprint 2.6)
            >>> users = await (
            ...     user_repo.query()
            ...     .with_("posts.comments", "posts.author")
            ...     .get()
            ... )
            >>> # Now user.posts[0].comments and user.posts[0].author are loaded!

        See: docs/relationships.md for N+1 prevention guide
        """
        for rel in relationships:
            if isinstance(rel, str):
                # Parse dot notation for nested relationships (Sprint 2.6)
                self._eager_loads.append(self._parse_nested_relationship(rel))
            else:
                # Existing behavior: object-based loading
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
    # GLOBAL SCOPES (Soft Deletes - Sprint 2.6)
    # ===========================

    def with_trashed(self) -> "QueryBuilder[T]":
        """
        Include soft-deleted records in query results.

        By default, queries automatically exclude soft-deleted records when
        the model has SoftDeletesMixin. Use this method to include them.

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Include both active and soft-deleted users
            >>> all_users = await (
            ...     user_repo.query()
            ...     .with_trashed()
            ...     .get()
            ... )
            >>>
            >>> # Count including deleted
            >>> total_count = await user_repo.query().with_trashed().count()

        See Also:
            only_trashed() - Show only soft-deleted records
        """
        self._include_trashed = True
        self._only_trashed = False
        return self

    def only_trashed(self) -> "QueryBuilder[T]":
        """
        Show only soft-deleted records.

        Restricts query to only return records that have been soft-deleted
        (deleted_at is not NULL).

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Get only soft-deleted users
            >>> deleted_users = await (
            ...     user_repo.query()
            ...     .only_trashed()
            ...     .get()
            ... )
            >>>
            >>> # Count deleted users
            >>> deleted_count = await user_repo.query().only_trashed().count()

        See Also:
            with_trashed() - Include both active and deleted records
        """
        self._only_trashed = True
        self._include_trashed = False
        return self

    # ===========================
    # LOCAL SCOPES (Sprint 2.6)
    # ===========================

    def scope(self, scope_callable: Callable[["QueryBuilder[T]"], "QueryBuilder[T]"]) -> "QueryBuilder[T]":
        """
        Apply a local scope (reusable query logic).

        Allows defining reusable query methods that can be applied to any query.
        The callable receives this QueryBuilder and returns a modified QueryBuilder.

        Args:
            scope_callable: Function that takes QueryBuilder and returns modified QueryBuilder

        Returns:
            QueryBuilder[T]: Self for method chaining

        Example:
            >>> # Define scope as static method in model
            >>> class User(Base):
            ...     @staticmethod
            ...     def active(query: QueryBuilder["User"]) -> QueryBuilder["User"]:
            ...         return query.where(User.status == "active")
            >>>
            >>> # Use scope in queries
            >>> active_users = await (
            ...     user_repo.query()
            ...     .scope(User.active)
            ...     .get()
            ... )
            >>>
            >>> # Or as lambda
            >>> adults = await (
            ...     user_repo.query()
            ...     .scope(lambda q: q.where(User.age >= 18))
            ...     .get()
            ... )
            >>>
            >>> # Chain multiple scopes
            >>> users = await (
            ...     user_repo.query()
            ...     .scope(User.active)
            ...     .scope(User.verified)
            ...     .get()
            ... )
        """
        return scope_callable(self)

    # ===========================
    # RELATIONSHIP FILTERS (Sprint 2.6)
    # ===========================

    def where_has(self, relationship_name: str) -> "QueryBuilder[T]":
        """
        Filter records that have at least one related record.

        Checks for the existence of a relationship. Uses SQLAlchemy's has()
        for to-one relationships or any() for to-many relationships.

        Args:
            relationship_name: Name of the relationship (as string)

        Returns:
            QueryBuilder[T]: Self for method chaining

        Raises:
            AttributeError: If relationship doesn't exist on model

        Example:
            >>> # Get users who have at least one post
            >>> users_with_posts = await (
            ...     user_repo.query()
            ...     .where_has("posts")
            ...     .get()
            ... )
            >>>
            >>> # Get posts that have at least one comment
            >>> posts_with_comments = await (
            ...     post_repo.query()
            ...     .where_has("comments")
            ...     .get()
            ... )
            >>>
            >>> # Combine with other filters
            >>> active_users_with_posts = await (
            ...     user_repo.query()
            ...     .where(User.status == "active")
            ...     .where_has("posts")
            ...     .get()
            ... )
        """
        # Get the relationship property from the model
        if not hasattr(self.model, relationship_name):
            raise AttributeError(
                f"Model {self.model.__name__} has no relationship '{relationship_name}'"
            )

        rel_attr = getattr(self.model, relationship_name)

        # Check if it's actually a relationship
        if not isinstance(rel_attr.property, RelationshipProperty):
            raise AttributeError(
                f"Attribute '{relationship_name}' on {self.model.__name__} is not a relationship"
            )

        # Determine if it's a to-one or to-many relationship
        # For to-one (uselist=False), use has()
        # For to-many (uselist=True), use any()
        if rel_attr.property.uselist:
            # One-to-many or many-to-many (collection)
            self._stmt = self._stmt.where(rel_attr.any())
        else:
            # Many-to-one or one-to-one (scalar)
            self._stmt = self._stmt.where(rel_attr.has())

        return self

    # ===========================
    # INTERNAL HELPER METHODS (Sprint 2.6)
    # ===========================

    def _parse_nested_relationship(self, path: str) -> Any:
        """
        Parse dot-separated relationship path into nested selectinload.

        Converts strings like "posts.comments" into:
            selectinload(User.posts).selectinload(Post.comments)

        Args:
            path: Dot-separated relationship path (e.g., "posts.comments.author")

        Returns:
            SQLAlchemy load option (selectinload chain)

        Raises:
            AttributeError: If any relationship in path doesn't exist

        Example:
            >>> # "posts.comments" becomes:
            >>> # selectinload(User.posts).selectinload(Post.comments)
        """
        parts = path.split(".")
        if len(parts) < 2:
            # Single relationship, treat as normal
            if not hasattr(self.model, parts[0]):
                raise AttributeError(
                    f"Model {self.model.__name__} has no relationship '{parts[0]}'"
                )
            return selectinload(getattr(self.model, parts[0]))

        # Build nested selectinload chain
        current_model = self.model
        load_option = None

        for i, part in enumerate(parts):
            if not hasattr(current_model, part):
                parent_path = ".".join(parts[:i])
                raise AttributeError(
                    f"Model {current_model.__name__} has no relationship '{part}' "
                    f"(in path '{path}', after '{parent_path}')"
                )

            rel_attr = getattr(current_model, part)

            if i == 0:
                # First relationship - start the chain
                load_option = selectinload(rel_attr)
            else:
                # Nested relationship - chain it
                load_option = load_option.selectinload(rel_attr)

            # Get the related model for next iteration
            # This allows us to validate the next relationship exists
            if hasattr(rel_attr.property, "mapper"):
                current_model = rel_attr.property.mapper.class_

        return load_option

    def _apply_global_scope(self) -> None:
        """
        Apply global scope for soft deletes if model has SoftDeletesMixin.

        This method is called by all terminal methods (get, first, count, etc.)
        to automatically filter out soft-deleted records unless explicitly
        requested with with_trashed() or only_trashed().

        Behavior:
            - Default: Exclude soft-deleted (deleted_at IS NULL)
            - with_trashed(): Include all records (no filter)
            - only_trashed(): Only soft-deleted (deleted_at IS NOT NULL)
        """
        from .mixins import SoftDeletesMixin

        # Check if model has SoftDeletesMixin
        if not issubclass(self.model, SoftDeletesMixin):
            return  # No soft deletes, skip global scope

        # Apply filter based on flags
        if self._only_trashed:
            # Show only soft-deleted records
            self._stmt = self._stmt.where(self.model.deleted_at.isnot(None))
        elif not self._include_trashed:
            # Default: exclude soft-deleted records
            self._stmt = self._stmt.where(self.model.deleted_at.is_(None))
        # If _include_trashed is True, don't apply any filter (show all)

    # ===========================
    # TERMINAL METHODS (Execute Query)
    # ===========================

    async def get(self) -> list[T]:
        """
        Execute query and return all results.

        Terminal method that executes the query and returns all matching
        records as a list.

        **Sprint 2.6:** Automatically excludes soft-deleted records if model
        has SoftDeletesMixin (unless with_trashed() or only_trashed() is used).

        Returns:
            list[T]: List of model instances (may be empty)

        Example:
            >>> # Get all active users (soft-deleted excluded automatically)
            >>> users = await (
            ...     repo.query()
            ...     .where(User.status == "active")
            ...     .get()
            ... )
            >>>
            >>> # Include soft-deleted users
            >>> all_users = await repo.query().with_trashed().get()
        """
        # Apply global scope for soft deletes (Sprint 2.6)
        self._apply_global_scope()

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

        **Sprint 2.6:** Automatically excludes soft-deleted records if model
        has SoftDeletesMixin.

        Returns:
            Optional[T]: First model instance or None

        Example:
            >>> # Get first active user (soft-deleted excluded)
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
        # Apply global scope for soft deletes (Sprint 2.6)
        self._apply_global_scope()

        stmt = self._stmt.limit(1)

        # Apply eager loading
        for load_option in self._eager_loads:
            stmt = stmt.options(load_option)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def first_or_fail(self) -> T:
        """
        Execute query and return first result or raise RecordNotFound.

        Terminal method that executes the query and returns the first
        matching record. Raises RecordNotFound if no record found.

        Returns:
            T: First model instance (guaranteed to exist)

        Raises:
            RecordNotFound: If no record found

        Example:
            >>> # Get first active user or fail
            >>> user = await (
            ...     repo.query()
            ...     .where(User.status == "active")
            ...     .first_or_fail()
            ... )
            >>> # No None check needed - either returns user or raises
            >>> print(user.name)
        """
        result = await self.first()

        if result is None:
            raise RecordNotFound(self.model.__name__)

        return result

    async def count(self) -> int:
        """
        Execute query and return count of matching records.

        Terminal method that executes a COUNT query and returns the
        number of matching records.

        **Sprint 2.6:** Automatically excludes soft-deleted records if model
        has SoftDeletesMixin.

        Returns:
            int: Number of matching records

        Example:
            >>> # Count active users (soft-deleted excluded)
            >>> total = await (
            ...     repo.query()
            ...     .where(User.status == "active")
            ...     .count()
            ... )
            >>> print(f"Found {total} active users")
            >>>
            >>> # Count all including deleted
            >>> total_users = await repo.query().with_trashed().count()
        """
        # Apply global scope for soft deletes (Sprint 2.6)
        self._apply_global_scope()

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

        **Sprint 2.6:** Automatically excludes soft-deleted records if model
        has SoftDeletesMixin.

        Args:
            column: Column attribute to extract values from

        Returns:
            list[Any]: List of column values (may be empty)

        Example:
            >>> # Get all user emails (soft-deleted excluded)
            >>> emails = await repo.query().pluck(User.email)
            >>> # ['alice@test.com', 'bob@test.com', ...]
            >>>
            >>> # Get IDs including deleted users
            >>> all_ids = await repo.query().with_trashed().pluck(User.id)
        """
        # Apply global scope for soft deletes (Sprint 2.6)
        self._apply_global_scope()

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
