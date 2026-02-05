"""
Authentication Contracts (Sprint 10)

This module defines abstract interfaces for the Guard Pattern.
Inspired by Laravel's authentication system.

Architecture:
    - AuthManager: Main entry point, manages multiple Guards
    - Guard Interface: Defines contract for authentication drivers
    - UserProvider: Defines how to retrieve users from data source

Educational Note:
    This is the "Laravel-inspired" Guard Pattern from Sprint 10.
    Unlike the old get_current_user() which was hardcoded to JWT only,
    this pattern allows switching between multiple authentication methods:
    - JwtGuard: Stateless (APIs)
    - SessionGuard: Stateful (Web apps)
    - TokenGuard: API tokens
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel


class Credentials(BaseModel):
    """
    Authentication credentials schema.

    This Pydantic model defines the contract for authentication inputs,
    providing type safety and validation.

    Attributes:
        email: User email or username
        password: User password
        token: API token (optional, for token-based auth)
    """

    email: str
    password: str
    token: Optional[str] = None


class UserProvider(ABC):
    """
    Abstract User Provider interface.

    Defines how to retrieve users from your data source.
    This abstracts the user model from authentication logic.

    Methods:
        retrieve_by_id: Fetch user by ID (from JWT payload)
        retrieve_by_credentials: Fetch user by email/password (for login)
        validate_credentials: Check if credentials are valid

    Example Implementation:
        >>> class DatabaseUserProvider(UserProvider):
        ...     def __init__(self, user_repo: UserRepository):
        ...         self.repo = user_repo
        ...
        ...     async def retrieve_by_id(self, user_id: int):
        ...         return await self.repo.find(user_id)
    """

    @abstractmethod
    async def retrieve_by_id(self, identifier: Any) -> Optional[Any]:
        """
        Retrieve user by identifier.

        Used by JWT Guard after decoding token payload.

        Args:
            identifier: User ID from JWT payload (typically int)

        Returns:
            User instance or None if not found

        Raises:
            Any: Provider-specific errors
        """
        pass

    @abstractmethod
    async def retrieve_by_credentials(self, credentials: Credentials) -> Optional[Any]:
        """
        Retrieve user by credentials.

        Used by login endpoints to validate email/password.

        Args:
            credentials: Email and password (or token)

        Returns:
            User instance if credentials valid, None otherwise

        Raises:
            Any: Provider-specific errors
        """
        pass


class Guard(ABC):
    """
    Abstract Guard interface.

    Defines the contract for authentication drivers.
    Guards authenticate requests and provide the authenticated user.

    Methods:
        user: Get authenticated user for current request
        check: Verify user has credentials (for login)
        id: Get user ID (for authorization)
        validate: Validate credentials
        authenticate: Authenticate and set user

    Example Implementation:
        >>> class JwtGuard(Guard):
        ...     def __init__(self, user_provider: UserProvider, jwt_secret: str):
        ...         self.user_provider = user_provider
        ...         self.jwt_secret = jwt_secret
        ...
        ...     async def user(self):
        ...         # Extract and validate JWT
        ...         return await self.user_provider.retrieve_by_id(user_id)
    """

    @abstractmethod
    async def user(self) -> Optional[Any]:
        """
        Get authenticated user for current request.

        This is the primary method used by route handlers.

        Returns:
            User instance or None if not authenticated

        Raises:
            Any: Guard-specific authentication errors
        """
        pass

    @abstractmethod
    async def check(self, credentials: Credentials) -> bool:
        """
        Check if credentials are valid.

        Used by login endpoints to validate email/password.

        Args:
            credentials: Email and password (or token)

        Returns:
            bool: True if valid, False otherwise

        Raises:
            Any: Guard-specific errors
        """
        pass

    @abstractmethod
    async def id(self) -> Optional[Any]:
        """
        Get authenticated user ID.

        Used by authorization system (Gates, Policies).

        Returns:
            User ID or None if not authenticated

        Example:
            >>> user_id = await guard.id()
            >>> if not await Gate.allows(user_id, "delete-post"):
            ...     raise Forbidden("Cannot delete post")
        """
        pass

    @abstractmethod
    async def validate(self, credentials: Credentials) -> bool:
        """
        Validate credentials (alias for check).

        This method provides a more explicit name for credential validation.

        Args:
            credentials: Email and password (or token)

        Returns:
            bool: True if valid, False otherwise
        """
        pass

    @abstractmethod
    async def authenticate(self, credentials: Credentials) -> Any:
        """
        Authenticate and set user.

        This is called by login endpoints after successful credential validation.

        Args:
            credentials: Valid email and password (or token)

        Returns:
            User instance or token (depending on guard type)

        Example:
            >>> # JWT Guard returns token
            >>> token = await jwt_guard.authenticate(credentials)
            >>> # Session Guard returns user
            >>> user = await session_guard.authenticate(credentials)
        """
        pass
