"""
Pending mail builder for fluent recipient management.

PendingMail provides a fluent API for specifying recipients before sending.
This allows patterns like: Mail.to("user@test.com").send(mailable)
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jtc.mail.mailable import Mailable
    from jtc.mail.manager import MailManager


class PendingMail:
    """
    Fluent builder for managing email recipients.

    This class provides a fluent interface for specifying email recipients
    before sending. It stores the recipients and applies them to the mailable
    when send() or queue() is called.

    Pattern: Builder Pattern
    ------------------------
    PendingMail acts as an intermediate builder that collects recipient
    information before passing it to the actual mailable.

    Usage:
        ```python
        # Single recipient
        await Mail.to("user@example.com").send(WelcomeEmail(user))

        # Multiple recipients
        await (
            Mail.to("user1@example.com")
            .to("user2@example.com")
            .cc("manager@example.com")
            .send(WelcomeEmail(user))
        )

        # Queue for background processing
        await Mail.to("user@example.com").queue(WelcomeEmail(user))
        ```

    Educational Note:
    ----------------
    This pattern is inspired by Laravel's Mail facade. It provides
    a clean, readable API for common scenarios where you want to
    specify recipients at the call site rather than in the mailable.
    """

    def __init__(self, manager: "MailManager") -> None:
        """
        Initialize pending mail builder.

        Args:
            manager: MailManager instance for sending
        """
        self._manager = manager
        self._to: list[tuple[str, str]] = []
        self._cc: list[tuple[str, str]] = []
        self._bcc: list[tuple[str, str]] = []

    def to(self, email: str, name: str = "") -> "PendingMail":
        """
        Add recipient.

        Args:
            email: Recipient email address
            name: Recipient display name (optional)

        Returns:
            Self for method chaining

        Example:
            Mail.to("user@example.com", "John Doe")
        """
        self._to.append((email, name))
        return self

    def cc(self, email: str, name: str = "") -> "PendingMail":
        """
        Add CC recipient.

        Args:
            email: CC recipient email address
            name: CC recipient display name (optional)

        Returns:
            Self for method chaining

        Example:
            Mail.to("user@example.com").cc("manager@example.com")
        """
        self._cc.append((email, name))
        return self

    def bcc(self, email: str, name: str = "") -> "PendingMail":
        """
        Add BCC recipient.

        Args:
            email: BCC recipient email address
            name: BCC recipient display name (optional)

        Returns:
            Self for method chaining

        Example:
            Mail.to("user@example.com").bcc("admin@example.com")
        """
        self._bcc.append((email, name))
        return self

    async def send(self, mailable: "Mailable") -> None:
        """
        Send email immediately.

        This method applies the collected recipients to the mailable
        and sends it via the mail manager.

        Args:
            mailable: Mailable to send

        Example:
            await Mail.to("user@example.com").send(WelcomeEmail(user))

        Educational Note:
        ----------------
        This is a "terminal" method - it executes the operation and returns
        None. The builder chain ends here.
        """
        # Apply recipients to mailable
        self._apply_recipients(mailable)

        # Send via manager
        await self._manager.send(mailable)

    async def queue(self, mailable: "Mailable") -> None:
        """
        Queue email for background processing.

        This method applies the collected recipients to the mailable,
        renders it, and dispatches a SendMailJob.

        Args:
            mailable: Mailable to queue

        Example:
            await Mail.to("user@example.com").queue(WelcomeEmail(user))

        Educational Note:
        ----------------
        Queuing emails is important for:
        1. Performance: Don't block request while sending
        2. Reliability: Retry on failure
        3. Scalability: Distribute load across workers
        """
        # Apply recipients to mailable
        self._apply_recipients(mailable)

        # Render to message
        message = await mailable.render()

        # Dispatch job
        from jtc.jobs.send_mail_job import SendMailJob

        job = SendMailJob()
        job.message = message
        await job.dispatch()

    def _apply_recipients(self, mailable: "Mailable") -> None:
        """
        Apply collected recipients to mailable.

        Args:
            mailable: Mailable to apply recipients to

        Note:
            This modifies the mailable in-place before sending.
        """
        for email, name in self._to:
            mailable.to(email, name)

        for email, name in self._cc:
            mailable.cc(email, name)

        for email, name in self._bcc:
            mailable.bcc(email, name)
