"""
Memory driver for testing.

Stores files in memory using a dictionary. Perfect for unit tests
where you want to verify file operations without touching the filesystem.
"""

import time
from typing import BinaryIO

from jtc.storage.exceptions import FileNotFoundException


class MemoryDriver:
    """
    In-memory storage driver for testing.

    This driver stores files in a dictionary in RAM. It's perfect for:
    - Unit tests (no filesystem I/O)
    - Fast testing (no disk operations)
    - Inspection (can easily check stored files)

    Pattern: Adapter Pattern
    ------------------------
    Adapts a Python dictionary to the StorageDriver interface.

    Educational Note:
    ----------------
    Even though this is in-memory, we keep the async interface for
    consistency. This allows tests to use the same code as production.

    Example Usage:
        driver = MemoryDriver()
        await driver.put("test.txt", b"Hello")
        content = await driver.get("test.txt")
        assert content == b"Hello"
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self._files: dict[str, bytes] = {}
        self._metadata: dict[str, dict[str, float]] = {}

    async def put(self, path: str, content: bytes | str | BinaryIO) -> str:
        """
        Store file content in memory.

        Args:
            path: Path where file should be stored
            content: File content as bytes, string, or file-like object

        Returns:
            The path where file was stored
        """
        # Convert content to bytes
        if isinstance(content, str):
            data = content.encode("utf-8")
        elif isinstance(content, bytes):
            data = content
        else:
            # File-like object
            data = content.read()
            if isinstance(data, str):
                data = data.encode("utf-8")

        # Store file
        self._files[path] = data

        # Store metadata
        self._metadata[path] = {
            "size": len(data),
            "modified": time.time(),
        }

        return path

    async def get(self, path: str) -> bytes:
        """
        Retrieve file content from memory.

        Args:
            path: Path to file

        Returns:
            File content as bytes

        Raises:
            FileNotFoundException: If file doesn't exist
        """
        if path not in self._files:
            raise FileNotFoundException(f"File not found: {path}")

        return self._files[path]

    async def exists(self, path: str) -> bool:
        """
        Check if file exists in memory.

        Args:
            path: Path to file

        Returns:
            True if file exists, False otherwise
        """
        return path in self._files

    async def delete(self, path: str) -> bool:
        """
        Delete file from memory.

        Args:
            path: Path to file

        Returns:
            True if file was deleted, False if file didn't exist
        """
        if path in self._files:
            del self._files[path]
            del self._metadata[path]
            return True
        return False

    async def size(self, path: str) -> int:
        """
        Get file size.

        Args:
            path: Path to file

        Returns:
            File size in bytes

        Raises:
            FileNotFoundException: If file doesn't exist
        """
        if path not in self._files:
            raise FileNotFoundException(f"File not found: {path}")

        return self._metadata[path]["size"]

    async def last_modified(self, path: str) -> float:
        """
        Get file last modified timestamp.

        Args:
            path: Path to file

        Returns:
            Unix timestamp of last modification

        Raises:
            FileNotFoundException: If file doesn't exist
        """
        if path not in self._files:
            raise FileNotFoundException(f"File not found: {path}")

        return self._metadata[path]["modified"]

    def url(self, path: str) -> str:
        """
        Generate memory URL (not a real URL).

        Args:
            path: Path to file

        Returns:
            Memory URL in format "memory://{path}"

        Note:
            This is not a real URL. It's just a placeholder for testing.
        """
        return f"memory://{path}"

    def path(self, path: str) -> str:
        """
        Get memory path (not a filesystem path).

        Args:
            path: Path to file

        Returns:
            Memory path in format "memory://{path}"

        Note:
            MemoryDriver has no filesystem path. This returns a
            placeholder for compatibility.
        """
        return f"memory://{path}"

    def flush(self) -> None:
        """
        Clear all files from memory.

        Useful for resetting state between tests.

        Example:
            # In pytest fixture
            @pytest.fixture(autouse=True)
            def reset_storage():
                Storage.driver.flush()
        """
        self._files.clear()
        self._metadata.clear()

    def count(self) -> int:
        """
        Get number of files in storage.

        Returns:
            Number of stored files

        Example:
            driver = MemoryDriver()
            await driver.put("test.txt", b"Hello")
            assert driver.count() == 1
        """
        return len(self._files)

    def all_paths(self) -> list[str]:
        """
        Get list of all stored file paths.

        Returns:
            List of file paths

        Example:
            driver = MemoryDriver()
            await driver.put("test1.txt", b"Hello")
            await driver.put("test2.txt", b"World")
            assert driver.all_paths() == ["test1.txt", "test2.txt"]
        """
        return list(self._files.keys())
