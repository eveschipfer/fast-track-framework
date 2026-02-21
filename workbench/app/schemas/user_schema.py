"""
User & Auth Schemas

Pydantic V2 schemas for User CRUD and JWT authentication.

Schemas:
    UserCreate:       Register / create a new user (includes raw password).
    UserUpdate:       Partial update — all fields optional.
    UserResponse:     Safe public representation — password is NEVER exposed.
    LoginRequest:     Credentials sent to the login endpoint.
    TokenResponse:    Returned by login — contains access + refresh tokens.
    RefreshRequest:   Payload for the /auth/refresh endpoint.
    AccessTokenResponse: Returned by /auth/refresh — new access token only.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# User CRUD schemas
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    """
    Payload for creating a new user.

    The password is accepted as plaintext here; the service layer hashes it
    with bcrypt before persisting.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's full name",
        examples=["Alice Smith"],
    )
    email: EmailStr = Field(
        ...,
        description="Unique email address",
        examples=["alice@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Plaintext password (min 8 characters). Hashed before storing.",
        examples=["s3cur3P@ssw0rd"],
    )

    model_config = ConfigDict(extra="forbid")


class UserUpdate(BaseModel):
    """
    Payload for updating an existing user.

    All fields are optional — only supplied fields are overwritten.
    If ``password`` is provided, it is re-hashed before saving.
    """

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, examples=["Alice Smith"]
    )
    email: Optional[EmailStr] = Field(None, examples=["alice@example.com"])
    password: Optional[str] = Field(
        None,
        min_length=8,
        description="New plaintext password (min 8 characters). Hashed before storing.",
        examples=["n3wP@ssw0rd"],
    )

    model_config = ConfigDict(extra="forbid")


class UserResponse(BaseModel):
    """
    Safe public representation of a user.

    Password and reset_token are intentionally excluded.
    """

    id: int = Field(..., description="Primary key", examples=[1])
    name: str = Field(..., examples=["Alice Smith"])
    email: str = Field(..., examples=["alice@example.com"])
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp (UTC)")

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """Credentials sent to POST /api/auth/login."""

    email: EmailStr = Field(..., examples=["alice@example.com"])
    password: str = Field(..., examples=["s3cur3P@ssw0rd"])

    model_config = ConfigDict(extra="forbid")


class TokenResponse(BaseModel):
    """
    Returned by a successful login.

    access_token:  Short-lived JWT (15 minutes). Use for authenticated requests.
    refresh_token: Long-lived JWT (7 days). Use to renew the access token.
    token_type:    Always "bearer" per RFC 6750.
    """

    access_token: str = Field(..., description="Short-lived JWT (15 min)")
    refresh_token: str = Field(..., description="Long-lived JWT (7 days)")
    token_type: str = Field(default="bearer", description="Token scheme")


class RefreshRequest(BaseModel):
    """Payload for POST /api/auth/refresh."""

    refresh_token: str = Field(..., description="A valid refresh token")

    model_config = ConfigDict(extra="forbid")


class AccessTokenResponse(BaseModel):
    """Returned by a successful token refresh."""

    access_token: str = Field(..., description="New short-lived JWT (15 min)")
    token_type: str = Field(default="bearer")
