"""
API Resources - Core Abstraction (Sprint 4.2)

This module provides a transformation layer between database models and JSON
responses, inspired by Laravel API Resources.

Key Concepts:
-----------
1. **Decoupling**: Separate database schema from API response format
2. **Transformation**: Control exactly what data is exposed and how it's formatted
3. **Conditional Attributes**: Include fields based on conditions (permissions, etc.)
4. **Relationship Control**: Only include loaded relationships (avoid N+1)

Design Patterns:
---------------
- **Adapter Pattern**: Transforms models to API-specific format
- **Builder Pattern**: Fluent API with make() and collection()
- **Template Method**: Abstract to_array() for subclass customization

Educational Note:
----------------
This solves a common problem: Your database schema rarely matches your API schema.
You might want to:
- Rename fields (user_id -> userId in camelCase APIs)
- Format dates (ISO 8601 strings instead of datetime objects)
- Hide sensitive fields (password, tokens)
- Add computed fields (full_name from first_name + last_name)
- Conditionally include fields based on permissions

Laravel Comparison:
------------------
```php
// Laravel
class UserResource extends JsonResource
{
    public function toArray($request)
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'email' => $this->when($request->user()->isAdmin(), $this->email),
            'posts' => PostResource::collection($this->whenLoaded('posts')),
        ];
    }
}
```

```python
# FTF (this sprint)
class UserResource(JsonResource[User]):
    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        return {
            "id": self.resource.id,
            "name": self.resource.name,
            "email": self.when(is_admin(request), self.resource.email),
            "posts": PostResource.collection(self.when_loaded("posts")),
        }
```
"""

from typing import Any, Generic, Iterable, TypeVar, Final

try:
    from fastapi import Request
except ImportError:
    Request = None  # type: ignore


# Sentinel value for missing/conditional attributes
MISSING: Final = object()

T = TypeVar("T")


class JsonResource(Generic[T]):
    """
    Base class for API Resources.

    Transforms database models into JSON-serializable dictionaries with
    control over field inclusion, formatting, and relationships.

    Type Parameter:
        T: The model type being transformed (e.g., User, Post, Comment)

    Usage:
        ```python
        class UserResource(JsonResource[User]):
            def to_array(self, request: Request | None = None) -> dict[str, Any]:
                return {
                    "id": self.resource.id,
                    "name": self.resource.name,
                    "email": self.resource.email,
                    "created_at": self.resource.created_at.isoformat(),
                }

        # Single resource
        user = await repo.find(1)
        return UserResource.make(user).resolve()
        # Returns: {"data": {"id": 1, "name": "John", ...}}

        # Collection
        users = await repo.all()
        return UserResource.collection(users).resolve()
        # Returns: {"data": [{...}, {...}]}
        ```

    Pattern: Template Method
    ------------------------
    The to_array() method is the "template" that subclasses must implement.
    The resolve() method is the "algorithm" that wraps the result.
    """

    def __init__(self, resource: T) -> None:
        """
        Initialize resource with a model instance.

        Args:
            resource: The model instance to transform (User, Post, etc.)
        """
        self.resource = resource

    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        """
        Transform resource to dictionary (abstract method).

        This is the main method you override in subclasses to define
        how your model should be serialized.

        Args:
            request: Optional FastAPI request object for conditional logic

        Returns:
            Dictionary representation of the resource

        Raises:
            NotImplementedError: If not implemented by subclass

        Example:
            ```python
            def to_array(self, request: Request | None = None) -> dict[str, Any]:
                return {
                    "id": self.resource.id,
                    "name": self.resource.name,
                    "admin": self.when(is_admin(request), True),
                }
            ```
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement to_array() method"
        )

    def resolve(self, request: Request | None = None) -> dict[str, Any]:
        """
        Resolve the resource with data wrapper.

        This method:
        1. Calls to_array() to get the transformed data
        2. Filters out MISSING values (from when() conditionals)
        3. Wraps result in {"data": ...} for consistent API structure

        Args:
            request: Optional FastAPI request object

        Returns:
            Wrapped dictionary with "data" key

        Example:
            ```python
            resource = UserResource.make(user)
            result = resource.resolve()
            # {"data": {"id": 1, "name": "John"}}
            ```

        Educational Note:
        ----------------
        The "data" wrapper is a common API pattern that:
        - Provides consistency (all endpoints return {data: ...})
        - Allows adding metadata (meta, links, etc.)
        - Makes it clear what's the actual payload vs metadata
        """
        data = self.to_array(request)

        # Filter out MISSING sentinel values
        # These come from when() calls that return MISSING
        filtered_data = {k: v for k, v in data.items() if v is not MISSING}

        return {"data": filtered_data}

    @classmethod
    def make(cls, resource: T) -> "JsonResource[T]":
        """
        Factory method to create a resource instance.

        This provides a fluent API for creating resources.

        Args:
            resource: The model instance to transform

        Returns:
            Resource instance

        Example:
            ```python
            # Instead of: UserResource(user).resolve()
            # Use: UserResource.make(user).resolve()
            return UserResource.make(user).resolve()
            ```

        Pattern: Factory Method
        ----------------------
        This is a static factory that creates instances of the resource.
        It provides a cleaner API than calling the constructor directly.
        """
        return cls(resource)

    @classmethod
    def collection(cls, resources: Iterable[T]) -> "ResourceCollection[T]":
        """
        Create a resource collection.

        Transforms a list/iterable of models into a collection of resources.

        Args:
            resources: Iterable of model instances

        Returns:
            ResourceCollection instance

        Example:
            ```python
            users = await repo.all()
            return UserResource.collection(users).resolve()
            # {"data": [{...}, {...}, ...]}
            ```

        Educational Note:
        ----------------
        This delegates to ResourceCollection which handles:
        - Transforming each item
        - Maintaining the "data" wrapper
        - Adding pagination metadata (if applicable)
        """
        from ftf.resources.collection import ResourceCollection

        return ResourceCollection(cls, resources)

    def when(self, condition: bool, value: Any, default: Any = MISSING) -> Any:
        """
        Conditionally include a value.

        If condition is True, returns value. Otherwise returns default (MISSING).
        MISSING values are filtered out in resolve(), so the key won't appear
        in the final JSON.

        Args:
            condition: Boolean condition to evaluate
            value: Value to include if condition is True
            default: Value to include if condition is False (default: MISSING)

        Returns:
            value if condition else default

        Example:
            ```python
            def to_array(self, request: Request | None = None) -> dict[str, Any]:
                is_admin = request and hasattr(request.state, "user") and request.state.user.is_admin

                return {
                    "id": self.resource.id,
                    "name": self.resource.name,
                    # Only include email for admins
                    "email": self.when(is_admin, self.resource.email),
                    # Include with default value
                    "role": self.when(is_admin, "admin", "user"),
                }

            # For admin: {"data": {"id": 1, "name": "John", "email": "...", "role": "admin"}}
            # For user:  {"data": {"id": 1, "name": "John", "role": "user"}}
            ```

        Educational Note:
        ----------------
        This is safer than manual if/else because:
        1. Keys are automatically removed (not set to null)
        2. Cleaner syntax (declarative vs imperative)
        3. Works with nested resources
        """
        return value if condition else default

    def when_loaded(self, relationship: str) -> Any:
        """
        Include relationship only if it's already loaded.

        This prevents N+1 queries by only including relationships that
        were eager-loaded. If the relationship isn't loaded, returns MISSING
        (which gets filtered out in resolve()).

        Args:
            relationship: Name of the relationship attribute

        Returns:
            Relationship value if loaded, MISSING otherwise

        Example:
            ```python
            class UserResource(JsonResource[User]):
                def to_array(self, request: Request | None = None) -> dict[str, Any]:
                    return {
                        "id": self.resource.id,
                        "name": self.resource.name,
                        # Only include if posts were eager-loaded
                        "posts": PostResource.collection(
                            self.when_loaded("posts")
                        ),
                    }

            # With eager loading
            user = await repo.find_with_posts(1)
            result = UserResource.make(user).resolve()
            # {"data": {"id": 1, "name": "John", "posts": [...]}}

            # Without eager loading
            user = await repo.find(1)
            result = UserResource.make(user).resolve()
            # {"data": {"id": 1, "name": "John"}}  (no posts key)
            ```

        Implementation Details:
        ----------------------
        For SQLAlchemy models, loaded relationships are in __dict__.
        Unloaded relationships are not in __dict__ (lazy loading).
        This check prevents triggering lazy loads.
        """
        # Check if relationship is loaded (SQLAlchemy pattern)
        if hasattr(self.resource, "__dict__"):
            # SQLAlchemy models store loaded relationships in __dict__
            # Unloaded relationships are NOT in __dict__ (lazy loading proxies)
            if relationship in self.resource.__dict__:
                value = getattr(self.resource, relationship)
                # Even if in __dict__, value might be None (null relationship)
                # We return None in that case (not MISSING) so it appears as null
                return value if value is not None else MISSING
        elif hasattr(self.resource, relationship):
            # For non-SQLAlchemy objects (Pydantic, dataclasses, etc.)
            value = getattr(self.resource, relationship, None)
            if value is not None:
                return value

        # Relationship not loaded
        return MISSING


__all__ = [
    "JsonResource",
    "MISSING",
]
