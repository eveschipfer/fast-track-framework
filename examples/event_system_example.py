"""
Example: Event Service Provider Usage (Sprint 14.0)

This file demonstrates how to use the EventServiceProvider to automatically
register event-listener mappings.

Example Use Case:
    When a user is registered, we want to:
    1. Send a welcome email (MailService)
    2. Log the activity (LogService)
    3. Update user statistics (AnalyticsService)

    Without EventServiceProvider, we'd need to manually:
        dispatcher.register(UserRegistered, SendWelcomeEmail)
        dispatcher.register(UserRegistered, LogActivity)
        dispatcher.register(UserRegistered, UpdateAnalytics)

    With EventServiceProvider, we just define the mappings:
        listen = {
            UserRegistered: [SendWelcomeEmail, LogActivity, UpdateAnalytics],
        }

Architecture:
    Controller → dispatch(UserRegistered) → EventDispatcher → Listeners
                                                      ↓
                                          1. SendWelcomeEmail (MailService via DI)
                                          2. LogActivity (LogService via DI)
                                          3. UpdateAnalytics (AnalyticsService via DI)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ftf.core.service_provider import ServiceProvider

if TYPE_CHECKING:
    from ftf.core import Container
    from ftf.events.core import Event


# ============================================================================
# EVENTS
# ============================================================================


@dataclass
class UserRegistered(Event):
    """
    Event fired when a user registers in the system.

    Attributes:
        user_id: The ID of the newly registered user
        email: The user's email address
        name: The user's full name
    """

    user_id: int
    email: str
    name: str


@dataclass
class UserUpdated(Event):
    """Event fired when a user is updated."""

    user_id: int
    changes: dict[str, str]


@dataclass
class UserDeleted(Event):
    """Event fired when a user is deleted."""

    user_id: int
    reason: str


# ============================================================================
# LISTENERS
# ============================================================================


class SendWelcomeEmail:
    """
    Listener that sends a welcome email when a user registers.

    Note: MailService is injected via constructor (dependency injection).
    """

    def __init__(self, mailer: "MailService") -> None:
        """
        Initialize with injected MailService.

        Args:
            mailer: The mail service for sending emails
        """
        self.mailer = mailer

    async def handle(self, event: UserRegistered) -> None:
        """
        Send welcome email.

        Args:
            event: The UserRegistered event
        """
        await self.mailer.send(
            to=event.email,
            subject=f"Welcome, {event.name}!",
            body=f"Thanks for registering with ID {event.user_id}",
        )


class LogUserActivity:
    """
    Listener that logs user activity events.

    Note: LogService is injected via constructor (dependency injection).
    """

    def __init__(self, logger: "LogService") -> None:
        """
        Initialize with injected LogService.

        Args:
            logger: The log service for recording activities
        """
        self.logger = logger

    async def handle(self, event: Event) -> None:
        """
        Log user activity event.

        Args:
            event: Any event (UserRegistered, UserUpdated, UserDeleted)
        """
        event_type = type(event).__name__
        self.logger.info(f"Event [{event_type}] occurred: {event}")


class UpdateUserStatistics:
    """
    Listener that updates user statistics.

    Note: AnalyticsService is injected via constructor (dependency injection).
    """

    def __init__(self, analytics: "AnalyticsService") -> None:
        """
        Initialize with injected AnalyticsService.

        Args:
            analytics: The analytics service for tracking statistics
        """
        self.analytics = analytics

    async def handle(self, event: UserRegistered) -> None:
        """
        Update user registration statistics.

        Args:
            event: The UserRegistered event
        """
        self.analytics.increment("users_registered")
        self.analytics.update("last_registration", timestamp=event.timestamp)


# ============================================================================
# EVENT SERVICE PROVIDER
# ============================================================================


class EventServiceProvider(ServiceProvider):
    """
    Service Provider for automatic event-listener discovery.

    This provider maps events to their listeners, eliminating manual
    registration code.

    Usage:
        # In workbench/config/app.py
        providers = [
            "app.providers.event.EventServiceProvider",
        ]
    """

    priority: int = 90  # Medium priority (register before routes)

    listen: dict[type[Event], list[type]] = {
        # User events
        UserRegistered: [
            SendWelcomeEmail,
            LogUserActivity,
            UpdateUserStatistics,
        ],
        UserUpdated: [
            LogUserActivity,
            UpdateUserStatistics,
        ],
        UserDeleted: [
            LogUserActivity,
        ],
    }

    def register(self, container: "Container") -> None:
        """
        Register EventDispatcher and event-listener mappings.

        This method is called automatically by the framework during application
        startup. It registers the EventDispatcher in the container and sets
        up all event-listener mappings.

        Args:
            container: The IoC Container instance
        """
        # Note: The parent class implementation handles the registration
        # This method is here for educational purposes
        from ftf.events.core import EventDispatcher

        if not container.is_registered(EventDispatcher):
            container.register(EventDispatcher, scope="singleton")

        # Get dispatcher and register all event-listener mappings
        dispatcher = container.resolve(EventDispatcher)

        for event_type, listener_types in self.listen.items():
            for listener_type in listener_types:
                dispatcher.register(event_type, listener_type)


# ============================================================================
# USAGE EXAMPLE: CONTROLLER
# ============================================================================


async def create_user(user_data: dict, dispatch) -> None:
    """
    Controller method that creates a user and dispatches an event.

    This demonstrates how to use the event system in a controller.

    Args:
        user_data: User registration data
        dispatch: The dispatch function (for simplicity)

    Example:
        # In a route handler
        @app.post("/users")
        async def create_user(request: CreateUserRequest, dispatch):
            user = await user_repo.create(request.dict())

            # Dispatch event - all listeners execute automatically
            await dispatch(UserRegistered(
                user_id=user.id,
                email=user.email,
                name=user.name,
            ))

            return user
    """
    from ftf.events.core import EventDispatcher
    from ftf.core import Container

    container = Container()

    # Register EventServiceProvider and EventDispatcher
    container.register(EventServiceProvider, scope="singleton")
    container.register(EventDispatcher, scope="singleton")

    # Initialize provider (registers listeners)
    event_provider = container.resolve(EventServiceProvider)
    event_provider.register(container)

    # Mock user creation
    user_id = 123

    # Dispatch event
    # All listeners (SendWelcomeEmail, LogUserActivity, UpdateUserStatistics)
    # will be resolved from container with their dependencies injected
    event = UserRegistered(
        user_id=user_id,
        email="user@example.com",
        name="John Doe",
    )

    dispatcher = container.resolve(EventDispatcher)
    await dispatcher.dispatch(event)

    # Output:
    # ✓ Welcome email sent to user@example.com
    # ✓ User registration logged
    # ✓ User statistics updated


# ============================================================================
# EXCEPTION HANDLING EXAMPLE (Sprint 14.0)
# ============================================================================


@dataclass
class PaymentFailed(Event):
    """
    Event fired when a payment fails.

    Attributes:
        user_id: The user ID
        amount: The payment amount
        error: The error message
        should_propagate: If False, exception logged but flow continues
    """

    user_id: int
    amount: float
    error: str
    should_propagate: bool = False  # Don't crash entire request


class LogPaymentFailure:
    """
    Listener that logs payment failures.

    This listener always fails (simulates error), but because
    event.should_propagate=False, the exception is logged and
    the request flow continues.
    """

    async def handle(self, event: PaymentFailed) -> None:
        """Log payment failure (will raise exception)."""
        raise Exception(f"Payment logging failed: {event.error}")


class RefundUser:
    """
    Listener that refunds the user on payment failure.

    This listener should execute even if LogPaymentFailure fails,
    because event.should_propagate=False.
    """

    async def handle(self, event: PaymentFailed) -> None:
        """Refund user on payment failure."""
        print(f"✓ Refunding user {event.user_id}: ${event.amount}")


async def exception_handling_example(dispatch) -> None:
    """
    Example: Exception handling with should_propagate flag.

    This demonstrates how to use should_propagate to prevent a single
    failing listener from crashing the entire request flow.
    """
    from ftf.events.core import EventDispatcher
    from ftf.core import Container

    container = Container()

    # Register listeners
    container.register(LogPaymentFailure, scope="singleton")
    container.register(RefundUser, scope="singleton")
    container.register(EventDispatcher, scope="singleton")

    # Initialize provider
    dispatcher = container.resolve(EventDispatcher)
    dispatcher.register(PaymentFailed, LogPaymentFailure)
    dispatcher.register(PaymentFailed, RefundUser)

    # Dispatch payment failure event
    event = PaymentFailed(
        user_id=456,
        amount=99.99,
        error="Payment gateway timeout",
        should_propagate=False,  # Don't crash!
    )

    # Output:
    # ⚠️  Event [PaymentFailed] Listener [LogPaymentFailure] failed: Payment logging failed: Payment gateway timeout
    # ✓ Refunding user 456: $99.99
    # (Note: No exception raised, request flow continues)

    await dispatch(event)

    # Request flow continues normally (user was refunded)


if __name__ == "__main__":
    """
    Run examples to demonstrate the event system.

    In production, you would use this in your actual controllers
    and service providers, not as a standalone script.
    """
    import asyncio

    # Example 1: Create user and dispatch event
    print("Example 1: User Registration with Event Dispatch")
    asyncio.run(create_user({}, None))
    print()

    # Example 2: Exception handling with should_propagate
    print("Example 2: Exception Handling with should_propagate=False")
    asyncio.run(exception_handling_example(dispatch))
