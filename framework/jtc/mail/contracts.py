"""
Mail system type definitions and contracts.

This module defines the core types and protocols used throughout the mail system:
- EmailAddress: Structured email with optional display name
- Attachment: File attachment with metadata
- Message: Complete email message structure
- MailDriver: Protocol for mail driver implementations

Educational Note:
-----------------
We use TypedDict instead of Pydantic models for these types because they represent
simple data structures that don't need validation or serialization. TypedDict provides
type safety with zero runtime overhead, making it perfect for internal DTOs.

The MailDriver uses Protocol (structural typing) instead of ABC (nominal typing)
because we want to allow any object that implements send() to be a valid driver,
even if it doesn't explicitly inherit from a base class.
"""

from typing import Protocol, TypedDict


class EmailAddress(TypedDict, total=False):
    """
    Structured email address with optional display name.

    Attributes:
        email: Email address (required)
        name: Display name (optional)

    Examples:
        {"email": "user@example.com"}
        {"email": "user@example.com", "name": "John Doe"}
    """

    email: str
    name: str


class Attachment(TypedDict):
    """
    Email attachment with metadata.

    Attributes:
        path: Absolute file path to attachment
        filename: Display filename in email
        content_type: MIME type (e.g., "application/pdf")

    Examples:
        {
            "path": "/tmp/invoice.pdf",
            "filename": "invoice.pdf",
            "content_type": "application/pdf"
        }
    """

    path: str
    filename: str
    content_type: str


class Message(TypedDict, total=False):
    """
    Complete email message structure.

    This is the canonical representation of an email that gets passed to drivers.
    All optional fields use total=False to allow partial construction.

    Required Fields:
        subject: Email subject line
        from_: Sender email address

    Optional Fields:
        to: List of recipients
        cc: List of CC recipients
        bcc: List of BCC recipients
        reply_to: Reply-to address
        html: HTML body content
        text: Plain text body content
        attachments: List of file attachments
        headers: Custom email headers

    Educational Note:
    ----------------
    We use 'from_' (with underscore) because 'from' is a Python keyword.
    This is a common pattern when working with email libraries.
    """

    subject: str
    from_: EmailAddress
    to: list[EmailAddress]
    cc: list[EmailAddress]
    bcc: list[EmailAddress]
    reply_to: EmailAddress
    html: str
    text: str
    attachments: list[Attachment]
    headers: dict[str, str]


class MailDriver(Protocol):
    """
    Protocol for mail driver implementations.

    Drivers are responsible for the actual delivery of email messages.
    Different drivers support different delivery methods:
    - LogDriver: Logs emails to logger (development)
    - ArrayDriver: Stores in memory (testing)
    - SmtpDriver: Sends via SMTP server (production)

    Educational Note:
    ----------------
    This uses Protocol (structural typing) instead of ABC (nominal typing).
    This means ANY class that implements these methods is a valid MailDriver,
    even if it doesn't explicitly inherit from this protocol.

    This is more flexible than ABC and allows for easier testing and mocking.
    """

    async def send(self, message: Message) -> None:
        """
        Send an email message.

        Args:
            message: Complete email message to send

        Raises:
            MailSendException: If sending fails

        Educational Note:
        ----------------
        All drivers must implement this async method. The Message TypedDict
        provides a standardized structure that all drivers can understand,
        regardless of their underlying implementation (SMTP, API, etc).
        """
        ...

    async def close(self) -> None:
        """
        Close driver connections and cleanup resources.

        This is called during application shutdown to ensure proper cleanup
        of network connections, file handles, etc.

        Default implementation does nothing (drivers can override if needed).
        """
        ...
