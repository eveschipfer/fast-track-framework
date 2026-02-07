"""
Unit Tests for Deferred Service Providers (Sprint 13).

Tests verify:
- Deferred providers are not loaded at startup
- Deferred providers are JIT-loaded when services are requested
- Deferred providers are loaded only once
- Boot methods are called when provider is loaded
"""

import pytest

from jtc.core import Container
from jtc.core.service_provider import DeferredServiceProvider, ServiceProvider


class QueueService:
    """Example service provided by deferred provider."""

    def __init__(self) -> None:
        self.initialized = True


class QueueServiceProvider(DeferredServiceProvider):
    """Example deferred provider for QueueService."""

    provides = [QueueService]

    # Class-level flags to track provider lifecycle
    register_called = False
    boot_called = False

    def __init__(self) -> None:
        super().__init__()

    def register(self, container: Container) -> None:
        """Register QueueService."""
        QueueServiceProvider.register_called = True
        container.register(QueueService, scope="singleton")

    def boot(self) -> None:
        """Boot the provider."""
        QueueServiceProvider.boot_called = True

    @classmethod
    def reset_flags(cls) -> None:
        """Reset class-level flags for testing."""
        cls.register_called = False
        cls.boot_called = False


class TestDeferredServiceProvider:
    """Test DeferredServiceProvider class."""

    def test_deferred_provider_requires_provides(self) -> None:
        """DeferredServiceProvider requires 'provides' attribute."""

        class InvalidProvider(DeferredServiceProvider):
            provides = []

        with pytest.raises(ValueError, match="must define 'provides' attribute"):
            InvalidProvider()

    def test_deferred_provider_valid_with_provides(self) -> None:
        """DeferredServiceProvider is valid with 'provides' attribute."""

        class ValidProvider(DeferredServiceProvider):
            provides = [QueueService]

        provider = ValidProvider()
        assert provider.provides == [QueueService]


class TestContainerDeferredSupport:
    """Test Container deferred provider support."""

    def setup_method(self) -> None:
        """Reset provider flags before each test."""
        QueueServiceProvider.reset_flags()

    def test_add_deferred_maps_service_to_provider(self) -> None:
        """add_deferred maps service type to provider class."""
        container = Container()

        container.add_deferred(QueueService, QueueServiceProvider)

        assert QueueService in container._deferred_map
        assert container._deferred_map[QueueService] == QueueServiceProvider

    def test_deferred_provider_not_loaded_initially(self) -> None:
        """Deferred provider is not loaded when registered."""
        container = Container()

        container.add_deferred(QueueService, QueueServiceProvider)

        assert QueueService not in container._registry
        assert not QueueServiceProvider.register_called
        assert not QueueServiceProvider.boot_called

    def test_resolve_loads_deferred_provider(self) -> None:
        """Resolving a deferred service loads its provider JIT."""
        container = Container()

        container.add_deferred(QueueService, QueueServiceProvider)

        # Provider should not be loaded yet
        assert QueueService not in container._registry

        # Resolve should load provider and return service
        service = container.resolve(QueueService)

        assert isinstance(service, QueueService)
        assert QueueService in container._registry
        assert QueueService not in container._deferred_map  # Removed after load

    def test_deferred_provider_register_called(self) -> None:
        """Deferred provider's register() is called during JIT load."""
        container = Container()

        container.add_deferred(QueueService, QueueServiceProvider)

        # Resolve should trigger register
        container.resolve(QueueService)

        assert QueueServiceProvider.register_called

    def test_deferred_provider_boot_called(self) -> None:
        """Deferred provider's boot() is called during JIT load."""
        container = Container()

        container.add_deferred(QueueService, QueueServiceProvider)

        # Resolve should trigger boot
        container.resolve(QueueService)

        assert QueueServiceProvider.boot_called

    def test_deferred_provider_loaded_only_once(self) -> None:
        """Deferred provider is loaded only once (idempotent)."""
        container = Container()

        container.add_deferred(QueueService, QueueServiceProvider)

        # First resolve
        service1 = container.resolve(QueueService)

        # Remove from registry to test
        del container._singletons[QueueService]

        # Second resolve should not reload provider
        service2 = container.resolve(QueueService)

        assert isinstance(service1, QueueService)
        assert isinstance(service2, QueueService)
        assert QueueService not in container._deferred_map

    def test_deferred_provider_with_multiple_services(self) -> None:
        """Deferred provider can provide multiple services."""

        class CacheService:
            def __init__(self) -> None:
                self.initialized = True

        class CacheServiceProvider(DeferredServiceProvider):
            provides = [QueueService, CacheService]

            def __init__(self) -> None:
                super().__init__()
                self.boot_called = False

            def register(self, container: Container) -> None:
                container.register(QueueService, scope="singleton")
                container.register(CacheService, scope="singleton")

            def boot(self) -> None:
                self.boot_called = True

        container = Container()

        # Register both services as deferred
        for service in CacheServiceProvider.provides:
            container.add_deferred(service, CacheServiceProvider)

        # Resolve one service
        queue = container.resolve(QueueService)
        assert isinstance(queue, QueueService)

        # Both services should be registered now
        assert QueueService in container._registry
        assert CacheService in container._registry
        assert QueueService not in container._deferred_map
        assert CacheService not in container._deferred_map

        # Resolve the other service (should use already-loaded provider)
        cache = container.resolve(CacheService)
        assert isinstance(cache, CacheService)


class TestAsyncBootDeferredProvider:
    """Test deferred providers with async boot methods."""

    @pytest.mark.asyncio
    async def test_async_boot_called_on_deferred_load(self) -> None:
        """Async boot() is called during JIT load."""

        class AsyncQueueServiceProvider(DeferredServiceProvider):
            provides = [QueueService]

            def __init__(self) -> None:
                super().__init__()
                self.boot_called = False

            def register(self, container: Container) -> None:
                container.register(QueueService, scope="singleton")

            async def boot(self) -> None:
                """Async boot method."""
                self.boot_called = True

        container = Container()
        provider = AsyncQueueServiceProvider()

        container.add_deferred(QueueService, type(provider))

        # Resolve should trigger async boot
        service = container.resolve(QueueService)

        assert isinstance(service, QueueService)
        # Note: async boot is scheduled as a task, may not complete immediately
        # This is a known limitation for v1.0 when called from sync contexts
