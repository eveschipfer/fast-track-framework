"""
Role Model

Example model demonstrating many-to-many relationship pattern.

This demonstrates:
    - BelongsToMany relationship using association table
    - secondary parameter for pivot/junction table
    - lazy="raise" for async safety
    - TYPE_CHECKING imports

Relationships:
    users: List[User] (many-to-many) - Each role has many users,
                                       each user has many roles

Association Table:
    user_roles - Pivot table connecting users and roles

Example Usage:
    # Eager load users with their roles
    from ftf.models import User

    class UserRepository(BaseRepository[User]):
        async def get_with_roles(self, user_id: int) -> User:
            return await (
                self.query()
                .where(User.id == user_id)
                .with_(User.roles)  # Eager load roles
                .first_or_fail()
            )

    # Access many-to-many relationship
    user = await repo.get_with_roles(1)
    for role in user.roles:
        print(role.name)  # OK! Roles loaded

    # Find users by role
    class UserRepository(BaseRepository[User]):
        async def find_admins(self) -> list[User]:
            return await (
                self.query()
                .join(User.roles)
                .where(Role.name == "admin")
                .with_(User.roles)  # Include roles in result
                .get()
            )

See: docs/relationships.md for many-to-many relationship guide
"""

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fast_query import Base

if TYPE_CHECKING:
    from .user import User

# Association table (pivot table) for many-to-many relationship
# This is a pure association table (no additional columns beyond foreign keys)
# For more complex pivot tables with extra data, use a proper model class
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)


class Role(Base):
    """
    User role model for authorization.

    Attributes:
        id: Primary key (auto-generated)
        name: Role name (unique, e.g., "admin", "moderator", "user")
        description: Role description
        users: Users who have this role (many-to-many)

    Table:
        roles

    Example:
        >>> role = Role(
        ...     name="admin",
        ...     description="Administrator with full access"
        ... )
        >>> print(role)
        Role(id=None, name='admin')
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str] = mapped_column(String(200))

    # BelongsToMany: Role belongs to many Users (many-to-many)
    # secondary parameter specifies the association/pivot table
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
        lazy="raise",  # Prevent N+1 queries
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Role(id={self.id}, name='{self.name}')"
