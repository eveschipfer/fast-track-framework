"""
Job for sending queued emails.

This job is dispatched when emails are queued for background processing.
It receives a rendered Message and sends it via the mail driver.
"""

from jtc.jobs import Job
from jtc.mail.contracts import Message
from jtc.mail.manager import Mail


class SendMailJob(Job):
    """
    Job for sending emails in the background.

    This job is used when emails are queued via:
    - Mail.to("user@test.com").queue(mailable)
    - PendingMail.queue()

    Pattern: Bridge Pattern
    -----------------------
    This job acts as a bridge between the Job Queue system and the Mail
    system. It allows emails to be sent asynchronously without blocking
    the HTTP request.

    Benefits:
    1. Performance: HTTP responses are faster
    2. Reliability: Jobs can be retried on failure
    3. Scalability: Multiple workers can process emails in parallel

    Educational Note:
    ----------------
    The message is pre-rendered before being queued. This is important
    because:
    1. The mailable might reference objects that won't exist in the worker
    2. Rendering might fail - better to fail during the request than worker
    3. Template context is available during the request
    """

    def __init__(self) -> None:
        """
        Initialize job.

        Note:
            The message attribute will be set by PendingMail.queue()
            before dispatching.
        """
        self.message: Message | None = None

    async def handle(self) -> None:
        """
        Send email via mail driver.

        Raises:
            MailSendException: If sending fails (will trigger job retry)

        Educational Note:
        ----------------
        If this raises an exception, the job queue will automatically
        retry the job according to the retry policy configured in
        the job manager.
        """
        if self.message is None:
            raise ValueError("SendMailJob.message must be set before dispatching")

        # Send via mail driver
        await Mail.driver.send(self.message)
