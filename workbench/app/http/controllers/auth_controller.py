"""
AuthController — HTTP Handler Layer for /auth resource

Architecture:
    Request → Route function → AuthController method
                → AuthService method (pure domain logic)
                → UserRepository → Database

Endpoints:
    POST /api/auth/login    → {access_token, refresh_token, token_type}
    POST /api/auth/refresh  → {access_token, token_type}
    GET  /api/auth/me       → UserResponse (authenticated user's profile)

Exception mapping (domain → HTTP):
    InvalidCredentials → 401 Unauthorized
    TokenExpired       → 401 Unauthorized
    ForbiddenToken     → 403 Forbidden
    InvalidToken       → 401 Unauthorized
    UserNotFound       → 401 Unauthorized (avoid user enumeration in auth context)
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from jtc.http import Inject

from app.exceptions.auth_exceptions import (
    ForbiddenToken,
    InvalidCredentials,
    InvalidToken,
    TokenExpired,
    UserNotFound,
)
from jtc.http import BaseController
from app.schemas import AccessTokenResponse, LoginRequest, RefreshRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from jtc.validation import Validate


# ============================================================================
# CONTROLLER
# ============================================================================


class AuthController(BaseController):
    """
    Handles HTTP concerns for JWT authentication.

    Receives ``AuthService`` from the IoC container (scoped lifetime).
    """

    def __init__(self, service: AuthService) -> None:
        self.service = service

    async def login(self, payload: LoginRequest) -> TokenResponse:
        """
        Authenticate user and issue token pair.

        Returns:
            TokenResponse: access_token (15 min) + refresh_token (7 days).

        Raises:
            HTTPException 401: Invalid credentials.
        """
        try:
            return self.ok(await self.service.login(payload.email, payload.password))
        except InvalidCredentials:
            # Generic message to prevent user enumeration
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def refresh(self, payload: RefreshRequest) -> AccessTokenResponse:
        """
        Exchange a valid refresh token for a new access token.

        Raises:
            HTTPException 401: Expired or invalid refresh token.
            HTTPException 403: Tampered refresh token signature.
        """
        try:
            return self.ok(await self.service.refresh(payload.refresh_token))
        except TokenExpired as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
                headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
            )
        except ForbiddenToken as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            )
        except (InvalidToken, UserNotFound) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
                headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
            )

    async def me(self, request: Request) -> UserResponse:
        """
        Return the authenticated user's profile.

        JwtMiddleware has already decoded the token and stored the payload in
        ``request.state.user``.  This method uses the ``sub`` claim to fetch
        fresh data from the database.

        Raises:
            HTTPException 401: No valid token provided.
        """
        user_payload: dict[str, Any] | None = getattr(request.state, "user", None)

        if not user_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id_str: str | None = user_payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not determine user from token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            return self.ok(await self.service.get_user_by_id(int(user_id_str)))
        except (UserNotFound, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user no longer exists.",
                headers={"WWW-Authenticate": "Bearer"},
            )


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses={
        401: {"description": "Unauthorized — invalid or missing token"},
        403: {"description": "Forbidden — token signature tampered"},
    },
)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    controller: AuthController = Inject(AuthController),
) -> TokenResponse:
    """
    Authenticate with email + password.

    Returns an ``access_token`` (valid for 15 minutes) and a
    ``refresh_token`` (valid for 7 days).

    Example request:
        POST /api/auth/login
        {"email": "alice@example.com", "password": "s3cur3P@ssw0rd"}
    """
    return await controller.login(payload)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    payload: RefreshRequest,
    controller: AuthController = Inject(AuthController),
) -> AccessTokenResponse:
    """
    Renew an expired access token using a valid refresh token.

    The refresh token is NOT invalidated after use (stateless design).
    To implement rotation, persist and revoke refresh tokens server-side.

    Example request:
        POST /api/auth/refresh
        {"refresh_token": "<refresh_jwt>"}
    """
    return await controller.refresh(payload)


@router.get("/me", response_model=UserResponse)
async def me(
    request: Request,
    controller: AuthController = Inject(AuthController),
) -> UserResponse:
    """
    Return the currently authenticated user's profile.

    Requires: ``Authorization: Bearer <access_token>``

    The JwtMiddleware validates the token and populates ``request.state.user``
    before this handler is invoked.
    """
    return await controller.me(request)
