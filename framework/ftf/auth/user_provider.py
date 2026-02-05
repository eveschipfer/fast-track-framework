"""
Database User Provider (Sprint 10)

This module provides a UserProvider that retrieves users from the database.

Architecture:
    - DatabaseUserProvider: Implements UserProvider contract
    - Uses Container to resolve UserRepository
    - Async database operations

Educational Note:
    This is the "Repository Pattern" from Sprint 8.0.
    The provider uses the Hybrid Repository to access user data.
"""

from typing import Optional

from ftf.auth.contracts import UserProvider, Credentials
from ftf.core import Container


class DatabaseUserProvider(UserProvider):
    """
    Database User Provider.

    This provider implements the UserProvider contract to retrieve
    users from the database using the Repository Pattern.

    Attributes:
        container: IoC Container for dependency injection

    Example:
        >>> provider = DatabaseUserProvider(container)
        >>> user = await provider.retrieve_by_id(123)
    """

    def __init__(self, container: Container) -> None:
        """
        Initialize User Provider.

        Args:
            container: IoC Container for dependency injection
        """
        self.container = container

    async def retrieve_by_id(self, identifier: int) -> Optional[dict]:
        """
        Retrieve user by ID.

        Args:
            identifier: User ID (from JWT payload)

        Returns:
            User as dict or None if not found

        Example:
            >>> user = await provider.retrieve_by_id(123)
            >>> print(user["email"])
        """
        from fast_query import BaseRepository
        from app.models import User

        user_repo: BaseRepository[User] = self.container.resolve(BaseRepository[User])

        try:
            user = await user_repo.find(identifier)
            if user is None:
                return None

            return {
                "id": user.id,
                "email": user.email,
                "name": user.name,
            }

        except Exception:
            return None

    async def retrieve_by_credentials(self, credentials: Credentials) -> Optional[dict]:
        """
        Retrieve user by credentials (email/password).

        Args:
            credentials: Email and password

        Returns:
            User as dict or None if not found

        Example:
            >>> from ftf.auth.contracts import Credentials
            >>> credentials = Credentials(email="test@example.com", password="secret")
            >>> user = await provider.retrieve_by_credentials(credentials)
            >>> if user and verify_password(credentials.password, user["password"]):
            ...         return user
        """
        from fast_query import BaseRepository
        from ftf.auth.crypto import verify_password
        from app.models import User

        user_repo: BaseRepository[User] = self.container.resolve(BaseRepository[User])

        try:
            users = await user_repo.all()

            for user in users:
                if user.email == credentials.email:
                    if verify_password(credentials.password, user.password):
                        return {
                            "id": user.id,
                            "email": user.email,
                            "name": user.name,
                            "password": user.password,
                        }

            return None

        except Exception:
            return None
