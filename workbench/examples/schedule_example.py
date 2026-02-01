"""
Schedule System Example - Cron & Interval Jobs

This example demonstrates how to use the Schedule system to create
periodic tasks that run on a schedule.

Features Demonstrated:
    - Cron-based scheduling with @Schedule.cron()
    - Interval-based scheduling with @Schedule.every()
    - Scheduled tasks with dependencies (via IoC Container)
    - Background jobs with @Job.dispatch()

Run the worker:
    $ ftf queue work

Then these tasks will automatically execute according to their schedules:
    - hourly_cleanup: Every hour at minute 0
    - daily_summary: Every day at midnight
    - frequent_health_check: Every 30 seconds
    - weekly_report: Every Sunday at midnight

You can also dispatch background jobs from anywhere in your app:
    >>> await ProcessOrderJob.dispatch(order_id=123)
"""

from datetime import datetime

from ftf.jobs import Job
from ftf.schedule import Schedule

# ============================================================================
# SCHEDULED TASKS (Cron & Interval)
# ============================================================================


@Schedule.cron("0 * * * *")  # Every hour at minute 0
async def hourly_cleanup(ctx):
    """
    Clean up temporary files and expired cache entries.

    This task runs every hour to keep the system clean.
    """
    print(f"[{datetime.now()}] Running hourly cleanup...")

    # Cleanup logic here
    # - Delete temp files older than 24 hours
    # - Clear expired cache entries
    # - Archive old logs

    print("  ✓ Temporary files cleaned")
    print("  ✓ Cache purged")
    print("  ✓ Logs archived")


@Schedule.cron("0 0 * * *")  # Daily at midnight
async def daily_summary(ctx):
    """
    Generate daily summary report.

    This task runs every day at midnight to generate reports.
    """
    print(f"[{datetime.now()}] Generating daily summary...")

    # Report generation logic here
    # - Calculate daily metrics
    # - Generate charts
    # - Send email to admins

    print("  ✓ Metrics calculated")
    print("  ✓ Report generated")
    print("  ✓ Email sent")


@Schedule.every(30)  # Every 30 seconds
async def frequent_health_check(ctx):
    """
    Check system health frequently.

    This task runs every 30 seconds to monitor system health.
    """
    print(f"[{datetime.now()}] Running health check...")

    # Health check logic here
    # - Check database connectivity
    # - Check Redis connectivity
    # - Check disk space
    # - Check memory usage

    print("  ✓ All systems operational")


@Schedule.cron("0 0 * * 0")  # Weekly on Sunday at midnight
async def weekly_report(ctx):
    """
    Generate weekly analytics report.

    This task runs every Sunday at midnight.
    """
    print(f"[{datetime.now()}] Generating weekly report...")

    # Weekly report logic here
    # - Aggregate weekly data
    # - Generate trend analysis
    # - Create PDF report
    # - Send to stakeholders

    print("  ✓ Weekly report generated")


@Schedule.cron("*/5 * * * *")  # Every 5 minutes
async def sync_external_data(ctx):
    """
    Sync data from external API.

    This task runs every 5 minutes to keep data in sync.
    """
    print(f"[{datetime.now()}] Syncing external data...")

    # Sync logic here
    # - Fetch from external API
    # - Transform data
    # - Update database

    print("  ✓ External data synced")


# ============================================================================
# BACKGROUND JOBS (Dispatch from anywhere)
# ============================================================================


class ProcessOrderJob(Job):
    """
    Background job to process an order.

    This job can be dispatched from anywhere in your application:
        await ProcessOrderJob.dispatch(order_id=123)

    The job will be queued and processed asynchronously by the worker.
    """

    def __init__(self):
        """Initialize the job (can inject dependencies here)."""
        # You can inject repositories, services, etc.
        # Example: def __init__(self, order_repo: OrderRepository)
        self.order_id: int = 0  # Will be set from dispatch payload

    async def handle(self) -> None:
        """Process the order."""
        print(f"[{datetime.now()}] Processing order {self.order_id}...")

        # Order processing logic
        # - Validate payment
        # - Update inventory
        # - Send confirmation email

        print(f"  ✓ Order {self.order_id} processed")


class SendWelcomeEmailJob(Job):
    """
    Send welcome email to new user.

    Usage:
        await SendWelcomeEmailJob.dispatch(user_id=456, email="user@example.com")
    """

    def __init__(self):
        """Initialize the job."""
        self.user_id: int = 0
        self.email: str = ""

    async def handle(self) -> None:
        """Send the email."""
        print(f"[{datetime.now()}] Sending welcome email to {self.email}...")

        # Email sending logic
        # - Fetch user details
        # - Render email template
        # - Send via email provider

        print(f"  ✓ Welcome email sent to user {self.user_id}")


class GenerateInvoiceJob(Job):
    """
    Generate invoice PDF for an order.

    Usage:
        await GenerateInvoiceJob.dispatch(order_id=789)
    """

    def __init__(self):
        """Initialize the job."""
        self.order_id: int = 0

    async def handle(self) -> None:
        """Generate the invoice."""
        print(f"[{datetime.now()}] Generating invoice for order {self.order_id}...")

        # Invoice generation logic
        # - Fetch order details
        # - Generate PDF
        # - Upload to S3
        # - Send download link

        print(f"  ✓ Invoice generated for order {self.order_id}")


# ============================================================================
# SCHEDULED TASK WITH DEPENDENCIES (Advanced)
# ============================================================================


@Schedule.cron("0 2 * * *")  # Daily at 2 AM
async def database_backup(ctx):
    """
    Create database backup.

    This example shows how to access services from a scheduled task.
    The ctx parameter contains the queue context.
    """
    print(f"[{datetime.now()}] Creating database backup...")

    # In a real app, you might want to:
    # 1. Get database connection from context or environment
    # 2. Run backup command
    # 3. Upload to S3 or remote storage
    # 4. Clean up old backups

    # Example with context access:
    # queue = ctx.get("queue")
    # job = ctx.get("job")

    print("  ✓ Database backup created")
    print("  ✓ Backup uploaded to S3")
    print("  ✓ Old backups cleaned")


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    """
    This file should NOT be run directly.
    Instead, start the worker which will automatically discover
    and register all scheduled tasks:

        $ ftf queue work

    To dispatch background jobs from your application:

        from examples.schedule_example import ProcessOrderJob

        # In a route handler or service:
        await ProcessOrderJob.dispatch(order_id=123)

    To list all scheduled tasks:

        $ ftf queue list
    """
    print("=" * 70)
    print("Schedule Example - DO NOT RUN DIRECTLY")
    print("=" * 70)
    print()
    print("To start the worker with scheduled tasks:")
    print("  $ ftf queue work")
    print()
    print("To list all scheduled tasks:")
    print("  $ ftf queue list")
    print()
    print("To dispatch background jobs:")
    print("  from examples.schedule_example import ProcessOrderJob")
    print("  await ProcessOrderJob.dispatch(order_id=123)")
    print()
