"""
AWS S3 driver for cloud storage.

Stores files in AWS S3 using aioboto3 for async operations.
This driver is optional and requires aioboto3 to be installed.
"""

import io
from typing import BinaryIO

from jtc.storage.exceptions import FileNotFoundException, StorageConfigException

# Try to import aioboto3 (optional dependency)
try:
    import aioboto3
    from botocore.exceptions import ClientError

    AIOBOTO3_AVAILABLE = True
except ImportError:
    AIOBOTO3_AVAILABLE = False
    aioboto3 = None  # type: ignore
    ClientError = Exception  # type: ignore


class S3Driver:
    """
    AWS S3 storage driver.

    This driver stores files in AWS S3 buckets. Features:
    - Async I/O with aioboto3 (non-blocking)
    - Public/private file access
    - Configurable region and ACL
    - Pre-signed URLs for private files

    Pattern: Adapter Pattern
    ------------------------
    Adapts AWS S3 to the StorageDriver interface.

    Educational Note:
    ----------------
    This driver requires aioboto3 which is an optional dependency.
    If aioboto3 is not installed, driver initialization will raise
    an exception with instructions.

    Configuration (Environment Variables):
        FILESYSTEM_DISK=s3
        AWS_ACCESS_KEY_ID=your-access-key
        AWS_SECRET_ACCESS_KEY=your-secret-key
        AWS_DEFAULT_REGION=us-east-1
        AWS_BUCKET=your-bucket-name
        AWS_URL=https://your-bucket.s3.amazonaws.com  # Optional custom URL

    Example Usage:
        driver = S3Driver(
            bucket="my-bucket",
            region="us-east-1",
            access_key="...",
            secret_key="..."
        )
        await driver.put("uploads/avatar.jpg", image_bytes)
        content = await driver.get("uploads/avatar.jpg")
    """

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        access_key: str | None = None,
        secret_key: str | None = None,
        endpoint_url: str | None = None,
        acl: str = "private",
    ) -> None:
        """
        Initialize S3 driver.

        Args:
            bucket: S3 bucket name
            region: AWS region
            access_key: AWS access key ID (or use environment variable)
            secret_key: AWS secret access key (or use environment variable)
            endpoint_url: Custom S3 endpoint URL (for S3-compatible services)
            acl: Default ACL for uploaded files (private, public-read, etc.)

        Raises:
            StorageConfigException: If aioboto3 is not installed or config is invalid
        """
        if not AIOBOTO3_AVAILABLE:
            msg = (
                "aioboto3 is required for S3Driver. "
                "Install it with: pip install aioboto3"
            )
            raise StorageConfigException(msg)

        if not bucket:
            raise StorageConfigException("S3 bucket name is required")

        self.bucket = bucket
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url
        self.acl = acl

        # Create session (credentials will be loaded from env if not provided)
        self.session = aioboto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    async def put(self, path: str, content: bytes | str | BinaryIO) -> str:
        """
        Upload file to S3.

        Args:
            path: S3 object key (path)
            content: File content as bytes, string, or file-like object

        Returns:
            The path (S3 key) where file was stored

        Note:
            - Path becomes the S3 object key
            - Overwrites existing object
            - Sets ACL based on driver configuration
        """
        # Convert content to bytes
        if isinstance(content, str):
            data = content.encode("utf-8")
        elif isinstance(content, bytes):
            data = content
        else:
            # File-like object
            content.seek(0)
            data = content.read()
            if isinstance(data, str):
                data = data.encode("utf-8")

        # Upload to S3
        async with self.session.client("s3", endpoint_url=self.endpoint_url) as s3:
            await s3.put_object(
                Bucket=self.bucket,
                Key=path,
                Body=data,
                ACL=self.acl,
            )

        return path

    async def get(self, path: str) -> bytes:
        """
        Download file from S3.

        Args:
            path: S3 object key (path)

        Returns:
            File content as bytes

        Raises:
            FileNotFoundException: If object doesn't exist
        """
        try:
            async with self.session.client("s3", endpoint_url=self.endpoint_url) as s3:
                response = await s3.get_object(Bucket=self.bucket, Key=path)

                # Read body
                async with response["Body"] as stream:
                    return await stream.read()

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundException(f"File not found: {path}") from e
            raise

    async def exists(self, path: str) -> bool:
        """
        Check if object exists in S3.

        Args:
            path: S3 object key (path)

        Returns:
            True if object exists, False otherwise
        """
        try:
            async with self.session.client("s3", endpoint_url=self.endpoint_url) as s3:
                await s3.head_object(Bucket=self.bucket, Key=path)
                return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    async def delete(self, path: str) -> bool:
        """
        Delete object from S3.

        Args:
            path: S3 object key (path)

        Returns:
            True if object was deleted, False if object didn't exist

        Note:
            S3 delete is idempotent - no error if object doesn't exist
        """
        try:
            async with self.session.client("s3", endpoint_url=self.endpoint_url) as s3:
                # Check if exists first
                exists = await self.exists(path)

                # Delete object
                await s3.delete_object(Bucket=self.bucket, Key=path)

                return exists

        except ClientError:
            return False

    async def size(self, path: str) -> int:
        """
        Get object size in bytes.

        Args:
            path: S3 object key (path)

        Returns:
            Object size in bytes

        Raises:
            FileNotFoundException: If object doesn't exist
        """
        try:
            async with self.session.client("s3", endpoint_url=self.endpoint_url) as s3:
                response = await s3.head_object(Bucket=self.bucket, Key=path)
                return response["ContentLength"]

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundException(f"File not found: {path}") from e
            raise

    async def last_modified(self, path: str) -> float:
        """
        Get object last modified timestamp.

        Args:
            path: S3 object key (path)

        Returns:
            Unix timestamp of last modification

        Raises:
            FileNotFoundException: If object doesn't exist
        """
        try:
            async with self.session.client("s3", endpoint_url=self.endpoint_url) as s3:
                response = await s3.head_object(Bucket=self.bucket, Key=path)
                return response["LastModified"].timestamp()

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundException(f"File not found: {path}") from e
            raise

    def url(self, path: str) -> str:
        """
        Generate public URL for S3 object.

        Args:
            path: S3 object key (path)

        Returns:
            Public S3 URL

        Example:
            driver.url("uploads/avatar.jpg")
            # Returns: "https://bucket.s3.amazonaws.com/uploads/avatar.jpg"

        Note:
            - This generates the standard S3 URL format
            - File must have public ACL to be accessible
            - For private files, use presigned URLs (future enhancement)
        """
        if self.endpoint_url:
            # Custom endpoint
            base = self.endpoint_url.rstrip("/")
            return f"{base}/{self.bucket}/{path}"
        else:
            # Standard S3 URL
            return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{path}"

    def path(self, path: str) -> str:
        """
        Get S3 object key (not a filesystem path).

        Args:
            path: S3 object key

        Returns:
            S3 URI in format "s3://bucket/path"

        Note:
            S3 has no filesystem path. This returns the S3 URI instead.
        """
        return f"s3://{self.bucket}/{path}"
