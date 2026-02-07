"""
Auth Manager (Sprint 10)

This module provides the main authentication entry point that manages multiple Guards.

Architecture:
    - AuthManager: Singleton (registered in Container)
    - Guards: JwtGuard (APIs), SessionGuard (Web)
    - UserProvider: Database user lookup

Educational Note:
    This is the "Laravel-inspired" Auth Facade pattern.
    It provides a single entry point for all authentication operations,
    automatically routing calls to the correct guard based on configuration.

Usage:
    >>> from jtc.auth import AuthManager
    >>> # Get default guard
    >>> user = await AuthManager.user()
    >>>
    >>> # Get specific guard
    >>> api_guard = AuthManager.guard('api')
    >>> user = await api_guard.user()
"""

from typing import Any, Optional

from jtc.auth.contracts import Guard, UserProvider, Credentials
from jtc.core import Container


class AuthManager:
    """
    Authentication Manager (Singleton).

    This class provides a facade over multiple authentication guards.
    It is registered as a singleton in the Container and manages
    all authentication operations.

    Design Pattern:
        - Facade: Single entry point for auth operations
        - Strategy: Routes to appropriate guard based on name
        - Proxy: Delegates to default guard when not specified

    Attributes:
        _container: IoC Container instance
        _guards: Dictionary of registered guard instances
        _default_guard: Name of default guard to use

    Example:
        >>> # Register guards
        >>> AuthManager.register('api', JwtGuard(...))
        >>> AuthManager.register('web', SessionGuard(...))
        >>>
        >>> # Use default guard
        >>> user = await AuthManager.user()  # Uses 'api' guard
        >>>
        >>> # Use specific guard
        >>> user = await AuthManager.guard('web').user()
    """

    _instance: "AuthManager | None" = None
    _container: Container | None = None
    _guards: dict[str, Guard] = {}
    _default_guard: str = "api"

    def __new__(cls) -> "AuthManager":
        """
        Ensure singleton instance.

        Educational Note:
            This is the Singleton pattern implemented via __new__.
            It ensures only one AuthManager exists per application.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """
        Initialize Auth Manager.

        Note: Actual initialization happens in `initialize()` method
        which is called after Container is set up.
        """
        pass

    @classmethod
    def initialize(cls, container: Container, default_guard: str = "api") -> None:
        """
        Initialize Auth Manager with Container.

        This method must be called after Container is set up,
        typically by AuthServiceProvider.

        Args:
            container: IoC Container instance
            default_guard: Name of default guard (default: 'api')

        Example:
            >>> # In AuthServiceProvider
            >>> from jtc.core import Container
            >>> AuthManager.initialize(container, default_guard='api')
        """
        cls._container = container

    @classmethod
    def register(cls, name: str, guard: Guard) -> None:
        """
        Register a guard.

        Args:
            name: Guard identifier (e.g., 'api', 'web')
            guard: Guard instance implementing Guard contract
        """
        cls._guards[name] = guard

    @classmethod
    def guard(cls, name: Optional[str] = None) -> Guard:
        """
        Get a guard by name.

        Args:
            name: Guard name (default uses default guard)

        Returns:
            Guard instance

        Raises:
            KeyError: If guard name not found
        """
        guard_name = name or cls._default_guard

        if guard_name not in cls._guards:
            available = ", ".join(cls._guards.keys())
            raise KeyError(
                f"Guard '{guard_name}' not found. Available guards: {available}"
            )

        return cls._guards[guard_name]

    def __getattr__(self, name: str) -> Any:
        """
        Proxy attribute access to default guard.

        This enables the Auth facade pattern:
            AuthManager.user() -> AuthManager.guard('api').user()
            AuthManager.check() -> AuthManager.guard('api').check()
            AuthManager.id() -> AuthManager.guard('api').id()

        Educational Note:
            This is Python's __getattr__ magic method. It intercepts
            undefined attribute access and delegates to the default guard.
            This provides Laravel-like syntax:
                Auth::user() -> AuthManager.guard().user()

        Args:
            name: Method name to proxy

        Returns:
            Result of calling method on default guard

        Example:
            >>> user = await AuthManager.user()
            >>> # Equivalent to:
            >>> user = await AuthManager.guard('api').user()
            >>>
            >>> is_valid = await AuthManager.check(credentials)
            >>> # Equivalent to:
            >>> is_valid = await AuthManager.guard('api').check(credentials)
        """
        default_guard = self.__class__.guard()

        if not hasattr(default_guard, name):
            raise AttributeError(
                f"Guard has no method '{name}'. "
                f"Available methods on default guard: {dir(default_guard)}"
            )

        return getattr(default_guard, name)

    @classmethod
    async def user(cls) -> Optional[Any]:
        """
        Get authenticated user from default guard.

        This is the primary method used by route handlers.

        Returns:
            User instance or None

        Example:
            >>> @app.get("/profile")
            >>> async def get_profile(user = Depends(AuthManager.user)):
            ...     return {"id": user.id, "name": user.name}
        """
        instance = cls()
        return await instance.user()

    @classmethod
    async def check(cls, credentials: Credentials) -> bool:
        """
        Check if credentials are valid (login endpoint).

        Args:
            credentials: Email and password (or token)

        Returns:
            bool: True if valid, False otherwise

        Example:
            >>> @app.post("/login")
            >>> async def login(credentials: Credentials):
            ...     if await AuthManager.check(credentials):
            ...         token = await AuthManager.authenticate(credentials)
            ...         return {"access_token": token}
        """
        instance = cls()
        return await instance.check(credentials)

    @classmethod
    async def id(cls) -> Optional[Any]:
        """
        Get authenticated user ID from default guard.

        Used by authorization system (Gates, Policies).

        Returns:
            User ID or None

        Example:
            >>> @app.delete("/posts/{id}")
            >>> async def delete_post(post_id: int, user_id: int = Depends(AuthManager.id)):
            ...     post = await post_repo.find(post_id)
            ...     if post.author_id != user_id:
            ...         raise Forbidden("Cannot delete other's post")
        """
        instance = cls()
        return await instance.id()

    @classmethod
    async def validate(cls, credentials: Credentials) -> bool:
        """
        Validate credentials (alias for check).

        This provides a more explicit name for credential validation.

        Args:
            credentials: Email and password (or token)

        Returns:
            bool: True if valid, False otherwise
        """
        instance = cls()
        return await instance.validate(credentials)

    @classmethod
    async def authenticate(cls, credentials: Credentials) -> Any:
        """
        Authenticate and set user for credentials.

        Used by login endpoints after credential validation.

        Args:
            credentials: Valid email and password (or token)

        Returns:
            User instance or token (depending on guard type)

        Example:
            >>> @app.post("/login")
            >>> async def login(credentials: Credentials):
            ...     if await AuthManager.check(credentials):
            ...         result = await AuthManager.authenticate(credentials)
            ...         return {"access_token": result}
        """
        instance = cls()
        return await instance.authenticate(credentials)
