# Cache Commands

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21

This section documents all `cache:*` commands used for managing the application cache system.

## Overview

Cache commands provide tools to manage cached data, similar to Laravel's `php artisan cache:*` commands. The framework supports multiple cache drivers including file, Redis, and in-memory (array).

**Supported Cache Drivers**:
- `file`: File-based cache (default)
- `redis`: Redis-backed cache
- `array`: In-memory cache (testing only)

---

## cache:clear

Clear all cached data from the active cache driver.

### Syntax

```bash
jtc cache:clear
```

### Description

Removes all cache entries from the active cache driver. This is a destructive operation that affects all cached data.

⚠️ **Warning**: This affects ALL cache keys. Use with caution in production.

### Examples

```bash
# Clear all cache
jtc cache:clear
# Output:
# Clearing cache...
# ✓ Cache cleared successfully!
# Driver: file
```

### Use Cases

- **After deployment**: Clear old cached configuration
- **After database changes**: Clear cached queries
- **Debugging cache issues**: Start with a clean slate
- **Configuration changes**: Clear cached settings

### Prerequisites

- Cache driver configured in environment variables (`.env` file)
- Appropriate permissions for cache storage directory (if using file driver)

### Configuration

```bash
# .env file
CACHE_DRIVER=file        # Options: file, redis, array
CACHE_FILE_PATH=storage/framework/cache

# Redis configuration (if using Redis)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_password
REDIS_CACHE_PREFIX=ftf_cache:
```

### Educational Note

Similar to:
- Laravel: `php artisan cache:clear`
- Django: `python manage.py cache`

---

## cache:forget

Remove a specific cache key from the cache.

### Syntax

```bash
jtc cache:forget <key>
```

### Arguments

- `key`: Cache key to remove

### Description

Surgically removes a specific cache key without affecting other cached data. This is more targeted than `cache:clear`.

### Examples

```bash
# Forget specific user cache
jtc cache:forget user:123
# Output:
# Removing cache key: user:123
# ✓ Cache key 'user:123' removed

# Forget config cache
jtc cache:forget config:app
# Output:
# Removing cache key: config:app
# ✓ Cache key 'config:app' removed
```

### Use Cases

- **User updated**: `jtc cache:forget user:123`
- **Config changed**: `jtc cache:forget config:app`
- **Product updated**: `jtc cache:forget product:456`
- **Post updated**: `jtc cache:forget post:789`

### Key Naming Conventions

Common cache key patterns:
- `user:{id}`: User data
- `config:{name}`: Configuration
- `query:{hash}`: Cached query results
- `product:{id}`: Product data
- `{entity}:{id}`: Generic entity cache

### Comparison

| Command | Scope | Use Case |
|----------|--------|-----------|
| `cache:clear` | All cache keys | Full cache reset |
| `cache:forget` | Single key | Targeted invalidation |

---

## cache:config

Display the current cache configuration.

### Syntax

```bash
jtc cache:config
```

### Description

Shows the active cache driver and configuration settings from environment variables. Useful for debugging cache setup issues.

### Examples

```bash
# Show file cache configuration
jtc cache:config
# Output:
# Cache Configuration
# ┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Setting       ┃ Value                    ┃
# ┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ Driver        │ file                     │
# │ File Path     │ storage/framework/cache  │
# └───────────────┴──────────────────────────┘

# Show Redis cache configuration
jtc cache:config
# Output:
# Cache Configuration
# ┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Setting       ┃ Value                    ┃
# ┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ Driver        │ redis                    │
# │ Redis Host    │ localhost                │
# │ Redis Port    │ 6379                    │
# │ Redis DB      │ 0                        │
# │ Redis Prefix  │ ftf_cache:              │
# └───────────────┴──────────────────────────┘
```

### Purpose

This command helps:
- Debug cache configuration issues
- Verify driver settings
- Check environment variable values
- Troubleshoot cache connection problems

### Configuration Display

The command displays:
- **Driver**: Active cache driver (file, redis, array)
- **File Path**: Cache directory (file driver)
- **Redis Settings**: Host, port, DB, prefix, password (Redis driver)
- **Type**: Cache type (array driver)

### Changing Configuration

```bash
# In .env file
CACHE_DRIVER=redis
```

```bash
# Then verify with config command
jtc cache:config
```

---

## cache:test

Test cache functionality to verify the cache is working correctly.

### Syntax

```bash
jtc cache:test
```

### Description

Performs basic cache operations (put, get, increment, forget) to verify the cache is configured and working correctly.

### Examples

```bash
# Test cache operations
jtc cache:test
# Output:
# Testing cache operations...
# 
# 1. Testing put...
#    ✓ Put: Stored test value
# 2. Testing get...
#    ✓ Get: Retrieved test value
# 3. Testing increment...
#    ✓ Increment: Counter works
# 4. Testing forget...
#    ✓ Forget: Removed test value
# 
# ✓ Cache is working correctly!
```

### Tests Performed

The command tests:
1. **Put**: Store a value in cache
2. **Get**: Retrieve the stored value
3. **Increment**: Test atomic counter increment
4. **Forget**: Remove a cached value

### Use Cases

- **After deployment**: Verify cache is accessible
- **After configuration changes**: Test new driver settings
- **Debugging**: Verify cache connectivity
- **Redis connection issues**: Test Redis is reachable

### Troubleshooting

```bash
# If test fails:
jtc cache:test
# Output: ✗ Cache tests failed
# Check cache configuration with:
jtc cache:config

# Verify Redis connection (if using Redis)
redis-cli ping

# Check file permissions (if using file driver)
ls -la storage/framework/cache
```

### Expected Behavior

All four tests should pass:
- ✓ Put: Stores data successfully
- ✓ Get: Retrieves exact same data
- ✓ Increment: Atomic counter operations work
- ✓ Forget: Removes data successfully

---

## Cache Driver Configuration

### File Cache (Default)

```bash
# .env
CACHE_DRIVER=file
CACHE_FILE_PATH=storage/framework/cache
```

**Pros**:
- Simple setup, no external dependencies
- Works offline
- Easy to inspect cache files

**Cons**:
- Slower than Redis
- Not shared across multiple servers
- Filesystem I/O overhead

**Use When**:
- Development environment
- Single server deployment
- Simple caching needs

### Redis Cache

```bash
# .env
CACHE_DRIVER=redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_password
REDIS_CACHE_PREFIX=ftf_cache:
```

**Pros**:
- Very fast
- Shared across servers
- Supports data persistence
- Atomic operations
- Advanced features (pub/sub, streams)

**Cons**:
- Requires Redis server
- External dependency

**Use When**:
- Production environment
- Multiple servers
- High-performance requirements
- Need atomic operations

### Array Cache (Testing)

```bash
# .env
CACHE_DRIVER=array
```

**Pros**:
- Fastest (in-memory)
- No external dependencies
- Perfect for unit tests

**Cons**:
- Not persistent
- Lost between requests
- Not for production

**Use When**:
- Unit tests
- Development only
- Debugging

---

## Common Cache Patterns

### Caching Database Queries

```python
from jtc.cache import Cache

# Check cache first
data = await Cache.get(f"user:{user_id}")
if data is None:
    # Cache miss - fetch from DB
    data = await repo.find(user_id)
    # Store in cache for 1 hour
    await Cache.put(f"user:{user_id}", data, ttl=3600)

return data
```

### Cache Invalidation

```python
# On user update
await repo.update(user)
# Invalidate cache
jtc cache:forget user:user_id

# Or clear all cache
jtc cache:clear
```

### Atomic Counters

```python
# Track view count
views = await Cache.increment(f"post:{post_id}:views")

# Rate limiting
requests = await Cache.increment(f"rate_limit:{ip}:{hour}")
if requests > 100:
    # Rate limit exceeded
```

---

## Best Practices

### Key Naming

- Use descriptive keys: `user:123`, `config:app`
- Use prefixes for organization: `cache:`, `session:`, `query:`
- Avoid spaces or special characters
- Keep keys reasonably short

### TTL (Time To Live)

- Set appropriate TTL: don't cache forever
- Short TTL for rapidly changing data
- Long TTL for static data
- Default to reasonable values (1 hour, 24 hours, 7 days)

### Cache Invalidation

- Invalidate on data changes
- Use `cache:forget` for targeted invalidation
- Use `cache:clear` sparingly in production
- Consider cache warming after clearing

### Production Considerations

- Use Redis in production
- Monitor cache hit/miss ratios
- Set up cache monitoring
- Document cache keys and TTLs
- Have cache warmup strategies

---

## Troubleshooting

### Cache Not Working

```bash
# 1. Check configuration
jtc cache:config

# 2. Test cache
jtc cache:test

# 3. Check permissions (file cache)
ls -la storage/framework/cache

# 4. Check Redis connection (Redis cache)
redis-cli ping
```

### Redis Connection Issues

```bash
# Check Redis is running
systemctl status redis

# Test Redis connection
redis-cli ping

# Check firewall
telnet localhost 6379

# Verify Redis logs
tail -f /var/log/redis/redis-server.log
```

### File Cache Permissions

```bash
# Check cache directory
ls -la storage/framework/cache

# Fix permissions
chmod -R 755 storage/framework/cache
chown -R www-data:www-data storage/framework/cache
```

---

## Comparison with Laravel

| Laravel | Fast Track | Purpose |
|---------|-------------|----------|
| `php artisan cache:clear` | `jtc cache:clear` | Clear all cache |
| `php artisan cache:forget key` | `jtc cache:forget key` | Forget specific key |
| `php artisan config:cache` | `jtc cache:config` | Show cache config (different purpose) |
| `php artisan cache:table` | N/A | Create cache table (framework supports multiple drivers) |

---

## Next Steps

- [Make Commands](make-commands.md) - Generate models, repositories, controllers, etc.
- [Database Commands](db-commands.md) - Migrate, rollback, and seed databases
- [Auth Commands](auth-commands.md) - Authentication utilities
- [Queue Commands](queue-commands.md) - Background job management
- [Test Commands](test-commands.md) - Testing utilities
- [Deploy Commands](deploy-commands.md) - Deployment automation

---

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21
