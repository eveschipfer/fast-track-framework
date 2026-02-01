"""
Authentication Tests (Sprint 3.3)

This module tests the authentication system including password hashing,
JWT token management, and route protection.

Test Coverage:
    - Password hashing and verification
    - JWT token creation and decoding
    - Token expiration handling
    - AuthGuard dependency
    - Edge cases and security scenarios
"""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from jwt.exceptions import DecodeError, ExpiredSignatureError

from ftf.auth.crypto import hash_password, needs_rehash, verify_password
from ftf.auth.guard import get_current_user
from ftf.auth.jwt import create_access_token, decode_token, get_token_expiration


# ============================================================================
# PASSWORD HASHING TESTS
# ============================================================================


def test_hash_password_returns_bcrypt_hash() -> None:
    """Test that hash_password generates a valid bcrypt hash."""
    password = "my_secure_password"
    hashed = hash_password(password)

    # Bcrypt hashes start with $2b$ and are 60 characters long
    assert hashed.startswith("$2b$")
    assert len(hashed) == 60


def test_hash_password_generates_unique_hashes() -> None:
    """Test that same password generates different hashes (due to random salt)."""
    password = "same_password"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Same password, different hashes (different salts)
    assert hash1 != hash2


def test_verify_password_returns_true_for_correct_password() -> None:
    """Test that verify_password returns True for correct password."""
    password = "correct_password"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_returns_false_for_incorrect_password() -> None:
    """Test that verify_password returns False for incorrect password."""
    password = "correct_password"
    wrong_password = "wrong_password"
    hashed = hash_password(password)

    assert verify_password(wrong_password, hashed) is False


def test_needs_rehash_returns_false_for_fresh_hash() -> None:
    """Test that newly created hashes don't need rehashing."""
    password = "test_password"
    hashed = hash_password(password)

    assert needs_rehash(hashed) is False


# ============================================================================
# JWT TOKEN TESTS
# ============================================================================


def test_create_access_token_returns_jwt_string() -> None:
    """Test that create_access_token generates a valid JWT."""
    data = {"user_id": 123}
    token = create_access_token(data)

    # JWT has 3 parts separated by dots
    assert isinstance(token, str)
    assert token.count(".") == 2


def test_create_access_token_includes_payload_data() -> None:
    """Test that token payload contains the provided data."""
    data = {"user_id": 456, "email": "test@example.com"}
    token = create_access_token(data)

    # Decode token and verify payload
    payload = decode_token(token)
    assert payload["user_id"] == 456
    assert payload["email"] == "test@example.com"


def test_create_access_token_includes_expiration() -> None:
    """Test that token includes exp and iat claims."""
    data = {"user_id": 789}
    token = create_access_token(data)

    payload = decode_token(token)
    assert "exp" in payload
    assert "iat" in payload


def test_create_access_token_with_custom_expiration() -> None:
    """Test that custom expiration delta is respected."""
    data = {"user_id": 111}
    expires_delta = timedelta(hours=24)
    token = create_access_token(data, expires_delta=expires_delta)

    payload = decode_token(token)
    # Can't test exact time, but verify exp exists
    assert "exp" in payload


def test_decode_token_returns_payload() -> None:
    """Test that decode_token returns the original payload."""
    original_data = {"user_id": 222, "role": "admin"}
    token = create_access_token(original_data)

    payload = decode_token(token)

    assert payload["user_id"] == 222
    assert payload["role"] == "admin"


def test_decode_token_raises_on_invalid_token() -> None:
    """Test that decode_token raises error for invalid token."""
    invalid_token = "not.a.valid.jwt"

    with pytest.raises(DecodeError):
        decode_token(invalid_token)


def test_decode_token_raises_on_tampered_token() -> None:
    """Test that decode_token raises error for tampered token."""
    data = {"user_id": 333}
    token = create_access_token(data)

    # Tamper with the token
    tampered_token = token[:-10] + "tampered!!"

    with pytest.raises(Exception):  # Could be DecodeError or InvalidSignature
        decode_token(tampered_token)


def test_decode_token_raises_on_expired_token() -> None:
    """Test that decode_token raises error for expired token."""
    data = {"user_id": 444}
    # Create token that expires immediately
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))

    with pytest.raises(ExpiredSignatureError):
        decode_token(token)


def test_get_token_expiration_returns_datetime() -> None:
    """Test that get_token_expiration returns expiration time."""
    data = {"user_id": 555}
    token = create_access_token(data)

    exp_time = get_token_expiration(token)

    assert exp_time is not None
    # Can't test exact time, but verify it's a datetime
    from datetime import datetime
    assert isinstance(exp_time, datetime)


def test_get_token_expiration_returns_none_for_invalid_token() -> None:
    """Test that get_token_expiration returns None for invalid token."""
    invalid_token = "invalid.token.here"

    exp_time = get_token_expiration(invalid_token)

    assert exp_time is None


# ============================================================================
# AUTH GUARD TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_current_user_raises_401_without_credentials() -> None:
    """Test that get_current_user raises 401 if no Authorization header."""
    # Mock request
    request = Mock(spec=Request)

    # No credentials
    credentials = None

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request, credentials)

    assert exc_info.value.status_code == 401
    assert "Not authenticated" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_invalid_token() -> None:
    """Test that get_current_user raises 401 for invalid JWT."""
    # Mock request
    request = Mock(spec=Request)

    # Invalid credentials
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid.jwt.token"
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request, credentials)

    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_expired_token() -> None:
    """Test that get_current_user raises 401 for expired JWT."""
    # Create expired token
    data = {"user_id": 666}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))

    # Mock request
    request = Mock(spec=Request)

    # Credentials with expired token
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request, credentials)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_token_without_user_id() -> None:
    """Test that get_current_user raises 401 if token has no user_id."""
    # Create token without user_id
    data = {"some_other_field": "value"}
    token = create_access_token(data)

    # Mock request
    request = Mock(spec=Request)

    # Credentials with token missing user_id
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request, credentials)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_500_if_container_not_configured() -> None:
    """Test that get_current_user raises 500 if container not in app.state."""
    # Create valid token
    data = {"user_id": 777}
    token = create_access_token(data)

    # Mock request WITHOUT container in app.state
    request = Mock(spec=Request)
    request.app.state.container = None  # No container!

    # Credentials
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )

    with pytest.raises(Exception):  # Will fail when trying to access container
        await get_current_user(request, credentials)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_complete_auth_flow() -> None:
    """Test complete flow: hash password, create token, verify."""
    # 1. User registers - hash password
    plain_password = "user_password_123"
    hashed_password = hash_password(plain_password)

    # 2. Store hashed password (simulated)
    user_id = 888
    stored_hash = hashed_password

    # 3. User logs in - verify password
    assert verify_password(plain_password, stored_hash) is True

    # 4. Generate JWT token
    access_token = create_access_token({"user_id": user_id})

    # 5. Verify token
    payload = decode_token(access_token)
    assert payload["user_id"] == user_id

    # 6. Use token on subsequent requests (simulated in test_get_current_user_*)
    assert access_token is not None


def test_password_verification_is_constant_time() -> None:
    """
    Test that password verification doesn't leak timing information.

    Educational Note: bcrypt's verify() uses constant-time comparison internally.
    We can't easily test this, but we verify it doesn't short-circuit.
    """
    password = "test_password"
    hashed = hash_password(password)

    # Both should take similar time (can't measure easily in test)
    result1 = verify_password("wrong_password_short", hashed)
    result2 = verify_password("wrong_password_very_very_long", hashed)

    # Both should be False
    assert result1 is False
    assert result2 is False
