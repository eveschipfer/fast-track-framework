"""
Schedule System Core (Sprint 3.8)

This module provides a Laravel-style Task Scheduling system built on top of SAQ
with cron expression support. Allows defining scheduled tasks using decorators.

Architecture:
    - Schedule: Class with decorator methods (@cron, @every)
    - ScheduledTask: Represents a single scheduled task with its schedule
    - ScheduleRegistry: Global registry storing all scheduled tasks

Key Patterns:
    - Decorator Pattern: @Schedule.cron() and @Schedule.every() wrap functions
    - Registry Pattern: All scheduled tasks are stored in a global registry
    - SAQ Integration: Scheduled tasks are registered as SAQ cron jobs

Educational Note:
    Unlike Laravel's scheduler which uses a cron entry that runs every minute,
    SAQ has built-in cron support. We register tasks directly with SAQ's cron
    system, which is more efficient.

Example:
    >>> from jtc.schedule import Schedule
    >>>
    >>> @Schedule.cron("0 * * * *")  # Every hour at minute 0
    >>> async def hourly_cleanup(ctx):
    ...     print("Running hourly cleanup...")
    >>>
    >>> @Schedule.every(60)  # Every 60 seconds
    >>> async def frequent_sync(ctx):
    ...     print("Running frequent sync...")
"""

import asyncio
from collections.abc import Callable
from typing import Any


class ScheduledTask:
    """
    Represents a scheduled task with its configuration.

    A scheduled task consists of:
    - The async function to execute
    - The schedule (cron expression or interval in seconds)
    - Metadata (name, description, etc.)

    Attributes:
        func: The async function to execute
        schedule: Cron expression (str) or interval in seconds (int)
        name: Task name (defaults to function name)
        description: Optional description
    """

    def __init__(
        self,
        func: Callable[[dict[str, Any]], Any],
        schedule: str | int,
        name: str | None = None,
        description: str | None = None,
    ):
        """
        Initialize a scheduled task.

        Args:
            func: Async function to execute (must accept ctx parameter)
            schedule: Cron expression (str) or interval in seconds (int)
            name: Task name (defaults to function name)
            description: Optional description
        """
        self.func = func
        self.schedule = schedule
        self.name = name or func.__name__
        self.description = description or func.__doc__

    def is_cron(self) -> bool:
        """Check if this task uses cron expression."""
        return isinstance(self.schedule, str)

    def is_interval(self) -> bool:
        """Check if this task uses interval scheduling."""
        return isinstance(self.schedule, int)

    def __repr__(self) -> str:
        """String representation of the task."""
        schedule_str = self.schedule if self.is_cron() else f"{self.schedule}s"
        return f"<ScheduledTask {self.name} schedule={schedule_str}>"


class ScheduleRegistry:
    """
    Global registry for all scheduled tasks.

    This singleton maintains a list of all tasks registered via @Schedule.cron()
    and @Schedule.every() decorators. The registry is used by the worker to
    register tasks with SAQ when it starts.

    Class Attributes:
        _tasks: List of all registered scheduled tasks

    Educational Note:
        This is a simple registry pattern. In a larger application, you might
        want to support multiple registries or namespacing.
    """

    _tasks: list[ScheduledTask] = []

    @classmethod
    def register(cls, task: ScheduledTask) -> None:
        """
        Register a scheduled task.

        Args:
            task: The scheduled task to register

        Example:
            >>> task = ScheduledTask(my_func, "0 * * * *")
            >>> ScheduleRegistry.register(task)
        """
        cls._tasks.append(task)

    @classmethod
    def get_all(cls) -> list[ScheduledTask]:
        """
        Get all registered scheduled tasks.

        Returns:
            List of all scheduled tasks

        Example:
            >>> tasks = ScheduleRegistry.get_all()
            >>> for task in tasks:
            ...     print(f"{task.name}: {task.schedule}")
        """
        return cls._tasks.copy()

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered tasks.

        This is primarily useful for testing.

        Example:
            >>> ScheduleRegistry.clear()
        """
        cls._tasks.clear()

    @classmethod
    def get_task(cls, name: str) -> ScheduledTask | None:
        """
        Get a specific task by name.

        Args:
            name: Task name to search for

        Returns:
            The scheduled task, or None if not found

        Example:
            >>> task = ScheduleRegistry.get_task("hourly_cleanup")
        """
        for task in cls._tasks:
            if task.name == name:
                return task
        return None


class Schedule:
    """
    Schedule decorator class for registering scheduled tasks.

    This class provides decorator methods to register tasks that should run
    on a schedule:
    - @Schedule.cron(expression): Run on a cron schedule
    - @Schedule.every(seconds): Run every N seconds

    All decorated functions are automatically registered in the ScheduleRegistry
    and will be executed by the worker when it starts.

    Example:
        >>> from jtc.schedule import Schedule
        >>>
        >>> @Schedule.cron("0 0 * * *")  # Daily at midnight
        >>> async def daily_report(ctx):
        ...     print("Generating daily report...")
        >>>
        >>> @Schedule.cron("*/5 * * * *")  # Every 5 minutes
        >>> async def check_health(ctx):
        ...     print("Checking system health...")
        >>>
        >>> @Schedule.every(30)  # Every 30 seconds
        >>> async def sync_cache(ctx):
        ...     print("Syncing cache...")
    """

    @staticmethod
    def cron(
        expression: str,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable[[Callable[[dict[str, Any]], Any]], Callable[[dict[str, Any]], Any]]:
        """
        Decorator to schedule a task using cron expression.

        Cron expression format (5 fields):
            * * * * *
            │ │ │ │ │
            │ │ │ │ └─── Day of week (0-6, Sunday=0)
            │ │ │ └───── Month (1-12)
            │ │ └─────── Day of month (1-31)
            │ └───────── Hour (0-23)
            └─────────── Minute (0-59)

        Common patterns:
            "0 * * * *"      - Every hour at minute 0
            "0 0 * * *"      - Daily at midnight
            "*/5 * * * *"    - Every 5 minutes
            "0 0 * * 0"      - Weekly on Sunday at midnight
            "0 0 1 * *"      - Monthly on the 1st at midnight

        Args:
            expression: Cron expression (5 fields)
            name: Task name (defaults to function name)
            description: Task description (defaults to function docstring)

        Returns:
            Decorator function

        Example:
            >>> @Schedule.cron("0 * * * *")
            >>> async def hourly_task(ctx):
            ...     print("Running every hour")
        """

        def decorator(
            func: Callable[[dict[str, Any]], Any]
        ) -> Callable[[dict[str, Any]], Any]:
            # Create and register the scheduled task
            task = ScheduledTask(
                func=func,
                schedule=expression,
                name=name,
                description=description,
            )
            ScheduleRegistry.register(task)

            # Return the original function unchanged
            return func

        return decorator

    @staticmethod
    def every(
        seconds: int,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable[[Callable[[dict[str, Any]], Any]], Callable[[dict[str, Any]], Any]]:
        """
        Decorator to schedule a task to run every N seconds.

        This is a simpler alternative to cron expressions for regular intervals.

        Args:
            seconds: Interval in seconds between executions
            name: Task name (defaults to function name)
            description: Task description (defaults to function docstring)

        Returns:
            Decorator function

        Example:
            >>> @Schedule.every(60)  # Every 60 seconds
            >>> async def minute_task(ctx):
            ...     print("Running every minute")
            >>>
            >>> @Schedule.every(3600)  # Every hour
            >>> async def hourly_task(ctx):
            ...     print("Running every hour")
        """

        def decorator(
            func: Callable[[dict[str, Any]], Any]
        ) -> Callable[[dict[str, Any]], Any]:
            # Create and register the scheduled task
            task = ScheduledTask(
                func=func,
                schedule=seconds,
                name=name,
                description=description,
            )
            ScheduleRegistry.register(task)

            # Return the original function unchanged
            return func

        return decorator


# Utility functions for working with schedules


def list_scheduled_tasks() -> list[dict[str, Any]]:
    """
    Get a list of all scheduled tasks with their metadata.

    Returns:
        List of task information dictionaries

    Example:
        >>> tasks = list_scheduled_tasks()
        >>> for task in tasks:
        ...     print(f"{task['name']}: {task['schedule']}")
    """
    tasks = ScheduleRegistry.get_all()
    return [
        {
            "name": task.name,
            "schedule": task.schedule,
            "type": "cron" if task.is_cron() else "interval",
            "description": task.description,
        }
        for task in tasks
    ]


async def run_task_by_name(name: str, ctx: dict[str, Any] | None = None) -> None:
    """
    Manually run a scheduled task by name.

    This is useful for testing or manual execution of scheduled tasks.

    Args:
        name: Name of the task to run
        ctx: Optional SAQ context (defaults to empty dict)

    Raises:
        ValueError: If task not found

    Example:
        >>> await run_task_by_name("hourly_cleanup")
    """
    task = ScheduleRegistry.get_task(name)
    if task is None:
        msg = f"Task '{name}' not found in registry"
        raise ValueError(msg)

    if ctx is None:
        ctx = {}

    await task.func(ctx)
