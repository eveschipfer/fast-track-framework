"""
Array driver for testing.

Stores email messages in memory for inspection during tests.
This allows tests to verify that emails were sent with correct content.
"""

import copy

from jtc.mail.contracts import Message
from jtc.mail.drivers.base import MailDriver


class ArrayDriver(MailDriver):
    """
    Testing mail driver that stores emails in memory.

    This driver keeps a list of all sent messages, allowing tests to:
    - Verify emails were sent
    - Inspect email content
    - Check recipients, subject, body, etc.

    Use Case:
        Perfect for unit tests where you want to verify email sending
        without actually sending emails or cluttering logs.

    Configuration:
        MAIL_DRIVER=array

    Example Usage in Tests:
        ```python
        driver = ArrayDriver()
        await Mail.send(WelcomeEmail(user))

        # Verify email was sent
        assert len(driver.messages) == 1

        # Inspect content
        message = driver.get_last()
        assert message["subject"] == "Welcome!"
        assert message["to"][0]["email"] == "user@example.com"
        ```
    """

    def __init__(self) -> None:
        """Initialize with empty message storage."""
        self.messages: list[Message] = []

    async def send(self, message: Message) -> None:
        """
        Store email message in memory.

        Args:
            message: Email message to store

        Note:
            We create a deep copy to prevent mutations to the original
            message from affecting stored messages.
        """
        # Deep copy to prevent external mutations
        self.messages.append(copy.deepcopy(message))

    def flush(self) -> None:
        """
        Clear all stored messages.

        Useful between test cases to ensure clean state.

        Example:
            ```python
            # In pytest fixture
            @pytest.fixture(autouse=True)
            def reset_mail():
                Mail.driver.flush()
            ```
        """
        self.messages.clear()

    def get_last(self) -> Message | None:
        """
        Get the most recently sent message.

        Returns:
            Last message or None if no messages sent

        Example:
            ```python
            await Mail.send(WelcomeEmail(user))
            message = Mail.driver.get_last()
            assert message["subject"] == "Welcome!"
            ```
        """
        return self.messages[-1] if self.messages else None

    def count(self) -> int:
        """
        Get total number of messages sent.

        Returns:
            Number of stored messages

        Example:
            ```python
            await Mail.send(WelcomeEmail(user))
            assert Mail.driver.count() == 1
            ```
        """
        return len(self.messages)
