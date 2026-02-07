# Schedule System Guide

Complete guide to using the Fast Track Framework Schedule system for periodic tasks with cron expressions and intervals.

---

## 📋 Overview

The Schedule system provides a Laravel-style task scheduler for running periodic background jobs. It supports both cron expressions (for complex schedules) and simple intervals (for repetitive tasks).

**Key Features:**
- **Cron Expressions**: Full cron syntax support (5 fields)
- **Simple Intervals**: Run tasks every N seconds
- **Decorator-Based**: Easy registration with `@Schedule.cron()` and `@Schedule.every()`
- **Auto-Discovery**: Worker automatically finds and registers all scheduled tasks
- **IoC Integration**: Scheduled tasks can access services via the container
- **SAQ Backend**: Built on SAQ (Simple Async Queue) with Redis

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
poetry add saq redis
```

### 2. Define Scheduled Tasks

```python
from jtc.schedule import Schedule

# Run every hour at minute 0
@Schedule.cron("0 * * * *")
async def hourly_cleanup(ctx):
    """Clean up temporary files."""
    print("Running cleanup...")
    # Cleanup logic here

# Run every 30 seconds
@Schedule.every(30)
async def health_check(ctx):
    """Check system health."""
    print("Checking health...")
    # Health check logic here
```

### 3. Start the Worker

```bash
# Start worker (discovers and runs all scheduled tasks)
ftf queue work

# List all registered scheduled tasks
ftf queue list
```

---

## 📅 Cron Expressions

### Format

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-6, Sunday=0)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Common Patterns

```python
from jtc.schedule import Schedule

# Every hour at minute 0
@Schedule.cron("0 * * * *")
async def every_hour(ctx):
    pass

# Daily at midnight
@Schedule.cron("0 0 * * *")
async def daily(ctx):
    pass

# Every 5 minutes
@Schedule.cron("*/5 * * * *")
async def every_5_minutes(ctx):
    pass

# Every 15 minutes
@Schedule.cron("*/15 * * * *")
async def every_15_minutes(ctx):
    pass

# Weekly on Sunday at midnight
@Schedule.cron("0 0 * * 0")
async def weekly(ctx):
    pass

# Monthly on the 1st at midnight
@Schedule.cron("0 0 1 * *")
async def monthly(ctx):
    pass

# Weekdays at 9 AM
@Schedule.cron("0 9 * * 1-5")
async def weekdays_9am(ctx):
    pass

# Every hour from 9 AM to 5 PM
@Schedule.cron("0 9-17 * * *")
async def business_hours(ctx):
    pass
```

---

## ⏱️ Interval Scheduling

For simple repetitive tasks, use `@Schedule.every()`:

```python
from jtc.schedule import Schedule

# Every 30 seconds
@Schedule.every(30)
async def frequent_task(ctx):
    print("Running every 30 seconds...")

# Every minute (60 seconds)
@Schedule.every(60)
async def minute_task(ctx):
    pass

# Every 5 minutes (300 seconds)
@Schedule.every(300)
async def five_minute_task(ctx):
    pass

# Every hour (3600 seconds)
@Schedule.every(3600)
async def hourly_task(ctx):
    pass

# Every day (86400 seconds)
@Schedule.every(86400)
async def daily_task(ctx):
    pass
```

---

## 🎯 Advanced Usage

### Custom Task Names and Descriptions

```python
@Schedule.cron(
    "0 * * * *",
    name="custom_hourly_task",
    description="This is a custom task description"
)
async def my_task(ctx):
    """Original docstring (overridden by description parameter)."""
    pass
```

### Accessing SAQ Context

```python
@Schedule.cron("0 * * * *")
async def task_with_context(ctx):
    """
    The ctx parameter contains SAQ context information.

    Available in ctx:
    - queue: The SAQ Queue instance
    - job: The SAQ Job instance (metadata)
    """
    queue = ctx.get("queue")
    job = ctx.get("job")

    print(f"Queue: {queue.name}")
    print(f"Job: {job}")
```

### Accessing Services (via IoC Container)

While scheduled tasks receive `ctx` as a parameter (required by SAQ), you can access services from the IoC Container by creating a wrapper:

```python
from jtc.schedule import Schedule
from jtc.jobs import get_container

@Schedule.cron("0 2 * * *")  # Daily at 2 AM
async def database_backup(ctx):
    """Create database backup with dependency injection."""
    # Get container
    container = get_container()

    # Resolve services
    from jtc.services import BackupService
    backup_service = container.resolve(BackupService)

    # Use service
    await backup_service.create_backup()
```

**Better Pattern**: Use a Job instead of accessing container directly:

```python
from jtc.jobs import Job
from jtc.schedule import Schedule

class DatabaseBackupJob(Job):
    def __init__(self, backup_service: BackupService):
        """Dependencies injected automatically."""
        self.backup_service = backup_service

    async def handle(self):
        await self.backup_service.create_backup()

@Schedule.cron("0 2 * * *")
async def schedule_backup(ctx):
    """Dispatch a job from scheduled task."""
    await DatabaseBackupJob.dispatch()
```

---

## 🔧 Worker Commands

### Start Worker

```bash
# Start worker with defaults
ftf queue work

# Custom queue name
ftf queue work --queue high

# Custom Redis URL
ftf queue work --redis redis://localhost:6380

# Custom concurrency
ftf queue work --concurrency 20

# All options
ftf queue work --queue high --redis redis://localhost:6380 --concurrency 20
```

### List Scheduled Tasks

```bash
ftf queue list
```

Output:
```
Scheduled Tasks
┌──────────────────┬──────────────┬──────────┬─────────────────────┐
│ Name             │ Schedule     │ Type     │ Description         │
├──────────────────┼──────────────┼──────────┼─────────────────────┤
│ hourly_cleanup   │ 0 * * * *    │ cron     │ Clean temp files    │
│ daily_report     │ 0 0 * * *    │ cron     │ Generate report     │
│ frequent_sync    │ 60s          │ interval │ Sync cache          │
└──────────────────┴──────────────┴──────────┴─────────────────────┘

Total: 3 task(s)
```

---

## 🧪 Testing Scheduled Tasks

### Unit Testing

```python
import pytest
from jtc.schedule import run_task_by_name, ScheduleRegistry

@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry before each test."""
    ScheduleRegistry.clear()
    yield
    ScheduleRegistry.clear()

@pytest.mark.asyncio
async def test_hourly_cleanup():
    """Test hourly cleanup task."""
    from your_app.tasks import hourly_cleanup

    # Run task manually
    await run_task_by_name("hourly_cleanup")

    # Assert side effects
    # ... verify files were cleaned, etc.

def test_task_is_registered():
    """Test that task is registered."""
    from your_app.tasks import hourly_cleanup

    task = ScheduleRegistry.get_task("hourly_cleanup")
    assert task is not None
    assert task.schedule == "0 * * * *"
```

### Manual Execution

```python
from jtc.schedule import run_task_by_name

# Run a scheduled task manually (for testing)
await run_task_by_name("hourly_cleanup")

# With custom context
await run_task_by_name("hourly_cleanup", ctx={"test": True})
```

---

## 📊 Comparison with Other Frameworks

### Laravel

**Laravel:**
```php
// app/Console/Kernel.php
protected function schedule(Schedule $schedule)
{
    $schedule->call(function () {
        // Task logic
    })->hourly();

    $schedule->command('emails:send')->daily();
}
```

**Fast Track:**
```python
from jtc.schedule import Schedule

@Schedule.cron("0 * * * *")  # Hourly
async def my_task(ctx):
    # Task logic
    pass
```

### Celery (Python)

**Celery:**
```python
from celery import Celery
from celery.schedules import crontab

app = Celery('tasks', broker='redis://localhost')

app.conf.beat_schedule = {
    'hourly-task': {
        'task': 'tasks.my_task',
        'schedule': crontab(minute=0),
    },
}

@app.task
def my_task():
    # Task logic
    pass
```

**Fast Track:**
```python
from jtc.schedule import Schedule

@Schedule.cron("0 * * * *")
async def my_task(ctx):
    # Task logic
    pass
```

**Advantages over Celery:**
- ✅ No separate beat process needed
- ✅ Simpler decorator-based API
- ✅ Auto-discovery (no manual registration)
- ✅ Native async/await support

---

## 🏗️ Architecture

### How It Works

1. **Task Registration**:
   - Decorators (`@Schedule.cron()`, `@Schedule.every()`) register tasks in `ScheduleRegistry`
   - Registry stores task metadata (function, schedule, name)

2. **Worker Startup**:
   - `QueueProvider` initializes Redis and SAQ Queue
   - Discovers all tasks from `ScheduleRegistry`
   - Registers each task with SAQ's cron system

3. **Task Execution**:
   - SAQ monitors schedules and triggers tasks
   - Tasks run in the worker process
   - Can dispatch Jobs for complex workflows

### Components

```
┌─────────────────────────────────────────┐
│  @Schedule.cron()  @Schedule.every()    │  Decorators
└──────────────┬──────────────────────────┘
               │ registers
               ▼
┌─────────────────────────────────────────┐
│        ScheduleRegistry                 │  Global Registry
└──────────────┬──────────────────────────┘
               │ discovered by
               ▼
┌─────────────────────────────────────────┐
│        QueueProvider                    │  Initialization
└──────────────┬──────────────────────────┘
               │ registers with
               ▼
┌─────────────────────────────────────────┐
│        SAQ Worker                       │  Execution
└─────────────────────────────────────────┘
```

---

## 🔐 Environment Variables

```bash
# Redis connection
REDIS_URL=redis://localhost:6379

# Queue configuration
QUEUE_NAME=default
QUEUE_CONCURRENCY=10
```

---

## 💡 Best Practices

### 1. Keep Tasks Idempotent

Tasks should be safe to run multiple times:

```python
# ✅ Good - idempotent
@Schedule.cron("0 * * * *")
async def sync_users(ctx):
    # Fetch from API
    users = await fetch_users_from_api()

    # Upsert (safe to run multiple times)
    for user in users:
        await db.upsert(user)

# ❌ Bad - not idempotent
@Schedule.cron("0 * * * *")
async def increment_counter(ctx):
    # Running twice increments twice!
    counter += 1
```

### 2. Use Jobs for Complex Workflows

```python
# ✅ Good - dispatch job from schedule
@Schedule.cron("0 * * * *")
async def schedule_report(ctx):
    await GenerateReportJob.dispatch()

class GenerateReportJob(Job):
    def __init__(self, report_service: ReportService):
        self.report_service = report_service

    async def handle(self):
        # Complex logic with DI
        await self.report_service.generate()
```

### 3. Add Logging

```python
import logging

logger = logging.getLogger(__name__)

@Schedule.cron("0 * * * *")
async def hourly_task(ctx):
    logger.info("Starting hourly task...")
    try:
        # Task logic
        logger.info("Hourly task completed successfully")
    except Exception as e:
        logger.error(f"Hourly task failed: {e}")
        raise
```

### 4. Use Descriptive Names

```python
# ✅ Good
@Schedule.cron("0 0 * * *", name="daily_user_activity_report")
async def generate_report(ctx):
    pass

# ❌ Bad
@Schedule.cron("0 0 * * *", name="task1")
async def x(ctx):
    pass
```

---

## 🐛 Troubleshooting

### Task Not Running

1. **Check if task is registered**:
   ```bash
   jtc queue list
   ```

2. **Verify Redis connection**:
   ```bash
   redis-cli ping
   ```

3. **Check worker logs**:
   Look for task execution in worker output

4. **Verify cron expression**:
   Use https://crontab.guru to validate

### Redis Connection Failed

```bash
# Check if Redis is running
redis-cli ping

# Start Redis (Docker)
docker run -d -p 6379:6379 redis:alpine

# Start Redis (local)
redis-server
```

### Task Running Multiple Times

- Ensure you're not running multiple workers
- Check if task is idempotent (can run multiple times safely)

---

## 📚 Additional Resources

- [SAQ Documentation](https://github.com/tobymao/saq)
- [Cron Expression Tester](https://crontab.guru)
- [Redis Documentation](https://redis.io/docs/)

---

**Built with ❤️ for production-ready task scheduling**
