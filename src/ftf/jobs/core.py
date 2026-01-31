"""
Job Queue Core (Sprint 3.2)

This module provides a Laravel-style class-based Job Queue system built on top of SAQ
(Simple Async Queue). While SAQ is function-based, we provide a class-based API with
full Dependency Injection support through the IoC Container.

Architecture:
    - Job: Abstract base class for all jobs (like Laravel Jobs)
    - runner: Universal function that executes class-based jobs
    - JobManager: Singleton managing the saq.Queue instance

Key Pattern:
    Job.dispatch() serializes the class name and payload, then enqueues to the
    runner() function. The runner dynamically resolves the Job class from the
    IoC Container (enabling DI) and executes it.

Educational Note:
    This is a "bridge pattern" - we wrap SAQ's function-based API with a
    class-based API. The runner() is the single function registered with SAQ,
    and it acts as a dispatcher for all Job classes.
"""

import importlib
from abc import ABC, abstractmethod
from typing import Any

import saq
from redis.asyncio import Redis

from ftf.core import Container

# Global container reference (set by worker)
_container: Container | None = None


def set_container(container: Container) -> None:
    """
    Set the global IoC Container for job resolution.

    This must be called before starting the worker so that jobs can be
    resolved with their dependencies.

    Args:
        container: The IoC Container instance

    Example:
        >>> from ftf.core import Container
        >>> from ftf.jobs import set_container
        >>> container = Container()
        >>> set_container(container)
    """
    global _container
    _container = container


def get_container() -> Container:
    """
    Get the global IoC Container.

    Returns:
        The IoC Container instance

    Raises:
        RuntimeError: If container not set

    Example:
        >>> container = get_container()
    """
    if _container is None:
        msg = "Container not set. Call set_container() before dispatching jobs."
        raise RuntimeError(msg)
    return _container


class Job(ABC):
    """
    Abstract base class for all background jobs.

    Jobs are class-based units of work that can be dispatched to a queue and
    executed asynchronously by workers. Jobs can receive dependencies through
    the IoC Container, making them testable and maintainable.

    Usage:
        1. Subclass Job
        2. Implement async def handle(self)
        3. Optionally add __init__ for dependency injection
        4. Dispatch with Job.dispatch(**kwargs)

    Example:
        >>> from ftf.jobs import Job
        >>> from ftf.repositories import UserRepository
        >>>
        >>> class SendWelcomeEmail(Job):
        ...     def __init__(self, user_repo: UserRepository):
        ...         self.user_repo = user_repo
        ...         self.user_id: int = 0  # Set by payload
        ...
        ...     async def handle(self) -> None:
        ...         user = await self.user_repo.find(self.user_id)
        ...         # Send email logic here
        >>>
        >>> # Dispatch the job
        >>> await SendWelcomeEmail.dispatch(user_id=123)
    """

    @classmethod
    async def dispatch(cls, **kwargs: Any) -> None:
        """
        Dispatch this job to the queue.

        This method serializes the job class name and payload, then enqueues
        it to the runner() function which will execute it asynchronously.

        Args:
            **kwargs: Job payload (attributes to set on the instance)

        Raises:
            RuntimeError: If JobManager not initialized

        Example:
            >>> await SendWelcomeEmail.dispatch(user_id=123, email="user@test.com")
        """
        # Get the fully qualified class name
        job_class = f"{cls.__module__}.{cls.__name__}"

        # Get the queue from JobManager
        queue = JobManager.get_queue()

        # Enqueue to the runner function with class name and payload
        await queue.enqueue(
            "ftf.jobs.core.runner",  # The universal runner function
            job_class=job_class,  # Fully qualified class name
            payload=kwargs,  # Job attributes
        )

    @abstractmethod
    async def handle(self) -> None:
        """
        Execute the job logic.

        This method contains the actual work to be performed. It will be called
        by the runner after the job instance is resolved from the IoC Container
        and the payload attributes are set.

        Subclasses must implement this method.

        Example:
            >>> async def handle(self) -> None:
            ...     user = await self.user_repo.find(self.user_id)
            ...     await self.mailer.send(user.email, "Welcome!")
        """


async def runner(ctx: dict[str, Any], *, job_class: str, payload: dict[str, Any]) -> None:
    """
    Universal job runner function.

    This is the single function registered with SAQ that executes all class-based
    jobs. It acts as a bridge between SAQ's function-based API and our class-based
    Job API.

    Process:
        1. Import the job class from the fully qualified name
        2. Resolve the job instance from the IoC Container (enables DI!)
        3. Set payload attributes on the instance
        4. Call await instance.handle()

    Args:
        ctx: SAQ context (contains queue, job metadata, etc.)
        job_class: Fully qualified class name (e.g., "ftf.jobs.SendWelcomeEmail")
        payload: Dictionary of attributes to set on the job instance

    Raises:
        ImportError: If the job class cannot be imported
        AttributeError: If the job class doesn't exist in the module
        RuntimeError: If container not set

    Example (SAQ Worker perspective):
        >>> # This is what SAQ calls internally
        >>> await runner(
        ...     ctx={"queue": queue, "job": job_meta},
        ...     job_class="ftf.jobs.SendWelcomeEmail",
        ...     payload={"user_id": 123}
        ... )
    """
    # Get the IoC Container
    container = get_container()

    # Import the module and get the class
    # Example: "ftf.jobs.SendWelcomeEmail" -> module="ftf.jobs", class="SendWelcomeEmail"
    module_path, class_name = job_class.rsplit(".", 1)

    try:
        # Dynamically import the module
        module = importlib.import_module(module_path)
    except ImportError as e:
        msg = f"Cannot import module {module_path}: {e}"
        raise ImportError(msg) from e

    try:
        # Get the class from the module
        job_cls = getattr(module, class_name)
    except AttributeError as e:
        msg = f"Class {class_name} not found in module {module_path}"
        raise AttributeError(msg) from e

    # Resolve the job instance from the IoC Container
    # This allows the job's __init__ to receive dependencies!
    job_instance = container.resolve(job_cls)

    # Set payload attributes on the instance
    # Example: payload={"user_id": 123} -> job_instance.user_id = 123
    for key, value in payload.items():
        setattr(job_instance, key, value)

    # Execute the job
    await job_instance.handle()


class JobManager:
    """
    Singleton managing the SAQ Queue instance.

    The JobManager is responsible for:
    - Creating and managing the Redis connection
    - Creating and managing the SAQ Queue
    - Providing configuration for Redis URL

    This is a singleton to ensure only one queue instance exists across
    the application.

    Educational Note:
        In production, you'd likely want to make this configurable via
        environment variables. For now, we use sensible defaults.
    """

    _queue: saq.Queue | None = None
    _redis: Redis | None = None

    @classmethod
    def initialize(cls, redis_url: str = "redis://localhost:6379") -> None:
        """
        Initialize the job queue with Redis connection.

        This should be called once during application startup (in the worker
        or when dispatching jobs).

        Args:
            redis_url: Redis connection URL (default: redis://localhost:6379)

        Example:
            >>> from ftf.jobs import JobManager
            >>> JobManager.initialize("redis://localhost:6379")
        """
        # Create Redis connection
        cls._redis = Redis.from_url(redis_url, decode_responses=True)

        # Create SAQ queue
        cls._queue = saq.Queue(cls._redis, name="default")

    @classmethod
    def get_queue(cls) -> saq.Queue:
        """
        Get the SAQ Queue instance.

        Returns:
            The SAQ Queue instance

        Raises:
            RuntimeError: If JobManager not initialized

        Example:
            >>> queue = JobManager.get_queue()
        """
        if cls._queue is None:
            msg = "JobManager not initialized. Call JobManager.initialize() first."
            raise RuntimeError(msg)
        return cls._queue

    @classmethod
    def get_redis(cls) -> Redis:
        """
        Get the Redis connection.

        Returns:
            The Redis client instance

        Raises:
            RuntimeError: If JobManager not initialized

        Example:
            >>> redis = JobManager.get_redis()
        """
        if cls._redis is None:
            msg = "JobManager not initialized. Call JobManager.initialize() first."
            raise RuntimeError(msg)
        return cls._redis

    @classmethod
    async def close(cls) -> None:
        """
        Close Redis connection and cleanup resources.

        This should be called during application shutdown.

        Example:
            >>> await JobManager.close()
        """
        if cls._redis is not None:
            await cls._redis.aclose()
            cls._redis = None
            cls._queue = None
