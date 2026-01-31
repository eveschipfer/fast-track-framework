"""
JWT Token Service (Sprint 3.3)

This module handles JSON Web Token (JWT) creation and verification for stateless
authentication. JWTs allow the server to verify user identity without maintaining
session state, making them ideal for REST APIs and microservices.

Educational Note:
    JWT Structure: header.payload.signature
    - Header: Algorithm and token type ({"alg": "HS256", "typ": "JWT"})
    - Payload: Claims (user_id, exp, iat, etc.)
    - Signature: HMAC-SHA256(header + payload, secret_key)

    Why JWT?
    - Stateless: No server-side session storage needed
    - Self-contained: All info in the token itself
    - Scalable: Works across multiple servers/services
    - Standard: RFC 7519, widely supported

Security Considerations:
    - NEVER put sensitive data in JWT payload (it's base64, not encrypted!)
    - ALWAYS use HTTPS in production (prevent token theft)
    - Use short expiration times (15-60 minutes)
    - Rotate SECRET_KEY periodically
    - Implement refresh tokens for long-lived sessions
"""

import os
import warnings
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError

# Load SECRET_KEY from environment variables
# Educational Note: We use os.getenv() instead of os.environ[] to provide
# a fallback value. In production, ALWAYS set this via environment variables.
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "INSECURE_DEFAULT_SECRET_KEY_CHANGE_IN_PRODUCTION_DO_NOT_USE_THIS",
)

# Warn if using default secret key
if SECRET_KEY == "INSECURE_DEFAULT_SECRET_KEY_CHANGE_IN_PRODUCTION_DO_NOT_USE_THIS":
    warnings.warn(
        "⚠️  Using default SECRET_KEY! Set JWT_SECRET_KEY environment variable in production.",
        stacklevel=2,
    )

# JWT algorithm (HS256 = HMAC with SHA-256)
ALGORITHM = "HS256"

# Default token expiration (30 minutes)
# Educational Note: Short expiration reduces risk of token theft.
# Use refresh tokens for longer sessions.
DEFAULT_EXPIRATION = timedelta(minutes=30)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    This function generates a signed JWT containing the provided data plus
    standard claims (exp, iat). The token can be verified later to authenticate
    requests without hitting the database every time.

    Args:
        data: Payload data to encode (e.g., {"user_id": 123})
        expires_delta: Token expiration time (default: 30 minutes)

    Returns:
        str: Encoded JWT token

    Example:
        >>> token = create_access_token({"user_id": 123})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsImV4cCI6MTY...
        >>>
        >>> # With custom expiration
        >>> token = create_access_token(
        ...     {"user_id": 123},
        ...     expires_delta=timedelta(hours=24)
        ... )

    Token Structure:
        {
            "user_id": 123,           # Custom payload
            "exp": 1234567890,        # Expiration timestamp (UTC)
            "iat": 1234567000         # Issued at timestamp (UTC)
        }

    Security Notes:
        - Token is signed, not encrypted (payload is visible)
        - Never include passwords or sensitive data
        - Expiration is enforced during decode
        - Signature prevents tampering
    """
    # Copy data to avoid mutating the original
    to_encode = data.copy()

    # Calculate expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + DEFAULT_EXPIRATION

    # Add standard JWT claims
    # exp: Expiration time (Unix timestamp)
    # iat: Issued at time (Unix timestamp)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    })

    # Encode and sign the token
    # Educational Note: jwt.encode() does:
    # 1. Convert payload to JSON
    # 2. Base64 encode header and payload
    # 3. Create signature: HMAC-SHA256(header.payload, secret)
    # 4. Return: header.payload.signature
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT token.

    This function verifies the token's signature and expiration, then returns
    the payload. If the token is invalid or expired, it raises an exception.

    Args:
        token: The JWT token to decode

    Returns:
        dict: The decoded payload

    Raises:
        ExpiredSignatureError: If the token has expired
        DecodeError: If the token is malformed
        InvalidTokenError: If the signature is invalid

    Example:
        >>> token = create_access_token({"user_id": 123})
        >>> payload = decode_token(token)
        >>> print(payload)
        {'user_id': 123, 'exp': 1234567890, 'iat': 1234567000}
        >>>
        >>> # Expired token
        >>> decode_token(old_token)
        jwt.exceptions.ExpiredSignatureError: Signature has expired
        >>>
        >>> # Tampered token
        >>> decode_token(modified_token)
        jwt.exceptions.InvalidTokenError: Signature verification failed

    Verification Process:
        1. Split token into header, payload, signature
        2. Verify signature: HMAC-SHA256(header.payload, secret) == signature
        3. Check expiration: exp > current_time
        4. Return payload if valid
        5. Raise exception if invalid

    Security Notes:
        - Signature verification prevents tampering
        - Expiration check prevents replay attacks
        - Constant-time comparison in HMAC prevents timing attacks
    """
    try:
        # Decode and verify the token
        # Educational Note: jwt.decode() does:
        # 1. Split token into parts
        # 2. Verify signature
        # 3. Check expiration (if verify_exp=True)
        # 4. Return payload
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "verify_signature": True,  # Verify HMAC signature
                "verify_exp": True,        # Verify expiration
                "require_exp": True,       # Require exp claim
            },
        )
        return payload

    except ExpiredSignatureError:
        # Token has expired (exp < current_time)
        # This is a 401 Unauthorized error
        raise

    except DecodeError:
        # Token is malformed (invalid base64, invalid JSON, etc.)
        # This is a 401 Unauthorized error
        raise

    except InvalidTokenError:
        # Signature verification failed (token was tampered with)
        # This is a 401 Unauthorized error
        raise


def get_token_expiration(token: str) -> datetime | None:
    """
    Get the expiration time of a token without full verification.

    This is useful for debugging or displaying token info to users.
    Does NOT verify the signature, so don't use for authentication.

    Args:
        token: The JWT token

    Returns:
        datetime | None: The expiration time (UTC) or None if no exp claim

    Example:
        >>> token = create_access_token({"user_id": 123})
        >>> exp = get_token_expiration(token)
        >>> print(exp)
        2024-01-31 15:30:00+00:00

    Warning:
        This does NOT verify the token! Only use for informational purposes.
        For authentication, always use decode_token() which verifies signature.
    """
    try:
        # Decode without verification (only parse)
        payload = jwt.decode(
            token,
            options={"verify_signature": False},  # Skip verification!
            algorithms=[ALGORITHM],
        )

        # Get exp claim
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        return None

    except Exception:
        return None
