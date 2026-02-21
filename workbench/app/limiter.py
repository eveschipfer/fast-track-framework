"""
Rate Limiter Instance

Shared slowapi Limiter for use across the application.
Defined in its own module to avoid circular imports between
main.py and controllers.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
