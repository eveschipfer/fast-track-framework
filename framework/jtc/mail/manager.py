"""
Mail manager - Singleton facade for sending emails.

The MailManager acts as:
1. Singleton: Single instance per application
2. Factory: Creates appropriate driver based on config
3. Facade: Provides simple API for sending emails
"""

import os

from jtc.mail.drivers.array_driver import ArrayDriver
from jtc.mail.drivers.base import MailDriver
from jtc.mail.drivers.log_driver import LogDriver
from jtc.mail.drivers.smtp_driver import SmtpDriver
from jtc.mail.exceptions import MailConfigException
from jtc.mail.mailable import Mailable
from jtc.mail.pending_mail import PendingMail


class MailManager:
    """
    Singleton mail manager.

    Responsibilities:
    1. Driver Management: Creates and manages mail driver instances
    2. Configuration: Reads environment variables for driver selection
    3. Facade: Provides simple API for sending emails

    Pattern: Singleton + Factory + Facade
    --------------------------------------
    - Singleton: Ensures single instance per application
    - Factory: Creates appropriate driver based on MAIL_DRIVER env var
    - Facade: Provides simple, unified API regardless of driver

    Configuration (Environment Variables):
        MAIL_DRIVER: Driver type (log, array, smtp)

        For SMTP driver:
        - MAIL_HOST: SMTP server hostname
        - MAIL_PORT: SMTP server port
        - MAIL_USERNAME: SMTP username
        - MAIL_PASSWORD: SMTP password
        - MAIL_ENCRYPTION: Encryption type (tls, ssl, none)

    Usage:
        ```python
        from jtc.mail import Mail, Mailable

        # Send immediately
        await Mail.send(WelcomeEmail(user))

        # Fluent API
        await Mail.to("user@example.com").send(WelcomeEmail(user))

        # Queue for background
        await Mail.to("user@example.com").queue(WelcomeEmail(user))
        ```

    Educational Note:
    ----------------
    The Singleton pattern ensures we don't create multiple SMTP connections
    or multiple driver instances. This is important for:
    - Resource efficiency (connection pooling)
    - Configuration consistency
    - Testing (easy to override driver)
    """

    _instance: "MailManager | None" = None
    _initialized: bool

    def __new__(cls) -> "MailManager":
        """
        Singleton pattern - ensure only one instance exists.

        Returns:
            Single MailManager instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """
        Initialize mail manager.

        Note:
            This is called every time MailManager() is called, but
            initialization only happens once due to _initialized flag.
        """
        if self._initialized:
            return

        self._driver: MailDriver | None = None
        self._initialized = True

    @property
    def driver(self) -> MailDriver:
        """
        Get mail driver (lazy initialization).

        Returns:
            Active mail driver

        Raises:
            MailConfigException: If driver configuration is invalid

        Note:
            Driver is created on first access (lazy initialization).
            This allows tests to override driver before it's created.
        """
        if self._driver is None:
            self._driver = self._create_driver()
        return self._driver

    def _create_driver(self) -> MailDriver:
        """
        Create mail driver based on configuration.

        Returns:
            Mail driver instance

        Raises:
            MailConfigException: If driver type is invalid

        Factory Pattern:
        ---------------
        Based on MAIL_DRIVER env var, we create the appropriate driver:
        - log: LogDriver (development)
        - array: ArrayDriver (testing)
        - smtp: SmtpDriver (production)
        """
        driver_type = os.getenv("MAIL_DRIVER", "log")

        if driver_type == "log":
            return LogDriver()

        if driver_type == "array":
            return ArrayDriver()

        if driver_type == "smtp":
            return self._create_smtp_driver()

        raise MailConfigException(
            f"Invalid MAIL_DRIVER: {driver_type}. "
            f"Valid options: log, array, smtp"
        )

    def _create_smtp_driver(self) -> SmtpDriver:
        """
        Create SMTP driver from environment variables.

        Returns:
            Configured SMTP driver

        Raises:
            MailConfigException: If SMTP configuration is missing

        Environment Variables:
            MAIL_HOST: SMTP server hostname (required)
            MAIL_PORT: SMTP server port (required)
            MAIL_USERNAME: SMTP username (optional)
            MAIL_PASSWORD: SMTP password (optional)
            MAIL_ENCRYPTION: tls, ssl, or none (default: none)
        """
        host = os.getenv("MAIL_HOST")
        if not host:
            raise MailConfigException(
                "MAIL_HOST is required when MAIL_DRIVER=smtp"
            )

        port_str = os.getenv("MAIL_PORT")
        if not port_str:
            raise MailConfigException(
                "MAIL_PORT is required when MAIL_DRIVER=smtp"
            )

        try:
            port = int(port_str)
        except ValueError:
            raise MailConfigException(
                f"MAIL_PORT must be a number, got: {port_str}"
            )

        username = os.getenv("MAIL_USERNAME")
        password = os.getenv("MAIL_PASSWORD")

        encryption = os.getenv("MAIL_ENCRYPTION", "none").lower()
        use_tls = encryption == "tls"
        use_ssl = encryption == "ssl"

        return SmtpDriver(
            host=host,
            port=port,
            username=username,
            password=password,
            use_tls=use_tls,
            use_ssl=use_ssl,
        )

    async def send(self, mailable: Mailable) -> None:
        """
        Send email immediately.

        Args:
            mailable: Mailable to send

        Example:
            await Mail.send(WelcomeEmail(user))

        Educational Note:
        ----------------
        This is the "immediate" send method. The email is sent synchronously
        (though the operation itself is async). For background sending, use
        the queue() method via PendingMail.
        """
        # Render mailable to message
        message = await mailable.render()

        # Send via driver
        await self.driver.send(message)

    def to(self, email: str, name: str = "") -> PendingMail:
        """
        Create fluent builder for recipient management.

        Args:
            email: Recipient email address
            name: Recipient display name (optional)

        Returns:
            PendingMail builder for method chaining

        Example:
            await Mail.to("user@example.com", "John").send(WelcomeEmail(user))

        Educational Note:
        ----------------
        This returns a PendingMail builder which collects recipients
        before sending. This pattern provides a fluent API for common
        cases where recipients are known at the call site.
        """
        pending = PendingMail(self)
        pending.to(email, name)
        return pending

    async def close(self) -> None:
        """
        Close driver connections and cleanup resources.

        This should be called during application shutdown to ensure
        proper cleanup of SMTP connections, file handles, etc.

        Example:
            # In application shutdown hook
            await Mail.close()
        """
        if self._driver is not None:
            await self._driver.close()

    def set_driver(self, driver: MailDriver) -> None:
        """
        Override mail driver (for testing).

        Args:
            driver: Driver instance to use

        Example:
            # In test setup
            Mail.set_driver(ArrayDriver())

        Educational Note:
        ----------------
        This is a testing convenience method. Instead of mocking environment
        variables, tests can directly inject a driver instance.
        """
        self._driver = driver


# Singleton instance (exported as "Mail")
Mail = MailManager()
