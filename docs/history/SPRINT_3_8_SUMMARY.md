# Sprint 3.8 Implementation - Async Jobs & Scheduler

**Sprint Goal**: Implement async task scheduling with cron expressions and intervals using SAQ + Redis

**Status**: ✅ Complete

---

## 📋 Overview

Sprint 3.8 extends the existing Job Queue system (Sprint 3.2) with a complete task scheduling solution. The system now supports both immediate background jobs and scheduled periodic tasks using cron expressions or simple intervals.

### Objectives

1. ✅ Create Schedule system with `@Schedule.cron()` and `@Schedule.every()` decorators
2. ✅ Implement ScheduleRegistry for task discovery
3. ✅ Create QueueProvider to unify job and schedule initialization
4. ✅ Add Redis connection verification to CLI
5. ✅ Integrate schedules with SAQ worker
6. ✅ Create comprehensive tests (21 tests, 100% coverage on schedule module)
7. ✅ Write complete documentation and examples

---

## 🎯 What Was Built

### 1. Schedule System Core (`src/jtc/schedule/core.py`)

**Components**:
- `Schedule` class with decorator methods
- `ScheduledTask` dataclass
- `ScheduleRegistry` singleton
- Utility functions

**Key Features**:

**@Schedule.cron()** - Cron expression support:
```python
@Schedule.cron("0 * * * *")  # Every hour
async def hourly_cleanup(ctx):
    print("Running cleanup...")
```

**@Schedule.every()** - Simple intervals:
```python
@Schedule.every(60)  # Every 60 seconds
async def frequent_sync(ctx):
    print("Syncing...")
```

**ScheduleRegistry** - Auto-discovery:
```python
# Tasks are automatically registered when decorated
tasks = ScheduleRegistry.get_all()
print(f"Found {len(tasks)} scheduled tasks")
```

### 2. Queue Provider (`src/jtc/providers/queue_provider.py`)

Unified provider for queue system initialization:

```python
provider = QueueProvider(
    redis_url="redis://localhost:6379",
    queue_name="default",
    concurrency=10
)

# Check Redis before starting
if await provider.check_redis_connection():
    await provider.initialize()
    worker = provider.get_worker()
    await worker.start()
```

**Responsibilities**:
- Redis connection management
- JobManager initialization
- IoC Container setup
- Scheduled task registration with SAQ
- Worker configuration

### 3. Enhanced CLI Commands (`src/jtc/cli/commands/queue.py`)

**Updated `jtc queue work`**:
- ✅ Verifies Redis connection before starting
- ✅ Discovers and registers all @Schedule tasks
- ✅ Shows registered tasks count on startup
- ✅ Better error messages and troubleshooting

**New `jtc queue list`**:
```bash
$ jtc queue list

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

### 4. Comprehensive Example (`examples/schedule_example.py`)

Complete working example demonstrating:
- Cron-based scheduling (hourly, daily, weekly)
- Interval-based scheduling (every N seconds)
- Background job dispatching
- Common scheduling patterns

**Example Patterns**:
```python
# Hourly
@Schedule.cron("0 * * * *")
async def hourly_cleanup(ctx): ...

# Daily at midnight
@Schedule.cron("0 0 * * *")
async def daily_summary(ctx): ...

# Every 5 minutes
@Schedule.cron("*/5 * * * *")
async def frequent_sync(ctx): ...

# Every 30 seconds
@Schedule.every(30)
async def health_check(ctx): ...

# Weekly on Sunday
@Schedule.cron("0 0 * * 0")
async def weekly_report(ctx): ...
```

### 5. Complete Test Suite (`tests/unit/test_schedule.py`)

**Test Coverage**: 21 tests, 100% coverage on schedule module

**Test Categories**:
1. **ScheduledTask Tests** (4 tests)
   - Task creation
   - Default values
   - Type checking (cron vs interval)
   - String representation

2. **ScheduleRegistry Tests** (3 tests)
   - Task registration
   - Task retrieval by name
   - Registry clearing

3. **@Schedule.cron() Tests** (4 tests)
   - Decorator registration
   - Custom name/description
   - Common cron patterns

4. **@Schedule.every() Tests** (3 tests)
   - Interval registration
   - Custom name/description
   - Common interval patterns

5. **Mixed Scheduling Tests** (1 test)
   - Cron and interval tasks together

6. **Utility Function Tests** (3 tests)
   - list_scheduled_tasks()
   - run_task_by_name()
   - Error handling

7. **Decorator Behavior Tests** (2 tests)
   - Function preservation
   - Direct callability

**Test Results**:
```
================================ 21 passed in 1.90s ================================
Coverage: 100% on ftf/schedule/core.py
```

### 6. Complete Documentation

**Created**:
- `docs/guides/schedule.md` - Complete scheduling guide
- `examples/schedule_example.py` - Working examples
- `SPRINT_3_8_IMPLEMENTATION.md` - This document

**Documentation Sections**:
- Quick start
- Cron expression reference
- Interval scheduling
- Advanced patterns
- Testing guide
- Troubleshooting
- Best practices

---

## 🎓 Key Learnings

### 1. Why Decorators for Scheduling?

**Pattern**: Decorator-based registration is cleaner than manual registration

**Laravel Pattern**:
```php
// Manual registration in Kernel.php
protected function schedule(Schedule $schedule) {
    $schedule->command('emails:send')->daily();
}
```

**Fast Track Pattern**:
```python
# Auto-registration with decorator
@Schedule.cron("0 0 * * *")
async def send_emails(ctx):
    pass
```

**Benefits**:
- ✅ Tasks defined where they're implemented
- ✅ No central registration file
- ✅ Auto-discovery at runtime
- ✅ Clear, concise syntax

### 2. SAQ Integration Pattern

**Challenge**: SAQ is function-based, we want class-based + schedules

**Solution**: Bridge pattern
- Use `runner()` as universal executor for class-based Jobs
- Register scheduled task functions directly with SAQ
- QueueProvider handles the integration

**Architecture**:
```
Class-based Job → runner() → SAQ Queue → Worker
Scheduled Task → SAQ Cron → Worker
```

### 3. Registry Pattern for Discovery

**Pattern**: Global registry for auto-discovery

```python
# Decorator registers task
@Schedule.cron("0 * * * *")
async def my_task(ctx): ...

# Worker discovers all tasks
tasks = ScheduleRegistry.get_all()
for task in tasks:
    queue.schedule(task.func, cron=task.schedule)
```

**Benefits**:
- ✅ No import needed
- ✅ Automatic discovery
- ✅ Testable (can clear registry)

### 4. Provider Pattern for Initialization

**Pattern**: Centralize all queue-related setup

**Before** (scattered setup):
```python
redis = Redis.from_url(url)
queue = saq.Queue(redis)
worker = saq.Worker(queue=queue, functions=[...])
```

**After** (unified provider):
```python
provider = QueueProvider()
await provider.initialize()
worker = provider.get_worker()
```

**Benefits**:
- ✅ Single source of truth
- ✅ Easier testing
- ✅ Better error handling

---

## 📊 Files Created/Modified

### Created Files (9)

1. **`src/jtc/schedule/core.py`** (287 lines)
   - Schedule class with decorators
   - ScheduledTask dataclass
   - ScheduleRegistry singleton
   - Utility functions

2. **`src/jtc/schedule/__init__.py`** (58 lines)
   - Module exports
   - Documentation

3. **`src/jtc/providers/queue_provider.py`** (267 lines)
   - QueueProvider class
   - Redis connection checking
   - Schedule integration
   - Worker configuration

4. **`src/jtc/providers/__init__.py`** (18 lines)
   - Module exports

5. **`examples/schedule_example.py`** (280 lines)
   - Complete working examples
   - Common scheduling patterns
   - Background job examples

6. **`tests/unit/test_schedule.py`** (387 lines)
   - 21 comprehensive tests
   - 100% coverage

7. **`docs/guides/schedule.md`** (~ 600 lines)
   - Complete scheduling guide
   - Cron reference
   - Best practices
   - Troubleshooting

8. **`SPRINT_3_8_IMPLEMENTATION.md`** (this file)
   - Implementation documentation

### Modified Files (1)

9. **`src/jtc/cli/commands/queue.py`** (enhanced)
   - Added Redis connection check
   - Integrated QueueProvider
   - Added `jtc queue list` command
   - Better error messages

---

## 🔄 Comparison with Other Frameworks

### Laravel Task Scheduler

**Laravel**:
```php
// app/Console/Kernel.php
protected function schedule(Schedule $schedule)
{
    $schedule->command('emails:send')->hourly();
    $schedule->call(function () {
        // Task logic
    })->daily();
}

// Requires cron entry:
// * * * * * php artisan schedule:run >> /dev/null 2>&1
```

**Fast Track**:
```python
@Schedule.cron("0 * * * *")
async def send_emails(ctx):
    # Task logic
    pass

# No cron entry needed - worker handles scheduling
$ jtc queue work
```

### Celery Beat (Python)

**Celery**:
```python
# Requires separate beat process
from celery.schedules import crontab

app.conf.beat_schedule = {
    'hourly-task': {
        'task': 'tasks.send_emails',
        'schedule': crontab(minute=0),
    },
}

# Run worker + beat
$ celery -A app worker --beat
```

**Fast Track**:
```python
@Schedule.cron("0 * * * *")
async def send_emails(ctx):
    pass

# Single process
$ jtc queue work
```

### NestJS Task Scheduling (Node.js)

**NestJS**:
```typescript
import { Cron, CronExpression } from '@nestjs/schedule';

@Injectable()
export class TasksService {
  @Cron(CronExpression.EVERY_HOUR)
  handleCron() {
    // Task logic
  }
}
```

**Fast Track**:
```python
@Schedule.cron("0 * * * *")
async def handle_cron(ctx):
    # Task logic
    pass
```

**Advantages**:
- ✅ Simpler than Celery (no beat process)
- ✅ More Pythonic than Laravel (decorators vs manual registration)
- ✅ Native async/await (unlike Celery)
- ✅ Auto-discovery (like NestJS)
- ✅ Built-in monitoring (SAQ dashboard)

---

## 📈 Sprint Metrics

```
Files Created:        9
Lines of Code:        ~2,000 (including tests and docs)
Tests Added:          21 (100% passing)
Test Coverage:        100% (schedule module)
Documentation:        ~600 lines
Examples:             280 lines
Commands Added:       1 (queue list)
Commands Enhanced:    1 (queue work)
```

---

## ✅ Sprint Success Criteria

- ✅ **Schedule Decorators**: @Schedule.cron() and @Schedule.every()
- ✅ **Registry Pattern**: Auto-discovery of scheduled tasks
- ✅ **QueueProvider**: Unified initialization
- ✅ **Redis Check**: Verify connection before starting
- ✅ **SAQ Integration**: Tasks registered with SAQ cron system
- ✅ **CLI Enhancement**: Better worker startup with task listing
- ✅ **Test Coverage**: 21 tests, 100% coverage
- ✅ **Documentation**: Complete guide with examples
- ✅ **Production Ready**: Error handling, logging, best practices

---

## 🚀 Production Impact

### Before Sprint 3.8

**Limitations**:
- ❌ No built-in task scheduling
- ❌ Manual cron job configuration needed
- ❌ No Redis connection verification
- ❌ Jobs and schedules managed separately

**Example** (manual cron setup):
```bash
# Add to crontab manually
0 * * * * python -m my_app.tasks.cleanup
0 0 * * * python -m my_app.tasks.reports
```

### After Sprint 3.8

**Capabilities**:
- ✅ Built-in task scheduling with decorators
- ✅ Automatic discovery and registration
- ✅ Redis connection verification
- ✅ Unified queue provider
- ✅ Single worker process

**Example** (decorator-based):
```python
@Schedule.cron("0 * * * *")
async def cleanup(ctx): ...

@Schedule.cron("0 0 * * *")
async def reports(ctx): ...

# Single command
$ jtc queue work
```

---

## 🏆 Sprint Completion

**Status**: ✅ Complete

**Next Steps**: Sprint 3.9 - Real-time Features (WebSockets)

**Sprint 3.8 delivered**:
- ✅ Complete task scheduling system
- ✅ Cron expression support
- ✅ Interval scheduling
- ✅ QueueProvider for unified initialization
- ✅ Enhanced CLI with Redis verification
- ✅ 21 comprehensive tests (100% coverage)
- ✅ Complete documentation and examples
- ✅ Production-ready implementation

**Impact**: Developers can now define scheduled tasks with simple decorators, no manual cron configuration needed.

---

## 📚 Usage Summary

### Define Scheduled Tasks

```python
from jtc.schedule import Schedule

@Schedule.cron("0 * * * *")  # Every hour
async def hourly_cleanup(ctx):
    # Cleanup logic
    pass

@Schedule.every(60)  # Every 60 seconds
async def health_check(ctx):
    # Health check logic
    pass
```

### Start Worker

```bash
# Start worker (auto-discovers and runs all schedules)
ftf queue work

# List all scheduled tasks
ftf queue list

# Custom configuration
ftf queue work --redis redis://localhost:6380 --concurrency 20
```

### Dispatch Background Jobs

```python
from jtc.jobs import Job

class ProcessOrderJob(Job):
    async def handle(self):
        # Process order
        pass

# Dispatch from anywhere
await ProcessOrderJob.dispatch(order_id=123)
```

---

**Built with ❤️ for production-ready async task scheduling**
