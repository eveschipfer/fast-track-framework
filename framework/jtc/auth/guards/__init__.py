"""
Authentication Guards (Sprint 10)

This module provides authentication guards implementing the Guard Pattern.

Available Guards:
    - JwtGuard: Stateless JWT authentication for APIs
    - SessionGuard: Stateful session authentication for Web (placeholder)
"""

from jtc.auth.guards.jwt_guard import JwtGuard

__all__ = [
    "JwtGuard",
]
