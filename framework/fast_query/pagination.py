"""
Fast Query - Pagination Support (Sprint 5.5 + 5.6)

This module provides Laravel-style pagination for the Fast Query ORM.
Inspired by Laravel's LengthAwarePaginator and cursor pagination patterns.

Sprint 5.5: Offset-Based Pagination
    - LengthAwarePaginator[T] with metadata (current_page, last_page, total)
    - Link generation (first, last, next, prev)
    - Laravel-compatible JSON response format
    - Integration with ResourceCollection

Sprint 5.6: Cursor-Based Pagination
    - CursorPaginator[T] for high-performance infinite scroll
    - O(1) performance using WHERE instead of OFFSET
    - next_cursor for stateless pagination
    - Perfect for large datasets and real-time feeds

Public API:
    LengthAwarePaginator[T]: Offset-based pagination (use for traditional UI)
    CursorPaginator[T]: Cursor-based pagination (use for infinite scroll)

Example (Offset):
    >>> # Traditional pagination with page numbers
    >>> users = await user_repo.query().paginate(page=2, per_page=20)
    >>> print(users.total)       # Total items across all pages
    >>> print(users.last_page)   # Total number of pages

Example (Cursor):
    >>> # High-performance cursor pagination
    >>> result = await user_repo.query().cursor_paginate(per_page=50)
    >>> print(result.items)      # First 50 users
    >>> print(result.next_cursor) # Cursor for next page
    >>>
    >>> # Get next page using cursor
    >>> result2 = await user_repo.query().cursor_paginate(
    ...     per_page=50,
    ...     cursor=result.next_cursor
    ... )
"""

import math
from typing import Any, Generic, TypeVar

# Generic type for paginated items
T = TypeVar("T")


class LengthAwarePaginator(Generic[T]):
    """
    Laravel-style pagination container.

    This class holds a page of items along with pagination metadata
    (total items, current page, etc.) and provides methods for
    generating pagination links.

    Attributes:
        items: List of items on the current page
        total: Total number of items across all pages
        per_page: Number of items per page
        current_page: Current page number (1-indexed)

    Example:
        >>> paginator = LengthAwarePaginator(
        ...     items=[user1, user2, user3],
        ...     total=97,
        ...     per_page=20,
        ...     current_page=2
        ... )
        >>> print(paginator.last_page)  # 5
        >>> print(paginator.from_item)  # 21
        >>> print(paginator.to_item)    # 40
        >>> print(paginator.has_more_pages)  # True
    """

    def __init__(
        self,
        items: list[T],
        total: int,
        per_page: int,
        current_page: int,
    ) -> None:
        """
        Initialize a paginator.

        Args:
            items: Items on the current page
            total: Total items across all pages
            per_page: Items per page
            current_page: Current page number (1-indexed)
        """
        self.items = items
        self.total = total
        self.per_page = max(per_page, 1)  # Ensure at least 1 per page
        self.current_page = max(current_page, 1)  # Ensure at least page 1

    @property
    def last_page(self) -> int:
        """
        Calculate the last page number.

        Returns:
            int: Total number of pages (minimum 1)

        Example:
            >>> paginator = LengthAwarePaginator([], 97, 20, 1)
            >>> paginator.last_page  # 5 (ceil(97/20))
        """
        if self.total == 0:
            return 1
        return math.ceil(self.total / self.per_page)

    @property
    def from_item(self) -> int | None:
        """
        Get the number of the first item on the current page.

        Returns:
            int | None: First item number (1-indexed), or None if no items

        Example:
            >>> paginator = LengthAwarePaginator([...], 97, 20, 2)
            >>> paginator.from_item  # 21 (first item on page 2)
        """
        if self.total == 0:
            return None
        return ((self.current_page - 1) * self.per_page) + 1

    @property
    def to_item(self) -> int | None:
        """
        Get the number of the last item on the current page.

        Returns:
            int | None: Last item number (1-indexed), or None if no items

        Example:
            >>> paginator = LengthAwarePaginator([...], 97, 20, 2)
            >>> paginator.to_item  # 40 (last item on page 2)
        """
        if self.total == 0:
            return None

        # Calculate expected last item on page
        expected_to = self.current_page * self.per_page

        # Don't exceed total items
        return min(expected_to, self.total)

    @property
    def has_pages(self) -> bool:
        """
        Determine if there are enough items to split into multiple pages.

        Returns:
            bool: True if more than one page exists

        Example:
            >>> paginator = LengthAwarePaginator([...], 97, 20, 1)
            >>> paginator.has_pages  # True (97 items / 20 per page = 5 pages)
        """
        return self.total > self.per_page

    @property
    def has_more_pages(self) -> bool:
        """
        Determine if there are more pages after the current page.

        Returns:
            bool: True if current page is not the last page

        Example:
            >>> paginator = LengthAwarePaginator([...], 97, 20, 2)
            >>> paginator.has_more_pages  # True (page 2 of 5)
        """
        return self.current_page < self.last_page

    @property
    def on_first_page(self) -> bool:
        """
        Determine if the paginator is on the first page.

        Returns:
            bool: True if current_page is 1

        Example:
            >>> paginator = LengthAwarePaginator([...], 97, 20, 1)
            >>> paginator.on_first_page  # True
        """
        return self.current_page == 1

    @property
    def on_last_page(self) -> bool:
        """
        Determine if the paginator is on the last page.

        Returns:
            bool: True if current_page equals last_page

        Example:
            >>> paginator = LengthAwarePaginator([...], 97, 20, 5)
            >>> paginator.on_last_page  # True (page 5 of 5)
        """
        return self.current_page == self.last_page

    def url(self, page: int, base_url: str = "?page=") -> str:
        """
        Generate URL for a specific page.

        Args:
            page: Page number to generate URL for
            base_url: Base URL pattern (default: "?page=")

        Returns:
            str: URL for the specified page

        Example:
            >>> paginator = LengthAwarePaginator([...], 97, 20, 2)
            >>> paginator.url(3)  # "?page=3"
            >>> paginator.url(3, "/users?page=")  # "/users?page=3"
        """
        return f"{base_url}{page}"

    def next_page_url(self, base_url: str = "?page=") -> str | None:
        """
        Get URL for the next page.

        Args:
            base_url: Base URL pattern (default: "?page=")

        Returns:
            str | None: URL for next page, or None if on last page

        Example:
            >>> paginator = LengthAwarePaginator([...], 97, 20, 2)
            >>> paginator.next_page_url()  # "?page=3"
        """
        if not self.has_more_pages:
            return None
        return self.url(self.current_page + 1, base_url)

    def previous_page_url(self, base_url: str = "?page=") -> str | None:
        """
        Get URL for the previous page.

        Args:
            base_url: Base URL pattern (default: "?page=")

        Returns:
            str | None: URL for previous page, or None if on first page

        Example:
            >>> paginator = LengthAwarePaginator([...], 97, 20, 2)
            >>> paginator.previous_page_url()  # "?page=1"
        """
        if self.on_first_page:
            return None
        return self.url(self.current_page - 1, base_url)

    def to_dict(self, base_url: str = "?page=") -> dict[str, Any]:
        """
        Convert paginator to dictionary for JSON serialization.

        This generates metadata in Laravel's pagination format, including
        pagination links (first, last, next, prev).

        Args:
            base_url: Base URL for link generation (default: "?page=")

        Returns:
            dict: Pagination metadata

        Example:
            >>> paginator = LengthAwarePaginator([...], 97, 20, 2)
            >>> paginator.to_dict()
            {
                "current_page": 2,
                "last_page": 5,
                "per_page": 20,
                "total": 97,
                "from": 21,
                "to": 40,
                "links": {
                    "first": "?page=1",
                    "last": "?page=5",
                    "next": "?page=3",
                    "prev": "?page=1"
                }
            }
        """
        return {
            "current_page": self.current_page,
            "last_page": self.last_page,
            "per_page": self.per_page,
            "total": self.total,
            "from": self.from_item,
            "to": self.to_item,
            "links": {
                "first": self.url(1, base_url),
                "last": self.url(self.last_page, base_url),
                "next": self.next_page_url(base_url),
                "prev": self.previous_page_url(base_url),
            },
        }

    def __repr__(self) -> str:
        """
        String representation of paginator.

        Returns:
            str: Debug-friendly representation

        Example:
            >>> paginator = LengthAwarePaginator([...], 97, 20, 2)
            >>> repr(paginator)
            '<LengthAwarePaginator page=2/5 per_page=20 total=97>'
        """
        return (
            f"<LengthAwarePaginator page={self.current_page}/{self.last_page} "
            f"per_page={self.per_page} total={self.total}>"
        )


class CursorPaginator(Generic[T]):
    """
    High-performance cursor-based pagination (Sprint 5.6).

    Instead of OFFSET (which has O(n) performance), this uses WHERE clauses
    on a sequential column (id or created_at) for O(1) performance.

    Perfect for:
        - Infinite scroll interfaces
        - Real-time feeds (Twitter, Facebook)
        - Large datasets where OFFSET is slow
        - Mobile apps with "Load More" UX

    Trade-offs:
        ✅ O(1) performance (always fast, even at page 1,000,000)
        ✅ Consistent results even if data changes (new inserts don't shift pages)
        ✅ Stateless (cursor is self-contained, no server-side session needed)
        ❌ Can't jump to arbitrary pages (no "Go to page 5")
        ❌ No total count (unknown number of results)
        ❌ Only works with sequential columns (id, created_at)

    Attributes:
        items: List of items on the current page
        next_cursor: Cursor value for fetching next page (None if no more)
        has_more_pages: True if more items exist after this page

    Example:
        >>> # First page
        >>> result = await post_repo.query().cursor_paginate(per_page=20)
        >>> print(len(result.items))  # 20 posts
        >>> print(result.next_cursor) # 987 (last item's ID)
        >>>
        >>> # Next page using cursor
        >>> result2 = await post_repo.query().cursor_paginate(
        ...     per_page=20,
        ...     cursor=result.next_cursor
        ... )
        >>> # Fetches 20 posts WHERE id > 987

    Technical Details:
        - Uses WHERE instead of OFFSET for performance
        - Requires indexed sequential column (id, created_at)
        - SQL: SELECT * FROM posts WHERE id > :cursor ORDER BY id LIMIT :per_page
        - Database can use index for O(1) seek
    """

    def __init__(
        self,
        items: list[T],
        next_cursor: int | str | None,
        per_page: int,
        cursor_column: str = "id",
    ) -> None:
        """
        Initialize a cursor paginator.

        Args:
            items: Items on the current page
            next_cursor: Cursor value for next page (None if no more pages)
            per_page: Items per page
            cursor_column: Column used for cursoring (default: "id")
        """
        self.items = items
        self.next_cursor = next_cursor
        self.per_page = per_page
        self.cursor_column = cursor_column

    @property
    def has_more_pages(self) -> bool:
        """
        Determine if there are more pages after the current page.

        Returns:
            bool: True if next_cursor is not None

        Example:
            >>> result = await repo.query().cursor_paginate(per_page=20)
            >>> if result.has_more_pages:
            ...     # Load more button should be visible
            ...     print("More items available")
        """
        return self.next_cursor is not None

    @property
    def count(self) -> int:
        """
        Get count of items on current page.

        Returns:
            int: Number of items in current page

        Example:
            >>> result = await repo.query().cursor_paginate(per_page=20)
            >>> print(result.count)  # Number of items returned (0-20)
        """
        return len(self.items)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert paginator to dictionary for JSON serialization.

        Returns:
            dict: Cursor pagination metadata

        Example:
            >>> result = await repo.query().cursor_paginate(per_page=20)
            >>> result.to_dict()
            {
                "per_page": 20,
                "next_cursor": 987,
                "has_more_pages": True,
                "count": 20
            }
        """
        return {
            "per_page": self.per_page,
            "next_cursor": self.next_cursor,
            "has_more_pages": self.has_more_pages,
            "count": self.count,
        }

    def __repr__(self) -> str:
        """
        String representation of cursor paginator.

        Returns:
            str: Debug-friendly representation

        Example:
            >>> result = CursorPaginator([...], 987, 20, "id")
            >>> repr(result)
            '<CursorPaginator count=20 next_cursor=987>'
        """
        return (
            f"<CursorPaginator count={self.count} "
            f"next_cursor={self.next_cursor}>"
        )
