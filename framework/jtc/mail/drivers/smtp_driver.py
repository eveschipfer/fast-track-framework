"""
SMTP driver for production email delivery.

Sends emails via SMTP using aiosmtplib (async SMTP client).
Supports TLS/SSL encryption and authentication.
"""

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import aiosmtplib

from jtc.mail.contracts import Attachment, EmailAddress, Message
from jtc.mail.drivers.base import MailDriver
from jtc.mail.exceptions import MailConfigException, MailSendException


class SmtpDriver(MailDriver):
    """
    Production mail driver that sends emails via SMTP.

    Supports:
    - TLS encryption (STARTTLS)
    - SSL encryption (SMTPS)
    - SMTP authentication
    - File attachments
    - HTML and plain text bodies
    - Custom headers

    Configuration (Environment Variables):
        MAIL_HOST: SMTP server hostname (e.g., smtp.gmail.com)
        MAIL_PORT: SMTP server port (e.g., 587 for TLS, 465 for SSL)
        MAIL_USERNAME: SMTP authentication username
        MAIL_PASSWORD: SMTP authentication password
        MAIL_ENCRYPTION: Encryption type (tls, ssl, or none)

    Example Configuration (.env):
        MAIL_DRIVER=smtp
        MAIL_HOST=smtp.gmail.com
        MAIL_PORT=587
        MAIL_USERNAME=your-email@gmail.com
        MAIL_PASSWORD=your-app-password
        MAIL_ENCRYPTION=tls

    Educational Note:
    ----------------
    This driver uses aiosmtplib for async SMTP operations. Unlike smtplib
    (which blocks the event loop), aiosmtplib uses asyncio for non-blocking
    network operations.

    For Gmail, you need an "App Password" (not your regular password):
    https://support.google.com/accounts/answer/185833
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = False,
        use_ssl: bool = False,
    ) -> None:
        """
        Initialize SMTP driver.

        Args:
            host: SMTP server hostname
            port: SMTP server port
            username: SMTP authentication username (optional)
            password: SMTP authentication password (optional)
            use_tls: Enable STARTTLS encryption
            use_ssl: Enable SSL/TLS encryption (SMTPS)

        Raises:
            MailConfigException: If configuration is invalid

        Note:
            use_tls and use_ssl are mutually exclusive.
            - use_tls: Connect plain, then upgrade with STARTTLS (port 587)
            - use_ssl: Connect with SSL/TLS from start (port 465)
        """
        if not host:
            raise MailConfigException("MAIL_HOST is required")

        if not port:
            raise MailConfigException("MAIL_PORT is required")

        if use_tls and use_ssl:
            raise MailConfigException("Cannot use both TLS and SSL")

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl

    async def send(self, message: Message) -> None:
        """
        Send email via SMTP.

        Args:
            message: Complete email message to send

        Raises:
            MailSendException: If SMTP sending fails
        """
        try:
            # Build MIME message
            mime_message = self._build_mime_message(message)

            # Send via SMTP
            await aiosmtplib.send(
                mime_message,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                use_tls=self.use_ssl,  # SSL from start
                start_tls=self.use_tls,  # Upgrade with STARTTLS
            )

        except aiosmtplib.SMTPException as e:
            # Extract recipient for better error message
            recipients = message.get("to", [])
            recipient_emails = [addr["email"] for addr in recipients]

            raise MailSendException(
                f"Failed to send email to {', '.join(recipient_emails)}: {e!s}"
            ) from e

        except Exception as e:
            raise MailSendException(f"Unexpected error sending email: {e!s}") from e

    def _build_mime_message(self, message: Message) -> MIMEMultipart:
        """
        Build MIME message from Message dict.

        Args:
            message: Email message data

        Returns:
            MIMEMultipart message ready to send

        Educational Note:
        ----------------
        MIME (Multipurpose Internet Mail Extensions) is the standard format
        for email messages. We use MIMEMultipart to support:
        - Both HTML and plain text (multipart/alternative)
        - File attachments (multipart/mixed)
        - Custom headers

        Structure:
            MIMEMultipart
            ├── MIMEText (plain text)
            ├── MIMEText (HTML)
            └── MIMEBase (attachments)
        """
        # Create multipart message
        mime_message = MIMEMultipart("alternative")

        # Set headers
        mime_message["Subject"] = message.get("subject", "(no subject)")

        from_addr = message.get("from_")
        if from_addr:
            mime_message["From"] = self._format_address(from_addr)

        to_addrs = message.get("to", [])
        if to_addrs:
            mime_message["To"] = ", ".join(
                self._format_address(addr) for addr in to_addrs
            )

        cc_addrs = message.get("cc", [])
        if cc_addrs:
            mime_message["Cc"] = ", ".join(
                self._format_address(addr) for addr in cc_addrs
            )

        reply_to = message.get("reply_to")
        if reply_to:
            mime_message["Reply-To"] = self._format_address(reply_to)

        # Add custom headers
        headers = message.get("headers", {})
        for key, value in headers.items():
            mime_message[key] = value

        # Add body content
        text_body = message.get("text")
        if text_body:
            mime_message.attach(MIMEText(text_body, "plain", "utf-8"))

        html_body = message.get("html")
        if html_body:
            mime_message.attach(MIMEText(html_body, "html", "utf-8"))

        # Add attachments
        attachments = message.get("attachments", [])
        for attachment in attachments:
            mime_attachment = self._build_attachment(attachment)
            mime_message.attach(mime_attachment)

        return mime_message

    def _build_attachment(self, attachment: Attachment) -> MIMEBase:
        """
        Build MIME attachment from Attachment dict.

        Args:
            attachment: Attachment metadata

        Returns:
            MIMEBase attachment ready to attach to message

        Raises:
            MailSendException: If file cannot be read
        """
        try:
            # Read file
            file_path = Path(attachment["path"])
            file_data = file_path.read_bytes()

            # Parse content type
            content_type = attachment["content_type"]
            maintype, subtype = content_type.split("/", 1)

            # Create MIME attachment
            mime_attachment = MIMEBase(maintype, subtype)
            mime_attachment.set_payload(file_data)

            # Encode with base64
            encoders.encode_base64(mime_attachment)

            # Add header
            filename = attachment["filename"]
            mime_attachment.add_header(
                "Content-Disposition", f"attachment; filename={filename}"
            )

            return mime_attachment

        except FileNotFoundError as e:
            raise MailSendException(
                f"Attachment file not found: {attachment['path']}"
            ) from e

        except Exception as e:
            raise MailSendException(
                f"Failed to build attachment: {e!s}"
            ) from e

    def _format_address(self, address: EmailAddress) -> str:
        """
        Format email address per RFC 2822.

        Args:
            address: Email address with optional name

        Returns:
            Formatted address: "email" or "Name <email>"

        Examples:
            {"email": "user@test.com"} -> "user@test.com"
            {"email": "user@test.com", "name": "John"} -> "John <user@test.com>"

        Educational Note:
        ----------------
        RFC 2822 specifies the standard format for email addresses.
        The "Name <email>" format is called "mailbox" format.
        """
        email = address["email"]
        name = address.get("name")

        if name:
            return f"{name} <{email}>"
        return email
