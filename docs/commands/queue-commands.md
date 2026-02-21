# Queue Commands

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21

This section documents all `queue:*` commands used for managing background job queues and scheduled tasks.

## Overview

Queue commands provide tools for managing asynchronous background job processing using SAQ (Simple Async Queue) with Redis as the backend. Similar to Laravel Horizon and Laravel Queue system.

**Features**:
- Background job processing
- Scheduled task execution (cron-like)
- Job monitoring and retry
- Web dashboard for monitoring (like Laravel Horizon)

---

## queue:work

Start a queue worker to process background jobs and scheduled tasks.

### Syntax

```bash
jtc queue work [options]
```

### Options

- `-q, --queue`: Queue name to process (default: "default")
- `--redis`: Redis connection URL (default: "redis://localhost:6379")
- `-c, --concurrency`: Number of concurrent jobs to process (default: 10)

### Description

Starts a SAQ worker that:
- Verifies Redis connection
- Initializes IoC Container
- Discovers and registers all `@Schedule` decorated tasks
- Processes jobs from the specified queue
- Executes scheduled tasks at their scheduled times

### Examples

```bash
# Start worker for default queue
jtc queue work
# Output:
# 🚀 Starting worker for queue: default
# 📡 Redis: redis://localhost:6379
# ⚙️  Concurrency: 10
# 
# Checking Redis connection...
# ✓ Redis connection OK
# 
# Initializing IoC Container...
# Initializing queue system...
# ✓ Registered 3 scheduled task(s)
#   • hourly_cleanup: 0 * * * (cron)
#   • daily_report: 0 0 * * (cron)
#   • frequent_sync: 60s (interval)
# 
# ✓ Worker ready!
# Press Ctrl+C to stop

# Start worker for high-priority queue
jtc queue work --queue high --redis redis://production-redis:6380 --concurrency 20
# Output:
# 🚀 Starting worker for queue: high
# 📡 Redis: redis://production-redis:6380
# ⚙️  Concurrency: 20
```

### What the Worker Does

The worker continuously:
1. **Polls for jobs** on the specified queue
2. **Checks for scheduled tasks** ready to run
3. **Processes jobs** using the registered job classes
4. **Retries failed jobs** (if configured)
5. **Logs activity** to console

### Multiple Workers

You can run multiple workers for different queues:

```bash
# Terminal 1: Process default queue
jtc queue work --queue default

# Terminal 2: Process high-priority queue
jtc queue work --queue high --concurrency 5

# Terminal 3: Process emails queue
jtc queue work --queue emails --concurrency 2
```

### Prerequisites

- Redis server running
- Redis configured in environment
- Job classes created (using `make:job`)
- Scheduled tasks defined (using `@Schedule` decorator)

### Redis Configuration

```bash
# .env file
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0

# Or use full URL
REDIS_URL=redis://localhost:6379/0
```

### Stopping the Worker

Press `Ctrl+C` to gracefully stop the worker. The worker will:
- Stop processing new jobs
- Finish current job (if possible)
- Disconnect from Redis

---

## queue:list

List all registered scheduled tasks.

### Syntax

```bash
jtc queue list
```

### Description

Displays all tasks that have been registered via `@Schedule.cron()` or `@Schedule.every()` decorators. This helps you verify scheduled tasks are properly registered.

### Examples

```bash
# List all scheduled tasks
jtc queue list
# Output:
# 
# Scheduled Tasks
# ┌──────────────────┬──────────────┬──────────┬─────────────────────┐
# │ Name             │ Schedule     │ Type     │ Description         │
# ├──────────────────┼──────────────┼──────────┼─────────────────────┤
# │ hourly_cleanup   │ 0 * * * *    │ cron     │ Clean temp files    │
# │ daily_report     │ 0 0 * * *    │ cron     │ Generate report     │
# │ frequent_sync    │ 60s           │ interval │ Sync cache          │
# └──────────────────┴──────────────┴──────────┴─────────────────────┘
# 
# Total: 3 task(s)
```

### No Tasks Registered

```bash
jtc queue list
# Output:
# No scheduled tasks registered
# 
# Register tasks using @Schedule.cron() or @Schedule.every()
```

### Task Types

The list shows two types of scheduled tasks:

#### Cron Tasks

```python
from jtc.schedule import Schedule

@Schedule.cron("0 * * * *")  # Every hour
async def hourly_cleanup():
    # Cleanup task code
    pass
```

#### Interval Tasks

```python
from jtc.schedule import Schedule

@Schedule.every(60)  # Every 60 seconds
async def frequent_sync():
    # Sync task code
    pass
```

---

## queue:dashboard

Start a SAQ monitoring web dashboard (like Laravel Horizon).

### Syntax

```bash
jtc queue dashboard [options]
```

### Options

- `--redis`: Redis connection URL (default: "redis://localhost:6379")
- `-p, --port`: Port to run dashboard on (default: 8080)

### Description

Starts a web UI where you can:
- Monitor running jobs
- View job history
- See queue statistics
- Retry failed jobs

⚠️ **Note**: The dashboard requires `aiohttp` to be installed.

### Examples

```bash
# Start dashboard on default port
jtc queue dashboard
# Output:
# 🎛️  Starting SAQ dashboard...
# 📡 Redis: redis://localhost:6379
# 🌐 Port: 8080
# ✓ Dashboard ready!
# 🌐 Visit: http://localhost:8080
# Press Ctrl+C to stop

# Start dashboard on custom port
jtc queue dashboard --port 9000
# Output:
# 🎛️  Starting SAQ dashboard...
# 📡 Redis: redis://localhost:6379
# 🌐 Port: 9000
# ✓ Dashboard ready!
# 🌐 Visit: http://localhost:9000
```

### Dashboard Features

The SAQ dashboard provides:
- **Queue Statistics**: Job counts, success/failure rates
- **Job History**: View past and current jobs
- **Worker Status**: Monitor active workers
- **Job Retries**: Manually retry failed jobs
- **Job Inspection**: View job payloads and results

### Installing aiohttp

If you get an error about aiohttp not being installed:

```bash
# Install aiohttp
poetry add aiohttp

# Then try again
jtc queue dashboard
```

### Stopping the Dashboard

Press `Ctrl+C` to stop the dashboard server.

---

## Creating Jobs and Scheduled Tasks

### Background Jobs

Create a job using `make:job`:

```bash
jtc make:job SendEmail
```

Then dispatch it:

```python
from app.jobs.send_email import SendEmail

# Dispatch to queue
await SendEmail(user).dispatch()

# Or with delay
await SendEmail(user).dispatch(delay=60)  # Delay 60 seconds
```

### Scheduled Tasks

Create a scheduled task using the `@Schedule` decorator:

```python
from jtc.schedule import Schedule

# Run every hour (cron: 0 * * * *)
@Schedule.cron("0 * * * *")
async def hourly_cleanup():
    # Cleanup temporary files
    pass

# Run every 60 seconds
@Schedule.every(60)
async def frequent_sync():
    # Sync data every minute
    pass

# Run every day at midnight (cron: 0 0 * * *)
@Schedule.cron("0 0 * * *")
async def daily_report():
    # Generate daily report
    pass
```

### Cron Syntax

```
# ┌─────────┬─────┬───────┬───────┬───────┐
# │ Minutes │ Hours │ Day   │ Month  │ Weekday│
# │ 0-59    │ 0-23  │ 1-31  │ 1-12  │ 0-6    │
# └─────────┴─────┴───────┴───────┴───────┘
# 
# * = any value
# */5 = every 5 minutes
# 0,15,30,45 = specific minutes
```

Examples:
- `0 * * * *` - Every hour at minute 0
- `*/15 * * * *` - Every 15 minutes
- `0 0 * * *` - Every day at midnight
- `0 0 * * 0` - Every Sunday at midnight
- `0 9 * * 1-5` - 9 AM on weekdays

---

## Queue Configuration

### Redis Setup

```bash
# .env file
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0
```

### Worker Configuration

```bash
# Multiple queues
jtc queue work --queue default --concurrency 10
jtc queue work --queue high --concurrency 5
jtc queue work --queue low --concurrency 2

# Production Redis
jtc queue work --redis redis://production-redis:6380
```

### Job Configuration

```python
# Job with retry
class SendEmail(Job):
    retry_on: [ConnectionError, TimeoutError]
    retry_delay: 60  # seconds
    retry_backoff: 2  # exponential backoff multiplier
    max_retries: 3
    
    async def handle(self):
        # Send email logic
        pass
```

---

## Common Patterns

### Processing Images

```python
from jtc.jobs import Job

class ProcessImage(Job):
    async def handle(self):
        # Process uploaded image
        image = await Image.find(self.image_id)
        processed = await process_image(image)
        image.processed_at = datetime.now()
        await self.image_repo.update(image)
```

### Sending Emails

```python
from jtc.jobs import Job

class SendWelcomeEmail(Job):
    async def handle(self):
        user = await self.user_repo.find(self.user_id)
        email = WelcomeEmail(user)
        await Mail.send(email)
```

### Data Synchronization

```python
from jtc.schedule import Schedule

@Schedule.every(300)  # Every 5 minutes
async def sync_external_data():
    # Fetch data from external API
    data = await external_api.fetch_data()
    # Store in database
    await repo.upsert(data)
```

---

## Best Practices

### Job Design

- **Idempotent**: Jobs should be safe to run multiple times
- **Atomic**: Operations should complete or roll back together
- **Small**: Break large tasks into smaller jobs
- **Dependencies**: Use constructor injection for dependencies

### Worker Configuration

- **Concurrent Workers**: Based on available resources and job type
- **Queue Separation**: Separate slow/fast jobs into different queues
- **Monitoring**: Use dashboard to monitor worker health
- **Graceful Shutdown**: Allow current jobs to finish before exiting

### Scheduled Tasks

- **Cron Accuracy**: Use specific times when needed
- **Error Handling**: Catch and log errors in scheduled tasks
- **Idempotency**: Scheduled tasks should be safe to run multiple times

---

## Troubleshooting

### Worker Not Processing Jobs

```bash
# 1. Check worker is running
jtc queue list

# 2. Check Redis connection
redis-cli ping

# 3. Check for jobs
redis-cli LRANGE default:queue 0 10

# 4. Check worker logs
# Worker console output shows connection status and job processing
```

### Redis Connection Issues

```bash
# Check Redis is running
systemctl status redis

# Test Redis connection
redis-cli ping

# Check firewall
telnet localhost 6379

# Verify Redis logs
tail -f /var/log/redis/redis-server.log
```

### Scheduled Task Not Running

```bash
# List scheduled tasks
jtc queue list

# Check task is registered
# Should appear in the list

# Check worker is running
jtc queue work
# Worker console shows: "Registered X scheduled task(s)"
```

### Dashboard Not Starting

```bash
# Error: aiohttp not installed
# Solution
poetry add aiohttp

# Error: SAQ web UI not available
# Solution: This may not be available in all SAQ versions
# Use redis-cli to monitor instead:
redis-cli MONITOR
```

---

## Comparison with Laravel

| Laravel | Fast Track | Purpose |
|---------|-------------|----------|
| `php artisan queue:work` | `jtc queue work` | Start queue worker |
| `php artisan queue:listen` | N/A | Same as `queue work` |
| `php artisan queue:retry` | N/A | Retry via dashboard |
| `php artisan queue:failed` | N/A | View via dashboard |
| `php artisan schedule:run` | N/A | Workers auto-run schedules |
| Laravel Horizon | `jtc queue dashboard` | Web monitoring UI |

---

## Next Steps

- [Make Commands](make-commands.md) - Create job classes
- [Database Commands](db-commands.md) - Database operations
- [Cache Commands](cache-commands.md) - Cache management
- [Test Commands](test-commands.md) - Testing utilities
- [Deploy Commands](deploy-commands.md) - Deployment automation

---

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21
