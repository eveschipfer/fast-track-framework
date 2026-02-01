"""
User Model

Example model using SQLAlchemy 2.0 style with Mapped types and relationships.

This demonstrates:
    - SQLAlchemy 2.0 declarative style
    - Type-safe column definitions
    - TimestampMixin for auto-managed created_at/updated_at
    - SoftDeletesMixin for soft delete functionality
    - One-to-many relationships (HasMany: posts, comments)
    - Many-to-many relationship (BelongsToMany: roles)
    - lazy="raise" for async safety
    - TYPE_CHECKING imports to avoid circular dependencies

Mixins:
    TimestampMixin: Automatically manages created_at and updated_at (UTC)
    SoftDeletesMixin: Enables soft delete with deleted_at column

Relationships:
    posts: List[Post] (one-to-many) - User has many posts
    comments: List[Comment] (one-to-many) - User has many comments
    roles: List[Role] (many-to-many) - User has many roles

Example Usage:
    # Creating users (timestamps auto-set)
    from app.models import User
    from fast_query import get_session

    async with get_session() as session:
        user = User(
            name="Alice Smith",
            email="alice@example.com"
        )
        session.add(user)
        await session.commit()
        # user.created_at and user.updated_at are now set

    # With Repository Pattern (recommended)
    from fast_query import BaseRepository

    class UserRepository(BaseRepository[User]):
        def __init__(self, session: AsyncSession):
            super().__init__(session, User)

        async def find_by_email(self, email: str) -> Optional[User]:
            return await (
                self.query()
                .where(User.email == email)
                .first()
            )

    # Soft delete (sets deleted_at instead of removing)
    await repo.delete(user)
    assert user.is_deleted  # True

    # Eager loading relationships
    user = await (
        repo.query()
        .where(User.id == 1)
        .where(User.deleted_at.is_(None))  # Exclude soft-deleted
        .with_(User.posts, User.roles)  # Load posts and roles
        .first_or_fail()
    )

See: docs/relationships.md for relationship usage guide
"""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fast_query import Base, TimestampMixin, SoftDeletesMixin

if TYPE_CHECKING:
    from .comment import Comment
    from .post import Post
    from .role import Role


class User(Base, TimestampMixin, SoftDeletesMixin):
    """
    User model for authentication and user management.

    Inherits from:
        Base: SQLAlchemy declarative base
        TimestampMixin: Auto-managed created_at and updated_at (UTC)
        SoftDeletesMixin: Soft delete with deleted_at column

    Attributes:
        id: Primary key (auto-generated)
        name: User's full name
        email: Unique email address
        created_at: When user was created (auto-set, from TimestampMixin)
        updated_at: When user was last updated (auto-set, from TimestampMixin)
        deleted_at: When user was soft-deleted (None if active, from SoftDeletesMixin)
        is_deleted: Property returning True if soft-deleted (from SoftDeletesMixin)
        posts: Posts created by this user (one-to-many)
        comments: Comments created by this user (one-to-many)
        roles: Roles assigned to this user (many-to-many)

    Table:
        users

    Example:
        >>> user = User(name="Bob", email="bob@example.com")
        >>> print(user)
        User(id=None, name='Bob', email='bob@example.com')
        >>>
        >>> # Timestamps are auto-set on create
        >>> await repo.create(user)
        >>> assert user.created_at is not None
        >>> assert user.updated_at is not None
        >>>
        >>> # Soft delete
        >>> await repo.delete(user)
        >>> assert user.is_deleted  # True
    """

    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)

    # HasMany: User has many Posts (one-to-many)
    posts: Mapped[list["Post"]] = relationship(
        "Post",
        back_populates="author",
        lazy="raise",  # Prevent N+1 queries
    )

    # HasMany: User has many Comments (one-to-many)
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="author",
        lazy="raise",  # Prevent N+1 queries
    )

    # BelongsToMany: User has many Roles (many-to-many)
    # secondary="user_roles" references the association table
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="raise",  # Prevent N+1 queries
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"User(id={self.id}, name='{self.name}', email='{self.email}')"
