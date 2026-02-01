"""
Tests for API Resources (Sprint 4.2)

This test suite covers:
- JsonResource base class
- ResourceCollection
- Conditional attributes (when)
- Relationship loading (when_loaded)
- Data wrapping
- Type safety
"""

from datetime import datetime
from typing import Any

import pytest

from ftf.resources import JsonResource, ResourceCollection, MISSING


# -------------------------------------------------------------------------
# Test Models (Mock SQLAlchemy-like models)
# -------------------------------------------------------------------------


class User:
    """Mock User model."""

    def __init__(
        self,
        id: int,
        name: str,
        email: str,
        is_admin: bool = False,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.name = name
        self.email = email
        self.is_admin = is_admin
        self.created_at = created_at or datetime(2026, 1, 1, 12, 0, 0)
        # Simulate SQLAlchemy relationship loading
        self.__dict__["posts"] = None  # Not loaded by default


class Post:
    """Mock Post model."""

    def __init__(self, id: int, title: str, user_id: int):
        self.id = id
        self.title = title
        self.user_id = user_id


# -------------------------------------------------------------------------
# Test Resources
# -------------------------------------------------------------------------


class UserResource(JsonResource[User]):
    """Basic user resource."""

    def to_array(self, request: Any = None) -> dict[str, Any]:
        return {
            "id": self.resource.id,
            "name": self.resource.name,
            "email": self.resource.email,
        }


class UserWithConditionalsResource(JsonResource[User]):
    """Resource with conditional fields."""

    def to_array(self, request: Any = None) -> dict[str, Any]:
        return {
            "id": self.resource.id,
            "name": self.resource.name,
            # Conditional: only show email for admins
            "email": self.when(self.resource.is_admin, self.resource.email),
            # Conditional with default
            "role": self.when(self.resource.is_admin, "admin", "user"),
        }


class PostResource(JsonResource[Post]):
    """Basic post resource."""

    def to_array(self, request: Any = None) -> dict[str, Any]:
        return {
            "id": self.resource.id,
            "title": self.resource.title,
        }


class UserWithPostsResource(JsonResource[User]):
    """Resource with relationship."""

    def to_array(self, request: Any = None) -> dict[str, Any]:
        posts = self.when_loaded("posts")

        return {
            "id": self.resource.id,
            "name": self.resource.name,
            # Only include if loaded
            "posts": PostResource.collection(posts).resolve()["data"]
            if posts is not MISSING
            else MISSING,
        }


# -------------------------------------------------------------------------
# JsonResource Tests
# -------------------------------------------------------------------------


def test_resource_make() -> None:
    """Resource.make() should create instance."""
    user = User(id=1, name="John Doe", email="john@example.com")

    resource = UserResource.make(user)

    assert isinstance(resource, UserResource)
    assert resource.resource == user


def test_resource_to_array() -> None:
    """Resource.to_array() should transform model."""
    user = User(id=1, name="John Doe", email="john@example.com")

    resource = UserResource(user)
    data = resource.to_array()

    assert data == {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
    }


def test_resource_resolve_wraps_data() -> None:
    """Resource.resolve() should wrap data in 'data' key."""
    user = User(id=1, name="John Doe", email="john@example.com")

    resource = UserResource.make(user)
    result = resource.resolve()

    assert "data" in result
    assert result["data"]["id"] == 1
    assert result["data"]["name"] == "John Doe"


def test_resource_not_implemented_error() -> None:
    """Resource without to_array() should raise NotImplementedError."""

    class IncompleteResource(JsonResource[User]):
        pass  # No to_array() implementation

    user = User(id=1, name="John", email="john@example.com")
    resource = IncompleteResource(user)

    with pytest.raises(NotImplementedError) as exc:
        resource.to_array()

    assert "must implement to_array()" in str(exc.value)


# -------------------------------------------------------------------------
# Conditional Attributes Tests
# -------------------------------------------------------------------------


def test_when_true_returns_value() -> None:
    """when(True, value) should return value."""
    user = User(id=1, name="John", email="john@example.com", is_admin=True)
    resource = UserResource(user)

    result = resource.when(True, "included")

    assert result == "included"


def test_when_false_returns_missing() -> None:
    """when(False, value) should return MISSING."""
    user = User(id=1, name="John", email="john@example.com")
    resource = UserResource(user)

    result = resource.when(False, "excluded")

    assert result is MISSING


def test_when_false_with_default_returns_default() -> None:
    """when(False, value, default) should return default."""
    user = User(id=1, name="John", email="john@example.com")
    resource = UserResource(user)

    result = resource.when(False, "excluded", "default_value")

    assert result == "default_value"


def test_conditional_field_included_when_true() -> None:
    """Conditional field should be included when condition is True."""
    user = User(id=1, name="John", email="john@example.com", is_admin=True)

    resource = UserWithConditionalsResource.make(user)
    result = resource.resolve()

    assert result["data"]["email"] == "john@example.com"
    assert result["data"]["role"] == "admin"


def test_conditional_field_excluded_when_false() -> None:
    """Conditional field should be excluded when condition is False."""
    user = User(id=1, name="John", email="john@example.com", is_admin=False)

    resource = UserWithConditionalsResource.make(user)
    result = resource.resolve()

    # Email should not be present (MISSING was filtered out)
    assert "email" not in result["data"]
    # Role should use default value
    assert result["data"]["role"] == "user"


# -------------------------------------------------------------------------
# Relationship Loading Tests
# -------------------------------------------------------------------------


def test_when_loaded_not_loaded_returns_missing() -> None:
    """when_loaded() should return MISSING if relationship not loaded."""
    user = User(id=1, name="John", email="john@example.com")
    # posts not loaded (not in __dict__)
    user.__dict__.pop("posts", None)

    resource = UserResource(user)
    result = resource.when_loaded("posts")

    assert result is MISSING


def test_when_loaded_loaded_returns_value() -> None:
    """when_loaded() should return value if relationship is loaded."""
    user = User(id=1, name="John", email="john@example.com")
    # Simulate eager loading
    user.__dict__["posts"] = [
        Post(id=1, title="Post 1", user_id=1),
        Post(id=2, title="Post 2", user_id=1),
    ]

    resource = UserResource(user)
    result = resource.when_loaded("posts")

    assert result is not MISSING
    assert len(result) == 2
    assert result[0].title == "Post 1"


def test_resource_without_loaded_relationship() -> None:
    """Resource should not include relationship if not loaded."""
    user = User(id=1, name="John", email="john@example.com")
    # posts not loaded
    user.__dict__.pop("posts", None)

    resource = UserWithPostsResource.make(user)
    result = resource.resolve()

    # Posts key should not be present
    assert "posts" not in result["data"]


def test_resource_with_loaded_relationship() -> None:
    """Resource should include relationship if loaded."""
    user = User(id=1, name="John", email="john@example.com")
    # Simulate eager loading
    user.__dict__["posts"] = [
        Post(id=1, title="Post 1", user_id=1),
        Post(id=2, title="Post 2", user_id=1),
    ]

    resource = UserWithPostsResource.make(user)
    result = resource.resolve()

    # Posts should be present
    assert "posts" in result["data"]
    assert len(result["data"]["posts"]) == 2
    assert result["data"]["posts"][0]["title"] == "Post 1"


# -------------------------------------------------------------------------
# ResourceCollection Tests
# -------------------------------------------------------------------------


def test_resource_collection() -> None:
    """Resource.collection() should create ResourceCollection."""
    users = [
        User(id=1, name="John", email="john@example.com"),
        User(id=2, name="Jane", email="jane@example.com"),
    ]

    collection = UserResource.collection(users)

    assert isinstance(collection, ResourceCollection)


def test_collection_resolve_transforms_all() -> None:
    """Collection.resolve() should transform all resources."""
    users = [
        User(id=1, name="John", email="john@example.com"),
        User(id=2, name="Jane", email="jane@example.com"),
    ]

    result = UserResource.collection(users).resolve()

    assert "data" in result
    assert len(result["data"]) == 2
    assert result["data"][0]["name"] == "John"
    assert result["data"][1]["name"] == "Jane"


def test_collection_empty_list() -> None:
    """Collection with empty list should return empty data array."""
    users: list[User] = []

    result = UserResource.collection(users).resolve()

    assert result == {"data": []}


def test_collection_filters_missing_values() -> None:
    """Collection should filter out MISSING values from each item."""
    users = [
        User(id=1, name="John", email="john@example.com", is_admin=False),
        User(id=2, name="Jane", email="jane@example.com", is_admin=True),
    ]

    result = UserWithConditionalsResource.collection(users).resolve()

    # First user (not admin) should not have email
    assert "email" not in result["data"][0]
    # Second user (admin) should have email
    assert "email" in result["data"][1]
    assert result["data"][1]["email"] == "jane@example.com"


# -------------------------------------------------------------------------
# Type Safety Tests
# -------------------------------------------------------------------------


def test_resource_generic_type() -> None:
    """Resource should preserve generic type."""
    user = User(id=1, name="John", email="john@example.com")

    resource: JsonResource[User] = UserResource.make(user)

    # Type checker should accept this
    assert resource.resource.id == 1
    assert resource.resource.name == "John"


def test_collection_generic_type() -> None:
    """Collection should preserve generic type."""
    users = [User(id=1, name="John", email="john@example.com")]

    collection: ResourceCollection[User] = UserResource.collection(users)

    # Type checker should accept this
    assert collection.resource_class == UserResource


# -------------------------------------------------------------------------
# MISSING Sentinel Tests
# -------------------------------------------------------------------------


def test_missing_is_singleton() -> None:
    """MISSING should be a singleton object."""
    from ftf.resources.core import MISSING as MISSING2

    assert MISSING is MISSING2


def test_missing_not_none() -> None:
    """MISSING should not be None."""
    assert MISSING is not None


def test_missing_not_equal_to_anything() -> None:
    """MISSING should only equal itself (identity check)."""
    assert MISSING is MISSING
    assert MISSING is not False
    assert MISSING is not 0
    assert MISSING is not ""
    assert MISSING is not []


# -------------------------------------------------------------------------
# Integration Tests
# -------------------------------------------------------------------------


def test_full_transformation_pipeline() -> None:
    """Full pipeline: Model -> Resource -> JSON."""
    # Create user with eager-loaded posts
    user = User(
        id=1,
        name="John Doe",
        email="john@example.com",
        is_admin=True,
        created_at=datetime(2026, 1, 1, 12, 0, 0),
    )
    user.__dict__["posts"] = [
        Post(id=1, title="First Post", user_id=1),
        Post(id=2, title="Second Post", user_id=1),
    ]

    # Transform
    result = UserWithPostsResource.make(user).resolve()

    # Verify structure
    assert "data" in result
    data = result["data"]
    assert data["id"] == 1
    assert data["name"] == "John Doe"
    assert "posts" in data
    assert len(data["posts"]) == 2
    assert data["posts"][0]["title"] == "First Post"


def test_collection_transformation_pipeline() -> None:
    """Full pipeline: Models -> Collection -> JSON."""
    users = [
        User(id=1, name="John", email="john@example.com", is_admin=True),
        User(id=2, name="Jane", email="jane@example.com", is_admin=False),
    ]

    result = UserWithConditionalsResource.collection(users).resolve()

    assert "data" in result
    assert len(result["data"]) == 2
    # Admin user has email
    assert result["data"][0]["email"] == "john@example.com"
    assert result["data"][0]["role"] == "admin"
    # Regular user doesn't have email
    assert "email" not in result["data"][1]
    assert result["data"][1]["role"] == "user"
