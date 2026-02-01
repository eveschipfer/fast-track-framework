"""
Tests for Mail System (Sprint 4.0)

This test suite covers:
- ArrayDriver (in-memory storage)
- LogDriver (logging)
- Mailable (email composition)
- MailManager (singleton, factory, facade)
- PendingMail (fluent API)
"""

import pytest
from pathlib import Path

from ftf.mail import Mail, Mailable, MailException
from ftf.mail.drivers.array_driver import ArrayDriver
from ftf.mail.drivers.log_driver import LogDriver
from ftf.mail.exceptions import MailTemplateException


class TestMailable(Mailable):
    """Simple test mailable."""

    def __init__(self, subject: str = "Test Subject") -> None:
        super().__init__()
        self.test_subject = subject

    async def build(self) -> None:
        self.subject(self.test_subject)
        self.from_("test@example.com", "Test Sender")
        self.text("Test body")


# -------------------------------------------------------------------------
# ArrayDriver Tests
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_array_driver_stores_messages() -> None:
    """ArrayDriver should store sent messages."""
    driver = ArrayDriver()

    # Create and send message
    mailable = TestMailable()
    message = await mailable.render()
    await driver.send(message)

    # Verify message was stored
    assert driver.count() == 1
    assert driver.get_last() == message


@pytest.mark.asyncio
async def test_array_driver_flush() -> None:
    """ArrayDriver.flush() should clear all messages."""
    driver = ArrayDriver()

    # Send messages
    mailable = TestMailable()
    message = await mailable.render()
    await driver.send(message)
    await driver.send(message)

    assert driver.count() == 2

    # Flush
    driver.flush()

    assert driver.count() == 0
    assert driver.get_last() is None


@pytest.mark.asyncio
async def test_array_driver_get_last() -> None:
    """ArrayDriver.get_last() should return most recent message."""
    driver = ArrayDriver()

    # Send first message
    mailable1 = TestMailable("First")
    message1 = await mailable1.render()
    await driver.send(message1)

    # Send second message
    mailable2 = TestMailable("Second")
    message2 = await mailable2.render()
    await driver.send(message2)

    # Last should be second
    last = driver.get_last()
    assert last is not None
    assert last["subject"] == "Second"


# -------------------------------------------------------------------------
# LogDriver Tests
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_log_driver_logs_email(caplog: pytest.LogCaptureFixture) -> None:
    """LogDriver should log email details."""
    import logging

    caplog.set_level(logging.INFO)

    driver = LogDriver()
    mailable = TestMailable("Log Test")
    message = await mailable.render()

    await driver.send(message)

    # Check logs contain subject and sender
    assert "Log Test" in caplog.text
    assert "test@example.com" in caplog.text


# -------------------------------------------------------------------------
# Mailable Tests
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mailable_subject() -> None:
    """Mailable should set subject correctly."""
    mailable = TestMailable("Custom Subject")
    message = await mailable.render()

    assert message["subject"] == "Custom Subject"


@pytest.mark.asyncio
async def test_mailable_from() -> None:
    """Mailable should set sender correctly."""
    mailable = TestMailable()
    message = await mailable.render()

    assert message["from_"]["email"] == "test@example.com"
    assert message["from_"]["name"] == "Test Sender"


@pytest.mark.asyncio
async def test_mailable_to() -> None:
    """Mailable should add recipients correctly."""

    class TestToMailable(Mailable):
        async def build(self) -> None:
            self.subject("Test")
            self.to("user1@test.com", "User 1")
            self.to("user2@test.com")

    mailable = TestToMailable()
    message = await mailable.render()

    assert len(message["to"]) == 2
    assert message["to"][0]["email"] == "user1@test.com"
    assert message["to"][0]["name"] == "User 1"
    assert message["to"][1]["email"] == "user2@test.com"


@pytest.mark.asyncio
async def test_mailable_cc_bcc() -> None:
    """Mailable should add CC and BCC recipients."""

    class TestCcBccMailable(Mailable):
        async def build(self) -> None:
            self.subject("Test")
            self.cc("manager@test.com", "Manager")
            self.bcc("admin@test.com")

    mailable = TestCcBccMailable()
    message = await mailable.render()

    assert len(message["cc"]) == 1
    assert message["cc"][0]["email"] == "manager@test.com"

    assert len(message["bcc"]) == 1
    assert message["bcc"][0]["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_mailable_text() -> None:
    """Mailable should set plain text body."""
    mailable = TestMailable()
    message = await mailable.render()

    assert message["text"] == "Test body"


@pytest.mark.asyncio
async def test_mailable_html() -> None:
    """Mailable should set HTML body."""

    class TestHtmlMailable(Mailable):
        async def build(self) -> None:
            self.subject("Test")
            self.html("<h1>HTML Content</h1>")

    mailable = TestHtmlMailable()
    message = await mailable.render()

    assert message["html"] == "<h1>HTML Content</h1>"


@pytest.mark.asyncio
async def test_mailable_attachment() -> None:
    """Mailable should add attachments."""
    # Create temp file
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("test content")
        temp_path = f.name

    try:

        class TestAttachmentMailable(Mailable):
            def __init__(self, path: str) -> None:
                super().__init__()
                self.path = path

            async def build(self) -> None:
                self.subject("Test")
                self.attach(self.path, "test.txt", "text/plain")

        mailable = TestAttachmentMailable(temp_path)
        message = await mailable.render()

        assert len(message["attachments"]) == 1
        assert message["attachments"][0]["path"] == temp_path
        assert message["attachments"][0]["filename"] == "test.txt"
        assert message["attachments"][0]["content_type"] == "text/plain"

    finally:
        Path(temp_path).unlink()


@pytest.mark.asyncio
async def test_mailable_view_template() -> None:
    """Mailable should render Jinja2 templates."""

    class TestViewMailable(Mailable):
        async def build(self) -> None:
            self.subject("Test")
            self.view("mail.welcome", {"user": {"name": "John"}})

    mailable = TestViewMailable()
    message = await mailable.render()

    # Should have HTML content from template
    assert "html" in message
    assert "John" in message["html"]
    assert "Welcome" in message["html"]


@pytest.mark.asyncio
async def test_mailable_template_not_found() -> None:
    """Mailable should raise exception for missing templates."""

    class TestMissingTemplateMailable(Mailable):
        async def build(self) -> None:
            self.subject("Test")
            self.view("mail.nonexistent", {})

    mailable = TestMissingTemplateMailable()

    with pytest.raises(MailTemplateException):
        await mailable.render()


# -------------------------------------------------------------------------
# MailManager Tests
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mail_manager_singleton() -> None:
    """MailManager should be singleton."""
    from ftf.mail.manager import MailManager

    instance1 = MailManager()
    instance2 = MailManager()

    assert instance1 is instance2


@pytest.mark.asyncio
async def test_mail_send() -> None:
    """Mail.send() should send email via driver."""
    # Set array driver for testing
    Mail.set_driver(ArrayDriver())

    mailable = TestMailable("Test Send")
    await Mail.send(mailable)

    # Verify message was sent
    assert isinstance(Mail.driver, ArrayDriver)
    assert Mail.driver.count() == 1

    last = Mail.driver.get_last()
    assert last is not None
    assert last["subject"] == "Test Send"


@pytest.mark.asyncio
async def test_mail_to_fluent_api() -> None:
    """Mail.to() should provide fluent API."""
    # Set array driver
    Mail.set_driver(ArrayDriver())

    # Use fluent API
    await Mail.to("user@example.com", "John Doe").send(TestMailable())

    # Verify recipient was added
    assert isinstance(Mail.driver, ArrayDriver)
    last = Mail.driver.get_last()
    assert last is not None
    assert len(last["to"]) == 1
    assert last["to"][0]["email"] == "user@example.com"
    assert last["to"][0]["name"] == "John Doe"


@pytest.mark.asyncio
async def test_pending_mail_multiple_recipients() -> None:
    """PendingMail should handle multiple recipients."""
    Mail.set_driver(ArrayDriver())

    # Add multiple recipients
    await (
        Mail.to("user1@test.com", "User 1")
        .to("user2@test.com", "User 2")
        .cc("manager@test.com", "Manager")
        .bcc("admin@test.com")
        .send(TestMailable())
    )

    # Verify all recipients
    assert isinstance(Mail.driver, ArrayDriver)
    last = Mail.driver.get_last()
    assert last is not None

    assert len(last["to"]) == 2
    assert last["to"][0]["email"] == "user1@test.com"
    assert last["to"][1]["email"] == "user2@test.com"

    assert len(last["cc"]) == 1
    assert last["cc"][0]["email"] == "manager@test.com"

    assert len(last["bcc"]) == 1
    assert last["bcc"][0]["email"] == "admin@test.com"


# -------------------------------------------------------------------------
# Cleanup
# -------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_mail() -> None:
    """Reset mail driver before each test."""
    Mail.set_driver(ArrayDriver())
