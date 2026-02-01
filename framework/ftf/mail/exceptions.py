"""
Mail system exceptions.

Hierarchy:
    MailException (base)
    ├── MailSendException (SMTP/delivery failures)
    ├── MailTemplateException (Jinja2 rendering errors)
    └── MailConfigException (configuration errors)
"""


class MailException(Exception):
    """Base exception for all mail-related errors."""



class MailSendException(MailException):
    """
    Raised when email delivery fails.

    Common causes:
    - SMTP connection errors
    - Authentication failures
    - Invalid recipient addresses
    - Network timeouts
    """



class MailTemplateException(MailException):
    """
    Raised when email template rendering fails.

    Common causes:
    - Template file not found
    - Invalid Jinja2 syntax
    - Missing template variables
    - Template inheritance errors
    """



class MailConfigException(MailException):
    """
    Raised when mail configuration is invalid.

    Common causes:
    - Missing required environment variables
    - Invalid MAIL_DRIVER value
    - Malformed SMTP credentials
    """

