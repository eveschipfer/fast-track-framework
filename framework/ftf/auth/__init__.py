"""
Authentication & Authorization Module (Sprint 3.3 + Sprint 5.5)

This module provides comprehensive authentication and authorization functionality:

Authentication (Sprint 3.3):
- Password hashing and verification (bcrypt)
- JWT token creation and verification
- Route protection via AuthGuard
- Type-safe CurrentUser dependency

Authorization (Sprint 5.5):
- RBAC Gates system for global abilities
- Policy base class for model-specific authorization
- Authorize() dependency for route protection
- Integration with JWT authentication

Usage:
    >>> from ftf.auth import hash_password, verify_password
    >>> from ftf.auth import create_access_token, decode_token
    >>> from ftf.auth import CurrentUser, get_current_user
    >>>
    >>> # Hash password on registration
    >>> hashed = hash_password("user_password")
    >>>
    >>> # Verify password on login
    >>> if verify_password("user_password", hashed):
    ...     token = create_access_token({"user_id": user.id})
    ...     return {"access_token": token}
    >>>
    >>> # Protect routes (JWT Authentication)
    >>> @app.get("/profile")
    >>> async def get_profile(user: CurrentUser):
    ...     return {"id": user.id, "email": user.email}
    >>>
    >>> # Authorization with Gates (Sprint 5.5)
    >>> from ftf.auth import Gate, Policy, Authorize
    >>>
    >>> # Define global ability
    >>> Gate.define("view-dashboard", lambda user: user.is_admin)
    >>>
    >>> # Protect route with authorization
    >>> @app.get("/dashboard", dependencies=[Depends(Authorize("view-dashboard"))])
    >>> async def dashboard(user: CurrentUser):
    ...     return {"message": "Admin dashboard"}
    >>>
    >>> # Policy-based authorization
    >>> class PostPolicy(Policy):
    ...     def update(self, user, post):
    ...         return user.id == post.author_id
    >>>
    >>> Gate.register_policy(Post, PostPolicy())

Educational Note:
    The CurrentUser type alias provides excellent DX:
    - Type-safe: MyPy knows the type is User
    - Concise: No need to write Depends(get_current_user) every time
    - Familiar: Similar to Laravel's Auth::user()

    This is achieved through Python's Annotated type:
        CurrentUser = Annotated[User, Depends(get_current_user)]

    When FastAPI sees CurrentUser in a route parameter, it:
    1. Recognizes it's Annotated with a Depends
    2. Calls get_current_user() to resolve the dependency
    3. Injects the result as the parameter value
"""

from typing import Annotated, Any

from fastapi import Depends

# Authentication imports (Sprint 3.3)
from ftf.auth.crypto import hash_password, needs_rehash, verify_password
from ftf.auth.guard import get_current_user
from ftf.auth.jwt import (
    create_access_token,
    decode_token,
    get_token_expiration,
)

# Authorization imports (Sprint 5.5)
from ftf.auth.dependencies import Authorize, Requires
from ftf.auth.gates import Gate, GateManager
from ftf.auth.policies import Policy

# CurrentUser type alias for route protection
# Educational Note: We use Any here instead of User to avoid circular imports
# (auth/__init__.py → models/user.py → might import auth)
# The actual type will be User, but we can't reference it directly here.
CurrentUser = Annotated[Any, Depends(get_current_user)]

# Public API exports
__all__ = [
    # Password hashing (Sprint 3.3)
    "hash_password",
    "verify_password",
    "needs_rehash",
    # JWT tokens (Sprint 3.3)
    "create_access_token",
    "decode_token",
    "get_token_expiration",
    # Auth guard (Sprint 3.3)
    "get_current_user",
    "CurrentUser",
    # Authorization (Sprint 5.5)
    "Gate",
    "GateManager",
    "Policy",
    "Authorize",
    "Requires",
]
