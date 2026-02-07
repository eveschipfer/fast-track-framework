"""
Local filesystem driver.

Stores files on the local filesystem using aiofiles for async I/O.
This is the default driver for development and production when using local storage.
"""

import os
from pathlib import Path
from typing import BinaryIO

import aiofiles
import aiofiles.os

from jtc.storage.exceptions import FileNotFoundException, StorageConfigException


class LocalDriver:
    """
    Local filesystem storage driver.

    This driver stores files on the local filesystem. Features:
    - Async I/O with aiofiles (non-blocking)
    - Automatic directory creation
    - Configurable root path
    - URL generation for web serving

    Pattern: Adapter Pattern
    ------------------------
    Adapts the local filesystem to the StorageDriver interface.

    Educational Note:
    ----------------
    We use aiofiles instead of regular file I/O to avoid blocking the
    event loop. Even filesystem operations can be slow (especially on
    network filesystems or slow disks).

    Configuration:
        FILESYSTEM_DISK=local
        FILESYSTEM_ROOT=storage/app  # Root directory for storage

    Example Usage:
        driver = LocalDriver(root="storage/app")
        await driver.put("uploads/avatar.jpg", image_bytes)
        content = await driver.get("uploads/avatar.jpg")
    """

    def __init__(self, root: str = "storage/app", base_url: str = "/storage") -> None:
        """
        Initialize local driver.

        Args:
            root: Root directory for file storage (relative or absolute)
            base_url: Base URL for serving files via web server

        Raises:
            StorageConfigException: If root path is invalid
        """
        if not root:
            raise StorageConfigException("Root path cannot be empty")

        self.root = Path(root).resolve()
        self.base_url = base_url.rstrip("/")

        # Create root directory if it doesn't exist
        self.root.mkdir(parents=True, exist_ok=True)

    async def put(self, path: str, content: bytes | str | BinaryIO) -> str:
        """
        Store file on local filesystem.

        Args:
            path: Relative path where file should be stored
            content: File content as bytes, string, or file-like object

        Returns:
            The path where file was stored

        Raises:
            StorageException: If file cannot be written

        Note:
            - Creates parent directories automatically
            - Overwrites existing file
        """
        full_path = self._full_path(path)

        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        if isinstance(content, bytes):
            async with aiofiles.open(full_path, "wb") as f:
                await f.write(content)
        elif isinstance(content, str):
            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(content)
        else:
            # File-like object
            data = content.read()
            async with aiofiles.open(full_path, "wb") as f:
                if isinstance(data, str):
                    await f.write(data.encode("utf-8"))
                else:
                    await f.write(data)

        return path

    async def get(self, path: str) -> bytes:
        """
        Retrieve file from local filesystem.

        Args:
            path: Relative path to file

        Returns:
            File content as bytes

        Raises:
            FileNotFoundException: If file doesn't exist
        """
        full_path = self._full_path(path)

        if not await aiofiles.os.path.exists(full_path):
            raise FileNotFoundException(f"File not found: {path}")

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def exists(self, path: str) -> bool:
        """
        Check if file exists on filesystem.

        Args:
            path: Relative path to file

        Returns:
            True if file exists, False otherwise
        """
        full_path = self._full_path(path)
        return await aiofiles.os.path.exists(full_path)

    async def delete(self, path: str) -> bool:
        """
        Delete file from filesystem.

        Args:
            path: Relative path to file

        Returns:
            True if file was deleted, False if file didn't exist

        Note:
            - No error if file doesn't exist
            - Only deletes files, not directories
        """
        full_path = self._full_path(path)

        if not await aiofiles.os.path.exists(full_path):
            return False

        try:
            await aiofiles.os.remove(full_path)
            return True
        except IsADirectoryError:
            # Not a file, it's a directory
            return False

    async def size(self, path: str) -> int:
        """
        Get file size in bytes.

        Args:
            path: Relative path to file

        Returns:
            File size in bytes

        Raises:
            FileNotFoundException: If file doesn't exist
        """
        full_path = self._full_path(path)

        if not await aiofiles.os.path.exists(full_path):
            raise FileNotFoundException(f"File not found: {path}")

        stat = await aiofiles.os.stat(full_path)
        return stat.st_size

    async def last_modified(self, path: str) -> float:
        """
        Get file last modified timestamp.

        Args:
            path: Relative path to file

        Returns:
            Unix timestamp of last modification

        Raises:
            FileNotFoundException: If file doesn't exist
        """
        full_path = self._full_path(path)

        if not await aiofiles.os.path.exists(full_path):
            raise FileNotFoundException(f"File not found: {path}")

        stat = await aiofiles.os.stat(full_path)
        return stat.st_mtime

    def url(self, path: str) -> str:
        """
        Generate public URL for file.

        Args:
            path: Relative path to file

        Returns:
            Public URL to access file

        Example:
            driver.url("uploads/avatar.jpg")
            # Returns: "/storage/uploads/avatar.jpg"

        Note:
            Assumes files are served by web server from base_url.
            You need to configure your web server to serve files from
            the storage root at the base_url path.
        """
        # Normalize path (remove leading slash, use forward slashes)
        normalized = path.lstrip("/").replace("\\", "/")
        return f"{self.base_url}/{normalized}"

    def path(self, path: str) -> str:
        """
        Get absolute filesystem path.

        Args:
            path: Relative path to file

        Returns:
            Absolute filesystem path

        Example:
            driver.path("uploads/avatar.jpg")
            # Returns: "/var/www/storage/app/uploads/avatar.jpg"
        """
        return str(self._full_path(path))

    def _full_path(self, path: str) -> Path:
        """
        Get full filesystem path from relative path.

        Args:
            path: Relative path

        Returns:
            Full Path object

        Note:
            - Joins root with relative path
            - Normalizes path separators
        """
        # Remove leading slash and normalize
        normalized = path.lstrip("/").replace("\\", "/")
        return self.root / normalized
