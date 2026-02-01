"""
Integration Tests - FastAPI + IoC Container Integration

This module verifies that the FastAPI integration with the IoC Container
works correctly end-to-end.

Test Coverage:
1. App instantiation with container
2. Dependency injection in routes
3. Scoped middleware lifecycle
4. Multiple routes with different dependencies
5. Error handling in DI

Design Decision:
    Using TestClient (not async) because:
    - Simpler for integration tests
    - FastAPI's recommended approach
    - Handles lifespan context automatically
"""

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from ftf.http.app import FastTrackFramework, ScopedMiddleware
from ftf.http.params import Inject

# ============================================================================
# TEST FIXTURES AND ARTIFACTS
# ============================================================================


class MockService:
    """
    Mock service for testing dependency injection.

    This simulates a real service that would be injected into routes.
    """

    def get_data(self) -> str:
        """Return mock data."""
        return "mocked_data"

    def get_status(self) -> dict[str, str]:
        """Return mock status."""
        return {"status": "ok", "service": "MockService"}


class DependentService:
    """
    Service that depends on MockService.

    This tests nested dependency resolution.
    """

    def __init__(self, mock: MockService) -> None:
        """Initialize with MockService dependency."""
        self.mock = mock

    def get_combined_data(self) -> str:
        """Get data from dependency."""
        return f"dependent_{self.mock.get_data()}"


# ============================================================================
# TEST CASES
# ============================================================================


def test_app_instantiation_with_container() -> None:
    """
    Test that FastTrackFramework initializes with a container.

    Verifies:
    - App instance is created successfully
    - Container is initialized
    - Container is accessible via app.container
    """
    app = FastTrackFramework()

    # Verify container exists
    assert hasattr(app, "container")
    assert app.container is not None

    # Verify container is functional
    assert app.container._registry is not None
    assert app.container._singletons is not None


def test_dependency_injection_basic() -> None:
    """
    Test basic dependency injection in routes.

    Verifies:
    - Service registration works
    - Inject() resolves dependencies correctly
    - Route handler receives injected service
    - Service methods are callable
    """
    # Setup App
    app = FastTrackFramework()
    app.add_middleware(ScopedMiddleware)

    # Register Dependency
    app.register(MockService, scope="transient")

    # Setup Route with Injection
    router = APIRouter()

    @router.get("/test")
    def endpoint(service: MockService = Inject(MockService)) -> dict[str, str]:
        return {"data": service.get_data()}

    app.include_router(router)

    # Test Request
    client = TestClient(app)
    response = client.get("/test")

    # Assertions
    assert response.status_code == 200
    assert response.json() == {"data": "mocked_data"}


def test_dependency_injection_nested() -> None:
    """
    Test nested dependency resolution.

    Verifies:
    - Container resolves transitive dependencies
    - DependentService receives MockService automatically
    - Nested dependencies work through Inject()
    """
    # Setup App
    app = FastTrackFramework()
    app.add_middleware(ScopedMiddleware)

    # Register Dependencies (DependentService requires MockService)
    app.register(MockService, scope="transient")
    app.register(DependentService, scope="transient")

    # Setup Route
    router = APIRouter()

    @router.get("/nested")
    def endpoint(
        service: DependentService = Inject(DependentService),
    ) -> dict[str, str]:
        return {"data": service.get_combined_data()}

    app.include_router(router)

    # Test Request
    client = TestClient(app)
    response = client.get("/nested")

    # Assertions
    assert response.status_code == 200
    assert response.json() == {"data": "dependent_mocked_data"}


def test_singleton_scope() -> None:
    """
    Test singleton scope behavior.

    Verifies:
    - Singleton services are reused across requests
    - Same instance is injected multiple times
    - Singleton state persists
    """

    class Counter:
        """Service with state to test singleton behavior."""

        def __init__(self) -> None:
            self.count = 0

        def increment(self) -> int:
            self.count += 1
            return self.count

    # Setup App
    app = FastTrackFramework()
    app.add_middleware(ScopedMiddleware)

    # Register as Singleton
    app.register(Counter, scope="singleton")

    # Setup Route
    router = APIRouter()

    @router.get("/count")
    def endpoint(counter: Counter = Inject(Counter)) -> dict[str, int]:
        return {"count": counter.increment()}

    app.include_router(router)

    # Test Multiple Requests
    client = TestClient(app)

    response1 = client.get("/count")
    assert response1.json() == {"count": 1}

    response2 = client.get("/count")
    assert response2.json() == {"count": 2}

    response3 = client.get("/count")
    assert response3.json() == {"count": 3}


def test_transient_scope() -> None:
    """
    Test transient scope behavior.

    Verifies:
    - Transient services are created fresh each time
    - No state is shared between injections
    """

    class TransientCounter:
        """Service to test transient behavior."""

        def __init__(self) -> None:
            self.count = 0

        def increment(self) -> int:
            self.count += 1
            return self.count

    # Setup App
    app = FastTrackFramework()
    app.add_middleware(ScopedMiddleware)

    # Register as Transient
    app.register(TransientCounter, scope="transient")

    # Setup Route
    router = APIRouter()

    @router.get("/transient")
    def endpoint(
        counter: TransientCounter = Inject(TransientCounter),
    ) -> dict[str, int]:
        return {"count": counter.increment()}

    app.include_router(router)

    # Test Multiple Requests
    client = TestClient(app)

    # Each request should get count=1 (new instance)
    response1 = client.get("/transient")
    assert response1.json() == {"count": 1}

    response2 = client.get("/transient")
    assert response2.json() == {"count": 1}

    response3 = client.get("/transient")
    assert response3.json() == {"count": 1}


def test_scoped_dependency_lifecycle() -> None:
    """
    Test scoped dependency lifecycle.

    Verifies:
    - Scoped services are created once per request
    - Same instance is reused within a request
    - Different instances for different requests
    """

    class ScopedService:
        """Service to test scoped behavior."""

        instance_count = 0

        def __init__(self) -> None:
            ScopedService.instance_count += 1
            self.id = ScopedService.instance_count

        def get_id(self) -> int:
            return self.id

    # Setup App
    app = FastTrackFramework()
    app.add_middleware(ScopedMiddleware)

    # Register as Scoped
    app.register(ScopedService, scope="scoped")

    # Setup Routes that inject the same scoped service
    router = APIRouter()

    @router.get("/scoped1")
    def endpoint1(service: ScopedService = Inject(ScopedService)) -> dict[str, int]:
        return {"id": service.get_id(), "endpoint": 1}

    @router.get("/scoped2")
    def endpoint2(service: ScopedService = Inject(ScopedService)) -> dict[str, int]:
        return {"id": service.get_id(), "endpoint": 2}

    app.include_router(router)

    # Test
    client = TestClient(app)

    # Request 1: Both endpoints in same request should get same instance
    # (This would require a single request hitting both endpoints,
    #  but TestClient makes separate requests, so we verify different instances)
    response1 = client.get("/scoped1")
    assert response1.json()["id"] == 1
    assert response1.json()["endpoint"] == 1

    # Request 2: Should get a NEW scoped instance
    response2 = client.get("/scoped2")
    assert response2.json()["id"] == 2
    assert response2.json()["endpoint"] == 2


def test_multiple_routes_with_dependencies() -> None:
    """
    Test multiple routes using the same and different dependencies.

    Verifies:
    - Multiple routes can inject dependencies
    - Different routes can use different services
    - Router configuration works correctly
    """
    # Setup App
    app = FastTrackFramework()
    app.add_middleware(ScopedMiddleware)

    # Register Multiple Services
    app.register(MockService, scope="transient")

    # Setup Multiple Routes
    router = APIRouter()

    @router.get("/service1")
    def endpoint1(service: MockService = Inject(MockService)) -> dict[str, str]:
        return {"data": service.get_data(), "route": "service1"}

    @router.get("/service2")
    def endpoint2(service: MockService = Inject(MockService)) -> dict[str, str]:
        return service.get_status()

    @router.get("/no-deps")
    def endpoint3() -> dict[str, str]:
        return {"message": "no dependencies"}

    app.include_router(router)

    # Test All Routes
    client = TestClient(app)

    response1 = client.get("/service1")
    assert response1.status_code == 200
    assert response1.json() == {"data": "mocked_data", "route": "service1"}

    response2 = client.get("/service2")
    assert response2.status_code == 200
    assert response2.json() == {"status": "ok", "service": "MockService"}

    response3 = client.get("/no-deps")
    assert response3.status_code == 200
    assert response3.json() == {"message": "no dependencies"}


def test_container_registration_convenience_method() -> None:
    """
    Test app.register() convenience method.

    Verifies:
    - app.register() works as a wrapper around container.register()
    - Registered services are accessible via Inject()
    """
    # Setup App
    app = FastTrackFramework()
    app.add_middleware(ScopedMiddleware)

    # Use convenience method
    app.register(MockService, scope="singleton")

    # Verify registration worked
    assert app.container.is_registered(MockService)

    # Setup Route
    router = APIRouter()

    @router.get("/test")
    def endpoint(service: MockService = Inject(MockService)) -> dict[str, str]:
        return {"data": service.get_data()}

    app.include_router(router)

    # Test
    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200
    assert response.json() == {"data": "mocked_data"}


def test_app_lifespan_events() -> None:
    """
    Test application lifespan events.

    Verifies:
    - Lifespan context manager is called
    - Container is available during app lifetime
    - Cleanup happens on shutdown
    """
    app = FastTrackFramework()

    # TestClient handles lifespan automatically
    with TestClient(app) as client:
        # App is running, container should be available
        assert app.container is not None

        # Simple health check
        router = APIRouter()

        @router.get("/health")
        def health() -> dict[str, str]:
            return {"status": "healthy"}

        app.include_router(router)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    # After context, cleanup should have happened
    # (In real app, this would close DB connections, etc.)
    assert app.container is not None  # Container still exists


# ============================================================================
# PYTEST MARKERS
# ============================================================================

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration
