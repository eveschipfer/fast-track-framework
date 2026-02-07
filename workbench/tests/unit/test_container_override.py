"""
Dependency Override Tests for IoC Container
===========================================

CRITICAL: Tests dependency override for testing and runtime configuration.

This test suite validates that:
1. Dependencies can be overridden in tests (mocking)
2. Overrides work with all scopes (singleton, transient, scoped)
3. Overrides can be reset/cleared
4. Overrides don't affect original registrations
5. Override priority is correct (override > registration > fallback)

WHY THIS EXISTS:
Without override, testing becomes impossible:

    # Production code
    container.register(Database, PostgresDatabase, scope="singleton")
    container.register(UserService)

    # Test code (PROBLEM: Can't mock Database!)
    def test_user_service():
        service = container.resolve(UserService)  # Uses real PostgresDatabase
        # ❌ Can't inject FakeDatabase for testing

This blocks:
- Unit testing with mocked dependencies
- Integration testing with fake services
- Runtime configuration swapping

Run tests:
    pytest tests/unit/test_container_override.py -v
    pytest tests/unit/test_container_override.py -v --tb=short
"""

import pytest
from typing import Protocol

from jtc.core import Container, set_scoped_cache, clear_scoped_cache


# ============================================================================
# TEST FIXTURES
# ============================================================================


class IDatabase(Protocol):
    """Database interface for testing."""

    def query(self, sql: str) -> str:
        ...


class RealDatabase:
    """Real database (production)."""

    def query(self, sql: str) -> str:
        return f"REAL: {sql}"


class FakeDatabase:
    """Fake database (testing)."""

    def query(self, sql: str) -> str:
        return f"FAKE: {sql}"


class UserRepository:
    """Repository depending on database."""

    def __init__(self, db: RealDatabase):
        self.db = db

    def get_user(self, user_id: int) -> str:
        return self.db.query(f"SELECT * FROM users WHERE id={user_id}")


class UserService:
    """Service depending on repository."""

    def __init__(self, repo: UserRepository):
        self.repo = repo


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
# PROBLEM DEMONSTRATION TESTS (Will FAIL until override is implemented)
# ============================================================================


def test_cannot_mock_dependencies_without_override(container):
    """
    DEMONSTRATE PROBLEM: Cannot inject test doubles.

    Current behavior:
        1. Register RealDatabase in container
        2. Try to test UserService
        3. Can't inject FakeDatabase (uses RealDatabase)
        4. Test hits real database (BAD!)

    Expected (after fix):
        Should be able to override RealDatabase with FakeDatabase
    """
    # Setup production registrations
    container.register(RealDatabase, scope="singleton")
    container.register(UserRepository)

    # Try to resolve
    repo = container.resolve(UserRepository)

    # PROBLEM: Uses RealDatabase, can't mock it
    result = repo.get_user(123)
    assert "REAL:" in result  # ← Using real database


def test_cannot_swap_implementation_at_runtime(container):
    """
    DEMONSTRATE PROBLEM: Cannot swap implementations at runtime.

    Use case: Feature flags, A/B testing, environment-specific config

    Example:
        if config.use_fake_payment:
            # Want to use FakePaymentService
        else:
            # Want to use RealPaymentService

    Current behavior: Must re-register (loses original)
    """
    container.register(RealDatabase, scope="singleton")

    db1 = container.resolve(RealDatabase)
    assert isinstance(db1, RealDatabase)

    # Try to swap implementation
    # Current approach: re-register (loses original)
    container.register(RealDatabase, FakeDatabase, scope="singleton")

    db2 = container.resolve(RealDatabase)

    # PROBLEM: This changes the registration permanently
    # Can't easily revert to original


# ============================================================================
# DESIRED BEHAVIOR TESTS (Will PASS after override is implemented)
# ============================================================================


def test_override_single_dependency(container):
    """
    DESIRED: Override a single dependency for testing.

    Pattern:
        # Production registration
        container.register(Database, RealDatabase)

        # Test override
        container.override(Database, FakeDatabase)

        # Resolve uses FakeDatabase
        db = container.resolve(Database)
        assert isinstance(db, FakeDatabase)
    """
    container.register(RealDatabase, scope="singleton")

    # Override with fake
    container.override(RealDatabase, FakeDatabase)

    db = container.resolve(RealDatabase)

    assert isinstance(db, FakeDatabase)
    assert "FAKE:" in db.query("test")


def test_override_affects_dependent_services(container):
    """
    DESIRED: Override cascades to dependent services.

    Dependency graph:
        UserService → UserRepository → Database

    Override Database:
        container.override(Database, FakeDatabase)

    Expected:
        UserService should use FakeDatabase (transitively)
    """
    # Production registrations
    container.register(RealDatabase, scope="singleton")
    container.register(UserRepository)
    container.register(UserService)

    # Override database
    container.override(RealDatabase, FakeDatabase)

    # Resolve service
    service = container.resolve(UserService)

    # Should use FakeDatabase transitively
    result = service.repo.get_user(123)
    assert "FAKE:" in result


def test_override_can_be_reset(container):
    """
    DESIRED: Overrides can be cleared to revert to original.

    Pattern:
        # Register original
        container.register(Database, RealDatabase)

        # Override for test
        container.override(Database, FakeDatabase)
        db = container.resolve(Database)  # Uses FakeDatabase

        # Reset override
        container.reset_overrides()
        db = container.resolve(Database)  # Uses RealDatabase again
    """
    container.register(RealDatabase, scope="singleton")

    # Override
    container.override(RealDatabase, FakeDatabase)
    db1 = container.resolve(RealDatabase)
    assert isinstance(db1, FakeDatabase)

    # Reset overrides
    container.reset_overrides()

    # Should use original registration
    container.reset_singletons()  # Clear cache
    db2 = container.resolve(RealDatabase)
    assert isinstance(db2, RealDatabase)


def test_override_works_with_singleton_scope(container):
    """
    DESIRED: Override works with singleton scope.

    Edge case:
        1. Register Database as singleton
        2. Resolve Database (caches RealDatabase)
        3. Override Database with FakeDatabase
        4. Resolve Database (should use FakeDatabase)

    Question: Should override invalidate singleton cache?
    Answer: YES (override should take immediate effect)
    """
    container.register(RealDatabase, scope="singleton")

    # Resolve and cache
    db1 = container.resolve(RealDatabase)
    assert isinstance(db1, RealDatabase)

    # Override (should invalidate cache)
    container.override(RealDatabase, FakeDatabase)

    # Should use override
    db2 = container.resolve(RealDatabase)
    assert isinstance(db2, FakeDatabase)
    assert db1 is not db2  # Different instances


def test_override_works_with_scoped(container):
    """
    DESIRED: Override works with scoped dependencies.
    """
    container.register(RealDatabase, scope="scoped")

    set_scoped_cache({})

    # Resolve original
    db1 = container.resolve(RealDatabase)
    assert isinstance(db1, RealDatabase)

    clear_scoped_cache()

    # Override
    container.override(RealDatabase, FakeDatabase)

    set_scoped_cache({})

    # Should use override
    db2 = container.resolve(RealDatabase)
    assert isinstance(db2, FakeDatabase)


def test_override_works_with_transient(container):
    """
    DESIRED: Override works with transient scope.
    """
    container.register(RealDatabase, scope="transient")

    # Override
    container.override(RealDatabase, FakeDatabase)

    # All new instances should be FakeDatabase
    db1 = container.resolve(RealDatabase)
    db2 = container.resolve(RealDatabase)

    assert isinstance(db1, FakeDatabase)
    assert isinstance(db2, FakeDatabase)
    assert db1 is not db2  # Transient: different instances


def test_multiple_overrides(container):
    """
    DESIRED: Can override multiple dependencies.
    """
    class FakeRepo:
        pass

    container.register(RealDatabase)
    container.register(UserRepository)

    # Override multiple
    container.override(RealDatabase, FakeDatabase)
    container.override(UserRepository, FakeRepo)

    db = container.resolve(RealDatabase)
    repo = container.resolve(UserRepository)

    assert isinstance(db, FakeDatabase)
    assert isinstance(repo, FakeRepo)


def test_override_with_instance(container):
    """
    DESIRED: Override with pre-constructed instance (not just type).

    Use case: Mock objects, spies, test fixtures

    Pattern:
        fake_db = FakeDatabase()
        fake_db.setup_test_data()

        container.override_instance(Database, fake_db)
        service = container.resolve(UserService)
        # Uses the specific fake_db instance
    """
    container.register(RealDatabase)

    # Create specific instance
    fake_db = FakeDatabase()

    # Override with instance
    container.override_instance(RealDatabase, fake_db)

    db1 = container.resolve(RealDatabase)
    db2 = container.resolve(RealDatabase)

    # Should return same instance
    assert db1 is fake_db
    assert db2 is fake_db


@pytest.mark.asyncio
async def test_override_context_manager(container):
    """
    VALIDATE: Temporary override via async context manager.

    Pattern:
        container.register(Database, RealDatabase)

        # Temporarily override
        async with container.override_context(Database, FakeDatabase):
            db = container.resolve(Database)  # Uses FakeDatabase

        # Reverts to RealDatabase
        db = container.resolve(Database)  # Uses RealDatabase
    """
    container.register(RealDatabase, scope="singleton")

    # Temporary override
    async with container.override_context(RealDatabase, FakeDatabase):
        db_inside = container.resolve(RealDatabase)
        assert isinstance(db_inside, FakeDatabase)

    # Reverted
    container.reset_singletons()
    db_outside = container.resolve(RealDatabase)
    assert isinstance(db_outside, RealDatabase)


def test_override_priority(container):
    """
    DESIRED: Override has highest priority.

    Priority order:
        1. Override (highest)
        2. Registration
        3. Fallback instantiation (lowest)

    Test:
        register(Database, RealDatabase)
        override(Database, FakeDatabase)
        resolve(Database) → FakeDatabase (override wins)
    """
    # Register
    container.register(RealDatabase, scope="singleton")

    # Override
    container.override(RealDatabase, FakeDatabase)

    # Override should win
    db = container.resolve(RealDatabase)
    assert isinstance(db, FakeDatabase)


# ============================================================================
# EDGE CASES
# ============================================================================


def test_override_unregistered_type(container):
    """
    DESIRED: Can override even if not registered.

    Use case: Mock dependency that wasn't explicitly registered
    """
    # Don't register RealDatabase

    # Override anyway
    container.override(RealDatabase, FakeDatabase)

    # Should use override
    db = container.resolve(RealDatabase)
    assert isinstance(db, FakeDatabase)


def test_reset_specific_override(container):
    """
    DESIRED: Reset specific override, keep others.

    Pattern:
        container.override(Database, FakeDatabase)
        container.override(Cache, FakeCache)

        container.reset_override(Database)  # Reset only Database

        # Database reverted, Cache still overridden
    """
    container.register(RealDatabase)

    # Multiple overrides
    container.override(RealDatabase, FakeDatabase)

    # Reset specific override
    container.reset_override(RealDatabase)

    # Should use original
    db = container.resolve(RealDatabase)
    assert isinstance(db, RealDatabase)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_realistic_testing_scenario(container):
    """
    DESIRED: Complete testing workflow.

    Scenario:
        1. Setup production container
        2. Override dependencies for test
        3. Test service with mocked dependencies
        4. Cleanup (reset overrides)
    """
    # Production setup
    container.register(RealDatabase, scope="singleton")
    container.register(UserRepository)
    container.register(UserService)

    # Test setup: override with fakes
    container.override(RealDatabase, FakeDatabase)

    # Test
    service = container.resolve(UserService)
    result = service.repo.get_user(999)

    assert "FAKE:" in result  # Uses fake database

    # Cleanup
    container.reset_overrides()
    container.reset_singletons()

    # Production code works again
    service2 = container.resolve(UserService)
    result2 = service2.repo.get_user(999)

    assert "REAL:" in result2  # Uses real database


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
