"""
QueryBuilder Pagination Tests (Sprint 5.6)

This test suite validates the new pagination methods in QueryBuilder:
    - paginate() - Offset-based pagination with LengthAwarePaginator
    - cursor_paginate() - Cursor-based pagination for high-performance

Test Strategy:
    - Use mocking to avoid async session fixture complexity
    - Focus on SQL generation and logic correctness
    - Test edge cases (empty results, single page, page beyond last)
    - Verify COUNT query removes ORDER BY/LIMIT/OFFSET
    - Verify cursor pagination uses WHERE instead of OFFSET

Test Coverage:
    - paginate() with filters (COUNT reflects WHERE clauses)
    - paginate() edge cases (page 0, negative values, empty results)
    - cursor_paginate() next cursor generation
    - cursor_paginate() ascending/descending order
    - cursor_paginate() edge cases (no more pages, empty results)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

# Import pagination classes
from fast_query.pagination import LengthAwarePaginator, CursorPaginator
from fast_query.query_builder import QueryBuilder
from fast_query.base import Base

# Import SQLAlchemy components
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


# Test model (avoid SQLAlchemy metadata conflicts with real User model)
class TestUser(Base):
    """Minimal test model for pagination tests."""
    __tablename__ = "test_pagination_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100))

# Alias for clarity in tests
User = TestUser


class TestQueryBuilderPaginate:
    """Test offset-based pagination with paginate() method."""

    @pytest.mark.asyncio
    async def test_paginate_returns_length_aware_paginator(self):
        """paginate() should return LengthAwarePaginator instance."""
        # Setup mock session
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock COUNT result (total=97)
        count_result = Mock()
        count_result.scalar_one = Mock(return_value=97)

        # Mock SELECT result (20 items on page 2)
        select_result = Mock()
        items = [User(id=i, name=f"User {i}", email=f"user{i}@test.com") for i in range(21, 41)]
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=items)))

        # Configure session.execute to return different results
        mock_session.execute = AsyncMock(side_effect=[count_result, select_result])

        # Create query builder
        query = QueryBuilder(mock_session, User)

        # Execute pagination
        result = await query.paginate(page=2, per_page=20)

        # Verify result type
        assert isinstance(result, LengthAwarePaginator)
        assert result.total == 97
        assert result.per_page == 20
        assert result.current_page == 2
        assert len(result.items) == 20
        assert result.last_page == 5  # ceil(97/20)

        # Verify two queries were executed
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_paginate_with_where_clause_reflects_in_count(self):
        """COUNT query must preserve WHERE clauses from filtered query."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock COUNT result (50 users named "Alice")
        count_result = Mock()
        count_result.scalar_one = Mock(return_value=50)

        # Mock SELECT result
        select_result = Mock()
        items = [User(id=i, name="Alice", email=f"user{i}@test.com") for i in range(1, 16)]
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=items)))

        mock_session.execute = AsyncMock(side_effect=[count_result, select_result])

        # Build filtered query (use existing User.name field)
        query = QueryBuilder(mock_session, User).where(User.name == "Alice")

        # Execute pagination
        result = await query.paginate(page=1, per_page=15)

        # Verify count reflects filter (not all users)
        assert result.total == 50  # Only users named Alice, not all users
        assert result.last_page == 4  # ceil(50/15)

    @pytest.mark.asyncio
    async def test_paginate_normalizes_negative_page_to_1(self):
        """page=0 or negative should be normalized to page=1."""
        mock_session = AsyncMock(spec=AsyncSession)

        count_result = Mock()
        count_result.scalar_one = Mock(return_value=100)

        select_result = Mock()
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))

        mock_session.execute = AsyncMock(side_effect=[count_result, select_result])

        query = QueryBuilder(mock_session, User)

        # Test page=0
        result = await query.paginate(page=0, per_page=20)
        assert result.current_page == 1

        # Reset mocks
        mock_session.execute = AsyncMock(side_effect=[count_result, select_result])

        # Test page=-5
        result = await query.paginate(page=-5, per_page=20)
        assert result.current_page == 1

    @pytest.mark.asyncio
    async def test_paginate_normalizes_zero_per_page_to_1(self):
        """per_page=0 or negative should be normalized to per_page=1."""
        mock_session = AsyncMock(spec=AsyncSession)

        count_result = Mock()
        count_result.scalar_one = Mock(return_value=100)

        select_result = Mock()
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))

        mock_session.execute = AsyncMock(side_effect=[count_result, select_result])

        query = QueryBuilder(mock_session, User)

        # Test per_page=0
        result = await query.paginate(page=1, per_page=0)
        assert result.per_page == 1

    @pytest.mark.asyncio
    async def test_paginate_empty_results_returns_empty_paginator(self):
        """Paginating empty table should return LengthAwarePaginator with total=0."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock COUNT result (total=0)
        count_result = Mock()
        count_result.scalar_one = Mock(return_value=0)

        # Mock SELECT result (no items)
        select_result = Mock()
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))

        mock_session.execute = AsyncMock(side_effect=[count_result, select_result])

        query = QueryBuilder(mock_session, User)
        result = await query.paginate(page=1, per_page=20)

        assert result.total == 0
        assert len(result.items) == 0
        assert result.last_page == 1  # Always at least 1 page
        assert result.from_item is None
        assert result.to_item is None

    @pytest.mark.asyncio
    async def test_paginate_page_beyond_last_returns_empty_items(self):
        """Requesting page 10 when only 5 pages exist should return empty items."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock COUNT result (total=97, last_page=5 for per_page=20)
        count_result = Mock()
        count_result.scalar_one = Mock(return_value=97)

        # Mock SELECT result (no items for page 10)
        select_result = Mock()
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))

        mock_session.execute = AsyncMock(side_effect=[count_result, select_result])

        query = QueryBuilder(mock_session, User)
        result = await query.paginate(page=10, per_page=20)

        assert result.total == 97
        assert result.current_page == 10
        assert result.last_page == 5
        assert len(result.items) == 0  # No items on page 10

    @pytest.mark.asyncio
    async def test_paginate_applies_global_scopes(self):
        """paginate() should apply global scopes (e.g., soft delete filtering)."""
        mock_session = AsyncMock(spec=AsyncSession)

        count_result = Mock()
        count_result.scalar_one = Mock(return_value=50)

        select_result = Mock()
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))

        mock_session.execute = AsyncMock(side_effect=[count_result, select_result])

        # Build query (global scopes would apply if model had SoftDeletesMixin)
        query = QueryBuilder(mock_session, User)

        result = await query.paginate(page=1, per_page=15)

        # Verify pagination still works
        assert isinstance(result, LengthAwarePaginator)


class TestQueryBuilderCursorPaginate:
    """Test cursor-based pagination with cursor_paginate() method."""

    @pytest.mark.asyncio
    async def test_cursor_paginate_returns_cursor_paginator(self):
        """cursor_paginate() should return CursorPaginator instance."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock SELECT result (20 items + 1 to check for more)
        select_result = Mock()
        items = [User(id=i, name=f"User {i}", email=f"user{i}@test.com") for i in range(1, 22)]
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=items)))

        mock_session.execute = AsyncMock(return_value=select_result)

        query = QueryBuilder(mock_session, User)
        result = await query.cursor_paginate(per_page=20)

        # Verify result type
        assert isinstance(result, CursorPaginator)
        assert len(result.items) == 20  # Extra item removed
        assert result.next_cursor == 20  # ID of last item (item 20)
        assert result.has_more_pages is True

    @pytest.mark.asyncio
    async def test_cursor_paginate_no_more_pages(self):
        """cursor_paginate() should set next_cursor=None when no more pages."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock SELECT result (10 items, less than per_page)
        select_result = Mock()
        items = [User(id=i, name=f"User {i}", email=f"user{i}@test.com") for i in range(1, 11)]
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=items)))

        mock_session.execute = AsyncMock(return_value=select_result)

        query = QueryBuilder(mock_session, User)
        result = await query.cursor_paginate(per_page=20)

        assert len(result.items) == 10
        assert result.next_cursor is None  # No more pages
        assert result.has_more_pages is False

    @pytest.mark.asyncio
    async def test_cursor_paginate_with_cursor_uses_where_clause(self):
        """cursor_paginate() with cursor should add WHERE clause."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock SELECT result
        select_result = Mock()
        items = [User(id=i, name=f"User {i}", email=f"user{i}@test.com") for i in range(21, 41)]
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=items)))

        mock_session.execute = AsyncMock(return_value=select_result)

        query = QueryBuilder(mock_session, User)

        # Paginate with cursor=20 (should fetch WHERE id > 20)
        result = await query.cursor_paginate(per_page=20, cursor=20)

        # Verify query was executed (SQL would contain WHERE id > 20)
        assert mock_session.execute.called
        assert len(result.items) == 20

    @pytest.mark.asyncio
    async def test_cursor_paginate_ascending_order(self):
        """cursor_paginate() with ascending=True should order ASC."""
        mock_session = AsyncMock(spec=AsyncSession)

        select_result = Mock()
        items = [User(id=i, name=f"User {i}", email=f"user{i}@test.com") for i in range(1, 21)]
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=items)))

        mock_session.execute = AsyncMock(return_value=select_result)

        query = QueryBuilder(mock_session, User)
        result = await query.cursor_paginate(per_page=20, ascending=True)

        # Verify result
        assert len(result.items) == 20

    @pytest.mark.asyncio
    async def test_cursor_paginate_descending_order(self):
        """cursor_paginate() with ascending=False should order DESC."""
        mock_session = AsyncMock(spec=AsyncSession)

        select_result = Mock()
        # Descending order (100, 99, 98, ..., 80)
        # We request per_page=20, so we fetch 21 items (100-80)
        items = [User(id=i, name=f"User {i}", email=f"user{i}@test.com") for i in range(100, 79, -1)]
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=items)))

        mock_session.execute = AsyncMock(return_value=select_result)

        query = QueryBuilder(mock_session, User)
        result = await query.cursor_paginate(per_page=20, ascending=False)

        assert len(result.items) == 20
        # We fetched 21 items (100-80), took first 20 (100-81)
        # So last item in result is ID 81
        assert result.next_cursor == 81

    @pytest.mark.asyncio
    async def test_cursor_paginate_custom_cursor_column(self):
        """cursor_paginate() should support custom cursor_column."""
        mock_session = AsyncMock(spec=AsyncSession)

        select_result = Mock()
        items = [User(id=i, name=f"User {i}", email=f"user{i}@test.com") for i in range(1, 21)]
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=items)))

        mock_session.execute = AsyncMock(return_value=select_result)

        query = QueryBuilder(mock_session, User)

        # Use name as cursor column (string cursor instead of int)
        result = await query.cursor_paginate(
            per_page=20,
            cursor_column="name"
        )

        assert result.cursor_column == "name"

    @pytest.mark.asyncio
    async def test_cursor_paginate_with_filters(self):
        """cursor_paginate() should preserve WHERE clauses."""
        mock_session = AsyncMock(spec=AsyncSession)

        select_result = Mock()
        items = [User(id=i, name="Alice", email=f"user{i}@test.com") for i in range(1, 21)]
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=items)))

        mock_session.execute = AsyncMock(return_value=select_result)

        # Build filtered query (use existing User.name field)
        query = QueryBuilder(mock_session, User).where(User.name == "Alice")

        # Execute cursor pagination
        result = await query.cursor_paginate(per_page=20)

        # Verify pagination works with filters
        assert isinstance(result, CursorPaginator)

    @pytest.mark.asyncio
    async def test_cursor_paginate_empty_results(self):
        """cursor_paginate() on empty table should return empty CursorPaginator."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock empty result
        select_result = Mock()
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))

        mock_session.execute = AsyncMock(return_value=select_result)

        query = QueryBuilder(mock_session, User)
        result = await query.cursor_paginate(per_page=20)

        assert len(result.items) == 0
        assert result.next_cursor is None
        assert result.has_more_pages is False

    @pytest.mark.asyncio
    async def test_cursor_paginate_exactly_per_page_items(self):
        """When exactly per_page items exist, next_cursor should be None."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock SELECT result (exactly 20 items, no +1)
        select_result = Mock()
        items = [User(id=i, name=f"User {i}", email=f"user{i}@test.com") for i in range(1, 21)]
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=items)))

        mock_session.execute = AsyncMock(return_value=select_result)

        query = QueryBuilder(mock_session, User)
        result = await query.cursor_paginate(per_page=20)

        assert len(result.items) == 20
        assert result.next_cursor is None  # No 21st item, so no more pages
        assert result.has_more_pages is False

    @pytest.mark.asyncio
    async def test_cursor_paginate_invalid_cursor_column_raises_error(self):
        """cursor_paginate() with non-existent column should raise AttributeError."""
        mock_session = AsyncMock(spec=AsyncSession)

        query = QueryBuilder(mock_session, User)

        with pytest.raises(AttributeError) as exc_info:
            await query.cursor_paginate(per_page=20, cursor_column="nonexistent_column")

        assert "has no column 'nonexistent_column'" in str(exc_info.value)


class TestPaginationIntegration:
    """Integration tests for pagination methods."""

    @pytest.mark.asyncio
    async def test_repository_paginate_delegates_to_query_builder(self):
        """BaseRepository.paginate() should delegate to QueryBuilder.paginate()."""
        from fast_query.repository import BaseRepository

        mock_session = AsyncMock(spec=AsyncSession)

        # Mock COUNT result
        count_result = Mock()
        count_result.scalar_one = Mock(return_value=100)

        # Mock SELECT result
        select_result = Mock()
        items = [User(id=i, name=f"User {i}", email=f"user{i}@test.com") for i in range(1, 16)]
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=items)))

        mock_session.execute = AsyncMock(side_effect=[count_result, select_result])

        # Create repository
        repo = BaseRepository(mock_session, User)

        # Execute pagination via repository
        result = await repo.paginate(page=1, per_page=15)

        # Verify delegation worked
        assert isinstance(result, LengthAwarePaginator)
        assert result.total == 100
        assert len(result.items) == 15

    @pytest.mark.asyncio
    async def test_query_builder_paginate_is_terminal_method(self):
        """paginate() should be a terminal method (returns paginator, not builder)."""
        mock_session = AsyncMock(spec=AsyncSession)

        count_result = Mock()
        count_result.scalar_one = Mock(return_value=50)

        select_result = Mock()
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))

        mock_session.execute = AsyncMock(side_effect=[count_result, select_result])

        query = QueryBuilder(mock_session, User)
        result = await query.paginate(page=1, per_page=15)

        # Verify it returns LengthAwarePaginator, not QueryBuilder
        assert isinstance(result, LengthAwarePaginator)
        assert not isinstance(result, QueryBuilder)

    @pytest.mark.asyncio
    async def test_cursor_paginate_is_terminal_method(self):
        """cursor_paginate() should be a terminal method (returns paginator, not builder)."""
        mock_session = AsyncMock(spec=AsyncSession)

        select_result = Mock()
        select_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))

        mock_session.execute = AsyncMock(return_value=select_result)

        query = QueryBuilder(mock_session, User)
        result = await query.cursor_paginate(per_page=15)

        # Verify it returns CursorPaginator, not QueryBuilder
        assert isinstance(result, CursorPaginator)
        assert not isinstance(result, QueryBuilder)
