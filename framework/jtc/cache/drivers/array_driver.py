"""
Array Cache Driver (Sprint 3.7)

In-memory cache driver for testing and development.
All data is lost when the application restarts.

Educational Note:
    Why an in-memory driver?
        ✅ Testing: No file I/O or network calls (fast tests)
        ✅ Development: Simple, no setup required
        ✅ Isolation: Each test gets fresh cache

    Comparison with Laravel:
        Laravel ArrayStore:
            - In-memory PHP array
            - Cleared on each request
            - Used for testing

        Fast Track ArrayDriver:
            - In-memory Python dict
            - Cleared manually or on restart
            - Used for testing
"""

import time
from typing import Any, Dict, Tuple

from jtc.cache.drivers.base import CacheDriver


class ArrayDriver(CacheDriver):
    """
    In-memory cache driver for testing.

    Stores cache entries in a Python dictionary. All data is lost
    when the driver is destroyed or the application restarts.

    Benefits:
        ✅ No external dependencies
        ✅ Fast (no I/O)
        ✅ Simple (just a dict)
        ✅ Perfect for testing

    Warning:
        ⚠️  NOT for production (data lost on restart)
        ⚠️  NOT shared across workers/processes
        ⚠️  NOT persistent
    """

    def __init__(self):
        """Initialize empty in-memory cache."""
        # Store: {key: (value, expiration_timestamp)}
        self.store: Dict[str, Tuple[Any, float]] = {}

    def _is_expired(self, expiration: float) -> bool:
        """
        Check if cache entry is expired.

        Args:
            expiration: Expiration timestamp

        Returns:
            True if expired, False otherwise
        """
        return time.time() > expiration

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from memory.

        Args:
            key: Cache key
            default: Default value if not found or expired

        Returns:
            Cached value or default

        Example:
            user = await driver.get("user:123")
        """
        if key not in self.store:
            return default

        value, expiration = self.store[key]

        # Check expiration
        if self._is_expired(expiration):
            # Expired, remove and return default
            del self.store[key]
            return default

        return value

    async def put(self, key: str, value: Any, ttl: int) -> None:
        """
        Store a value in memory with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Example:
            await driver.put("user:123", user, ttl=3600)
        """
        expiration = time.time() + ttl
        self.store[key] = (value, expiration)

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in memory.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment

        Example:
            count = await driver.increment(f"throttle:{ip}")
        """
        # Get current value
        current = await self.get(key, default=0)

        # Ensure it's an integer
        if not isinstance(current, int):
            current = 0

        # Increment
        new_value = current + amount

        # Store with 1 hour TTL
        await self.put(key, new_value, ttl=3600)

        return new_value

    async def forget(self, key: str) -> None:
        """
        Remove a value from memory.

        Args:
            key: Cache key to delete

        Example:
            await driver.forget("user:123")
        """
        if key in self.store:
            del self.store[key]

    async def flush(self) -> None:
        """
        Clear all values from memory.

        Example:
            await driver.flush()
        """
        self.store.clear()
