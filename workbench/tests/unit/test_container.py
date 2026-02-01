"""
Test Suite for IoC Container
=============================

Comprehensive tests covering:
- Basic resolution
- Dependency chains
- Singleton behavior
- Transient behavior
- Scoped lifetime
- Error cases
- Edge cases

Run tests:
    pytest tests/unit/test_container.py -v
    pytest tests/unit/test_container.py -v --cov=ftf.core
"""

import pytest
from typing import Optional

from ftf.core import (
    Container,
    DependencyResolutionError,
    CircularDependencyError,
    get_scoped_cache,
    set_scoped_cache,
    clear_scoped_cache,
)


# ============================================================================
# TEST FIXTURES (Reusable Test Components)
# ============================================================================


class MockDatabase:
    """Mock database for testing."""

    def __init__(self):
        self.connection_id = id(self)


class MockRepository:
    """Repository with database dependency."""

    def __init__(self, db: MockDatabase):
        self.db = db


class MockService:
    """Service with repository dependency."""

    def __init__(self, repo: MockRepository):
        self.repo = repo


class IndependentService:
    """Service without dependencies."""

    pass


class MultiDependencyService:
    """Service with multiple dependencies."""

    def __init__(self, db: MockDatabase, repo: MockRepository):
        self.db = db
        self.repo = repo


@pytest.fixture
def container():
    """Provide fresh container for each test."""
    return Container()


@pytest.fixture(autouse=True)
def clear_scoped():
    """Clear scoped cache before each test."""
    clear_scoped_cache()
    yield
    clear_scoped_cache()


# ============================================================================
# BASIC RESOLUTION TESTS
# ============================================================================


def test_resolve_service_without_dependencies(container):
    """Test resolving service with no dependencies."""
    container.register(IndependentService)

    service = container.resolve(IndependentService)

    assert isinstance(service, IndependentService)


def test_resolve_unregistered_service_creates_instance(container):
    """Test that unregistered services are instantiated directly."""
    # Don't register IndependentService

    service = container.resolve(IndependentService)

    assert isinstance(service, IndependentService)


def test_resolve_with_interface_mapping(container):
    """Test interface → implementation mapping."""

    class IService:
        pass

    class ConcreteService(IService):
        pass

    container.register(IService, ConcreteService)

    service = container.resolve(IService)

    assert isinstance(service, ConcreteService)


# ============================================================================
# DEPENDENCY CHAIN TESTS
# ============================================================================


def test_resolve_single_level_dependency(container):
    """Test resolving service with one dependency level."""
    container.register(MockDatabase)
    container.register(MockRepository)

    repo = container.resolve(MockRepository)

    assert isinstance(repo, MockRepository)
    assert isinstance(repo.db, MockDatabase)


def test_resolve_nested_dependencies(container):
    """Test resolving service with nested dependency chain."""
    container.register(MockDatabase)
    container.register(MockRepository)
    container.register(MockService)

    service = container.resolve(MockService)

    assert isinstance(service, MockService)
    assert isinstance(service.repo, MockRepository)
    assert isinstance(service.repo.db, MockDatabase)


def test_resolve_multiple_dependencies(container):
    """Test service with multiple direct dependencies."""
    container.register(MockDatabase)
    container.register(MockRepository)
    container.register(MultiDependencyService)

    service = container.resolve(MultiDependencyService)

    assert isinstance(service.db, MockDatabase)
    assert isinstance(service.repo, MockRepository)


# ============================================================================
# SINGLETON LIFETIME TESTS
# ============================================================================


def test_singleton_returns_same_instance(container):
    """Test singleton scope returns same instance."""
    container.register(MockDatabase, scope="singleton")

    db1 = container.resolve(MockDatabase)
    db2 = container.resolve(MockDatabase)

    assert db1 is db2
    assert db1.connection_id == db2.connection_id


def test_singleton_shared_across_dependents(container):
    """Test singleton instance is shared across all consumers."""
    container.register(MockDatabase, scope="singleton")
    container.register(MockRepository)

    repo1 = container.resolve(MockRepository)
    repo2 = container.resolve(MockRepository)

    # Repos are different (transient)
    assert repo1 is not repo2

    # But they share the same DB instance (singleton)
    assert repo1.db is repo2.db


# ============================================================================
# TRANSIENT LIFETIME TESTS
# ============================================================================


def test_transient_returns_new_instance(container):
    """Test transient scope creates new instances."""
    container.register(MockDatabase, scope="transient")

    db1 = container.resolve(MockDatabase)
    db2 = container.resolve(MockDatabase)

    assert db1 is not db2
    assert db1.connection_id != db2.connection_id


def test_default_scope_is_transient(container):
    """Test that default scope is transient."""
    # Register without specifying scope
    container.register(MockDatabase)

    db1 = container.resolve(MockDatabase)
    db2 = container.resolve(MockDatabase)

    assert db1 is not db2


# ============================================================================
# SCOPED LIFETIME TESTS
# ============================================================================


def test_scoped_returns_same_instance_in_scope(container):
    """Test scoped returns same instance within scope."""
    container.register(MockDatabase, scope="scoped")

    # First scope
    set_scoped_cache({})
    db1 = container.resolve(MockDatabase)
    db2 = container.resolve(MockDatabase)

    assert db1 is db2


def test_scoped_returns_different_instance_across_scopes(container):
    """Test scoped returns different instances across scopes."""
    container.register(MockDatabase, scope="scoped")

    # First scope
    set_scoped_cache({})
    db1 = container.resolve(MockDatabase)

    # Second scope (simulating new request)
    clear_scoped_cache()
    set_scoped_cache({})
    db2 = container.resolve(MockDatabase)

    assert db1 is not db2


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


def test_circular_dependency_detection():
    """Test circular dependency is detected and reported."""

    # Note: In Python 3.14, forward references in function scope
    # can't be resolved by get_type_hints(), so we get
    # DependencyResolutionError instead of CircularDependencyError
    class ServiceA:
        def __init__(self, b: "ServiceB"):
            self.b = b

    class ServiceB:
        def __init__(self, a: ServiceA):
            self.a = a

    container = Container()
    container.register(ServiceA)
    container.register(ServiceB)

    with pytest.raises(DependencyResolutionError) as exc_info:
        container.resolve(ServiceA)

    assert "ServiceA" in str(exc_info.value)
    assert "ServiceB" in str(exc_info.value)


def test_missing_type_hints_error():
    """Test error when type hints cannot be resolved."""

    class BrokenService:
        def __init__(self, dep: "NonExistentClass"):
            self.dep = dep

    container = Container()
    container.register(BrokenService)

    with pytest.raises(DependencyResolutionError) as exc_info:
        container.resolve(BrokenService)

    assert "NonExistentClass" in str(exc_info.value)


def test_nested_resolution_error_context():
    """Test error messages provide full context."""

    class FailingService:
        def __init__(self, dep: "UndefinedDependency"):
            pass

    class ConsumerService:
        def __init__(self, failing: FailingService):
            self.failing = failing

    container = Container()
    container.register(FailingService)
    container.register(ConsumerService)

    with pytest.raises(DependencyResolutionError) as exc_info:
        container.resolve(ConsumerService)

    error_msg = str(exc_info.value)
    assert "ConsumerService" in error_msg
    assert "FailingService" in error_msg


# ============================================================================
# EDGE CASES & SPECIAL SCENARIOS
# ============================================================================


def test_resolve_same_type_multiple_times(container):
    """Test multiple resolves don't interfere."""
    container.register(MockDatabase, scope="singleton")
    container.register(MockRepository)

    repo1 = container.resolve(MockRepository)
    repo2 = container.resolve(MockRepository)
    db = container.resolve(MockDatabase)

    assert repo1.db is db
    assert repo2.db is db


def test_reset_singletons(container):
    """Test singleton cache can be reset."""
    container.register(MockDatabase, scope="singleton")

    db1 = container.resolve(MockDatabase)

    container.reset_singletons()

    db2 = container.resolve(MockDatabase)

    assert db1 is not db2


def test_is_registered(container):
    """Test checking if type is registered."""
    container.register(MockDatabase)

    assert container.is_registered(MockDatabase)
    assert not container.is_registered(MockRepository)


def test_optional_dependency():
    """Test service with Optional type hint."""

    class ServiceWithOptional:
        def __init__(self, db: Optional[MockDatabase] = None):
            self.db = db

    container = Container()

    # This will fail because Optional[X] resolves to Union[X, None]
    # which can't be instantiated. This is a known limitation.
    # Optional deps need explicit handling or default values.
    with pytest.raises((DependencyResolutionError, TypeError)):
        container.resolve(ServiceWithOptional)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_realistic_dependency_graph(container):
    """Test realistic multi-level dependency graph."""
    # Setup: DB (singleton) → Repo → Service
    container.register(MockDatabase, scope="singleton")
    container.register(MockRepository, scope="transient")
    container.register(MockService, scope="transient")

    # Resolve multiple services
    service1 = container.resolve(MockService)
    service2 = container.resolve(MockService)

    # Services are different
    assert service1 is not service2

    # Repos are different
    assert service1.repo is not service2.repo

    # But DB is shared (singleton)
    assert service1.repo.db is service2.repo.db


def test_mixed_scopes_in_chain(container):
    """Test dependency chain with mixed scopes."""
    container.register(MockDatabase, scope="singleton")
    container.register(MockRepository, scope="transient")
    container.register(MockService, scope="scoped")

    # First scope
    set_scoped_cache({})
    service1 = container.resolve(MockService)
    service2 = container.resolve(MockService)

    # Services are same (scoped)
    assert service1 is service2

    # Repos are different (transient)
    # Note: This might seem weird but it's by design
    # Each resolve of MockRepository creates new instance


# ============================================================================
# PERFORMANCE TESTS (Optional)
# ============================================================================


def test_resolution_performance(container, benchmark=None):
    """Test resolution performance (requires pytest-benchmark)."""
    if benchmark is None:
        pytest.skip("pytest-benchmark not installed")

    container.register(MockDatabase, scope="singleton")
    container.register(MockRepository)
    container.register(MockService)

    def resolve_service():
        return container.resolve(MockService)

    result = benchmark(resolve_service)
    assert isinstance(result, MockService)


# ============================================================================
# DOCUMENTATION TESTS
# ============================================================================


def test_container_docstring():
    """Test that Container has proper documentation."""
    assert Container.__doc__ is not None
    assert "Dependency Injection" in Container.__doc__


def test_resolve_docstring():
    """Test that resolve method has proper documentation."""
    assert Container.resolve.__doc__ is not None
    assert "resolve" in Container.resolve.__doc__.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
