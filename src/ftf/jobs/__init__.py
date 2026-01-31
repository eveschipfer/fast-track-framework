"""
Job Queue System (Sprint 3.2)

Laravel-style class-based background job system built on SAQ (Simple Async Queue).

This module provides:
    - Job: Base class for all background jobs
    - JobManager: Singleton managing the queue
    - runner: Universal function executing jobs (SAQ bridge)
    - set_container/get_container: Container management

Usage:
    >>> from ftf.jobs import Job, JobManager, set_container
    >>> from ftf.core import Container
    >>>
    >>> # Initialize
    >>> container = Container()
    >>> set_container(container)
    >>> JobManager.initialize("redis://localhost:6379")
    >>>
    >>> # Define job
    >>> class SendEmail(Job):
    ...     def __init__(self, mailer: Mailer):
    ...         self.mailer = mailer
    ...         self.email: str = ""
    ...
    ...     async def handle(self) -> None:
    ...         await self.mailer.send(self.email, "Hello!")
    >>>
    >>> # Dispatch
    >>> await SendEmail.dispatch(email="user@test.com")

Educational Note:
    This is a "bridge pattern" - we wrap SAQ's function-based API with a
    class-based API that supports Dependency Injection. The runner() function
    is the bridge that connects SAQ to our Job classes.
"""

from ftf.jobs.core import Job, JobManager, get_container, runner, set_container

__all__ = [
    "Job",
    "JobManager",
    "runner",
    "set_container",
    "get_container",
]
