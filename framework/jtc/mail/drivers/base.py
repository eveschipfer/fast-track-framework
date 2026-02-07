"""
Base mail driver abstract class.

All mail drivers must inherit from this class and implement the send() method.
"""

from abc import ABC, abstractmethod

from jtc.mail.contracts import Message


class MailDriver(ABC):
    """
    Abstract base class for mail drivers.

    Drivers are responsible for the actual delivery of email messages.
    Each driver implements a different delivery mechanism:
    - LogDriver: Logs to application logger (development)
    - ArrayDriver: Stores in memory (testing)
    - SmtpDriver: Sends via SMTP (production)

    Educational Note:
    ----------------
    This is the Adapter Pattern - we define a common interface (send/close)
    and each driver adapts a different underlying system (logger, array, SMTP)
    to work with our mail system.
    """

    @abstractmethod
    async def send(self, message: Message) -> None:
        """
        Send an email message.

        Args:
            message: Complete email message to send

        Raises:
            MailSendException: If sending fails

        Note:
            Implementations should be idempotent where possible.
            If sending fails, the exception should include enough context
            for debugging (recipient, error details, etc).
        """

    async def close(self) -> None:
        """
        Close driver connections and cleanup resources.

        Default implementation does nothing. Drivers that maintain persistent
        connections (like SmtpDriver) should override this to close connections.

        This is called during application shutdown via MailManager.close().
        """
