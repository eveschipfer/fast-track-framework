"""
BaseController

Abstract base class for all application controllers. Provides a thin set of
standardised HTTP-response helpers so every controller speaks the same language,
and a strategy-agnostic `paginated()` helper that works transparently with both
CursorPage and OffsetPage envelopes.

Responsibilities of this class:
    - Standardise how 200/201/204 responses are shaped.
    - Provide a single `paginated()` entry-point that delegates to the correct
      strategy based on the page object received.

Responsibilities NOT belonging here:
    - Domain logic (belongs in the service layer).
    - Exception-to-status-code translation (belongs in each concrete controller).
"""

from abc import ABC
from typing import Any

from fastapi import status
from fastapi.responses import Response

from fast_query import CursorPage, OffsetPage


class BaseController(ABC):
    """Abstract base for all controllers.

    Concrete controllers inherit this class to gain a consistent vocabulary for
    building HTTP responses.  No abstract methods are mandated — subclasses pick
    whichever helpers they need.
    """

    # ------------------------------------------------------------------
    # Simple response helpers
    # ------------------------------------------------------------------

    def ok[_T](self, data: _T) -> _T:
        """Pass-through for a 200 OK payload.

        Returns the data unchanged.  FastAPI serialises it via the route's
        ``response_model`` annotation, so callers can return typed objects
        directly without calling ``.model_dump()`` themselves.
        """
        return data

    def created[_T](self, data: _T) -> _T:
        """Pass-through for a 201 Created payload.

        Pair with ``status_code=status.HTTP_201_CREATED`` on the route decorator.
        """
        return data

    def no_content(self) -> Response:
        """Return an empty 204 No Content response."""
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # ------------------------------------------------------------------
    # Pagination helper
    # ------------------------------------------------------------------

    def paginated(self, page: CursorPage[Any] | OffsetPage[Any]) -> dict[str, Any]:
        """Serialise a paginated result to a plain dictionary.

        Accepts **either** strategy transparently:
            - ``CursorPage[T]`` → ``{ data, meta: { next_cursor, has_more_pages, ... } }``
            - ``OffsetPage[T]``  → ``{ data, meta: { total, page, last_page, ... } }``

        FastAPI will further validate / serialise the returned dict against the
        route's ``response_model`` if one is declared.

        Args:
            page: A ``CursorPage`` or ``OffsetPage`` instance produced by the
                  service layer.

        Returns:
            dict with ``"data"`` and ``"meta"`` keys whose shape depends on the
            pagination strategy used.
        """
        return page.model_dump()
