"""
Fast Query - Pagination Support (Sprint 5.5)

This module provides Laravel-style pagination for the Fast Query ORM.
Inspired by Laravel's LengthAwarePaginator, it provides rich pagination
metadata and link generation.

Key Features:
    - Generic LengthAwarePaginator[T] for type safety
    - Automatic metadata calculation (current_page, last_page, total, etc.)
    - Link generation for first, last, next, prev
    - Laravel-compatible JSON response format
    - Integration with ResourceCollection for API responses

Public API:
    LengthAwarePaginator[T]: Main pagination container

Example:
    >>> from fast_query import BaseRepository, LengthAwarePaginator
    >>>
    >>> # Repository pagination
    >>> users = await user_repo.paginate(page=2, per_page=20)
    >>> print(users.total)  # Total items across all pages
    >>> print(users.items)  # Items on current page
    >>>
    >>> # Convert to dict for JSON response
    >>> data = users.to_dict()
    >>> # {
    >>> #   "current_page": 2,
    >>> #   "last_page": 5,
    >>> #   "per_page": 20,
    >>> #   "total": 97,
    >>> #   "from": 21,
    >>> #   "to": 40
    >>> # }
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
