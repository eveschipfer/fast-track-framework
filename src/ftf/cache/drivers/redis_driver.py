"""
Redis Cache Driver (Sprint 3.7)

Production-grade cache driver using Redis for high performance.

Educational Note:
    Why Redis for production?
        ✅ In-memory storage (microsecond latency)
        ✅ Atomic operations (thread-safe increment)
        ✅ Built-in TTL support (automatic expiration)
        ✅ Horizontal scalability (Redis Cluster)
        ✅ Pub/Sub for cache invalidation
        ✅ Persistence options (RDB, AOF)

    Why pickle?
        - Redis stores bytes, so we can store any Python object
        - Alternative: JSON (but limited to JSON-serializable types)
        - Pydantic models, SQLAlchemy objects, dataclasses all work

Comparison with Laravel:
    Laravel RedisStore:
        - Uses phpredis or predis
        - Serializes with serialize()
        - Namespaces keys with prefix

    Fast Track RedisDriver:
        - Uses redis-py (async)
        - Serializes with pickle
        - Optional key prefix support
"""

import pickle
from typing import Any, Optional

from ftf.cache.drivers.base import CacheDriver

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None  # Redis not installed


class RedisDriver(CacheDriver):
    """
    Redis-based cache driver for production.

    Requires redis-py with async support:
        pip install redis[async]

    Benefits:
        ✅ High performance (in-memory, sub-millisecond latency)
        ✅ Atomic operations (thread-safe)
        ✅ Built-in TTL (automatic expiration)
        ✅ Scalable (Redis Cluster, Sentinel)

    Configuration:
        REDIS_HOST=localhost
        REDIS_PORT=6379
        REDIS_DB=0
        REDIS_PASSWORD=secret
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "ftf_cache:",
    ):
        """
        Initialize Redis cache driver.

        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number (0-15)
            password: Redis password (if auth enabled)
            prefix: Key prefix to namespace cache keys

        Example:
            driver = RedisDriver(
                host="localhost",
                port=6379,
                db=0,
                password="secret",
                prefix="myapp:"
            )

        Raises:
            ImportError: If redis-py is not installed
        """
        if aioredis is None:
            raise ImportError(
                "Redis driver requires redis-py with async support. "
                "Install with: pip install 'redis[async]'"
            )

        self.prefix = prefix
        self.redis = aioredis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False,  # We handle bytes (pickle)
        )

    def _make_key(self, key: str) -> str:
        """
        Add prefix to key for namespacing.

        Args:
            key: Original cache key

        Returns:
            Prefixed key

        Example:
            >>> driver._make_key("user:123")
            'ftf_cache:user:123'
        """
        return f"{self.prefix}{key}"

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from Redis.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value (unpickled) or default

        Example:
            user = await driver.get("user:123")
        """
        prefixed_key = self._make_key(key)

        try:
            data = await self.redis.get(prefixed_key)

            if data is None:
                return default

            # Unpickle value
            return pickle.loads(data)

        except (redis.RedisError, pickle.PickleError):
            return default

    async def put(self, key: str, value: Any, ttl: int) -> None:
        """
        Store a value in Redis with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be pickled)
            ttl: Time to live in seconds

        Example:
            await driver.put("user:123", user, ttl=3600)
        """
        prefixed_key = self._make_key(key)

        # Pickle the value
        pickled_value = pickle.dumps(value)

        # Store with TTL (Redis handles expiration automatically)
        await self.redis.setex(prefixed_key, ttl, pickled_value)

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Atomically increment a counter in Redis.

        Redis's INCRBY is atomic, making it perfect for rate limiting.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment

        Example:
            count = await driver.increment(f"throttle:{ip}")
        """
        prefixed_key = self._make_key(key)

        # Redis INCRBY is atomic
        new_value = await self.redis.incrby(prefixed_key, amount)

        # Set TTL if this is a new key (first increment)
        # Note: For rate limiting, caller should manage TTL
        ttl = await self.redis.ttl(prefixed_key)
        if ttl == -1:  # No expiration set
            await self.redis.expire(prefixed_key, 3600)  # Default 1 hour

        return new_value

    async def forget(self, key: str) -> None:
        """
        Remove a value from Redis.

        Args:
            key: Cache key to delete

        Example:
            await driver.forget("user:123")
        """
        prefixed_key = self._make_key(key)
        await self.redis.delete(prefixed_key)

    async def flush(self) -> None:
        """
        Clear all keys with our prefix from Redis.

        Warning:
            This only clears keys with the configured prefix.
            To clear entire Redis DB, use FLUSHDB (dangerous!).

        Example:
            await driver.flush()  # Clears all ftf_cache:* keys
        """
        # Find all keys with our prefix
        pattern = f"{self.prefix}*"
        cursor = 0

        while True:
            # Scan with cursor (handles large datasets)
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)

            if keys:
                # Delete batch of keys
                await self.redis.delete(*keys)

            if cursor == 0:
                break

    async def close(self) -> None:
        """
        Close Redis connection.

        Should be called on application shutdown.

        Example:
            await driver.close()
        """
        await self.redis.aclose()
