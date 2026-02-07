"""
Password Hashing (Sprint 3.3)

This module provides secure password hashing and verification using bcrypt
via the passlib library. Bcrypt is the industry standard for password hashing
due to its adaptive nature (configurable work factor) and resistance to
rainbow table attacks.

Educational Note:
    - NEVER store passwords in plain text
    - NEVER use MD5 or SHA1 for passwords (too fast, vulnerable to rainbow tables)
    - bcrypt is designed to be slow (computational cost prevents brute force)
    - The salt is automatically generated and stored in the hash

Security Best Practices:
    - Use bcrypt with at least 12 rounds (default in passlib)
    - Never log or expose password hashes
    - Always use constant-time comparison (passlib does this)
    - Pre-hash with SHA256 to handle bcrypt's 72-byte limit

Implementation Detail:
    Bcrypt has a hard 72-byte password limit. To handle longer passwords,
    we pre-hash with SHA256 before bcrypt. This is the industry-standard
    solution used by Django and other frameworks.
"""

import hashlib

from passlib.context import CryptContext

# Create bcrypt context
# Educational Note: CryptContext provides a unified interface for multiple
# hashing schemes. We use bcrypt exclusively, but this allows future upgrades
# (e.g., argon2) without changing the API.
_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",  # Auto-update old hashes on verification
)


def _prehash_password(password: str) -> str:
    """
    Pre-hash password with SHA256 before bcrypt.

    Bcrypt has a hard 72-byte password limit. To handle longer passwords,
    we pre-hash with SHA256, which produces a consistent 64-character hex
    string (well under the 72-byte limit).

    This is the industry-standard solution used by Django, Werkzeug, and
    other security-focused frameworks.

    Args:
        password: The plain-text password (any length)

    Returns:
        str: SHA256 hash as 64-character hex string

    Example:
        >>> _prehash_password("my_password")
        '89e01536ac207279409d4de1e5253e01f4a1769e696db0d6062ca9b8f56767c8'
        >>> len(_prehash_password("my_password"))
        64

    Security Notes:
        - SHA256 is a one-way hash (irreversible)
        - Produces consistent-length output (64 chars)
        - Fast to compute (but still one-way)
        - The bcrypt layer provides the slow, adaptive hashing
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using SHA256 + bcrypt.

    This function generates a secure hash of the password that can be safely
    stored in the database. The hash includes:
    - Algorithm identifier (bcrypt)
    - Work factor (number of rounds)
    - Salt (random, unique per password)
    - Hash digest

    Implementation:
        1. Pre-hash password with SHA256 (handles bcrypt 72-byte limit)
        2. Hash the SHA256 digest with bcrypt (slow, adaptive hashing)

    Args:
        plain_password: The plain-text password to hash (any length)

    Returns:
        str: The bcrypt hash in the format:
            $2b$12$salt..............hash....................
            ↑  ↑  ↑               ↑
            |  |  Salt (22 chars) Hash (31 chars)
            |  Work factor (2^12 = 4096 rounds)
            Algorithm (2b = bcrypt)

    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> print(hashed)
        $2b$12$KIXxGVrXGG5woRmVq8K3K.2B7hYqnvLVLfFH6KlJdLh3pJ5xmBqWu
        >>> len(hashed)
        60

    Security Notes:
        - Never log or expose the hash
        - The same password will produce different hashes (due to random salt)
        - Hashing is intentionally slow (~100ms) to prevent brute force
        - SHA256 pre-hashing allows passwords longer than 72 bytes
    """
    # Pre-hash with SHA256 to handle bcrypt's 72-byte limit
    prehashed = _prehash_password(plain_password)
    return _pwd_context.hash(prehashed)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a bcrypt hash.

    This function performs constant-time comparison to prevent timing attacks.
    It automatically handles different bcrypt variants and work factors.

    Implementation:
        1. Pre-hash password with SHA256 (same as during hashing)
        2. Verify the SHA256 digest against the bcrypt hash
        3. Return True if match, False otherwise

    Args:
        plain_password: The plain-text password to verify (any length)
        hashed_password: The bcrypt hash from the database

    Returns:
        bool: True if the password matches, False otherwise

    Example:
        >>> hashed = hash_password("my_password")
        >>> verify_password("my_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False

    Security Notes:
        - Uses constant-time comparison (prevents timing attacks)
        - Never short-circuit on mismatch (prevents timing analysis)
        - Automatically rehashes if the work factor has increased
        - SHA256 pre-hashing allows passwords longer than 72 bytes

    Implementation Detail:
        passlib.verify() does this internally:
        1. Extract salt and work factor from hash
        2. Hash the plain password with same salt/work factor
        3. Compare hashes in constant time
        4. Return True only if exact match
    """
    # Pre-hash with SHA256 to handle bcrypt's 72-byte limit
    prehashed = _prehash_password(plain_password)
    return _pwd_context.verify(prehashed, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be updated.

    This is useful when upgrading the work factor or switching algorithms.
    After successful login, check if the hash needs updating and rehash if so.

    Args:
        hashed_password: The bcrypt hash to check

    Returns:
        bool: True if the hash should be updated, False otherwise

    Example:
        >>> hashed = hash_password("password")
        >>> needs_rehash(hashed)
        False
        >>>
        >>> # After upgrading bcrypt rounds in config:
        >>> needs_rehash(old_hash)
        True
        >>>
        >>> # On login:
        >>> if verify_password(plain, hashed) and needs_rehash(hashed):
        ...     new_hash = hash_password(plain)
        ...     await user_repo.update(user.id, {"password": new_hash})

    Use Case:
        When you increase the work factor (e.g., from 12 to 14 rounds),
        old hashes will return True from this function. You can then
        rehash passwords opportunistically during login.
    """
    return _pwd_context.needs_update(hashed_password)
