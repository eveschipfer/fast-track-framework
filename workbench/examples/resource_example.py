"""
API Resources Example (Sprint 4.2)

This example demonstrates how to use the Fast Track Framework resource system
to transform database models into API responses.

Run with:
    poetry run python examples/resource_example.py
"""

import asyncio
from datetime import datetime
from typing import Any

from ftf.resources import JsonResource, MISSING

try:
    from fastapi import Request
except ImportError:
    Request = None  # type: ignore


# Mock User model (in real app, this would be from ftf.models)
class User:
    def __init__(
        self,
        id: int,
        name: str,
        email: str,
        password: str,
        is_admin: bool = False,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.is_admin = is_admin
        self.created_at = created_at or datetime.now()
        # Simulate relationship that may or may not be loaded
        self.__dict__["posts"] = None  # Not loaded by default


# Mock Post model
class Post:
    def __init__(self, id: int, title: str, content: str):
        self.id = id
        self.title = title
        self.content = content


# =============================================================================
# Example 1: Basic Resource
# =============================================================================


class UserResource(JsonResource[User]):
    """Transform User model to API response."""

    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        return {
            "id": self.resource.id,
            "name": self.resource.name,
            "email": self.resource.email,
            # Format datetime as ISO 8601 string
            "created_at": self.resource.created_at.isoformat(),
            # Never expose password
            # "password": NEVER!
        }


# =============================================================================
# Example 2: Conditional Attributes
# =============================================================================


class UserWithConditionalsResource(JsonResource[User]):
    """Resource with conditional fields based on permissions."""

    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        # Simulate checking if current user is admin
        is_admin = self.resource.is_admin

        return {
            "id": self.resource.id,
            "name": self.resource.name,
            # Only show email to admins
            "email": self.when(is_admin, self.resource.email),
            # Show admin badge only for admins
            "admin_badge": self.when(is_admin, "⭐ Admin"),
            # Show role with default value
            "role": self.when(is_admin, "admin", "user"),
            "created_at": self.resource.created_at.isoformat(),
        }


# =============================================================================
# Example 3: Relationship Loading
# =============================================================================


class PostResource(JsonResource[Post]):
    """Transform Post model to API response."""

    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        return {
            "id": self.resource.id,
            "title": self.resource.title,
            # Truncate content for list view
            "excerpt": self.resource.content[:100] + "..."
            if len(self.resource.content) > 100
            else self.resource.content,
        }


class UserWithPostsResource(JsonResource[User]):
    """Resource that conditionally includes posts relationship."""

    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        # Get posts if loaded
        posts = self.when_loaded("posts")

        return {
            "id": self.resource.id,
            "name": self.resource.name,
            "email": self.resource.email,
            # Only include posts if they were eager-loaded
            # If not loaded, this key won't appear in the response
            "posts": PostResource.collection(posts).resolve()["data"]
            if posts is not MISSING
            else MISSING,
            "created_at": self.resource.created_at.isoformat(),
        }


# =============================================================================
# Example 4: Computed Fields
# =============================================================================


class UserWithComputedResource(JsonResource[User]):
    """Resource with computed/derived fields."""

    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        return {
            "id": self.resource.id,
            "name": self.resource.name,
            "email": self.resource.email,
            # Computed field: initials
            "initials": "".join([n[0].upper() for n in self.resource.name.split()]),
            # Computed field: member duration
            "member_for_days": (datetime.now() - self.resource.created_at).days,
            # Computed field: email domain
            "email_domain": self.resource.email.split("@")[1],
        }


# =============================================================================
# Main Examples
# =============================================================================


async def main() -> None:
    print("=" * 70)
    print("Fast Track Framework - API Resources Examples")
    print("=" * 70)
    print()

    # Create sample users
    user1 = User(
        id=1,
        name="John Doe",
        email="john@example.com",
        password="hashed_password",
        is_admin=False,
    )

    user2 = User(
        id=2,
        name="Jane Smith",
        email="jane@example.com",
        password="hashed_password",
        is_admin=True,
    )

    # Example 1: Basic Resource
    print("-" * 70)
    print("Example 1: Basic Resource Transformation")
    print("-" * 70)
    result = UserResource.make(user1).resolve()
    print("Input: User(id=1, name='John Doe', email='john@example.com', password='...')")
    print(f"Output: {result}")
    print("✓ Password is hidden")
    print("✓ Datetime is formatted as ISO 8601")
    print()

    # Example 2: Collection
    print("-" * 70)
    print("Example 2: Resource Collection")
    print("-" * 70)
    users = [user1, user2]
    result = UserResource.collection(users).resolve()
    print(f"Input: List of {len(users)} users")
    print(f"Output: {result}")
    print("✓ All users transformed")
    print("✓ Wrapped in 'data' key")
    print()

    # Example 3: Conditional Attributes
    print("-" * 70)
    print("Example 3: Conditional Attributes (Regular User)")
    print("-" * 70)
    result = UserWithConditionalsResource.make(user1).resolve()
    print(f"User: {user1.name} (is_admin={user1.is_admin})")
    print(f"Output: {result}")
    print("✓ Email is hidden (not admin)")
    print("✓ Admin badge is hidden")
    print("✓ Role is 'user'")
    print()

    print("-" * 70)
    print("Example 4: Conditional Attributes (Admin User)")
    print("-" * 70)
    result = UserWithConditionalsResource.make(user2).resolve()
    print(f"User: {user2.name} (is_admin={user2.is_admin})")
    print(f"Output: {result}")
    print("✓ Email is visible (admin)")
    print("✓ Admin badge is shown")
    print("✓ Role is 'admin'")
    print()

    # Example 5: Relationship Loading
    print("-" * 70)
    print("Example 5: Relationship Loading (Without Eager Load)")
    print("-" * 70)
    # Posts not loaded
    result = UserWithPostsResource.make(user1).resolve()
    print(f"User: {user1.name}")
    print(f"Output: {result}")
    print("✓ Posts key is not present (relationship not loaded)")
    print()

    print("-" * 70)
    print("Example 6: Relationship Loading (With Eager Load)")
    print("-" * 70)
    # Simulate eager loading
    user1.__dict__["posts"] = [
        Post(id=1, title="First Post", content="This is my first post!"),
        Post(id=2, title="Second Post", content="Another great post with more content..."),
    ]
    result = UserWithPostsResource.make(user1).resolve()
    print(f"User: {user1.name}")
    print(f"Output: {result}")
    print("✓ Posts are included (relationship was loaded)")
    print()

    # Example 7: Computed Fields
    print("-" * 70)
    print("Example 7: Computed Fields")
    print("-" * 70)
    result = UserWithComputedResource.make(user1).resolve()
    print(f"Input: {user1.name} (email: {user1.email})")
    print(f"Output: {result}")
    print("✓ Initials computed from name")
    print("✓ Member duration calculated")
    print("✓ Email domain extracted")
    print()

    print("=" * 70)
    print("✓ All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
