"""
Cache System (Sprint 3.7)

Multi-driver caching system inspired by Laravel's Cache facade.
Supports Redis, File, and Array drivers with seamless switching via .env

Public API:
    Cache - Singleton cache manager (auto-configured from CACHE_DRIVER)
    get(key, default=None) - Retrieve cached value
    put(key, value, ttl) - Store value with TTL
    remember(key, ttl, callback) - Cache with callback on miss
    increment(key, amount=1) - Increment counter (for rate limiting)
    forget(key) - Delete cached value
    flush() - Clear all cache

Usage:
    from ftf.cache import Cache

    # Get cached value
    user = await Cache.get("user:123")

    # Store with TTL
    await Cache.put("user:123", user, ttl=3600)

    # Remember pattern (cache on miss)
    user = await Cache.remember("user:123", 3600, lambda: fetch_user(123))

    # Rate limiting
    count = await Cache.increment(f"throttle:{ip}")

Educational Note:
    This follows Laravel's Cache facade pattern but adapted for async Python:

    Laravel (PHP):
        Cache::get('key');
        Cache::put('key', $value, $seconds);
        Cache::remember('key', $seconds, fn() => expensive());

    Fast Track (Python):
        await Cache.get('key')
        await Cache.put('key', value, seconds)
        await Cache.remember('key', seconds, expensive_async)

    The Strategy Pattern allows switching drivers via .env without code changes:
        CACHE_DRIVER=file   # Development (no Redis required)
        CACHE_DRIVER=redis  # Production (high performance)
"""

from ftf.cache.manager import Cache

__all__ = ["Cache"]
