"""
UserRepository

Extends BaseRepository with user-specific query helpers.

Custom methods:
    find_by_email(email):          Lookup by unique email — returns User | None.
    find_by_email_or_fail(email):  Same but raises RecordNotFound if missing.
    find_by_reset_token(token):    Lookup by password-reset token.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fast_query import BaseRepository, RecordNotFound
from app.models import User


class UserRepository(BaseRepository[User]):
    """
    Repository for User database operations.

    Inherits all BaseRepository generics (find, find_or_fail, all, create,
    update, delete, query) and adds user-specific methods.

    Example:
        >>> user = await repo.find_by_email("alice@example.com")
        >>> user = await repo.find_or_fail(1)
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by their unique email address.

        Args:
            email: The email to search for (case-sensitive as stored in DB).

        Returns:
            User instance if found, None otherwise.
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_email_or_fail(self, email: str) -> User:
        """
        Find a user by email or raise RecordNotFound.

        Args:
            email: The email to search for.

        Returns:
            User instance.

        Raises:
            RecordNotFound: If no user with that email exists.
        """
        user = await self.find_by_email(email)
        if user is None:
            raise RecordNotFound(f"User with email '{email}' not found")
        return user

    async def find_by_reset_token(self, token: str) -> Optional[User]:
        """
        Find a user by their password-reset token.

        Args:
            token: The reset token stored on the user record.

        Returns:
            User instance if found, None otherwise.
        """
        stmt = select(User).where(User.reset_token == token)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
