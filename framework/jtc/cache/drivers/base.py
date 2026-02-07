"""
Abstract Cache Driver (Sprint 3.7)

This module defines the CacheDriver abstract base class that all cache drivers
must implement. This ensures a consistent interface across drivers.

Educational Note:
    This is the Strategy interface in the Strategy Pattern. All concrete drivers
    (FileDriver, RedisDriver, ArrayDriver) must implement these methods.

    Why async?
        - Redis operations are I/O-bound (network calls)
        - File operations can block the event loop
        - Consistency: all drivers use the same async interface

    Why pickle?
        - Allows caching complex Python objects (not just strings)
        - Can cache Pydantic models, SQLAlchemy objects, dataclasses
        - Laravel uses serialize() in PHP, we use pickle in Python

Comparison with Laravel:
    Laravel:
        interface Store {
            public function get($key);
            public function put($key, $value, $seconds);
            public function increment($key, $value = 1);
            public function forget($key);
            public function flush();
        }

    Fast Track:
        class CacheDriver(ABC):
            async def get(self, key: str, default: Any = None) -> Any
            async def put(self, key: str, value: Any, ttl: int) -> None
            async def increment(self, key: str, amount: int = 1) -> int
            async def forget(self, key: str) -> None
            async def flush(self) -> None
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheDriver(ABC):
    """
    Abstract base class for cache drivers.

    All cache drivers (File, Redis, Array) must implement these methods.
    This ensures consistent behavior across all drivers.
    """

    @abstractmethod
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from the cache.

        Args:
            key: Cache key
            default: Default value if key not found or expired

        Returns:
            Cached value (unpickled) or default

        Example:
            user = await driver.get("user:123")
            if user is None:
                user = await fetch_user(123)
        """
        pass

    @abstractmethod
    async def put(self, key: str, value: Any, ttl: int) -> None:
        """
        Store a value in the cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be pickled)
            ttl: Time to live in seconds

        Example:
            await driver.put("user:123", user, ttl=3600)  # 1 hour
        """
        pass

    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in the cache.

        This is crucial for rate limiting. If the key doesn't exist,
        it should be created with the initial value of `amount`.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment

        Example:
            # Rate limiting
            count = await driver.increment(f"throttle:{ip}:{path}")
            if count > 60:
                raise RateLimitExceeded
        """
        pass

    @abstractmethod
    async def forget(self, key: str) -> None:
        """
        Remove a value from the cache.

        Args:
            key: Cache key to delete

        Example:
            await driver.forget("user:123")
        """
        pass

    @abstractmethod
    async def flush(self) -> None:
        """
        Clear all values from the cache.

        Warning:
            This removes ALL cached data. Use with caution in production.

        Example:
            # Clear all cache (e.g., deployment, testing)
            await driver.flush()
        """
        pass

    async def remember(
        self, key: str, ttl: int, callback: callable
    ) -> Any:
        """
        Get cached value or execute callback and cache result.

        This is a convenience method that implements the "cache aside" pattern:
        1. Try to get from cache
        2. If miss, execute callback
        3. Store result in cache
        4. Return result

        Args:
            key: Cache key
            ttl: Time to live in seconds
            callback: Async function to call on cache miss

        Returns:
            Cached or newly computed value

        Example:
            async def fetch_user(user_id: int) -> User:
                return await db.query(User).filter(User.id == user_id).first()

            # Caches for 1 hour on first call, returns cached on subsequent calls
            user = await driver.remember(
                f"user:{user_id}",
                3600,
                lambda: fetch_user(user_id)
            )

        Educational Note:
            This is called "remember" in Laravel:
                $user = Cache::remember('user:123', 3600, function() {
                    return User::find(123);
                });

            Fast Track equivalent:
                user = await Cache.remember('user:123', 3600, lambda: User.find(123))
        """
        # Try to get from cache
        value = await self.get(key)

        # Cache hit - return cached value
        if value is not None:
            return value

        # Cache miss - execute callback
        value = await callback()

        # Store in cache
        await self.put(key, value, ttl)

        return value
