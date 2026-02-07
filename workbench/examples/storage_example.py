"""
Storage System Example (Sprint 4.1)

This example demonstrates how to use the Fast Track Framework storage system.

Run with:
    FILESYSTEM_DISK=memory python examples/storage_example.py
    FILESYSTEM_DISK=local python examples/storage_example.py
"""

import asyncio
import os
from datetime import datetime

from jtc.storage import Storage


async def main() -> None:
    """
    Run storage examples.

    Set FILESYSTEM_DISK environment variable to control driver:
    - memory: In-memory storage (default, for testing)
    - local: Local filesystem storage
    - s3: AWS S3 storage (requires AWS credentials)
    """
    print("=" * 70)
    print("Fast Track Framework - Storage System Examples")
    print("=" * 70)
    print()

    # Get driver type from environment
    driver_type = os.getenv("FILESYSTEM_DISK", "memory")
    print(f"Using driver: {driver_type}")
    print()

    # Example 1: Store text file
    print("-" * 70)
    print("Example 1: Store Text File")
    print("-" * 70)
    path = await Storage.put("files/readme.txt", "Hello, Fast Track Framework!")
    print(f"✓ Stored file at: {path}")
    print()

    # Example 2: Retrieve file content
    print("-" * 70)
    print("Example 2: Retrieve File Content")
    print("-" * 70)
    content = await Storage.get("files/readme.txt")
    print(f"Content: {content.decode('utf-8')}")
    print()

    # Example 3: Store binary file
    print("-" * 70)
    print("Example 3: Store Binary File")
    print("-" * 70)
    binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"  # PNG header
    await Storage.put("images/test.png", binary_data)
    print("✓ Stored binary file (PNG)")
    print()

    # Example 4: Check file existence
    print("-" * 70)
    print("Example 4: Check File Existence")
    print("-" * 70)
    exists = await Storage.exists("files/readme.txt")
    print(f"files/readme.txt exists: {exists}")

    not_exists = await Storage.exists("files/nonexistent.txt")
    print(f"files/nonexistent.txt exists: {not_exists}")
    print()

    # Example 5: Get file metadata
    print("-" * 70)
    print("Example 5: Get File Metadata")
    print("-" * 70)
    size = await Storage.size("files/readme.txt")
    print(f"Size: {size} bytes")

    modified = await Storage.last_modified("files/readme.txt")
    dt = datetime.fromtimestamp(modified)
    print(f"Last modified: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Example 6: Generate file URL
    print("-" * 70)
    print("Example 6: Generate File URL")
    print("-" * 70)
    url = Storage.url("files/readme.txt")
    print(f"URL: {url}")
    print()

    # Example 7: Get file path
    print("-" * 70)
    print("Example 7: Get File Path")
    print("-" * 70)
    file_path = Storage.path("files/readme.txt")
    print(f"Path: {file_path}")
    print()

    # Example 8: Store file from file-like object
    print("-" * 70)
    print("Example 8: Store File from File-Like Object")
    print("-" * 70)
    import io
    buffer = io.BytesIO(b"File from buffer")
    await Storage.put("files/buffer.txt", buffer)
    print("✓ Stored file from buffer")
    print()

    # Example 9: Delete file
    print("-" * 70)
    print("Example 9: Delete File")
    print("-" * 70)
    deleted = await Storage.delete("files/buffer.txt")
    print(f"Deleted files/buffer.txt: {deleted}")

    not_deleted = await Storage.delete("files/nonexistent.txt")
    print(f"Deleted files/nonexistent.txt: {not_deleted}")
    print()

    # Example 10: Multi-disk support
    print("-" * 70)
    print("Example 10: Multi-Disk Support")
    print("-" * 70)
    # Store in default disk
    await Storage.put("temp/default.txt", "Default disk")
    print("✓ Stored in default disk")

    # Store in memory disk (always works)
    await Storage.disk("memory").put("temp/memory.txt", "Memory disk")
    print("✓ Stored in memory disk")
    print()

    # Example 11: Inspect stored files (MemoryDriver only)
    if driver_type == "memory":
        print("-" * 70)
        print("Example 11: Inspect Stored Files (MemoryDriver)")
        print("-" * 70)
        from jtc.storage.drivers.memory_driver import MemoryDriver

        driver = Storage.driver
        if isinstance(driver, MemoryDriver):
            print(f"Total files: {driver.count()}")
            print("Files:")
            for path in driver.all_paths():
                size = await Storage.size(path)
                print(f"  - {path} ({size} bytes)")
        print()

    # Example 12: Batch operations
    print("-" * 70)
    print("Example 12: Batch Operations")
    print("-" * 70)
    files_to_create = [
        ("batch/file1.txt", "Content 1"),
        ("batch/file2.txt", "Content 2"),
        ("batch/file3.txt", "Content 3"),
    ]

    for path, content in files_to_create:
        await Storage.put(path, content)

    print(f"✓ Created {len(files_to_create)} files")

    # Check all exist
    all_exist = all([await Storage.exists(path) for path, _ in files_to_create])
    print(f"All files exist: {all_exist}")

    # Delete all
    for path, _ in files_to_create:
        await Storage.delete(path)

    print("✓ Deleted all batch files")
    print()

    print("=" * 70)
    print("✓ All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
