"""
Schedule System - Task Scheduling with Cron Support

This module provides a Laravel-style task scheduling system for running
periodic tasks using cron expressions or simple intervals.

Main Components:
    - Schedule: Decorator class for registering scheduled tasks
    - ScheduledTask: Represents a single scheduled task
    - ScheduleRegistry: Global registry of all scheduled tasks

Quick Start:
    >>> from jtc.schedule import Schedule
    >>>
    >>> # Run every hour at minute 0
    >>> @Schedule.cron("0 * * * *")
    >>> async def hourly_cleanup(ctx):
    ...     print("Running cleanup...")
    >>>
    >>> # Run every 60 seconds
    >>> @Schedule.every(60)
    >>> async def frequent_sync(ctx):
    ...     print("Running sync...")

Cron Expression Format:
    * * * * *
    │ │ │ │ │
    │ │ │ │ └─── Day of week (0-6, Sunday=0)
    │ │ │ └───── Month (1-12)
    │ │ └─────── Day of month (1-31)
    │ └───────── Hour (0-23)
    └─────────── Minute (0-59)

Common Patterns:
    "0 * * * *"      - Every hour
    "0 0 * * *"      - Daily at midnight
    "*/5 * * * *"    - Every 5 minutes
    "0 0 * * 0"      - Weekly on Sunday
    "0 0 1 * *"      - Monthly on the 1st

Integration with Worker:
    The queue worker automatically discovers and registers all scheduled
    tasks when it starts. No manual registration needed.

    $ jtc queue work
"""

from .core import (
    Schedule,
    ScheduleRegistry,
    ScheduledTask,
    list_scheduled_tasks,
    run_task_by_name,
)

__all__ = [
    # Main API
    "Schedule",
    # Task management
    "ScheduledTask",
    "ScheduleRegistry",
    # Utilities
    "list_scheduled_tasks",
    "run_task_by_name",
]
