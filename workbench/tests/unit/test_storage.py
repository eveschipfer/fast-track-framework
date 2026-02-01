"""
Tests for Storage System (Sprint 4.1)

This test suite covers:
- MemoryDriver (in-memory storage)
- LocalDriver (filesystem storage)
- StorageManager (singleton, factory, facade)
- Multi-disk support
"""

import io
import tempfile
from pathlib import Path

import pytest

from ftf.storage import Storage, FileNotFoundException
from ftf.storage.drivers.memory_driver import MemoryDriver
from ftf.storage.drivers.local_driver import LocalDriver


# -------------------------------------------------------------------------
# MemoryDriver Tests
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_memory_driver_put_and_get() -> None:
    """MemoryDriver should store and retrieve files."""
    driver = MemoryDriver()

    # Store file
    path = await driver.put("test.txt", b"Hello World")
    assert path == "test.txt"

    # Retrieve file
    content = await driver.get("test.txt")
    assert content == b"Hello World"


@pytest.mark.asyncio
async def test_memory_driver_put_string() -> None:
    """MemoryDriver should handle string content."""
    driver = MemoryDriver()

    await driver.put("test.txt", "Hello World")
    content = await driver.get("test.txt")
    assert content == b"Hello World"


@pytest.mark.asyncio
async def test_memory_driver_put_file_object() -> None:
    """MemoryDriver should handle file-like objects."""
    driver = MemoryDriver()

    buffer = io.BytesIO(b"Buffer content")
    await driver.put("test.txt", buffer)

    content = await driver.get("test.txt")
    assert content == b"Buffer content"


@pytest.mark.asyncio
async def test_memory_driver_exists() -> None:
    """MemoryDriver should check file existence."""
    driver = MemoryDriver()

    assert await driver.exists("test.txt") is False

    await driver.put("test.txt", b"content")
    assert await driver.exists("test.txt") is True


@pytest.mark.asyncio
async def test_memory_driver_delete() -> None:
    """MemoryDriver should delete files."""
    driver = MemoryDriver()

    await driver.put("test.txt", b"content")

    # Delete existing file
    deleted = await driver.delete("test.txt")
    assert deleted is True
    assert await driver.exists("test.txt") is False

    # Delete non-existent file
    deleted = await driver.delete("nonexistent.txt")
    assert deleted is False


@pytest.mark.asyncio
async def test_memory_driver_size() -> None:
    """MemoryDriver should return file size."""
    driver = MemoryDriver()

    await driver.put("test.txt", b"Hello")
    size = await driver.size("test.txt")
    assert size == 5


@pytest.mark.asyncio
async def test_memory_driver_size_not_found() -> None:
    """MemoryDriver should raise exception for non-existent file."""
    driver = MemoryDriver()

    with pytest.raises(FileNotFoundException):
        await driver.size("nonexistent.txt")


@pytest.mark.asyncio
async def test_memory_driver_last_modified() -> None:
    """MemoryDriver should return last modified timestamp."""
    driver = MemoryDriver()

    await driver.put("test.txt", b"content")
    timestamp = await driver.last_modified("test.txt")
    assert isinstance(timestamp, float)
    assert timestamp > 0


@pytest.mark.asyncio
async def test_memory_driver_url() -> None:
    """MemoryDriver should generate memory URL."""
    driver = MemoryDriver()

    url = driver.url("test.txt")
    assert url == "memory://test.txt"


@pytest.mark.asyncio
async def test_memory_driver_path() -> None:
    """MemoryDriver should generate memory path."""
    driver = MemoryDriver()

    path = driver.path("test.txt")
    assert path == "memory://test.txt"


@pytest.mark.asyncio
async def test_memory_driver_flush() -> None:
    """MemoryDriver should clear all files."""
    driver = MemoryDriver()

    await driver.put("test1.txt", b"content1")
    await driver.put("test2.txt", b"content2")

    assert driver.count() == 2

    driver.flush()

    assert driver.count() == 0
    assert await driver.exists("test1.txt") is False


@pytest.mark.asyncio
async def test_memory_driver_all_paths() -> None:
    """MemoryDriver should list all paths."""
    driver = MemoryDriver()

    await driver.put("test1.txt", b"content1")
    await driver.put("test2.txt", b"content2")

    paths = driver.all_paths()
    assert set(paths) == {"test1.txt", "test2.txt"}


# -------------------------------------------------------------------------
# LocalDriver Tests
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_local_driver_put_and_get() -> None:
    """LocalDriver should store and retrieve files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        driver = LocalDriver(root=tmpdir)

        # Store file
        path = await driver.put("test.txt", b"Hello World")
        assert path == "test.txt"

        # Retrieve file
        content = await driver.get("test.txt")
        assert content == b"Hello World"


@pytest.mark.asyncio
async def test_local_driver_create_directory() -> None:
    """LocalDriver should create directories automatically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        driver = LocalDriver(root=tmpdir)

        # Store file in nested directory
        await driver.put("uploads/images/test.jpg", b"image data")

        # Directory should be created
        assert (Path(tmpdir) / "uploads" / "images").exists()

        # File should exist
        content = await driver.get("uploads/images/test.jpg")
        assert content == b"image data"


@pytest.mark.asyncio
async def test_local_driver_exists() -> None:
    """LocalDriver should check file existence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        driver = LocalDriver(root=tmpdir)

        assert await driver.exists("test.txt") is False

        await driver.put("test.txt", b"content")
        assert await driver.exists("test.txt") is True


@pytest.mark.asyncio
async def test_local_driver_delete() -> None:
    """LocalDriver should delete files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        driver = LocalDriver(root=tmpdir)

        await driver.put("test.txt", b"content")

        # Delete existing file
        deleted = await driver.delete("test.txt")
        assert deleted is True
        assert await driver.exists("test.txt") is False

        # Delete non-existent file
        deleted = await driver.delete("nonexistent.txt")
        assert deleted is False


@pytest.mark.asyncio
async def test_local_driver_size() -> None:
    """LocalDriver should return file size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        driver = LocalDriver(root=tmpdir)

        await driver.put("test.txt", b"Hello")
        size = await driver.size("test.txt")
        assert size == 5


@pytest.mark.asyncio
async def test_local_driver_last_modified() -> None:
    """LocalDriver should return last modified timestamp."""
    with tempfile.TemporaryDirectory() as tmpdir:
        driver = LocalDriver(root=tmpdir)

        await driver.put("test.txt", b"content")
        timestamp = await driver.last_modified("test.txt")
        assert isinstance(timestamp, float)
        assert timestamp > 0


@pytest.mark.asyncio
async def test_local_driver_url() -> None:
    """LocalDriver should generate public URL."""
    driver = LocalDriver(root="storage", base_url="/storage")

    url = driver.url("uploads/avatar.jpg")
    assert url == "/storage/uploads/avatar.jpg"


@pytest.mark.asyncio
async def test_local_driver_path() -> None:
    """LocalDriver should return absolute path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        driver = LocalDriver(root=tmpdir)

        path = driver.path("test.txt")
        assert path == str(Path(tmpdir) / "test.txt")


# -------------------------------------------------------------------------
# StorageManager Tests
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_storage_manager_singleton() -> None:
    """StorageManager should be singleton."""
    from ftf.storage.manager import StorageManager

    instance1 = StorageManager()
    instance2 = StorageManager()

    assert instance1 is instance2


@pytest.mark.asyncio
async def test_storage_put_and_get() -> None:
    """Storage should store and retrieve files."""
    # Use memory driver for testing
    Storage.set_driver(MemoryDriver())

    # Store file
    path = await Storage.put("test.txt", b"Hello Storage")
    assert path == "test.txt"

    # Retrieve file
    content = await Storage.get("test.txt")
    assert content == b"Hello Storage"


@pytest.mark.asyncio
async def test_storage_exists() -> None:
    """Storage should check file existence."""
    driver = MemoryDriver()
    Storage.set_driver(driver, "default")

    assert await Storage.disk("default").exists("test.txt") is False

    await Storage.disk("default").put("test.txt", b"content")
    assert await Storage.disk("default").exists("test.txt") is True


@pytest.mark.asyncio
async def test_storage_delete() -> None:
    """Storage should delete files."""
    Storage.set_driver(MemoryDriver())

    await Storage.put("test.txt", b"content")

    deleted = await Storage.delete("test.txt")
    assert deleted is True
    assert await Storage.exists("test.txt") is False


@pytest.mark.asyncio
async def test_storage_size() -> None:
    """Storage should return file size."""
    Storage.set_driver(MemoryDriver())

    await Storage.put("test.txt", b"Hello")
    size = await Storage.size("test.txt")
    assert size == 5


@pytest.mark.asyncio
async def test_storage_url() -> None:
    """Storage should generate file URL."""
    driver = MemoryDriver()
    Storage.set_driver(driver, "default")

    url = Storage.disk("default").url("test.txt")
    assert url == "memory://test.txt"


@pytest.mark.asyncio
async def test_storage_disk() -> None:
    """Storage should support multiple disks."""
    # Set default to memory
    Storage.set_driver(MemoryDriver(), "default")

    # Create separate memory driver for "backup" disk
    backup_driver = MemoryDriver()
    Storage.set_driver(backup_driver, "backup")

    # Store in backup disk
    await Storage.disk("backup").put("backup.txt", b"backup content")

    # Should exist in backup disk
    content = await Storage.disk("backup").get("backup.txt")
    assert content == b"backup content"


# -------------------------------------------------------------------------
# Cleanup
# -------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_storage() -> None:
    """Reset storage driver before each test."""
    Storage.set_driver(MemoryDriver())
