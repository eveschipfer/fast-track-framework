"""
Event System Package (Sprint 3.1)

This package provides an async Event Bus system with Observer Pattern and
IoC Container integration.

Public API:
    - Event: Base class for events
    - Listener[E]: Generic base class for listeners
    - EventDispatcher: Manages event-listener registry
    - dispatch(event): Helper function to dispatch events

Educational Note:
    The dispatch() helper function is a convenience wrapper that resolves
    the EventDispatcher from the IoC Container automatically. This simplifies
    the API:

    Instead of:
        dispatcher = container.resolve(EventDispatcher)
        await dispatcher.dispatch(event)

    You can just:
        await dispatch(event)

    This pattern is similar to Laravel's event() helper and Django's
    signal.send().

Example:
    >>> from dataclasses import dataclass
    >>> from jtc.events import Event, Listener, dispatch
    >>>
    >>> @dataclass
    >>> class UserRegistered(Event):
    ...     user_id: int
    ...     email: str
    >>>
    >>> class SendWelcomeEmail(Listener[UserRegistered]):
    ...     async def handle(self, event: UserRegistered) -> None:
    ...         print(f"Sending welcome email to {event.email}")
    >>>
    >>> # In your controller
    >>> await dispatch(UserRegistered(user_id=1, email="user@test.com"))
"""

from jtc.core import Container
from jtc.events.core import Event, EventDispatcher, Listener

# Global container reference (set by FastTrackFramework on startup)
_container: Container | None = None


def set_container(container: Container) -> None:
    """
    Set the global container reference.

    This is called by FastTrackFramework during initialization.
    It allows the dispatch() helper to work without explicit container passing.

    Args:
        container: The IoC Container instance

    Educational Note:
        This is a pragmatic approach to avoid passing the container everywhere.
        In a pure DI system, you'd always inject the dispatcher. However, for
        convenience (like Laravel's event() helper), we use a global reference.

        Trade-offs:
        - Pro: Simple API (just call dispatch())
        - Pro: No need to inject dispatcher in every controller
        - Con: Global state (but managed by framework)
        - Con: Testing requires setup (but we handle this in test fixtures)

    Example:
        >>> # In FastTrackFramework.__init__
        >>> from jtc.events import set_container
        >>> set_container(self.container)
    """
    global _container
    _container = container


async def dispatch(event: Event) -> None:
    """
    Dispatch an event to all registered listeners.

    This is a convenience helper that resolves the EventDispatcher from the
    global container and dispatches the event.

    Args:
        event: The event instance to dispatch

    Raises:
        RuntimeError: If container not set (call set_container first)

    Educational Note:
        This function makes event dispatching very simple:

        In a controller:
        ```python
        @app.post("/users")
        async def create_user(data: CreateUserRequest):
            user = await user_repo.create(data.dict())
            await dispatch(UserRegistered(user_id=user.id, email=user.email))
            return user
        ```

        Behind the scenes, it:
        1. Gets EventDispatcher from container
        2. Dispatcher resolves listeners from container (DI!)
        3. Listeners run concurrently (asyncio.gather)

    Example:
        >>> from jtc.events import dispatch
        >>> await dispatch(UserRegistered(user_id=1, email="user@test.com"))
    """
    if _container is None:
        raise RuntimeError(
            "Container not set. Call set_container() during app initialization."
        )

    # Resolve dispatcher from container
    dispatcher = _container.resolve(EventDispatcher)

    # Dispatch the event
    await dispatcher.dispatch(event)


# Public API
__all__ = [
    "Event",
    "Listener",
    "EventDispatcher",
    "dispatch",
    "set_container",
]
