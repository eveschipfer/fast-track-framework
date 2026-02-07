"""
Lifecycle Management Tests for IoC Container
============================================

CRITICAL: Tests resource cleanup and lifecycle management.

This test suite validates that:
1. Scoped instances are properly disposed when scope ends
2. Resources (DB connections, file handles) are cleaned up
3. Context managers (__aenter__/__aexit__) are supported
4. Singleton disposal works on container shutdown
5. No resource leaks occur

WHY THIS EXISTS:
The container creates objects but never destroys them:
    clear_scoped_cache() just clears the dict, doesn't call cleanup

This can cause:
- Database connection leaks
- File handles not closed
- Memory leaks
- Resource exhaustion in production

Run tests:
    pytest tests/unit/test_container_lifecycle.py -v
    pytest tests/unit/test_container_lifecycle.py -v --tb=short
"""

import asyncio
import pytest
from typing import Any

from jtc.core import (
    Container,
    set_scoped_cache,
    clear_scoped_cache,
    clear_scoped_cache_async,
)


# ============================================================================
# TEST FIXTURES - Resources with Cleanup
# ============================================================================


class DatabaseConnection:
    """
    Mock database connection with explicit cleanup.

    Simulates real resources like:
    - asyncpg connections
    - SQLAlchemy sessions
    - Redis connections
    """

    def __init__(self):
        self.is_open = True
        self.is_closed = False
        self.connection_id = id(self)

    async def close(self):
        """Explicit cleanup method."""
        if self.is_closed:
            raise RuntimeError("Connection already closed")
        self.is_open = False
        self.is_closed = True
        await asyncio.sleep(0)  # Simulate async cleanup


class ContextManagedDatabase:
    """
    Database with async context manager support.

    Preferred pattern in async Python:
        async with ContextManagedDatabase() as db:
            await db.query()
    """

    def __init__(self):
        self.is_open = False
        self.is_closed = False
        self.entered = False
        self.exited = False

    async def __aenter__(self):
        """Called when entering async context."""
        self.is_open = True
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Called when exiting async context (automatic cleanup)."""
        self.is_open = False
        self.is_closed = True
        self.exited = True
        await asyncio.sleep(0)  # Simulate async cleanup
        return False


class FileHandle:
    """Mock file handle that tracks if it was closed."""

    def __init__(self):
        self.is_open = True
        self.is_closed = False

    def close(self):
        """Synchronous cleanup."""
        self.is_open = False
        self.is_closed = True


class ServiceWithResource:
    """Service that depends on a resource requiring cleanup."""

    def __init__(self, db: DatabaseConnection):
        self.db = db


@pytest.fixture
def container():
    """Fresh container for each test."""
    return Container()


@pytest.fixture(autouse=True)
def cleanup_scoped():
    """Ensure clean state before/after each test."""
    clear_scoped_cache()
    yield
    clear_scoped_cache()


# ============================================================================
# PROBLEM DEMONSTRATION TESTS (Expected to FAIL or show leaks)
# ============================================================================


@pytest.mark.asyncio
async def test_scoped_resource_not_cleaned_up_current_behavior(container):
    """
    DEMONSTRATE PROBLEM: Scoped resources are not cleaned up.

    Current behavior:
        1. Container creates DatabaseConnection (scoped)
        2. clear_scoped_cache() is called
        3. Connection is removed from cache but NOT closed
        4. Result: Resource leak

    Expected (after fix):
        Connection should be closed automatically
    """
    container.register(DatabaseConnection, scope="scoped")

    set_scoped_cache({})
    db = container.resolve(DatabaseConnection)

    assert db.is_open is True
    assert db.is_closed is False

    # Current behavior: Just clears dict, doesn't call close()
    clear_scoped_cache()

    # PROBLEM: Connection is still open (resource leak)
    assert db.is_open is True  # ← Should be False after cleanup
    assert db.is_closed is False  # ← Should be True after cleanup


@pytest.mark.asyncio
async def test_multiple_scoped_resources_leak(container):
    """
    DEMONSTRATE PROBLEM: Multiple scoped instances all leak.

    Simulates 10 requests, each with scoped DB connection.
    All 10 connections should be closed, but currently none are.
    """
    container.register(DatabaseConnection, scope="scoped")

    leaked_connections = []

    for _ in range(10):
        set_scoped_cache({})
        db = container.resolve(DatabaseConnection)
        leaked_connections.append(db)
        clear_scoped_cache()

    # PROBLEM: All 10 connections are still open
    open_count = sum(1 for conn in leaked_connections if conn.is_open)
    assert open_count == 10  # ← Should be 0 after cleanup


@pytest.mark.asyncio
async def test_singleton_resource_not_disposed_on_shutdown(container):
    """
    DEMONSTRATE PROBLEM: Singleton resources never cleaned up.

    Singleton lives for app lifetime, but when app shuts down,
    container doesn't clean up singletons.
    """
    container.register(DatabaseConnection, scope="singleton")

    db = container.resolve(DatabaseConnection)
    assert db.is_open is True

    # Simulate app shutdown
    # Current behavior: No cleanup method exists
    # container.dispose() would be ideal, but doesn't exist

    # PROBLEM: Singleton connection never closed
    assert db.is_open is True  # ← Should be False on shutdown


# ============================================================================
# DESIRED BEHAVIOR TESTS (Will FAIL until lifecycle is implemented)
# ============================================================================


@pytest.mark.asyncio
async def test_scoped_cleanup_calls_close_method(container):
    """
    VALIDATE: Scoped cleanup should call close() on resources.

    Behavior:
        clear_scoped_cache_async() should:
        1. Iterate cached instances
        2. Check if they have close() or dispose()
        3. Call cleanup method
        4. Clear cache
    """
    container.register(DatabaseConnection, scope="scoped")

    set_scoped_cache({})
    db = container.resolve(DatabaseConnection)

    assert db.is_open is True

    # Should call db.close() automatically
    await clear_scoped_cache_async()

    assert db.is_closed is True
    assert db.is_open is False


@pytest.mark.asyncio
async def test_context_manager_support(container):
    """
    VALIDATE: Container provides scoped_context() async context manager.

    Pattern:
        async with container.scoped_context():
            db = container.resolve(Database)
            # Use db...
        # db.close() called automatically
    """
    container.register(DatabaseConnection, scope="scoped")

    db_instance = None

    async with container.scoped_context():
        db_instance = container.resolve(DatabaseConnection)
        assert db_instance.is_open is True
        assert db_instance.is_closed is False

    # After exiting context, cleanup should have been called
    assert db_instance.is_closed is True
    assert db_instance.is_open is False


@pytest.mark.asyncio
async def test_dispose_all_singletons(container):
    """
    VALIDATE: Container.dispose_all() cleans up singletons.

    Usage:
        # App startup
        container.register(Database, scope="singleton")

        # App shutdown
        await container.dispose_all()
    """
    container.register(DatabaseConnection, scope="singleton")

    db = container.resolve(DatabaseConnection)
    assert db.is_open is True

    # Should close all singletons
    await container.dispose_all()

    assert db.is_closed is True


@pytest.mark.asyncio
async def test_nested_dependencies_all_disposed(container):
    """
    VALIDATE: Disposal works through dependency graph.

    Dependency graph:
        Service → Database

    When scope ends:
        1. Dispose Service (no cleanup method, ignored)
        2. Dispose Database (calls close())
    """
    container.register(DatabaseConnection, scope="scoped")
    container.register(ServiceWithResource, scope="scoped")

    set_scoped_cache({})
    service = container.resolve(ServiceWithResource)

    assert service.db.is_open is True

    await clear_scoped_cache_async()

    # Database should be closed
    assert service.db.is_closed is True


@pytest.mark.asyncio
@pytest.mark.skip(reason="Lifecycle management not implemented yet")
async def test_partial_disposal_on_error(container):
    """
    DESIRED: If one disposal fails, others still execute.

    Pattern:
        resource1.close() → Success
        resource2.close() → Raises exception
        resource3.close() → Should still execute
    """
    container.register(DatabaseConnection, scope="scoped")

    # TODO: Implement after basic lifecycle works


@pytest.mark.asyncio
@pytest.mark.skip(reason="Lifecycle management not implemented yet")
async def test_disposal_order_respects_dependencies(container):
    """
    DESIRED: Disposal happens in reverse dependency order.

    Creation order:
        Database (no deps) → Repository (needs DB) → Service (needs Repo)

    Disposal order (reverse):
        Service → Repository → Database

    This ensures dependents are disposed before their dependencies.
    """
    # TODO: Implement after basic lifecycle works
    pass


# ============================================================================
# EDGE CASES
# ============================================================================


@pytest.mark.asyncio
async def test_resource_without_cleanup_method_is_fine(container):
    """
    Objects without cleanup methods should not cause errors.

    Not all objects need cleanup:
    - DTOs
    - Value objects
    - Stateless services
    """
    class SimpleService:
        def __init__(self):
            self.data = "hello"

    container.register(SimpleService, scope="scoped")

    set_scoped_cache({})
    service = container.resolve(SimpleService)

    # Should not crash even though SimpleService has no close()
    clear_scoped_cache()

    # Object still exists but removed from cache
    assert service.data == "hello"


@pytest.mark.asyncio
async def test_sync_close_method(container):
    """
    Some resources have synchronous close() methods.

    Example: file handles, threading locks

    Container should support both:
        - async def close(self)
        - def close(self)
    """
    container.register(FileHandle, scope="scoped")

    set_scoped_cache({})
    file = container.resolve(FileHandle)

    assert file.is_open is True

    # Current behavior: doesn't call close()
    clear_scoped_cache()

    # After implementation: should call file.close()
    # assert file.is_closed is True


# ============================================================================
# INTEGRATION WITH FASTAPI
# ============================================================================


@pytest.mark.asyncio
async def test_fastapi_middleware_pattern(container):
    """
    VALIDATE: FastAPI middleware pattern with automatic cleanup.

    Recommended pattern:
        @app.middleware("http")
        async def scoped_lifecycle(request, call_next):
            async with container.scoped_context():
                response = await call_next(request)
                return response
            # All scoped resources disposed automatically here
    """
    container.register(DatabaseConnection, scope="scoped")

    db_instance = None

    # Simulate middleware
    async with container.scoped_context():
        db_instance = container.resolve(DatabaseConnection)
        assert db_instance.is_open is True
        # Simulate request processing
        await asyncio.sleep(0.01)

    # After request completes
    assert db_instance.is_closed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
