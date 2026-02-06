"""
Event System Core (Sprint 3.1)

This module provides the core components for the Event Bus system, implementing
the Observer Pattern with async support and IoC Container integration.

Key Components:
    - Event: Base class for all events (DTO pattern)
    - Listener[E]: Generic base class for event handlers
    - EventDispatcher: Singleton that manages event-listener registry

Educational Note:
    This implements the Observer Pattern (GoF) where Events are subjects and
    Listeners are observers. Unlike traditional implementations, we use:
    1. Async execution (asyncio.gather for concurrent processing)
    2. IoC Container integration (listeners get dependency injection)
    3. Type-safe generics (Listener[UserRegistered] vs raw types)

    This pattern is used in Laravel (Event Dispatcher), Symfony (EventDispatcher),
    and Django (Signals), but our implementation is async-first and type-safe.

Architecture:
    Controllers → dispatch(Event) → EventDispatcher → Listeners (via IoC)
                                                    ↓
                                            async handle(event)

Example:
    # Define event
    @dataclass
    class UserRegistered(Event):
        user_id: int
        email: str

    # Define listener
    class SendWelcomeEmail(Listener[UserRegistered]):
        def __init__(self, mailer: MailService):
            self.mailer = mailer

        async def handle(self, event: UserRegistered) -> None:
            await self.mailer.send(event.email, "Welcome!")

    # Register
    dispatcher.register(UserRegistered, SendWelcomeEmail)

    # Dispatch
    await dispatcher.dispatch(UserRegistered(user_id=1, email="user@test.com"))
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from ftf.core import Container

# Type variable for generic Event
E = TypeVar("E", bound="Event")


class Event(ABC):
    """
    Base class for all events.

    Events are DTOs (Data Transfer Objects) that carry information about
    something that happened in the system. They should be immutable and
    contain only data (no business logic).

    Attributes:
        should_propagate: bool - Whether exceptions in listeners should propagate

    Educational Note:
        We use ABC to make this a "marker" base class. In production, you'd
        typically use dataclass for events, but inheriting from Event helps
        with type checking and documentation.

    Example:
        >>> from dataclasses import dataclass
        >>> @dataclass
        >>> ... class UserRegistered(Event):
        ...     user_id: int
        ...     email: str
        ...     name: str
        ...     should_propagate: bool = True
    """

    should_propagate: bool = True

    pass


class Listener(ABC, Generic[E]):
    """
    Base class for event listeners.

    Listeners handle specific events. They are resolved via IoC Container,
    so they can receive dependencies via __init__ (dependency injection).

    The Generic[E] allows type-safe listener registration:
        Listener[UserRegistered] only handles UserRegistered events

    Educational Note:
        Unlike Laravel's "listener classes" which are just callables, we use
        a base class with an abstract method to enforce the contract and
        enable IDE autocomplete.

    Example:
        >>> class SendWelcomeEmail(Listener[UserRegistered]):
        ...     def __init__(self, mailer: MailService):
        ...         self.mailer = mailer
        ...
        ...     async def handle(self, event: UserRegistered) -> None:
        ...         await self.mailer.send(event.email, "Welcome!")
    """

    @abstractmethod
    async def handle(self, event: E) -> None:
        """
        Handle the event.

        This method is called when the event is dispatched. It should contain
        business logic for responding to the event.

        Args:
            event: The event instance containing data

        Returns:
            None

        Raises:
            Exception: Any exception raised will be handled based on
                      event.should_propagate flag (default: True)

        Educational Note (Sprint 14.0):
            We use async def to allow I/O operations (database, HTTP, etc.)
            without blocking. Multiple listeners run concurrently via
            asyncio.gather().

            Exception behavior (Sprint 14.0):
            - If event.should_propagate == False: Exception is logged, flow continues
            - If event.should_propagate == True: Exception is raised (default)
        """
        pass


class EventDispatcher:
    """
    Singleton that manages event-listener registry and dispatches events.

    This is the core of the Event Bus. It maintains a registry of which
    listeners should handle which events, and dispatches events to all
    registered listeners concurrently.

    Educational Note:
        We use the Singleton pattern here because there should only be one
        event dispatcher per application. However, we don't enforce it with
        __new__ magic - instead, we register a single instance in the IoC
        Container.

    Attributes:
        _listeners: Registry mapping Event types to Listener types
        _container: IoC Container for resolving listeners with DI

    Example:
        >>> dispatcher = EventDispatcher(container)
        >>> dispatcher.register(UserRegistered, SendWelcomeEmail)
        >>> dispatcher.register(UserRegistered, LogUserActivity)
        >>> await dispatcher.dispatch(UserRegistered(user_id=1, ...))
        # Both SendWelcomeEmail and LogUserActivity run concurrently
    """

    def __init__(self, container: Container):
        """
        Initialize the event dispatcher.

        Args:
            container: IoC Container for resolving listeners
        """
        self._listeners: dict[type[Event], list[type[Listener[Any]]]] = {}
        self._container = container

    def register(
        self, event_type: type[Event], listener_type: type[Listener[Any]]
    ) -> None:
        """
        Register a listener for an event type.

        This binds a listener class to an event type. When the event is
        dispatched, all registered listeners will be resolved from the
        container and executed.

        Args:
            event_type: The Event class to listen for
            listener_type: The Listener class that handles the event

        Example:
            >>> dispatcher.register(UserRegistered, SendWelcomeEmail)
            >>> dispatcher.register(UserRegistered, LogUserActivity)
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []

        if listener_type not in self._listeners[event_type]:
            self._listeners[event_type].append(listener_type)

    def unregister(
        self, event_type: type[Event], listener_type: type[Listener[Any]]
    ) -> None:
        """
        Unregister a listener from an event type.

        Args:
            event_type: The Event class
            listener_type: The Listener class to remove

        Example:
            >>> dispatcher.unregister(UserRegistered, SendWelcomeEmail)
        """
        if event_type in self._listeners:
            if listener_type in self._listeners[event_type]:
                self._listeners[event_type].remove(listener_type)

    async def dispatch(self, event: Event) -> None:
        """
        Dispatch an event to all registered listeners.

        This method:
        1. Finds all listeners registered for this event type
        2. Resolves each listener from the IoC Container (enables DI)
        3. Calls handle() on each listener concurrently (asyncio.gather)
        4. Handles exceptions based on event.should_propagate flag (Sprint 14.0)

        Args:
            event: The event instance to dispatch

        Raises:
            Exception: If event.should_propagate is True and any listener fails

        Educational Note:
            Sprint 14.0: Added support for event.should_propagate flag.
            When should_propagate=False, exceptions are logged but don't crash
            the application. When should_propagate=True (default), exceptions
            propagate normally, maintaining fail-fast behavior.

            We use asyncio.gather() with return_exceptions=True to run all
            listeners concurrently and handle exceptions gracefully.

        Example (Sprint 14.0 - Exception Handling):
            >>> # Event with should_propagate=False
            >>> @dataclass
            >>> class UserRegistered(Event):
            ...     user_id: int
            ...     should_propagate: bool = False
            >>>
            >>> # Listener that fails
            >>> class FailingListener(Listener[UserRegistered]):
            ...     async def handle(self, event: UserRegistered) -> None:
            ...         raise ValueError("This listener failed")
            >>>
            >>> await dispatcher.dispatch(UserRegistered(user_id=1))
            >>> # Exception logged, flow continues (no crash)

            >>> # Event with should_propagate=True (default)
            >>> @dataclass
            >>> class OrderPlaced(Event):
            ...     order_id: int
            ...     # should_propagate defaults to True
            >>>
            >>> await dispatcher.dispatch(OrderPlaced(order_id=1))
            >>> # Exception propagates, application handles it
        """
        event_type = type(event)

        # Get registered listeners for this event type
        listener_types = self._listeners.get(event_type, [])

        if not listener_types:
            # No listeners registered - this is fine, not an error
            return

        # Resolve listeners from container and create tasks
        tasks = []
        for listener_type in listener_types:
            # Resolve listener from container (enables dependency injection)
            listener = self._container.resolve(listener_type)

            # Create task for this listener
            task = listener.handle(event)
            tasks.append(task)

        # Execute all listeners concurrently
        # return_exceptions=True ensures we get all results (including exceptions)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Sprint 14.0: Handle exceptions based on should_propagate flag
        exceptions = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                listener_name = listener_types[i].__name__
                exception = result

                # Log exception (in production, use proper logging)
                print(
                    f"⚠️  Event [{event_type.__name__}] "
                    f"Listener [{listener_name}] failed: {exception}"
                )

                exceptions.append((listener_name, exception))

        # Sprint 14.0: Propagate exception if event.should_propagate is True
        if exceptions and event.should_propagate:
            # Raise first exception to fail fast
            raise exceptions[0][1]
        # If should_propagate is False, exceptions were logged but not raised

    def get_listeners(self, event_type: type[Event]) -> list[type[Listener[Any]]]:
        """
        Get all listeners registered for an event type.

        Args:
            event_type: The Event class

        Returns:
            List of Listener types registered for this event

        Example:
            >>> listeners = dispatcher.get_listeners(UserRegistered)
            >>> # [SendWelcomeEmail, LogUserActivity]
        """
        return self._listeners.get(event_type, [])

    def clear(self) -> None:
        """
        Clear all event-listener registrations.

        This is mainly useful for testing to reset the dispatcher state.

        Example:
            >>> dispatcher.clear()
        """
        self._listeners.clear()
