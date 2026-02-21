"""
Generic Pagination Schemas

Provides two reusable, type-safe pagination strategies:

    CursorPage[T]  — O(1) cursor-based pagination (WHERE id > :cursor).
                     Ideal for infinite-scroll UIs and large datasets.

    OffsetPage[T]  — Classic offset pagination with total counts.
                     Ideal for numbered-page UIs that need a page count.

Both are Pydantic v2 generics: instantiate with a concrete type, e.g.
    CursorPage[ProductResponse]
    OffsetPage[UserResponse]

Python 3.10+ / Pydantic v2 — no GenericModel import required.

Zero dependencies on any web framework or application layer.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Cursor Strategy
# ---------------------------------------------------------------------------


class CursorMeta(BaseModel):
    """Metadata returned alongside a cursor-paginated result set."""

    per_page: int = Field(..., description="Maximum items returned per page")
    next_cursor: str | None = Field(
        None,
        description="Opaque cursor pointing to the first item of the next page. "
        "Pass this as the `cursor` query parameter to advance.",
    )
    has_more_pages: bool = Field(
        ..., description="True when at least one more page exists beyond this one"
    )
    count: int = Field(..., description="Number of items returned in this page")


class CursorPage(BaseModel, Generic[T]):
    """
    Cursor-based pagination envelope.

    Uses a single SQL query with no COUNT(*) — O(1) regardless of table size.

    Example response:
        {
            "data": [ ... ],
            "meta": {
                "per_page": 15,
                "next_cursor": "660f9500-...",
                "has_more_pages": true,
                "count": 15
            }
        }
    """

    data: list[T] = Field(..., description="Current page of items")
    meta: CursorMeta = Field(..., description="Cursor pagination metadata")


# ---------------------------------------------------------------------------
# Offset Strategy
# ---------------------------------------------------------------------------


class OffsetMeta(BaseModel):
    """Metadata returned alongside an offset-paginated result set."""

    total: int = Field(..., ge=0, description="Total number of matching records")
    page: int = Field(..., ge=1, description="Current page number (1-based)")
    per_page: int = Field(..., ge=1, description="Maximum items returned per page")
    last_page: int = Field(..., ge=1, description="Number of the final available page")


class OffsetPage(BaseModel, Generic[T]):
    """
    Offset-based pagination envelope.

    Performs a COUNT(*) query so callers know the total result set size.
    Use when the UI needs to display a total count or jump to a specific page.

    Example response:
        {
            "data": [ ... ],
            "meta": {
                "total": 480,
                "page": 3,
                "per_page": 15,
                "last_page": 32
            }
        }
    """

    data: list[T] = Field(..., description="Current page of items")
    meta: OffsetMeta = Field(..., description="Offset pagination metadata")


# Convenience alias so callers can import a single union type for type hints.
AnyPage = CursorPage[Any] | OffsetPage[Any]
