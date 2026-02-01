"""
Log driver for development.

Logs email messages instead of sending them. Perfect for local development
where you want to see email content without actually sending emails.
"""

import logging

from ftf.mail.contracts import EmailAddress, Message
from ftf.mail.drivers.base import MailDriver

logger = logging.getLogger(__name__)


class LogDriver(MailDriver):
    """
    Development mail driver that logs emails instead of sending.

    This driver writes email details to the application logger at INFO level.
    The email body is logged at DEBUG level to avoid cluttering logs.

    Use Case:
        Perfect for local development where you want to verify email content
        without setting up SMTP or sending real emails.

    Configuration:
        MAIL_DRIVER=log

    Example Log Output:
        [MAIL] Subject: Welcome to My App
        [MAIL] From: noreply@app.com (My App)
        [MAIL] To: user@example.com (John Doe)
        [MAIL] Attachments: invoice.pdf, receipt.pdf
    """

    async def send(self, message: Message) -> None:
        """
        Log email message details.

        Args:
            message: Email message to log
        """
        # Log header information at INFO level
        logger.info("[MAIL] " + "=" * 60)
        logger.info(f"[MAIL] Subject: {message.get('subject', '(no subject)')}")

        # Log sender
        from_addr = message.get("from_")
        if from_addr:
            logger.info(f"[MAIL] From: {self._format_address(from_addr)}")

        # Log recipients
        for to_addr in message.get("to", []):
            logger.info(f"[MAIL] To: {self._format_address(to_addr)}")

        for cc_addr in message.get("cc", []):
            logger.info(f"[MAIL] CC: {self._format_address(cc_addr)}")

        for bcc_addr in message.get("bcc", []):
            logger.info(f"[MAIL] BCC: {self._format_address(bcc_addr)}")

        # Log reply-to
        reply_to = message.get("reply_to")
        if reply_to:
            logger.info(f"[MAIL] Reply-To: {self._format_address(reply_to)}")

        # Log attachments
        attachments = message.get("attachments", [])
        if attachments:
            filenames = [att["filename"] for att in attachments]
            logger.info(f"[MAIL] Attachments: {', '.join(filenames)}")

        # Log custom headers
        headers = message.get("headers", {})
        if headers:
            for key, value in headers.items():
                logger.info(f"[MAIL] Header: {key}: {value}")

        # Log body at DEBUG level (can be long)
        logger.debug("[MAIL] " + "-" * 60)

        html_body = message.get("html")
        if html_body:
            # Truncate long HTML bodies
            max_length = 500
            truncated = (
                html_body[:max_length] + "..."
                if len(html_body) > max_length
                else html_body
            )
            logger.debug(f"[MAIL] HTML Body:\n{truncated}")

        text_body = message.get("text")
        if text_body:
            # Truncate long text bodies
            max_length = 500
            truncated = (
                text_body[:max_length] + "..."
                if len(text_body) > max_length
                else text_body
            )
            logger.debug(f"[MAIL] Text Body:\n{truncated}")

        logger.info("[MAIL] " + "=" * 60)

    def _format_address(self, address: EmailAddress) -> str:
        """
        Format email address for logging.

        Args:
            address: Email address with optional name

        Returns:
            Formatted string: "email" or "email (name)"

        Examples:
            {"email": "user@test.com"} -> "user@test.com"
            {"email": "user@test.com", "name": "John"} -> "user@test.com (John)"
        """
        email = address["email"]
        name = address.get("name")

        if name:
            return f"{email} ({name})"
        return email
