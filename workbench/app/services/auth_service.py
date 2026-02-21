"""
AuthService — JWT Authentication Business Logic

Pure domain layer for authentication operations.

Design rules:
    ✅ Repositories, domain models, Pydantic schemas, domain exceptions
    ❌ HTTPException, fastapi.status, JSONResponse, Request, Response

Public API:
    login(email, password)  → TokenResponse
    refresh(refresh_token)  → AccessTokenResponse
    get_user_by_id(id)      → UserResponse   (used by /me endpoint)

Token Contract:
    Access token payload:  { sub, name, email, iat, exp }
    Refresh token payload: { sub, token_type="refresh", iat, exp }

Raises:
    InvalidCredentials — wrong email/password.
    TokenExpired       — refresh token has expired.
    InvalidToken       — refresh token is malformed or is not a refresh token.
    ForbiddenToken     — refresh token signature was tampered with.
    UserNotFound       — user referenced in token no longer exists.
"""

from datetime import timedelta

from jtc.auth.crypto import verify_password
from jtc.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidTokenError,
)
from app.exceptions.auth_exceptions import (
    ForbiddenToken,
    InvalidCredentials,
    InvalidToken,
    TokenExpired,
    UserNotFound,
)
from app.repositories.user_repository import UserRepository
from app.schemas import AccessTokenResponse, TokenResponse, UserResponse
from fast_query import RecordNotFound

# Strict 15-minute window for access tokens (per spec)
ACCESS_TOKEN_TTL = timedelta(minutes=15)


class AuthService:
    """
    Handles JWT-based authentication: login, token refresh, and user lookup.

    Receives ``UserRepository`` via the IoC container (scoped lifetime).
    """

    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def login(self, email: str, password: str) -> TokenResponse:
        """
        Validate credentials and issue an access + refresh token pair.

        Args:
            email:    User's email address.
            password: Plaintext password to verify.

        Returns:
            TokenResponse with ``access_token``, ``refresh_token``, and
            ``token_type="bearer"``.

        Raises:
            InvalidCredentials: If the email is not found or the password
                                 does not match the stored bcrypt hash.
        """
        user = await self.repo.find_by_email(email)

        # Use constant-time comparison to prevent timing-based user enumeration
        if user is None or not verify_password(password, user.password):
            raise InvalidCredentials()

        # Build access token payload per spec: sub, name, email, iat (+ exp added by helper)
        access_payload = {
            "sub": str(user.id),
            "name": user.name,
            "email": user.email,
        }
        access_token = create_access_token(access_payload, expires_delta=ACCESS_TOKEN_TTL)

        # Refresh token carries only the subject — minimise payload exposure
        refresh_payload = {"sub": str(user.id)}
        refresh_token = create_refresh_token(refresh_payload)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh(self, refresh_token: str) -> AccessTokenResponse:
        """
        Issue a new access token from a valid refresh token.

        Args:
            refresh_token: A non-expired refresh token previously issued by login().

        Returns:
            AccessTokenResponse with a fresh ``access_token``.

        Raises:
            TokenExpired:   Refresh token has expired — user must log in again.
            ForbiddenToken: Refresh token signature is invalid (tampered).
            InvalidToken:   Token is malformed or is not typed as "refresh".
            UserNotFound:   The user referenced in the token no longer exists.
        """
        try:
            payload = decode_token(refresh_token)
        except ExpiredSignatureError:
            raise TokenExpired("Refresh token has expired. Please log in again.")
        except InvalidSignatureError:
            raise ForbiddenToken("Refresh token signature verification failed.")
        except (DecodeError, InvalidTokenError) as exc:
            raise InvalidToken(f"Refresh token is invalid: {exc}") from exc

        # Verify it's actually a refresh token (not an access token being replayed)
        if payload.get("token_type") != "refresh":
            raise InvalidToken("Provided token is not a refresh token.")

        user_id_str: str | None = payload.get("sub")
        if not user_id_str:
            raise InvalidToken("Refresh token is missing the 'sub' claim.")

        try:
            user = await self.repo.find_or_fail(int(user_id_str))
        except (RecordNotFound, ValueError):
            raise UserNotFound(user_id_str)

        # Issue new access token with fresh user data
        new_access_token = create_access_token(
            {"sub": str(user.id), "name": user.name, "email": user.email},
            expires_delta=ACCESS_TOKEN_TTL,
        )

        return AccessTokenResponse(access_token=new_access_token, token_type="bearer")

    async def get_user_by_id(self, user_id: int) -> UserResponse:
        """
        Fetch user data by primary key.

        Used by the /me endpoint to return fresh profile data from the DB
        (rather than potentially stale data from the JWT payload).

        Raises:
            UserNotFound: If the user no longer exists.
        """
        try:
            user = await self.repo.find_or_fail(user_id)
        except RecordNotFound:
            raise UserNotFound(user_id)
        return UserResponse.model_validate(user)
