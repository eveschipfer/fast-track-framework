"""
Resource Collection - Handle Lists of Resources (Sprint 4.2)

This module handles transforming collections (lists) of models into JSON responses.
It preserves the "data" wrapper and optionally adds pagination metadata.

Key Features:
------------
1. **Batch Transformation**: Transform multiple models at once
2. **Consistent Wrapping**: Maintains {"data": [...]} structure
3. **Pagination Support**: Automatic meta/links for paginated results
4. **Type Safety**: Generic type preservation

Educational Note:
----------------
Collections are more than just lists. They provide:
- Consistent API structure (always {"data": [...]})
- Pagination metadata (page, total, links)
- Resource-level transformation (each item uses JsonResource.to_array())

Laravel Comparison:
------------------
```php
// Laravel
return UserResource::collection($users);
// {"data": [{...}, {...}], "meta": {...}, "links": {...}}
```

```python
# FTF (this sprint)
return UserResource.collection(users).resolve()
# {"data": [{...}, {...}], "meta": {...}, "links": {...}}
```
"""

from typing import TYPE_CHECKING, Any, Generic, Iterable, Type, TypeVar

try:
    from fastapi import Request
except ImportError:
    Request = None  # type: ignore

from jtc.resources.core import MISSING, JsonResource

if TYPE_CHECKING:
    from fast_query.pagination import LengthAwarePaginator

T = TypeVar("T")


class ResourceCollection(Generic[T]):
    """
    Handle collections of resources.

    Transforms a list of models into a JSON response with consistent
    structure and optional pagination metadata.

    Type Parameter:
        T: The model type in the collection (e.g., User, Post)

    Usage:
        ```python
        # Basic collection
        users = await repo.all()
        return UserResource.collection(users).resolve()
        # {"data": [{...}, {...}]}

        # With pagination (bonus feature - requires Paginator from Sprint 2.2)
        users = await repo.paginate(page=1, per_page=10)
        return UserResource.collection(users).resolve()
        # {
        #   "data": [{...}, {...}],
        #   "meta": {"current_page": 1, "total": 100, ...},
        #   "links": {"first": "...", "last": "...", ...}
        # }
        ```

    Pattern: Adapter
    ---------------
    Adapts a list of models to a JSON structure with metadata.
    """

    def __init__(
        self,
        resource_class: Type[JsonResource[T]],
        resources: Iterable[T] | "LengthAwarePaginator[T]",
    ) -> None:
        """
        Initialize collection.

        Args:
            resource_class: The JsonResource subclass to use for transformation
            resources: Iterable of model instances OR LengthAwarePaginator

        Example:
            ```python
            # From regular list
            users = await repo.all()
            collection = UserResource.collection(users)

            # From paginator (Sprint 5.5)
            users = await repo.paginate(page=1, per_page=15)
            collection = UserResource.collection(users)
            # Automatically adds meta and links sections
            ```
        """
        self.resource_class = resource_class
        self.resources = resources

    def resolve(self, request: Request | None = None) -> dict[str, Any]:
        """
        Resolve the collection with data wrapper.

        This method:
        1. Detects if resources is a LengthAwarePaginator (Sprint 5.5)
        2. Transforms each resource using resource_class.to_array()
        3. Filters out MISSING values from each item
        4. Wraps in {"data": [...]}
        5. Adds pagination metadata if Paginator detected

        Args:
            request: Optional FastAPI request object

        Returns:
            Dictionary with "data" key and optional "meta"/"links"

        Example:
            ```python
            # Regular list (Sprint 4.2)
            users = await repo.all()
            collection = UserResource.collection(users)
            result = collection.resolve()
            # {"data": [{"id": 1, "name": "John"}, ...]}

            # Paginated (Sprint 5.5)
            users = await repo.paginate(page=2, per_page=15)
            collection = UserResource.collection(users)
            result = collection.resolve()
            # {
            #   "data": [{"id": 1, "name": "John"}, ...],
            #   "meta": {
            #     "current_page": 2,
            #     "last_page": 5,
            #     "per_page": 15,
            #     "total": 75,
            #     "from": 16,
            #     "to": 30
            #   },
            #   "links": {
            #     "first": "?page=1",
            #     "last": "?page=5",
            #     "next": "?page=3",
            #     "prev": "?page=1"
            #   }
            # }
            ```

        Educational Note:
        ----------------
        - Regular lists: Returns simple {"data": [...]}
        - Paginators: Returns {"data": [...], "meta": {...}, "links": {...}}
        - MISSING values are filtered out from each item (when() conditionals)
        """
        # Import here to avoid circular dependency
        from fast_query.pagination import LengthAwarePaginator

        # Detect if resources is a Paginator
        is_paginated = isinstance(self.resources, LengthAwarePaginator)

        # Get items list (from paginator.items or directly from iterable)
        items = self.resources.items if is_paginated else self.resources

        # Transform each resource
        data = [self.resource_class(resource).to_array(request) for resource in items]

        # Filter out MISSING values from each item
        # This handles when() conditionals that return MISSING
        filtered_data = [
            {k: v for k, v in item.items() if v is not MISSING} for item in data
        ]

        # Base response structure
        result: dict[str, Any] = {"data": filtered_data}

        # Add pagination metadata if using Paginator (Sprint 5.5)
        if is_paginated:
            paginator: LengthAwarePaginator[T] = self.resources  # type: ignore
            pagination_dict = paginator.to_dict()

            # Add meta section (current_page, last_page, per_page, total, from, to)
            result["meta"] = {
                "current_page": pagination_dict["current_page"],
                "last_page": pagination_dict["last_page"],
                "per_page": pagination_dict["per_page"],
                "total": pagination_dict["total"],
                "from": pagination_dict["from"],
                "to": pagination_dict["to"],
            }

            # Add links section (first, last, next, prev)
            result["links"] = pagination_dict["links"]

        return result


__all__ = [
    "ResourceCollection",
]
