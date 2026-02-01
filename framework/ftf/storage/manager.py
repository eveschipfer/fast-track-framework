"""
Storage manager - Singleton facade for file operations.

The StorageManager acts as:
1. Singleton: Single instance per application
2. Factory: Creates appropriate driver based on config
3. Facade: Provides simple API for file operations
"""

import os
from typing import BinaryIO

from ftf.storage.drivers.local_driver import LocalDriver
from ftf.storage.drivers.memory_driver import MemoryDriver
from ftf.storage.drivers.s3_driver import S3Driver
from ftf.storage.exceptions import StorageConfigException


class StorageManager:
    """
    Singleton storage manager.

    Responsibilities:
    1. Driver Management: Creates and manages storage driver instances
    2. Configuration: Reads environment variables for driver selection
    3. Facade: Provides simple API for file operations
    4. Multi-Disk: Supports multiple storage disks (local, s3, etc.)

    Pattern: Singleton + Factory + Facade
    --------------------------------------
    - Singleton: Ensures single instance per application
    - Factory: Creates appropriate driver based on FILESYSTEM_DISK env var
    - Facade: Provides simple, unified API regardless of driver

    Configuration (Environment Variables):
        FILESYSTEM_DISK: Driver type (local, memory, s3)

        For Local driver:
        - FILESYSTEM_ROOT: Root directory (default: storage/app)
        - FILESYSTEM_URL: Base URL for serving files (default: /storage)

        For S3 driver:
        - AWS_ACCESS_KEY_ID: AWS access key
        - AWS_SECRET_ACCESS_KEY: AWS secret key
        - AWS_DEFAULT_REGION: AWS region
        - AWS_BUCKET: S3 bucket name
        - AWS_URL: Custom S3 endpoint (optional)

    Usage:
        ```python
        from ftf.storage import Storage

        # Upload file
        await Storage.put("uploads/avatar.jpg", image_bytes)

        # Download file
        content = await Storage.get("uploads/avatar.jpg")

        # Check existence
        if await Storage.exists("uploads/avatar.jpg"):
            print("File exists")

        # Delete file
        await Storage.delete("uploads/old_avatar.jpg")

        # Get file URL
        url = Storage.url("uploads/avatar.jpg")

        # Switch to different disk
        await Storage.disk("s3").put("backups/data.json", json_data)
        ```

    Educational Note:
    ----------------
    The Singleton pattern ensures we don't create multiple driver instances.
    This is important for:
    - Resource efficiency (connection pooling for S3)
    - Configuration consistency
    - Testing (easy to override driver)
    """

    _instance: "StorageManager | None" = None
    _initialized: bool

    def __new__(cls) -> "StorageManager":
        """
        Singleton pattern - ensure only one instance exists.

        Returns:
            Single StorageManager instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """
        Initialize storage manager.

        Note:
            This is called every time StorageManager() is called, but
            initialization only happens once due to _initialized flag.
        """
        if self._initialized:
            return

        self._default_disk: str | None = None
        self._disks: dict[str, LocalDriver | MemoryDriver | S3Driver] = {}
        self._initialized = True

    def disk(self, name: str | None = None) -> "StorageManager":
        """
        Get storage disk (or set default disk).

        Args:
            name: Disk name (local, s3, etc.) or None for default

        Returns:
            Self for method chaining

        Example:
            # Use default disk
            await Storage.put("file.txt", b"content")

            # Use specific disk
            await Storage.disk("s3").put("file.txt", b"content")

            # Chain operations
            await Storage.disk("local").put("temp.txt", b"temp").delete("old.txt")

        Note:
            This sets the active disk for the current operation.
            The default disk is restored after the operation.
        """
        self._default_disk = name
        return self

    @property
    def driver(self) -> LocalDriver | MemoryDriver | S3Driver:
        """
        Get active storage driver (lazy initialization).

        Returns:
            Active storage driver

        Raises:
            StorageConfigException: If driver configuration is invalid

        Note:
            Driver is created on first access (lazy initialization).
            This allows tests to override configuration before it's created.
        """
        disk_name = self._default_disk or os.getenv("FILESYSTEM_DISK", "local")

        # Check cache
        if disk_name not in self._disks:
            self._disks[disk_name] = self._create_driver(disk_name)

        return self._disks[disk_name]

    def _create_driver(
        self, disk: str
    ) -> LocalDriver | MemoryDriver | S3Driver:
        """
        Create storage driver based on configuration.

        Args:
            disk: Disk name (local, memory, s3)

        Returns:
            Storage driver instance

        Raises:
            StorageConfigException: If disk type is invalid

        Factory Pattern:
        ---------------
        Based on disk name, we create the appropriate driver with
        configuration from environment variables.
        """
        if disk == "local":
            return self._create_local_driver()

        if disk == "memory":
            return MemoryDriver()

        if disk == "s3":
            return self._create_s3_driver()

        msg = (
            f"Invalid FILESYSTEM_DISK: {disk}. "
            f"Valid options: local, memory, s3"
        )
        raise StorageConfigException(msg)

    def _create_local_driver(self) -> LocalDriver:
        """
        Create local filesystem driver from environment variables.

        Returns:
            Configured LocalDriver

        Environment Variables:
            FILESYSTEM_ROOT: Root directory (default: storage/app)
            FILESYSTEM_URL: Base URL (default: /storage)
        """
        root = os.getenv("FILESYSTEM_ROOT", "storage/app")
        base_url = os.getenv("FILESYSTEM_URL", "/storage")

        return LocalDriver(root=root, base_url=base_url)

    def _create_s3_driver(self) -> S3Driver:
        """
        Create S3 driver from environment variables.

        Returns:
            Configured S3Driver

        Raises:
            StorageConfigException: If S3 configuration is missing

        Environment Variables:
            AWS_BUCKET: S3 bucket name (required)
            AWS_DEFAULT_REGION: AWS region (default: us-east-1)
            AWS_ACCESS_KEY_ID: AWS access key (optional, can use IAM)
            AWS_SECRET_ACCESS_KEY: AWS secret key (optional, can use IAM)
            AWS_URL: Custom endpoint URL (optional)
        """
        bucket = os.getenv("AWS_BUCKET")
        if not bucket:
            raise StorageConfigException(
                "AWS_BUCKET is required when FILESYSTEM_DISK=s3"
            )

        region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        endpoint_url = os.getenv("AWS_URL")

        return S3Driver(
            bucket=bucket,
            region=region,
            access_key=access_key,
            secret_key=secret_key,
            endpoint_url=endpoint_url,
        )

    # -------------------------------------------------------------------------
    # Facade Methods (delegate to driver)
    # -------------------------------------------------------------------------

    async def put(self, path: str, content: bytes | str | BinaryIO) -> str:
        """
        Store file.

        Args:
            path: Relative path where file should be stored
            content: File content

        Returns:
            Path where file was stored

        Example:
            await Storage.put("uploads/avatar.jpg", image_bytes)
        """
        result = await self.driver.put(path, content)
        self._default_disk = None  # Reset to default
        return result

    async def get(self, path: str) -> bytes:
        """
        Retrieve file content.

        Args:
            path: Relative path to file

        Returns:
            File content as bytes

        Example:
            content = await Storage.get("uploads/avatar.jpg")
        """
        result = await self.driver.get(path)
        self._default_disk = None  # Reset to default
        return result

    async def exists(self, path: str) -> bool:
        """
        Check if file exists.

        Args:
            path: Relative path to file

        Returns:
            True if file exists, False otherwise

        Example:
            if await Storage.exists("uploads/avatar.jpg"):
                print("Avatar exists")
        """
        result = await self.driver.exists(path)
        self._default_disk = None  # Reset to default
        return result

    async def delete(self, path: str) -> bool:
        """
        Delete file.

        Args:
            path: Relative path to file

        Returns:
            True if file was deleted, False if file didn't exist

        Example:
            deleted = await Storage.delete("uploads/old_avatar.jpg")
        """
        result = await self.driver.delete(path)
        self._default_disk = None  # Reset to default
        return result

    async def size(self, path: str) -> int:
        """
        Get file size.

        Args:
            path: Relative path to file

        Returns:
            File size in bytes

        Example:
            size = await Storage.size("uploads/avatar.jpg")
        """
        result = await self.driver.size(path)
        self._default_disk = None  # Reset to default
        return result

    async def last_modified(self, path: str) -> float:
        """
        Get file last modified timestamp.

        Args:
            path: Relative path to file

        Returns:
            Unix timestamp

        Example:
            timestamp = await Storage.last_modified("uploads/avatar.jpg")
        """
        result = await self.driver.last_modified(path)
        self._default_disk = None  # Reset to default
        return result

    def url(self, path: str) -> str:
        """
        Generate public URL for file.

        Args:
            path: Relative path to file

        Returns:
            Public URL

        Example:
            url = Storage.url("uploads/avatar.jpg")
        """
        result = self.driver.url(path)
        self._default_disk = None  # Reset to default
        return result

    def path(self, path: str) -> str:
        """
        Get absolute filesystem path (if applicable).

        Args:
            path: Relative path to file

        Returns:
            Absolute path

        Example:
            abs_path = Storage.path("uploads/avatar.jpg")
        """
        result = self.driver.path(path)
        self._default_disk = None  # Reset to default
        return result

    def set_driver(
        self, driver: LocalDriver | MemoryDriver | S3Driver, disk: str = "default"
    ) -> None:
        """
        Override storage driver (for testing).

        Args:
            driver: Driver instance to use
            disk: Disk name (default: "default")

        Example:
            # In test setup
            Storage.set_driver(MemoryDriver())
        """
        self._disks[disk] = driver
        if disk == "default":
            self._default_disk = None


# Singleton instance (exported as "Storage")
Storage = StorageManager()
