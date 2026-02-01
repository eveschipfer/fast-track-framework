"""
Queue Provider (Sprint 3.8)

This module provides a unified provider for initializing the queue system
with both regular jobs and scheduled tasks.

The QueueProvider:
    1. Initializes Redis connection
    2. Creates SAQ Queue instance
    3. Registers scheduled tasks from ScheduleRegistry
    4. Provides worker configuration

This centralizes all queue-related initialization in one place, making it
easy to start the worker with all features enabled.

Educational Note:
    This is a "provider" pattern common in Laravel. Providers are responsible
    for bootstrapping and configuring services. The QueueProvider handles
    both immediate jobs (via Job.dispatch()) and scheduled tasks (via @Schedule).
"""

import os
from typing import Any

import saq
from redis.asyncio import Redis

from ftf.core import Container
from ftf.jobs import JobManager, runner, set_container
from ftf.schedule import ScheduleRegistry


class QueueProvider:
    """
    Provider for initializing and configuring the queue system.

    This class handles:
    - Redis connection setup
    - SAQ Queue initialization
    - Scheduled task registration
    - Worker configuration

    All configuration is read from environment variables with sensible defaults.

    Environment Variables:
        REDIS_URL: Redis connection URL (default: redis://localhost:6379)
        QUEUE_NAME: Queue name (default: default)
        QUEUE_CONCURRENCY: Worker concurrency (default: 10)

    Example:
        >>> from ftf.providers import QueueProvider
        >>>
        >>> # Initialize the queue system
        >>> provider = QueueProvider()
        >>> await provider.initialize()
        >>>
        >>> # Get worker instance
        >>> worker = provider.get_worker()
        >>> await worker.start()
    """

    def __init__(
        self,
        redis_url: str | None = None,
        queue_name: str | None = None,
        concurrency: int | None = None,
    ):
        """
        Initialize the queue provider.

        Args:
            redis_url: Redis URL (defaults to env REDIS_URL or redis://localhost:6379)
            queue_name: Queue name (defaults to env QUEUE_NAME or "default")
            concurrency: Worker concurrency (defaults to env QUEUE_CONCURRENCY or 10)
        """
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL", "redis://localhost:6379"
        )
        self.queue_name = queue_name or os.getenv("QUEUE_NAME", "default")
        self.concurrency = concurrency or int(os.getenv("QUEUE_CONCURRENCY", "10"))

        self.redis: Redis | None = None
        self.queue: saq.Queue | None = None
        self.worker: saq.Worker | None = None

    async def initialize(self, container: Container | None = None) -> None:
        """
        Initialize the queue system.

        This method:
        1. Creates Redis connection
        2. Initializes JobManager
        3. Sets up IoC Container for job resolution
        4. Creates SAQ Queue
        5. Registers scheduled tasks

        Args:
            container: IoC Container for job dependency injection
                      (if None, creates a new Container)

        Example:
            >>> provider = QueueProvider()
            >>> await provider.initialize()
        """
        # 1. Create Redis connection
        self.redis = Redis.from_url(self.redis_url, decode_responses=True)

        # 2. Initialize JobManager for Job.dispatch()
        JobManager.initialize(self.redis_url)

        # 3. Set up IoC Container for job resolution
        if container is None:
            container = Container()
        set_container(container)

        # 4. Create SAQ Queue
        self.queue = saq.Queue(self.redis, name=self.queue_name)

        # 5. Register scheduled tasks with SAQ
        await self._register_scheduled_tasks()

    async def _register_scheduled_tasks(self) -> None:
        """
        Register all scheduled tasks from ScheduleRegistry with SAQ.

        This converts our @Schedule decorators into SAQ cron jobs.
        SAQ will automatically execute these tasks according to their schedules.

        Educational Note:
            SAQ supports both cron expressions and interval-based scheduling.
            We map our ScheduledTask objects to SAQ's cron job format.
        """
        if self.queue is None:
            msg = "Queue not initialized. Call initialize() first."
            raise RuntimeError(msg)

        tasks = ScheduleRegistry.get_all()

        for task in tasks:
            if task.is_cron():
                # Register cron-based task
                # SAQ uses croniter library for cron parsing
                await self.queue.schedule(
                    task.func,
                    cron=task.schedule,  # Cron expression (str)
                    key=task.name,  # Unique identifier
                )
            elif task.is_interval():
                # Register interval-based task (every N seconds)
                # SAQ doesn't have native "every N seconds" support,
                # so we convert to a cron-like schedule
                # For now, we'll use SAQ's schedule with a simple approach
                await self.queue.schedule(
                    task.func,
                    seconds=task.schedule,  # Interval in seconds (int)
                    key=task.name,  # Unique identifier
                )

    def get_worker(self) -> saq.Worker:
        """
        Get or create the SAQ Worker instance.

        The worker is configured with:
        - The queue instance
        - The runner function (for class-based jobs)
        - All scheduled task functions
        - Concurrency settings

        Returns:
            Configured SAQ Worker instance

        Raises:
            RuntimeError: If queue not initialized

        Example:
            >>> provider = QueueProvider()
            >>> await provider.initialize()
            >>> worker = provider.get_worker()
            >>> await worker.start()
        """
        if self.queue is None:
            msg = "Queue not initialized. Call initialize() first."
            raise RuntimeError(msg)

        if self.worker is not None:
            return self.worker

        # Collect all functions to register with the worker
        functions = [runner]  # Universal runner for class-based jobs

        # Add all scheduled task functions
        tasks = ScheduleRegistry.get_all()
        for task in tasks:
            functions.append(task.func)

        # Create worker with all functions
        settings: dict[str, Any] = {
            "queue": self.queue,
            "functions": functions,
            "concurrency": self.concurrency,
        }

        self.worker = saq.Worker(**settings)
        return self.worker

    async def close(self) -> None:
        """
        Close Redis connection and cleanup resources.

        This should be called during application shutdown.

        Example:
            >>> provider = QueueProvider()
            >>> await provider.initialize()
            >>> # ... use the worker ...
            >>> await provider.close()
        """
        if self.redis is not None:
            await self.redis.aclose()
            self.redis = None
            self.queue = None
            self.worker = None

        # Also cleanup JobManager
        await JobManager.close()

    async def check_redis_connection(self) -> bool:
        """
        Check if Redis is reachable.

        Returns:
            True if Redis is reachable, False otherwise

        Example:
            >>> provider = QueueProvider()
            >>> if await provider.check_redis_connection():
            ...     await provider.initialize()
            ... else:
            ...     print("Redis not available!")
        """
        try:
            # Create temporary connection
            redis = Redis.from_url(self.redis_url, decode_responses=True)

            # Try to ping
            await redis.ping()

            # Close connection
            await redis.aclose()

            return True
        except Exception:
            return False

    def get_redis_config(self) -> dict[str, Any]:
        """
        Get current Redis configuration.

        Returns:
            Dictionary with Redis configuration

        Example:
            >>> provider = QueueProvider()
            >>> config = provider.get_redis_config()
            >>> print(config["redis_url"])
        """
        return {
            "redis_url": self.redis_url,
            "queue_name": self.queue_name,
            "concurrency": self.concurrency,
        }
