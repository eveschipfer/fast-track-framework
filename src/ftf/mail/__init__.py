"""
Fast Track Framework - Mail System

This module provides a comprehensive email system with multi-driver support,
Jinja2 templates, and job queue integration.

Public API:
-----------
- Mail: Singleton manager for sending emails
- Mailable: Base class for email composition
- Exceptions: Custom exceptions for mail operations

Usage:
------
```python
from ftf.mail import Mail, Mailable

class WelcomeEmail(Mailable):
    def __init__(self, user: User):
        self.user = user

    async def build(self) -> None:
        await (
            self.subject("Welcome!")
            .from_("noreply@app.com", "My App")
            .view("mail.welcome", {"user": self.user})
        )

# Send immediately
await Mail.send(WelcomeEmail(user))

# Fluent API
await Mail.to("user@example.com").send(WelcomeEmail(user))

# Queue for background
await Mail.to("user@example.com").queue(WelcomeEmail(user))
```

Configuration:
--------------
Environment Variables:
    MAIL_DRIVER: Driver type (log, array, smtp)
    MAIL_HOST: SMTP server (when using smtp driver)
    MAIL_PORT: SMTP port (when using smtp driver)
    MAIL_USERNAME: SMTP username (optional)
    MAIL_PASSWORD: SMTP password (optional)
    MAIL_ENCRYPTION: Encryption (tls, ssl, none)

Educational Note:
-----------------
This mail system demonstrates several design patterns:
- Singleton: MailManager ensures single instance
- Factory: Drivers created based on configuration
- Builder: Mailable provides fluent API
- Adapter: Different drivers adapt different systems
- Bridge: SendMailJob bridges mail and queue systems
"""

from ftf.mail.exceptions import (
    MailConfigException,
    MailException,
    MailSendException,
    MailTemplateException,
)
from ftf.mail.mailable import Mailable
from ftf.mail.manager import Mail

__all__ = [
    "Mail",
    "MailConfigException",
    "MailException",
    "MailSendException",
    "MailTemplateException",
    "Mailable",
]
