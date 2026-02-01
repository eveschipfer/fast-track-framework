"""
Mailable base class for composing emails.

Mailables use the Builder Pattern to construct emails fluently.
Each mailable represents a type of email your application sends.
"""

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from ftf.mail.contracts import Attachment, EmailAddress, Message
from ftf.mail.exceptions import MailTemplateException


class Mailable(ABC):
    """
    Abstract base class for composing email messages.

    Mailables use the Builder Pattern for fluent email composition.
    Each mailable class represents a specific type of email (welcome,
    password reset, invoice, etc).

    Pattern: Builder Pattern
    ------------------------
    Instead of constructing emails with constructor arguments, we use
    method chaining to build emails step-by-step. This provides:
    - Fluent, readable API
    - Flexible composition (optional parts)
    - Consistent interface across all emails

    Usage:
        ```python
        class WelcomeEmail(Mailable):
            def __init__(self, user: User):
                self.user = user

            async def build(self) -> None:
                self.subject("Welcome to My App!")
                self.from_("noreply@app.com", "My App")
                self.view("mail.welcome", {"user": self.user})

        # Send email
        await Mail.send(WelcomeEmail(user))
        ```

    Template Rendering:
        Templates are rendered using Jinja2 with auto-escaping enabled.
        Template names use dot notation: "mail.welcome" -> "mail/welcome.html"

    Educational Note:
    ----------------
    This pattern is inspired by Laravel's Mailable class. The key difference
    is that our build() method is async, allowing database queries or API
    calls during email construction.
    """

    def __init__(self) -> None:
        """
        Initialize mailable with empty message structure.

        Note:
            Subclasses should call super().__init__() if they override this.
        """
        self._subject: str = ""
        self._from: EmailAddress | None = None
        self._to: list[EmailAddress] = []
        self._cc: list[EmailAddress] = []
        self._bcc: list[EmailAddress] = []
        self._reply_to: EmailAddress | None = None
        self._view_name: str | None = None
        self._view_data: dict[str, Any] = {}
        self._html: str | None = None
        self._text: str | None = None
        self._attachments: list[Attachment] = []
        self._headers: dict[str, str] = {}

    @abstractmethod
    async def build(self) -> None:
        """
        Build email content.

        This is where you define email structure using fluent methods:
        - subject(): Set email subject
        - from_(): Set sender
        - to(): Add recipient
        - view(): Set template
        - attach(): Add attachment

        Example:
            ```python
            async def build(self) -> None:
                self.subject("Welcome!")
                self.from_("noreply@app.com")
                self.view("mail.welcome", {"user": self.user})
            ```

        Note:
            This method is called automatically by render().
            You don't need to call it directly.
        """

    # -------------------------------------------------------------------------
    # Builder Methods (Fluent API)
    # -------------------------------------------------------------------------

    def subject(self, subject: str) -> "Mailable":
        """
        Set email subject.

        Args:
            subject: Email subject line

        Returns:
            Self for method chaining

        Example:
            mailable.subject("Welcome to My App!")
        """
        self._subject = subject
        return self

    def from_(self, email: str, name: str = "") -> "Mailable":
        """
        Set email sender.

        Args:
            email: Sender email address
            name: Sender display name (optional)

        Returns:
            Self for method chaining

        Example:
            mailable.from_("noreply@app.com", "My App")

        Note:
            Named 'from_' (with underscore) because 'from' is a Python keyword.
        """
        self._from = {"email": email, "name": name} if name else {"email": email}
        return self

    def to(self, email: str, name: str = "") -> "Mailable":
        """
        Add recipient.

        Args:
            email: Recipient email address
            name: Recipient display name (optional)

        Returns:
            Self for method chaining

        Example:
            mailable.to("user@example.com", "John Doe")

        Note:
            Can be called multiple times to add multiple recipients.
        """
        address: EmailAddress = {"email": email, "name": name} if name else {"email": email}
        self._to.append(address)
        return self

    def cc(self, email: str, name: str = "") -> "Mailable":
        """
        Add CC recipient.

        Args:
            email: CC recipient email address
            name: CC recipient display name (optional)

        Returns:
            Self for method chaining

        Example:
            mailable.cc("manager@example.com", "Manager")
        """
        address: EmailAddress = {"email": email, "name": name} if name else {"email": email}
        self._cc.append(address)
        return self

    def bcc(self, email: str, name: str = "") -> "Mailable":
        """
        Add BCC recipient.

        Args:
            email: BCC recipient email address
            name: BCC recipient display name (optional)

        Returns:
            Self for method chaining

        Example:
            mailable.bcc("admin@example.com")
        """
        address: EmailAddress = {"email": email, "name": name} if name else {"email": email}
        self._bcc.append(address)
        return self

    def reply_to(self, email: str, name: str = "") -> "Mailable":
        """
        Set reply-to address.

        Args:
            email: Reply-to email address
            name: Reply-to display name (optional)

        Returns:
            Self for method chaining

        Example:
            mailable.reply_to("support@example.com", "Support Team")
        """
        self._reply_to = {"email": email, "name": name} if name else {"email": email}
        return self

    def view(self, template: str, data: dict[str, Any] | None = None) -> "Mailable":
        """
        Set email template.

        Args:
            template: Template name in dot notation (e.g., "mail.welcome")
            data: Template variables (optional)

        Returns:
            Self for method chaining

        Example:
            mailable.view("mail.welcome", {"user": user})

        Note:
            Template names use dot notation which maps to file paths:
            - "mail.welcome" -> "mail/welcome.html"
            - "invoices.receipt" -> "invoices/receipt.html"
        """
        self._view_name = template
        self._view_data = data or {}
        return self

    def text(self, content: str) -> "Mailable":
        """
        Set plain text body (instead of template).

        Args:
            content: Plain text email content

        Returns:
            Self for method chaining

        Example:
            mailable.text("Hello! Welcome to our app.")

        Note:
            If both view() and text() are used, text() takes precedence
            for the plain text part of the email.
        """
        self._text = content
        return self

    def html(self, content: str) -> "Mailable":
        """
        Set HTML body (instead of template).

        Args:
            content: HTML email content

        Returns:
            Self for method chaining

        Example:
            mailable.html("<h1>Welcome!</h1><p>Thanks for joining.</p>")

        Note:
            If both view() and html() are used, html() takes precedence.
        """
        self._html = content
        return self

    def attach(
        self, path: str, filename: str | None = None, content_type: str = "application/octet-stream"
    ) -> "Mailable":
        """
        Add file attachment.

        Args:
            path: Absolute file path
            filename: Display filename (defaults to basename of path)
            content_type: MIME type (defaults to application/octet-stream)

        Returns:
            Self for method chaining

        Example:
            mailable.attach("/tmp/invoice.pdf", "invoice.pdf", "application/pdf")

        Common MIME types:
            - application/pdf
            - image/png, image/jpeg
            - text/plain, text/csv
            - application/zip
        """
        if filename is None:
            filename = Path(path).name

        attachment: Attachment = {
            "path": path,
            "filename": filename,
            "content_type": content_type,
        }
        self._attachments.append(attachment)
        return self

    def header(self, key: str, value: str) -> "Mailable":
        """
        Add custom email header.

        Args:
            key: Header name
            value: Header value

        Returns:
            Self for method chaining

        Example:
            mailable.header("X-Priority", "1")
            mailable.header("X-Mailer", "My App Mailer")
        """
        self._headers[key] = value
        return self

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    async def render(self) -> Message:
        """
        Render mailable to Message dict.

        This method:
        1. Calls build() to construct email
        2. Renders template if view() was used
        3. Returns complete Message dict

        Returns:
            Complete email message ready to send

        Raises:
            MailTemplateException: If template rendering fails

        Note:
            This is called automatically by MailManager.send().
            You typically don't need to call it directly.
        """
        # Call build() to construct email
        await self.build()

        # Render template if specified
        html_body = self._html
        if self._view_name and not html_body:
            html_body = await self._render_template(self._view_name, self._view_data)

        # Build message
        message: Message = {
            "subject": self._subject,
        }

        if self._from:
            message["from_"] = self._from

        if self._to:
            message["to"] = self._to

        if self._cc:
            message["cc"] = self._cc

        if self._bcc:
            message["bcc"] = self._bcc

        if self._reply_to:
            message["reply_to"] = self._reply_to

        if html_body:
            message["html"] = html_body

        if self._text:
            message["text"] = self._text

        if self._attachments:
            message["attachments"] = self._attachments

        if self._headers:
            message["headers"] = self._headers

        return message

    async def _render_template(self, template_name: str, data: dict[str, Any]) -> str:
        """
        Render Jinja2 template.

        Args:
            template_name: Template name in dot notation
            data: Template variables

        Returns:
            Rendered HTML string

        Raises:
            MailTemplateException: If template not found or rendering fails

        Educational Note:
        ----------------
        We use asyncio.to_thread() to run Jinja2 rendering in a thread pool.
        Jinja2 is synchronous, so running it directly would block the event
        loop. Using to_thread() keeps our async code non-blocking.
        """
        try:
            # Convert dot notation to file path
            # "mail.welcome" -> "mail/welcome.html"
            template_path = template_name.replace(".", "/") + ".html"

            # Get Jinja2 environment
            env = self._get_jinja_environment()

            # Render template (in thread pool to avoid blocking)
            template = await asyncio.to_thread(env.get_template, template_path)
            html = await asyncio.to_thread(template.render, **data)

            return html

        except TemplateNotFound as e:
            raise MailTemplateException(
                f"Email template not found: {template_name} ({template_path})"
            ) from e

        except Exception as e:
            raise MailTemplateException(
                f"Failed to render email template: {e!s}"
            ) from e

    def _get_jinja_environment(self) -> Environment:
        """
        Get Jinja2 environment for template rendering.

        Returns:
            Configured Jinja2 environment

        Educational Note:
        ----------------
        We enable autoescape to prevent XSS attacks. All variables in
        templates are HTML-escaped by default. To output raw HTML, use
        the |safe filter: {{ content|safe }}
        """
        views_dir = self._get_views_directory()

        return Environment(
            loader=FileSystemLoader(views_dir),
            autoescape=True,  # Prevent XSS
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _get_views_directory(self) -> Path:
        """
        Get views directory path.

        Returns:
            Path to views directory

        Note:
            Default is src/ftf/resources/views/
            Override this in subclasses to use a different directory.
        """
        # Get project root (4 levels up from this file)
        # /src/ftf/mail/mailable.py -> /
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent

        return project_root / "src" / "ftf" / "resources" / "views"
