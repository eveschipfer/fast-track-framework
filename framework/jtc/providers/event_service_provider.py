"""
Event Service Provider (Sprint 14.0)

This module provides the EventServiceProvider for discovering and registering
event-listener mappings in the IoC Container.

Architecture:
    EventServiceProvider → EventDispatcher (via DI) → Listeners (resolved via DI)

Key Features:
    - Automatic discovery: Maps Event classes to lists of Listener classes
    - Container registration: Registers EventDispatcher in container
    - Zero manual registration: Just define `listen` attribute on provider

Educational Note:
    This follows Laravel's EventServiceProvider pattern, where providers define
    which events they listen to. The framework automatically wires everything
    together, eliminating manual dispatcher.register() calls.

Example:
    class EventServiceProvider(ftf.core.service_provider.ServiceProvider):
        listen = {
            UserRegistered: [SendWelcomeEmail, LogRegistration],
            OrderPlaced: [SendOrderConfirmation, UpdateInventory],
        }

        def register(self, container):
            container.register(EventDispatcher, scope="singleton")
            # Automatically registers all event-listener mappings
"""
from typing import TYPE_CHECKING

from jtc.core.service_provider import ServiceProvider

if TYPE_CHECKING:
    from jtc.core import Container
    from jtc.events.core import Event, EventDispatcher


class EventServiceProvider(ServiceProvider):
    """
    Service Provider for automatic event-listener discovery and registration.

    This provider eliminates manual event registration by allowing you to define
    event-listener mappings in the `listen` class attribute.

    Attributes:
        listen: Dictionary mapping Event classes to lists of Listener classes

    Example:
        class EventServiceProvider(ServiceProvider):
            listen = {
                UserRegistered: [SendWelcomeEmail, LogRegistration],
            }

            def register(self, container):
                # Registers EventDispatcher and all event-listener mappings
                # Listeners are automatically registered with EventDispatcher
                container.register(EventDispatcher, scope="singleton")
    """

    listen: dict[type["Event"], list[type]] = {}

    def register(self, container: "Container") -> None:
        """
        Register EventDispatcher and all event-listener mappings.

        This method:
        1. Resolves EventDispatcher from container (or registers if not exists)
        2. Iterates through `listen` dictionary
        3. Registers each listener class with the dispatcher

        Args:
            container: The IoC Container instance
        """
        # Note: The parent class implementation handles the registration
        from jtc.events.core import EventDispatcher

        if not container.is_registered(EventDispatcher):
            container.register(EventDispatcher, implementation=EventDispatcher, scope="singleton")

        # Get dispatcher and register all event-listener mappings
        dispatcher = container.resolve(EventDispatcher)

        for event_type, listener_types in self.listen.items():
            for listener_type in listener_types:
                dispatcher.register(event_type, listener_type)
