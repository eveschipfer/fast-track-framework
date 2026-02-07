"""
Fast Track Framework - Storage System

This module provides a comprehensive file storage system with multi-driver support.

Public API:
-----------
- Storage: Singleton manager for file operations
- Exceptions: Custom exceptions for storage operations

Usage:
------
```python
from jtc.storage import Storage

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

# Get file size
size = await Storage.size("uploads/avatar.jpg")

# Switch to different disk
await Storage.disk("s3").put("backups/data.json", json_data)
```

Configuration:
--------------
Environment Variables:
    FILESYSTEM_DISK: Driver type (local, memory, s3)
    FILESYSTEM_ROOT: Root directory for local driver
    FILESYSTEM_URL: Base URL for serving files
    AWS_BUCKET: S3 bucket name (when using S3)
    AWS_DEFAULT_REGION: AWS region (when using S3)
    AWS_ACCESS_KEY_ID: AWS access key (when using S3)
    AWS_SECRET_ACCESS_KEY: AWS secret key (when using S3)

Educational Note:
-----------------
This storage system demonstrates several design patterns:
- Singleton: StorageManager ensures single instance
- Factory: Drivers created based on configuration
- Adapter: Different drivers adapt different storage backends
- Facade: Simple API regardless of underlying driver
"""

from jtc.storage.manager import Storage
from jtc.storage.exceptions import (
    StorageException,
    FileNotFoundException,
    DirectoryNotFoundException,
    StorageConfigException,
)

__all__ = [
    "Storage",
    "StorageException",
    "FileNotFoundException",
    "DirectoryNotFoundException",
    "StorageConfigException",
]
