"""
Schedule System Tests (Sprint 3.8)

This module tests the Schedule decorator system and ScheduleRegistry.

Tests cover:
    - @Schedule.cron() decorator
    - @Schedule.every() decorator
    - ScheduleRegistry task storage
    - Task discovery and listing
    - Manual task execution
"""

import pytest

from ftf.schedule import (
    Schedule,
    ScheduleRegistry,
    ScheduledTask,
    list_scheduled_tasks,
    run_task_by_name,
)


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear the registry before and after each test."""
    ScheduleRegistry.clear()
    yield
    ScheduleRegistry.clear()


# ============================================================================
# ScheduledTask Tests
# ============================================================================


def test_scheduled_task_creation():
    """Test creating a scheduled task."""

    async def my_task(ctx):
        pass

    task = ScheduledTask(
        func=my_task, schedule="0 * * * *", name="test_task", description="Test task"
    )

    assert task.func == my_task
    assert task.schedule == "0 * * * *"
    assert task.name == "test_task"
    assert task.description == "Test task"


def test_scheduled_task_defaults():
    """Test scheduled task with default name and description."""

    async def my_task(ctx):
        """My task description."""
        pass

    task = ScheduledTask(func=my_task, schedule="0 * * * *")

    assert task.name == "my_task"  # Defaults to function name
    assert task.description == "My task description."  # Defaults to docstring


def test_scheduled_task_is_cron():
    """Test checking if task uses cron expression."""

    async def my_task(ctx):
        pass

    cron_task = ScheduledTask(func=my_task, schedule="0 * * * *")
    interval_task = ScheduledTask(func=my_task, schedule=60)

    assert cron_task.is_cron() is True
    assert cron_task.is_interval() is False

    assert interval_task.is_cron() is False
    assert interval_task.is_interval() is True


def test_scheduled_task_repr():
    """Test scheduled task string representation."""

    async def my_task(ctx):
        pass

    cron_task = ScheduledTask(func=my_task, schedule="0 * * * *")
    interval_task = ScheduledTask(func=my_task, schedule=60)

    assert "<ScheduledTask my_task schedule=0 * * * *>" == repr(cron_task)
    assert "<ScheduledTask my_task schedule=60s>" == repr(interval_task)


# ============================================================================
# ScheduleRegistry Tests
# ============================================================================


def test_schedule_registry_register():
    """Test registering tasks in the registry."""

    async def task1(ctx):
        pass

    async def task2(ctx):
        pass

    task_obj1 = ScheduledTask(func=task1, schedule="0 * * * *")
    task_obj2 = ScheduledTask(func=task2, schedule=60)

    ScheduleRegistry.register(task_obj1)
    ScheduleRegistry.register(task_obj2)

    tasks = ScheduleRegistry.get_all()
    assert len(tasks) == 2
    assert tasks[0] == task_obj1
    assert tasks[1] == task_obj2


def test_schedule_registry_get_task():
    """Test getting a specific task by name."""

    async def my_task(ctx):
        pass

    task_obj = ScheduledTask(func=my_task, schedule="0 * * * *", name="test_task")
    ScheduleRegistry.register(task_obj)

    found_task = ScheduleRegistry.get_task("test_task")
    assert found_task == task_obj

    not_found = ScheduleRegistry.get_task("nonexistent")
    assert not_found is None


def test_schedule_registry_clear():
    """Test clearing the registry."""

    async def my_task(ctx):
        pass

    task_obj = ScheduledTask(func=my_task, schedule="0 * * * *")
    ScheduleRegistry.register(task_obj)

    assert len(ScheduleRegistry.get_all()) == 1

    ScheduleRegistry.clear()

    assert len(ScheduleRegistry.get_all()) == 0


# ============================================================================
# @Schedule.cron() Decorator Tests
# ============================================================================


def test_schedule_cron_decorator():
    """Test @Schedule.cron() decorator registers task."""
    executed = []

    @Schedule.cron("0 * * * *")
    async def hourly_task(ctx):
        executed.append("hourly")

    tasks = ScheduleRegistry.get_all()
    assert len(tasks) == 1
    assert tasks[0].name == "hourly_task"
    assert tasks[0].schedule == "0 * * * *"
    assert tasks[0].is_cron() is True


def test_schedule_cron_with_custom_name():
    """Test @Schedule.cron() with custom name."""

    @Schedule.cron("0 * * * *", name="custom_hourly")
    async def hourly_task(ctx):
        pass

    task = ScheduleRegistry.get_task("custom_hourly")
    assert task is not None
    assert task.name == "custom_hourly"


def test_schedule_cron_with_description():
    """Test @Schedule.cron() with custom description."""

    @Schedule.cron("0 * * * *", description="Custom description")
    async def hourly_task(ctx):
        """Original docstring."""
        pass

    task = ScheduleRegistry.get_task("hourly_task")
    assert task is not None
    assert task.description == "Custom description"


def test_schedule_cron_common_patterns():
    """Test common cron patterns."""

    @Schedule.cron("0 * * * *")  # Every hour
    async def every_hour(ctx):
        pass

    @Schedule.cron("0 0 * * *")  # Daily at midnight
    async def daily(ctx):
        pass

    @Schedule.cron("*/5 * * * *")  # Every 5 minutes
    async def every_5_min(ctx):
        pass

    @Schedule.cron("0 0 * * 0")  # Weekly on Sunday
    async def weekly(ctx):
        pass

    tasks = ScheduleRegistry.get_all()
    assert len(tasks) == 4


# ============================================================================
# @Schedule.every() Decorator Tests
# ============================================================================


def test_schedule_every_decorator():
    """Test @Schedule.every() decorator registers task."""

    @Schedule.every(60)
    async def minute_task(ctx):
        pass

    tasks = ScheduleRegistry.get_all()
    assert len(tasks) == 1
    assert tasks[0].name == "minute_task"
    assert tasks[0].schedule == 60
    assert tasks[0].is_interval() is True


def test_schedule_every_with_custom_name():
    """Test @Schedule.every() with custom name."""

    @Schedule.every(60, name="custom_minute")
    async def minute_task(ctx):
        pass

    task = ScheduleRegistry.get_task("custom_minute")
    assert task is not None
    assert task.name == "custom_minute"


def test_schedule_every_common_intervals():
    """Test common interval patterns."""

    @Schedule.every(30)  # Every 30 seconds
    async def every_30s(ctx):
        pass

    @Schedule.every(60)  # Every minute
    async def every_minute(ctx):
        pass

    @Schedule.every(3600)  # Every hour
    async def every_hour(ctx):
        pass

    @Schedule.every(86400)  # Every day
    async def every_day(ctx):
        pass

    tasks = ScheduleRegistry.get_all()
    assert len(tasks) == 4


# ============================================================================
# Mixed Scheduling Tests
# ============================================================================


def test_mixed_cron_and_interval():
    """Test registering both cron and interval tasks."""

    @Schedule.cron("0 * * * *")
    async def cron_task(ctx):
        pass

    @Schedule.every(60)
    async def interval_task(ctx):
        pass

    tasks = ScheduleRegistry.get_all()
    assert len(tasks) == 2

    cron_tasks = [t for t in tasks if t.is_cron()]
    interval_tasks = [t for t in tasks if t.is_interval()]

    assert len(cron_tasks) == 1
    assert len(interval_tasks) == 1


# ============================================================================
# Utility Function Tests
# ============================================================================


def test_list_scheduled_tasks():
    """Test list_scheduled_tasks() utility."""

    @Schedule.cron("0 * * * *", description="Hourly task")
    async def hourly(ctx):
        pass

    @Schedule.every(60, description="Minute task")
    async def minute(ctx):
        pass

    tasks = list_scheduled_tasks()

    assert len(tasks) == 2

    # Check structure
    assert all("name" in task for task in tasks)
    assert all("schedule" in task for task in tasks)
    assert all("type" in task for task in tasks)
    assert all("description" in task for task in tasks)

    # Check types
    cron_task = next(t for t in tasks if t["type"] == "cron")
    interval_task = next(t for t in tasks if t["type"] == "interval")

    assert cron_task["name"] == "hourly"
    assert cron_task["schedule"] == "0 * * * *"

    assert interval_task["name"] == "minute"
    assert interval_task["schedule"] == 60


@pytest.mark.asyncio
async def test_run_task_by_name():
    """Test manual task execution by name."""
    executed = []

    @Schedule.cron("0 * * * *")
    async def test_task(ctx):
        executed.append("ran")

    # Run the task manually
    await run_task_by_name("test_task")

    assert executed == ["ran"]


@pytest.mark.asyncio
async def test_run_task_by_name_with_context():
    """Test manual task execution with context."""
    received_ctx = []

    @Schedule.cron("0 * * * *")
    async def test_task(ctx):
        received_ctx.append(ctx)

    # Run with custom context
    custom_ctx = {"key": "value"}
    await run_task_by_name("test_task", ctx=custom_ctx)

    assert len(received_ctx) == 1
    assert received_ctx[0] == custom_ctx


@pytest.mark.asyncio
async def test_run_task_by_name_not_found():
    """Test running nonexistent task raises error."""
    with pytest.raises(ValueError, match="Task 'nonexistent' not found"):
        await run_task_by_name("nonexistent")


# ============================================================================
# Decorator Preserves Function Tests
# ============================================================================


def test_decorator_preserves_function():
    """Test that decorator doesn't modify the original function."""

    async def original_func(ctx):
        """Original docstring."""
        return "result"

    decorated = Schedule.cron("0 * * * *")(original_func)

    # Function should be unchanged
    assert decorated == original_func
    assert decorated.__name__ == "original_func"
    assert decorated.__doc__ == "Original docstring."


@pytest.mark.asyncio
async def test_decorated_function_still_callable():
    """Test that decorated functions can still be called directly."""
    result = []

    @Schedule.cron("0 * * * *")
    async def my_task(ctx):
        result.append("called")
        return "done"

    # Should be able to call the function directly
    return_value = await my_task({})

    assert return_value == "done"
    assert result == ["called"]
