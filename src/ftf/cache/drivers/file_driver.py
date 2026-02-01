"""
File Cache Driver (Sprint 3.7)

Stores cache entries as files in storage/framework/cache/.
Each file contains: expiration timestamp + pickled data.

This is the default driver for development since it doesn't require Redis.

Educational Note:
    File Structure:
        storage/framework/cache/
        ├── 5f4dcc3b5aa765d61d8327deb882cf99  # hash("user:123")
        ├── 098f6bcd4621d373cade4e832627b4f6  # hash("config:app")
        └── ...

    File Format (binary):
        [8 bytes: expiration timestamp as float]
        [remaining bytes: pickled data]

    Why hash the key?
        - File systems have limits on filename characters
        - Keys might contain slashes, colons, etc.
        - Hashing ensures valid filenames

    Why pickle?
        - Can cache complex Python objects (Pydantic models, SQLAlchemy)
        - Laravel uses serialize() in PHP
        - Alternative: JSON (but limited to JSON-serializable types)

Comparison with Laravel:
    Laravel FileStore:
        - Stores in storage/framework/cache/data/
        - Uses serialize() for PHP objects
        - Filename = hash of key

    Fast Track FileDriver:
        - Stores in storage/framework/cache/
        - Uses pickle for Python objects
        - Filename = md5 hash of key
"""

import hashlib
import os
import pickle
import struct
import time
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os

from ftf.cache.drivers.base import CacheDriver


class FileDriver(CacheDriver):
    """
    File-based cache driver for development.

    Stores cache entries as files with expiration timestamps.
    Good for development, but not recommended for production (use Redis instead).

    Warning:
        - Not suitable for high-traffic production (file I/O overhead)
        - Limited concurrency support (file locking not implemented)
        - Use Redis for production environments

    Benefits:
        ✅ No external dependencies (no Redis/Memcached required)
        ✅ Easy to inspect cached data (just read files)
        ✅ Survives app restarts (persistent)
        ✅ Good for development and testing
    """

    def __init__(self, cache_path: str = "storage/framework/cache"):
        """
        Initialize file cache driver.

        Args:
            cache_path: Directory to store cache files (relative to project root)

        Example:
            driver = FileDriver("storage/framework/cache")
        """
        self.cache_path = Path(cache_path)

        # Create cache directory if it doesn't exist
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """
        Get file path for a cache key.

        Uses MD5 hash to ensure valid filename regardless of key characters.

        Args:
            key: Cache key (e.g., "user:123", "config:app")

        Returns:
            Path to cache file

        Example:
            >>> driver._get_file_path("user:123")
            Path('storage/framework/cache/5f4dcc3b5aa765d61d8327deb882cf99')
        """
        # Hash the key to create a valid filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_path / key_hash

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from file cache.

        Checks expiration timestamp. If expired, deletes file and returns default.

        Args:
            key: Cache key
            default: Default value if not found or expired

        Returns:
            Cached value (unpickled) or default

        Example:
            user = await driver.get("user:123")
            if user is None:
                user = await fetch_user(123)
                await driver.put("user:123", user, 3600)
        """
        file_path = self._get_file_path(key)

        # Check if file exists
        if not await aiofiles.os.path.exists(file_path):
            return default

        try:
            # Read file
            async with aiofiles.open(file_path, "rb") as f:
                data = await f.read()

            # Parse expiration and value
            # Format: [8 bytes timestamp][pickled data]
            if len(data) < 8:
                # Corrupted file, delete it
                await aiofiles.os.remove(file_path)
                return default

            # Unpack expiration timestamp (8 bytes, double)
            expiration = struct.unpack("d", data[:8])[0]

            # Check if expired
            if time.time() > expiration:
                # Expired, delete file
                await aiofiles.os.remove(file_path)
                return default

            # Unpickle value
            value = pickle.loads(data[8:])
            return value

        except (OSError, pickle.PickleError, struct.error):
            # File error or corrupted data, return default
            # Try to clean up corrupted file
            try:
                await aiofiles.os.remove(file_path)
            except OSError:
                pass
            return default

    async def put(self, key: str, value: Any, ttl: int) -> None:
        """
        Store a value in file cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be pickled)
            ttl: Time to live in seconds

        Example:
            await driver.put("user:123", user, ttl=3600)  # 1 hour
        """
        file_path = self._get_file_path(key)

        # Calculate expiration timestamp
        expiration = time.time() + ttl

        # Pickle the value
        pickled_value = pickle.dumps(value)

        # Pack expiration + pickled data
        # Format: [8 bytes timestamp][pickled data]
        data = struct.pack("d", expiration) + pickled_value

        # Write to file (atomic write using temp file)
        temp_path = file_path.with_suffix(".tmp")
        try:
            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(data)

            # Atomic rename (overwrites existing file)
            await aiofiles.os.rename(temp_path, file_path)

        except OSError:
            # Clean up temp file on error
            try:
                await aiofiles.os.remove(temp_path)
            except OSError:
                pass
            raise

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in file cache.

        If key doesn't exist, creates it with initial value of `amount`.
        If value is not an integer, treats it as 0 and increments.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment

        Example:
            # Rate limiting
            count = await driver.increment(f"throttle:{ip}")
            if count > 60:
                raise RateLimitExceeded
        """
        # Get current value
        current = await self.get(key, default=0)

        # Ensure it's an integer
        if not isinstance(current, int):
            current = 0

        # Increment
        new_value = current + amount

        # Store with 1 hour TTL (default for counters)
        # Note: For rate limiting, caller should set appropriate TTL
        await self.put(key, new_value, ttl=3600)

        return new_value

    async def forget(self, key: str) -> None:
        """
        Remove a value from file cache.

        Args:
            key: Cache key to delete

        Example:
            await driver.forget("user:123")
        """
        file_path = self._get_file_path(key)

        try:
            await aiofiles.os.remove(file_path)
        except FileNotFoundError:
            # Already deleted, no problem
            pass
        except OSError:
            # Permission error or other OS error
            # In production, you might want to log this
            pass

    async def flush(self) -> None:
        """
        Clear all files from cache directory.

        Warning:
            This removes ALL cached data. Use with caution.

        Example:
            # Clear all cache (e.g., deployment, testing)
            await driver.flush()
        """
        # Remove all files in cache directory
        for file_path in self.cache_path.glob("*"):
            if file_path.is_file():
                try:
                    await aiofiles.os.remove(file_path)
                except OSError:
                    # Permission error, skip
                    pass
