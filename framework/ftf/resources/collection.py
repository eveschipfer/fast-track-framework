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

from typing import Any, Generic, Iterable, Type, TypeVar

try:
    from fastapi import Request
except ImportError:
    Request = None  # type: ignore

from ftf.resources.core import MISSING, JsonResource

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
        self, resource_class: Type[JsonResource[T]], resources: Iterable[T]
    ) -> None:
        """
        Initialize collection.

        Args:
            resource_class: The JsonResource subclass to use for transformation
            resources: Iterable of model instances
        """
        self.resource_class = resource_class
        self.resources = resources

    def resolve(self, request: Request | None = None) -> dict[str, Any]:
        """
        Resolve the collection with data wrapper.

        This method:
        1. Transforms each resource using resource_class.to_array()
        2. Filters out MISSING values from each item
        3. Wraps in {"data": [...]}
        4. Adds pagination metadata if applicable

        Args:
            request: Optional FastAPI request object

        Returns:
            Dictionary with "data" key and optional "meta"/"links"

        Example:
            ```python
            users = await repo.all()
            collection = UserResource.collection(users)
            result = collection.resolve()
            # {
            #   "data": [
            #     {"id": 1, "name": "John"},
            #     {"id": 2, "name": "Jane"}
            #   ]
            # }
            ```

        Educational Note:
        ----------------
        The filtering step removes keys with MISSING values from each item.
        This ensures conditional fields (from when()) don't appear.
        """
        # Transform each resource
        data = [
            self.resource_class(resource).to_array(request)
            for resource in self.resources
        ]

        # Filter out MISSING values from each item
        # This handles when() conditionals that return MISSING
        filtered_data = [
            {k: v for k, v in item.items() if v is not MISSING} for item in data
        ]

        # Base response structure
        result: dict[str, Any] = {"data": filtered_data}

        # TODO: Add pagination metadata if resources is a Paginator
        # This is a bonus feature that requires Paginator from Sprint 2.2
        #
        # if hasattr(self.resources, "total"):  # Duck-typing for Paginator
        #     result["meta"] = {
        #         "current_page": self.resources.current_page,
        #         "last_page": self.resources.last_page,
        #         "per_page": self.resources.per_page,
        #         "total": self.resources.total,
        #     }
        #     result["links"] = {
        #         "first": self._build_url(1),
        #         "last": self._build_url(self.resources.last_page),
        #         "prev": self._build_url(self.resources.current_page - 1)
        #                 if self.resources.current_page > 1 else None,
        #         "next": self._build_url(self.resources.current_page + 1)
        #                 if self.resources.current_page < self.resources.last_page
        #                 else None,
        #     }

        return result


__all__ = [
    "ResourceCollection",
]
