"""
JWT Guard (Sprint 10)

This module provides JwtGuard for stateless API authentication.

Architecture:
    - JwtGuard: Stateless JWT authentication
    - Uses UserProvider to retrieve users from database
    - Validates JWT tokens using settings.auth.jwt_secret

Educational Note:
    This is the "Guard Pattern" from Laravel.
    Unlike the old get_current_user() which was hardcoded to JWT,
    JwtGuard allows switching between multiple authentication methods.
"""

from typing import Optional, Any

from jtc.auth.contracts import Guard, UserProvider, Credentials


class JwtGuard(Guard):
    """
    JWT Authentication Guard.

    This guard provides stateless authentication using JWT tokens.
    It validates the Authorization: Bearer header and retrieves
    the authenticated user from the UserProvider.

    Attributes:
        user_provider: UserProvider instance for user lookup
        jwt_secret: Secret key for JWT verification

    Example:
        >>> guard = JwtGuard(user_provider, jwt_secret="secret")
        >>> user = await guard.user()
        >>> is_valid = await guard.check(credentials)
    """

    def __init__(self, user_provider: UserProvider, jwt_secret: str) -> None:
        """
        Initialize JWT Guard.

        Args:
            user_provider: UserProvider instance for user lookup
            jwt_secret: Secret key for JWT signing/verification
        """
        self.user_provider = user_provider
        self.jwt_secret = jwt_secret

    async def user(self) -> Optional[Any]:
        """
        Get authenticated user from JWT token.

        This is the primary method used by route handlers.

        Returns:
            User instance or None if not authenticated

        Example:
            >>> @app.get("/profile")
            >>> async def get_profile(user = Depends(AuthManager.user)):
            ...     return {"id": user.id}
        """
        import jwt
        from fastapi import Request, HTTPException, status
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

        _bearer_scheme = HTTPBearer(auto_error=False)

        credentials: Optional[HTTPAuthorizationCredentials] = None

        async def extract_token() -> Optional[str]:
            """Extract JWT token from Authorization header."""
            try:
                credentials = await _bearer_scheme(request)
                return credentials.credentials
            except Exception:
                return None

        token = await extract_token()

        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                options={"verify_signature": True, "verify_exp": True, "require_exp": True},
            )

            user_id = payload.get("user_id")

            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return await self.user_provider.retrieve_by_id(user_id)

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    async def check(self, credentials: Credentials) -> bool:
        """
        Check if credentials are valid.

        Used by login endpoints to validate email/password.

        Args:
            credentials: Email and password

        Returns:
            bool: True if valid, False otherwise

        Example:
            >>> @app.post("/login")
            >>> async def login(data: Credentials):
            ...     if await AuthManager.check(data):
            ...         token = await AuthManager.authenticate(data)
            ...         return {"access_token": token}
        """
        user = await self.user_provider.retrieve_by_credentials(credentials)

        if user is None:
            return False

        return True

    async def id(self) -> Optional[Any]:
        """
        Get authenticated user ID.

        Used by authorization system (Gates, Policies).

        Returns:
            User ID or None

        Example:
            >>> user_id = await guard.id()
            >>> if not await Gate.allows(user_id, "delete-post"):
            ...     raise Forbidden("Cannot delete post")
        """
        user = await self.user()

        if user is None:
            return None

        return getattr(user, "id", None)

    async def validate(self, credentials: Credentials) -> bool:
        """
        Validate credentials (alias for check).

        Args:
            credentials: Email and password

        Returns:
            bool: True if valid, False otherwise
        """
        return await self.check(credentials)

    async def authenticate(self, credentials: Credentials) -> str:
        """
        Authenticate and return JWT token.

        Used by login endpoints after credential validation.

        Args:
            credentials: Valid email and password

        Returns:
            str: JWT access token

        Example:
            >>> @app.post("/login")
            >>> async def login(data: Credentials):
            ...     if await AuthManager.check(data):
            ...         token = await AuthManager.authenticate(data)
            ...         return {"access_token": token}
        """
        import jwt
        from datetime import datetime, timedelta, timezone

        user = await self.user_provider.retrieve_by_credentials(credentials)

        if user is None:
            raise ValueError("Invalid credentials")

        user_id = getattr(user, "id", None)

        if user_id is None:
            raise ValueError("User model must have 'id' attribute")

        expire = datetime.now(timezone.utc) + timedelta(minutes=30)

        payload = {"user_id": user_id, "exp": expire, "iat": datetime.now(timezone.utc)}

        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")

        return token
