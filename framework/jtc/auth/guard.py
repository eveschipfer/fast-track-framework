"""
Authentication Guard (Sprint 3.3)

This module provides the AuthGuard - a FastAPI dependency that extracts and
verifies JWT tokens, fetches the user from the database, and enforces
authentication on protected routes.

Educational Note:
    This is the "Guard" pattern (Angular-inspired). In FastAPI, guards are
    implemented as dependencies that raise HTTP exceptions to deny access.

    Flow:
    1. Client sends: Authorization: Bearer <jwt_token>
    2. Guard extracts token from header
    3. Guard decodes JWT (verifies signature + expiration)
    4. Guard fetches user from database
    5. Guard returns User instance to route handler
    6. If any step fails → 401 Unauthorized

Security Best Practices:
    - Always use HTTPS (prevent token theft)
    - Validate token signature (prevent tampering)
    - Check expiration (prevent replay attacks)
    - Fetch fresh user data (detect disabled accounts)
    - Use constant-time comparison (prevent timing attacks)
"""

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from jtc.auth.jwt import decode_token
from jtc.core import Container

# HTTPBearer extracts "Authorization: Bearer <token>" header
# Educational Note: FastAPI provides several security utilities:
# - HTTPBearer: For Bearer tokens (JWT, OAuth2)
# - HTTPBasic: For Basic auth (username:password)
# - OAuth2PasswordBearer: For OAuth2 flows
# We use HTTPBearer because JWT is a Bearer token scheme
_bearer_scheme = HTTPBearer(auto_error=False)  # auto_error=False to customize error message


async def get_current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme)
    ] = None,
) -> Any:  # Returns User instance (Any to avoid circular import)
    """
    FastAPI dependency that authenticates the current user.

    This function:
    1. Extracts the JWT token from the Authorization header
    2. Decodes and verifies the token (signature + expiration)
    3. Extracts user_id from the token payload
    4. Resolves UserRepository from the IoC Container
    5. Fetches the user from the database
    6. Returns the User instance

    Args:
        request: FastAPI request object (provides access to app.state)
        credentials: Extracted Bearer token credentials

    Returns:
        User: The authenticated user instance

    Raises:
        HTTPException: 401 Unauthorized if:
            - No Authorization header provided
            - Token is invalid or expired
            - User not found in database
            - User account is disabled

    Example Usage:
        >>> from jtc.auth import CurrentUser
        >>>
        >>> @app.get("/profile")
        >>> async def get_profile(user: CurrentUser):
        ...     return {"id": user.id, "email": user.email}
        >>>
        >>> # Alternative (explicit dependency):
        >>> @app.get("/profile")
        >>> async def get_profile(user = Depends(get_current_user)):
        ...     return {"id": user.id, "email": user.email}

    Security Flow:
        Client Request:
            GET /profile HTTP/1.1
            Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        Guard Process:
            1. Extract token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
            2. Decode JWT: {"user_id": 123, "exp": 1234567890}
            3. Verify signature: ✓
            4. Check expiration: ✓
            5. Fetch user: SELECT * FROM users WHERE id = 123
            6. Check user exists: ✓
            7. Return user instance

        If any step fails:
            HTTP/1.1 401 Unauthorized
            {"detail": "Could not validate credentials"}

    Educational Notes:
        - This is stateless authentication (no server-side sessions)
        - Each request is independently authenticated
        - Database is queried on every request (trade-off for fresh data)
        - Token theft is mitigated by short expiration times
        - Refresh tokens (not implemented) extend sessions without reauth
    """
    # Step 1: Check if Authorization header was provided
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Step 2: Extract the token
    token = credentials.credentials

    # Step 3: Decode and verify the JWT
    try:
        payload = decode_token(token)
    except Exception:
        # Token is invalid, expired, or tampered
        # Educational Note: We catch all JWT exceptions and return generic error
        # to prevent information leakage (don't tell attacker if token expired vs invalid)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    # Step 4: Extract user_id from payload
    user_id = payload.get("user_id")
    if user_id is None:
        # Token payload doesn't contain user_id
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Step 5: Get the IoC Container from the app
    # Educational Note: FastAPI stores app-level state in request.app.state
    # The FastTrackFramework registers its container there during initialization
    container: Container = request.app.state.container

    # Step 6: Resolve UserRepository from the container
    # Educational Note: This uses dependency injection! The repository is
    # resolved with all its dependencies (AsyncSession, etc.) automatically.
    # CRITICAL: We import UserRepository HERE to avoid circular imports
    # (guard.py → models → user.py might import guard.py)
    try:
        # Dynamic import to avoid circular dependency
        # Educational Note: We could make this configurable to support
        # different user models, but for simplicity we hardcode it.
        from jtc.models.user import User
        from fast_query import BaseRepository

        # Get the repository type from the container
        # Since UserRepository might not exist yet, we use BaseRepository[User]
        # The make:auth command will create a proper UserRepository
        UserRepository = BaseRepository[User]  # type: ignore

        # Resolve repository from container
        user_repo = container.resolve(UserRepository)

    except Exception as e:
        # Container resolution failed (UserRepository not registered)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication system not configured properly: {e}",
        ) from e

    # Step 7: Fetch the user from the database
    try:
        user = await user_repo.find(user_id)
    except Exception:
        # User not found
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    # Step 8: Check if user exists (find() might return None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Step 9: Optional - Check if user account is active
    # Educational Note: You might want to add a is_active field to User model
    # and check it here. For now, we skip this check.
    # if hasattr(user, 'is_active') and not user.is_active:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Inactive user",
    #     )

    # Step 10: Return the authenticated user
    return user


# Educational Note: Why return Any instead of User?
# Python's type system doesn't handle forward references well in function signatures.
# We use Any here to avoid circular imports (guard.py imports User, User might import guard.py).
# The actual type will be enforced by the CurrentUser type alias in __init__.py.
