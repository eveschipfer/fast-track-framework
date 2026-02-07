"""
Cache Drivers (Sprint 3.7)

Abstract base class and concrete implementations for cache storage.

Drivers:
    - CacheDriver: Abstract base class (contract)
    - FileDriver: Filesystem storage (development)
    - RedisDriver: Redis storage (production)
    - ArrayDriver: In-memory storage (testing)

Educational Note:
    This uses the Strategy Pattern:
    - CacheDriver is the Strategy interface
    - FileDriver, RedisDriver, ArrayDriver are concrete strategies
    - CacheManager is the Context that delegates to strategies

    Laravel equivalent:
        - Illuminate\\Contracts\\Cache\\Store (interface)
        - FileStore, RedisStore, ArrayStore (concrete)
"""

from jtc.cache.drivers.base import CacheDriver
from jtc.cache.drivers.file_driver import FileDriver
from jtc.cache.drivers.redis_driver import RedisDriver
from jtc.cache.drivers.array_driver import ArrayDriver

__all__ = ["CacheDriver", "FileDriver", "RedisDriver", "ArrayDriver"]
