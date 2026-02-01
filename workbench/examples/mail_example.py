"""
Mail System Example (Sprint 4.0)

This example demonstrates how to use the Fast Track Framework mail system.

Run with:
    MAIL_DRIVER=log python examples/mail_example.py
    MAIL_DRIVER=array python examples/mail_example.py (for testing)
"""

import asyncio
import logging
import os
from typing import Any

from ftf.mail import Mail, Mailable

# Configure logging to see mail output
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s - %(name)s - %(message)s"
)


class WelcomeEmail(Mailable):
    """
    Welcome email sent to new users.

    This mailable demonstrates:
    - Template rendering with Jinja2
    - Fluent builder API
    - Constructor parameters
    """

    def __init__(self, user_name: str, user_email: str) -> None:
        """
        Initialize welcome email.

        Args:
            user_name: Name of the user
            user_email: Email of the user
        """
        super().__init__()
        self.user_name = user_name
        self.user_email = user_email

    async def build(self) -> None:
        """Build email content using template."""
        self.subject(f"Welcome to Fast Track Framework, {self.user_name}!")
        self.from_("noreply@ftf.dev", "Fast Track Framework")
        self.view(
            "mail.welcome",
            {
                "user": {
                    "name": self.user_name,
                    "email": self.user_email,
                },
                "app_name": "Fast Track Framework",
                "verification_url": "https://ftf.dev/verify/abc123",
            },
        )


class PasswordResetEmail(Mailable):
    """
    Password reset email.

    Demonstrates using a different template.
    """

    def __init__(self, user_name: str, reset_token: str) -> None:
        """
        Initialize password reset email.

        Args:
            user_name: Name of the user
            reset_token: Password reset token
        """
        super().__init__()
        self.user_name = user_name
        self.reset_token = reset_token

    async def build(self) -> None:
        """Build email content using template."""
        self.subject("Reset Your Password")
        self.from_("noreply@ftf.dev", "Fast Track Framework")
        self.view(
            "mail.password_reset",
            {
                "user": {"name": self.user_name},
                "app_name": "Fast Track Framework",
                "reset_url": f"https://ftf.dev/reset/{self.reset_token}",
                "expiration": "60 minutes",
            },
        )


class PlainTextEmail(Mailable):
    """
    Plain text email (no template).

    Demonstrates using text() instead of view().
    """

    def __init__(self, message: str) -> None:
        """
        Initialize plain text email.

        Args:
            message: Email message
        """
        super().__init__()
        self.message = message

    async def build(self) -> None:
        """Build email content with plain text."""
        self.subject("Plain Text Email")
        self.from_("noreply@ftf.dev", "Fast Track Framework")
        self.text(self.message)


async def main() -> None:
    """
    Run mail examples.

    Set MAIL_DRIVER environment variable to control driver:
    - log: Log emails to console (default)
    - array: Store in memory (for testing)
    - smtp: Send via SMTP (requires SMTP config)
    """
    print("=" * 70)
    print("Fast Track Framework - Mail System Examples")
    print("=" * 70)
    print()

    # Get driver type from environment
    driver_type = os.getenv("MAIL_DRIVER", "log")
    print(f"Using driver: {driver_type}")
    print()

    # Example 1: Send welcome email
    print("-" * 70)
    print("Example 1: Welcome Email (Template)")
    print("-" * 70)
    welcome = WelcomeEmail("John Doe", "john@example.com")
    await Mail.send(welcome)
    print()

    # Example 2: Send password reset email
    print("-" * 70)
    print("Example 2: Password Reset Email (Template)")
    print("-" * 70)
    reset = PasswordResetEmail("Jane Smith", "abc123xyz")
    await Mail.send(reset)
    print()

    # Example 3: Send plain text email
    print("-" * 70)
    print("Example 3: Plain Text Email")
    print("-" * 70)
    plain = PlainTextEmail("Hello! This is a plain text email.")
    await Mail.send(plain)
    print()

    # Example 4: Fluent API with recipients
    print("-" * 70)
    print("Example 4: Fluent API with Recipients")
    print("-" * 70)
    await Mail.to("alice@example.com", "Alice").send(
        WelcomeEmail("Alice", "alice@example.com")
    )
    print()

    # Example 5: Multiple recipients
    print("-" * 70)
    print("Example 5: Multiple Recipients (CC/BCC)")
    print("-" * 70)
    await (
        Mail.to("bob@example.com", "Bob")
        .cc("manager@example.com", "Manager")
        .bcc("admin@example.com")
        .send(WelcomeEmail("Bob", "bob@example.com"))
    )
    print()

    # If using array driver, show stored messages
    if driver_type == "array":
        from ftf.mail.drivers.array_driver import ArrayDriver

        driver = Mail.driver
        if isinstance(driver, ArrayDriver):
            print("-" * 70)
            print(f"Array Driver: {driver.count()} messages stored")
            print("-" * 70)
            last_message = driver.get_last()
            if last_message:
                print(f"Last subject: {last_message.get('subject', 'N/A')}")
                to_addrs = last_message.get("to", [])
                if to_addrs:
                    print(f"Last recipient: {to_addrs[0]['email']}")
            print()

    # Close driver connections
    await Mail.close()

    print("=" * 70)
    print("✓ All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
