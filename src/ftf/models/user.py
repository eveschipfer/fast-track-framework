"""
User Model

Example model using SQLAlchemy 2.0 style with Mapped types.

This demonstrates:
    - SQLAlchemy 2.0 declarative style
    - Type-safe column definitions
    - Proper table naming convention
    - __repr__ for debugging

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
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ftf.database import Base


class User(Base):
    """
    User model for authentication and user management.

    Attributes:
        id: Primary key (auto-generated)
        name: User's full name
        email: Unique email address

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

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"User(id={self.id}, name='{self.name}', email='{self.email}')"
