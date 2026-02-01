"""
Storage system contracts and type definitions.

This module defines the core interfaces and types for the storage system:
- StorageDriver: Protocol for storage driver implementations
- FileInfo: TypedDict for file metadata

Educational Note:
-----------------
We use Protocol (structural typing) instead of ABC because we want to allow
any object that implements the required methods to be a valid storage driver,
even without explicit inheritance. This makes testing and mocking easier.
"""

from typing import Protocol, BinaryIO


class StorageDriver(Protocol):
    """
    Protocol for storage driver implementations.

    Drivers handle file operations across different storage backends:
    - LocalDriver: Local filesystem storage
    - MemoryDriver: In-memory storage (testing)
    - S3Driver: AWS S3 object storage

    Pattern: Adapter Pattern
    ------------------------
    Each driver adapts a different storage backend (filesystem, memory, S3)
    to a common interface. This allows the application to switch storage
    backends without changing code.

    Educational Note:
    ----------------
    All methods that perform I/O are async to avoid blocking the event loop.
    Even local filesystem operations should be async using aiofiles.
    """

    async def put(self, path: str, content: bytes | str | BinaryIO) -> str:
        """
        Store file content at the given path.

        Args:
            path: Relative path where file should be stored (e.g., "uploads/avatar.jpg")
            content: File content as bytes, string, or file-like object

        Returns:
            The path where file was stored (may be modified by driver)

        Raises:
            StorageException: If file cannot be stored

        Example:
            await driver.put("uploads/avatar.jpg", image_bytes)
            await driver.put("files/doc.txt", "Hello World")
            await driver.put("files/upload.pdf", open("file.pdf", "rb"))

        Note:
            - Directories are created automatically if they don't exist
            - If path exists, file is overwritten
            - For S3, path becomes the object key
        """
        ...

    async def get(self, path: str) -> bytes:
        """
        Retrieve file content from storage.

        Args:
            path: Relative path to file

        Returns:
            File content as bytes

        Raises:
            FileNotFoundException: If file doesn't exist
            StorageException: If file cannot be read

        Example:
            content = await driver.get("uploads/avatar.jpg")
            text = (await driver.get("files/doc.txt")).decode("utf-8")
        """
        ...

    async def exists(self, path: str) -> bool:
        """
        Check if file exists.

        Args:
            path: Relative path to file

        Returns:
            True if file exists, False otherwise

        Example:
            if await driver.exists("uploads/avatar.jpg"):
                print("Avatar exists")
        """
        ...

    async def delete(self, path: str) -> bool:
        """
        Delete file from storage.

        Args:
            path: Relative path to file

        Returns:
            True if file was deleted, False if file didn't exist

        Raises:
            StorageException: If deletion fails

        Example:
            deleted = await driver.delete("uploads/old_avatar.jpg")

        Note:
            - No error if file doesn't exist (returns False)
            - For S3, this deletes the object
        """
        ...

    async def size(self, path: str) -> int:
        """
        Get file size in bytes.

        Args:
            path: Relative path to file

        Returns:
            File size in bytes

        Raises:
            FileNotFoundException: If file doesn't exist

        Example:
            size = await driver.size("uploads/avatar.jpg")
            print(f"File size: {size} bytes")
        """
        ...

    async def last_modified(self, path: str) -> float:
        """
        Get file last modified timestamp.

        Args:
            path: Relative path to file

        Returns:
            Unix timestamp of last modification

        Raises:
            FileNotFoundException: If file doesn't exist

        Example:
            timestamp = await driver.last_modified("uploads/avatar.jpg")
            from datetime import datetime
            dt = datetime.fromtimestamp(timestamp)
        """
        ...

    def url(self, path: str) -> str:
        """
        Generate public URL for file.

        Args:
            path: Relative path to file

        Returns:
            Public URL to access file

        Example:
            url = driver.url("uploads/avatar.jpg")
            # LocalDriver: "http://localhost:8000/storage/uploads/avatar.jpg"
            # S3Driver: "https://bucket.s3.amazonaws.com/uploads/avatar.jpg"

        Note:
            - This is NOT async (just string manipulation)
            - For LocalDriver, assumes files are served via web server
            - For S3, returns the public S3 URL
        """
        ...

    def path(self, path: str) -> str:
        """
        Get absolute filesystem path (if applicable).

        Args:
            path: Relative path to file

        Returns:
            Absolute filesystem path

        Example:
            abs_path = driver.path("uploads/avatar.jpg")
            # LocalDriver: "/var/www/storage/uploads/avatar.jpg"
            # S3Driver: raises NotImplementedError (no filesystem path)

        Note:
            - Only applicable for filesystem-based drivers
            - S3Driver should raise NotImplementedError
        """
        ...
