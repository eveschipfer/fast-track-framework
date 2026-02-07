"""
Storage system exceptions.

Hierarchy:
    StorageException (base)
    ├── FileNotFoundException (file doesn't exist)
    ├── DirectoryNotFoundException (directory doesn't exist)
    └── StorageConfigException (configuration errors)
"""


class StorageException(Exception):
    """Base exception for all storage-related errors."""

    pass


class FileNotFoundException(StorageException):
    """
    Raised when file doesn't exist.

    Common causes:
    - Trying to read non-existent file
    - Trying to get metadata of non-existent file
    - File was deleted after existence check
    """

    pass


class DirectoryNotFoundException(StorageException):
    """
    Raised when directory doesn't exist.

    Common causes:
    - Trying to list non-existent directory
    - Trying to delete non-existent directory
    """

    pass


class StorageConfigException(StorageException):
    """
    Raised when storage configuration is invalid.

    Common causes:
    - Missing required environment variables
    - Invalid FILESYSTEM_DRIVER value
    - Invalid S3 credentials
    - Invalid root path
    """

    pass
