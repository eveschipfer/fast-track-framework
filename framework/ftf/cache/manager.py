"""
Cache Manager (Sprint 3.7)

Singleton cache manager that delegates to the appropriate driver based on
the CACHE_DRIVER environment variable.

This is the main entry point for all caching operations.

Educational Note:
    This implements two patterns:
    1. **Singleton Pattern**: Only one Cache instance exists
    2. **Strategy Pattern**: Delegates to different drivers

    Laravel equivalent:
        Cache::get('key')           → await Cache.get('key')
        Cache::put('key', $val, 60) → await Cache.put('key', val, 60)
        Cache::remember('key', 60, fn() => ...) → await Cache.remember('key', 60, async fn)

    Configuration (.env):
        CACHE_DRIVER=file   # Development (no Redis)
        CACHE_DRIVER=redis  # Production (high performance)
        CACHE_DRIVER=array  # Testing (in-memory)

Usage:
    from ftf.cache import Cache

    # Get cached value
    user = await Cache.get("user:123")

    # Store with TTL
    await Cache.put("user:123", user, ttl=3600)

    # Remember pattern (cache on miss)
    user = await Cache.remember("user:123", 3600, fetch_user)

    # Rate limiting
    count = await Cache.increment(f"throttle:{ip}")
"""

import os
from typing import Any, Callable, Optional

from ftf.cache.drivers.array_driver import ArrayDriver
from ftf.cache.drivers.base import CacheDriver
from ftf.cache.drivers.file_driver import FileDriver


class CacheManager:
    """
    Singleton cache manager.

    Automatically configured from CACHE_DRIVER environment variable.
    Delegates all operations to the active driver.

    Drivers:
        - file: FileDriver (development, no Redis required)
        - redis: RedisDriver (production, high performance)
        - array: ArrayDriver (testing, in-memory)

    Default: file (development-friendly)
    """

    _instance: Optional["CacheManager"] = None
    _driver: Optional[CacheDriver] = None

    def __new__(cls) -> "CacheManager":
        """
        Singleton pattern: ensure only one instance exists.

        Returns:
            Singleton Cache instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_driver()
        return cls._instance

    def _initialize_driver(self) -> None:
        """
        Initialize cache driver based on CACHE_DRIVER env var.

        Reads configuration from environment:
            CACHE_DRIVER=file|redis|array (default: file)

        For Redis:
            REDIS_HOST=localhost (default)
            REDIS_PORT=6379 (default)
            REDIS_DB=0 (default)
            REDIS_PASSWORD=<password> (optional)

        Raises:
            ValueError: If CACHE_DRIVER is invalid
            ImportError: If Redis driver requested but redis-py not installed
        """
        driver_name = os.getenv("CACHE_DRIVER", "file").lower()

        if driver_name == "file":
            # File driver (development)
            cache_path = os.getenv("CACHE_FILE_PATH", "storage/framework/cache")
            self._driver = FileDriver(cache_path=cache_path)

        elif driver_name == "redis":
            # Redis driver (production)
            from ftf.cache.drivers.redis_driver import RedisDriver

            self._driver = RedisDriver(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
                password=os.getenv("REDIS_PASSWORD"),
                prefix=os.getenv("REDIS_CACHE_PREFIX", "ftf_cache:"),
            )

        elif driver_name == "array":
            # Array driver (testing)
            self._driver = ArrayDriver()

        else:
            raise ValueError(
                f"Invalid CACHE_DRIVER: {driver_name}. "
                f"Supported drivers: file, redis, array"
            )

    @property
    def driver(self) -> CacheDriver:
        """
        Get the active cache driver.

        Returns:
            Active CacheDriver instance

        Example:
            driver = Cache.driver
            await driver.flush()
        """
        if self._driver is None:
            self._initialize_driver()
        return self._driver

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default

        Example:
            user = await Cache.get("user:123")
            if user is None:
                user = await fetch_user(123)
        """
        return await self.driver.get(key, default)

    async def put(self, key: str, value: Any, ttl: int) -> None:
        """
        Store a value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be pickled)
            ttl: Time to live in seconds

        Example:
            await Cache.put("user:123", user, ttl=3600)  # 1 hour
        """
        await self.driver.put(key, value, ttl)

    async def remember(
        self, key: str, ttl: int, callback: Callable[[], Any]
    ) -> Any:
        """
        Get cached value or execute callback and cache result.

        This is the "cache aside" pattern:
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
            user = await Cache.remember(
                f"user:{user_id}",
                3600,
                lambda: fetch_user(user_id)
            )

        Educational Note:
            Laravel:
                $user = Cache::remember('user:123', 3600, function() {
                    return User::find(123);
                });

            Fast Track:
                user = await Cache.remember('user:123', 3600, lambda: User.find(123))
        """
        # Check cache
        value = await self.get(key)
        if value is not None:
            return value

        # Cache miss - execute callback
        value = await callback()

        # Store in cache
        await self.put(key, value, ttl)

        return value

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in cache.

        This is crucial for rate limiting.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment

        Example:
            # Rate limiting
            count = await Cache.increment(f"throttle:{ip}:{path}")
            if count > 60:
                raise RateLimitExceeded
        """
        return await self.driver.increment(key, amount)

    async def forget(self, key: str) -> None:
        """
        Remove a value from cache.

        Args:
            key: Cache key to delete

        Example:
            await Cache.forget("user:123")
        """
        await self.driver.forget(key)

    async def flush(self) -> None:
        """
        Clear all cache.

        Warning:
            This removes ALL cached data. Use with caution in production.

        Example:
            # Clear all cache (e.g., deployment, testing)
            await Cache.flush()
        """
        await self.driver.flush()

    async def close(self) -> None:
        """
        Close cache driver connections (for Redis).

        Should be called on application shutdown.

        Example:
            # In FastAPI lifespan
            await Cache.close()
        """
        if hasattr(self.driver, "close"):
            await self.driver.close()


# Singleton instance
Cache = CacheManager()
