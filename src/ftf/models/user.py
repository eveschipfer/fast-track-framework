"""
User Model

Example model using SQLAlchemy 2.0 style with Mapped types and relationships.

This demonstrates:
    - SQLAlchemy 2.0 declarative style
    - Type-safe column definitions
    - One-to-many relationships (HasMany: posts, comments)
    - Many-to-many relationship (BelongsToMany: roles)
    - lazy="raise" for async safety
    - TYPE_CHECKING imports to avoid circular dependencies

Relationships:
    posts: List[Post] (one-to-many) - User has many posts
    comments: List[Comment] (one-to-many) - User has many comments
    roles: List[Role] (many-to-many) - User has many roles

Example Usage:
    # Creating users
    from ftf.models import User
    from ftf.database import get_session

    async with get_session() as session:
        user = User(
            name="Alice Smith",
            email="alice@example.com"
        )
        session.add(user)
        await session.commit()

    # With Repository Pattern (recommended)
    from ftf.database import BaseRepository

    class UserRepository(BaseRepository[User]):
        def __init__(self, session: AsyncSession):
            super().__init__(session, User)

        async def find_by_email(self, email: str) -> Optional[User]:
            stmt = select(User).where(User.email == email)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()

    # Eager loading relationships
    user = await (
        repo.query()
        .where(User.id == 1)
        .with_(User.posts, User.roles)  # Load posts and roles
        .first_or_fail()
    )

See: docs/relationships.md for relationship usage guide
"""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ftf.database import Base

if TYPE_CHECKING:
    from .comment import Comment
    from .post import Post
    from .role import Role


class User(Base):
    """
    User model for authentication and user management.

    Attributes:
        id: Primary key (auto-generated)
        name: User's full name
        email: Unique email address
        posts: Posts created by this user (one-to-many)
        comments: Comments created by this user (one-to-many)
        roles: Roles assigned to this user (many-to-many)

    Table:
        users

    Example:
        >>> user = User(name="Bob", email="bob@example.com")
        >>> print(user)
        User(id=None, name='Bob', email='bob@example.com')
    """

    __tablename__ = "users"

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
