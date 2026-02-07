"""
Queue Worker Commands (Sprint 3.8 - Enhanced)

This module provides commands for managing the background job queue:
    - queue:work: Start the SAQ worker to process jobs and scheduled tasks
    - queue:dashboard: Start the monitoring UI (Laravel Horizon-like)
    - queue:list: List all registered scheduled tasks

Educational Note:
    These commands initialize the IoC Container, SAQ worker, and scheduled
    tasks. The worker automatically discovers and registers all @Schedule
    decorated functions when it starts.

Commands:
    $ jtc queue work                    # Start worker (default queue)
    $ jtc queue work --queue high       # Start worker for specific queue
    $ jtc queue dashboard               # Start monitoring UI at http://localhost:8080
    $ jtc queue list                    # List all scheduled tasks
"""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from jtc.core import Container
from jtc.jobs import JobManager, runner, set_container
from jtc.providers import QueueProvider
from jtc.schedule import list_scheduled_tasks

# Create command group
app = typer.Typer()
console = Console()


@app.command("work")
def queue_work(
    queue_name: str = typer.Option("default", "--queue", "-q", help="Queue name"),
    redis_url: str = typer.Option(
        "redis://localhost:6379", "--redis", help="Redis URL"
    ),
    concurrency: int = typer.Option(10, "--concurrency", "-c", help="Worker concurrency"),
) -> None:
    """
    Start the queue worker to process background jobs and scheduled tasks.

    This command:
    1. Verifies Redis connection
    2. Initializes the IoC Container
    3. Discovers and registers all @Schedule decorated tasks
    4. Sets up the SAQ worker with the runner function
    5. Starts processing jobs and scheduled tasks

    The worker will run indefinitely until stopped with Ctrl+C.

    Args:
        queue_name: Name of the queue to process (default: "default")
        redis_url: Redis connection URL (default: redis://localhost:6379)
        concurrency: Number of concurrent jobs to process (default: 10)

    Example:
        $ jtc queue work
        🚀 Worker started for queue: default
        📡 Listening for jobs on redis://localhost:6379
        ⏰ Registered 3 scheduled tasks

        $ jtc queue work --queue high --redis redis://localhost:6380 --concurrency 20
        🚀 Worker started for queue: high
    """
    console.print(f"[green]🚀 Starting worker for queue:[/green] {queue_name}")
    console.print(f"[dim]📡 Redis:[/dim] {redis_url}")
    console.print(f"[dim]⚙️  Concurrency:[/dim] {concurrency}")

    async def start_worker() -> None:
        """Async wrapper to start the worker."""
        # Create Queue Provider
        provider = QueueProvider(
            redis_url=redis_url,
            queue_name=queue_name,
            concurrency=concurrency,
        )

        # Check Redis connection first
        console.print("\n[dim]Checking Redis connection...[/dim]")
        if not await provider.check_redis_connection():
            console.print(
                f"[red]✗ Cannot connect to Redis at {redis_url}[/red]"
            )
            console.print("[yellow]Make sure Redis is running:[/yellow]")
            console.print("  • docker run -d -p 6379:6379 redis:alpine")
            console.print("  • redis-server")
            sys.exit(1)

        console.print("[green]✓ Redis connection OK[/green]")

        # Initialize Container
        console.print("\n[dim]Initializing IoC Container...[/dim]")
        container = Container()

        # Initialize the queue system (including scheduled tasks)
        console.print("[dim]Initializing queue system...[/dim]")
        await provider.initialize(container)

        # Show registered scheduled tasks
        tasks = list_scheduled_tasks()
        if tasks:
            console.print(
                f"[green]✓ Registered {len(tasks)} scheduled task(s)[/green]"
            )
            for task in tasks:
                schedule_str = task["schedule"] if task["type"] == "cron" else f"{task['schedule']}s"
                console.print(f"  • {task['name']}: {schedule_str}")
        else:
            console.print("[dim]  No scheduled tasks registered[/dim]")

        # Get worker
        worker = provider.get_worker()

        console.print(f"\n[green]✓ Worker ready![/green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        # Run the worker (blocking)
        try:
            await worker.start()
        finally:
            # Cleanup
            await provider.close()

    try:
        asyncio.run(start_worker())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Worker stopped by user[/yellow]")
        sys.exit(0)
    except ImportError as e:
        console.print(f"[red]✗ Import error:[/red] {e}")
        console.print("[yellow]Make sure dependencies are installed:[/yellow]")
        console.print("  poetry add saq redis")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error starting worker:[/red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@app.command("list")
def queue_list() -> None:
    """
    List all registered scheduled tasks.

    This command displays all tasks that have been registered via
    @Schedule.cron() or @Schedule.every() decorators.

    Example:
        $ jtc queue list

        Scheduled Tasks
        ┌──────────────────┬──────────────┬──────────┬─────────────────────┐
        │ Name             │ Schedule     │ Type     │ Description         │
        ├──────────────────┼──────────────┼──────────┼─────────────────────┤
        │ hourly_cleanup   │ 0 * * * *    │ cron     │ Clean temp files    │
        │ daily_report     │ 0 0 * * *    │ cron     │ Generate report     │
        │ frequent_sync    │ 60s          │ interval │ Sync cache          │
        └──────────────────┴──────────────┴──────────┴─────────────────────┘
    """
    tasks = list_scheduled_tasks()

    if not tasks:
        console.print("[yellow]No scheduled tasks registered[/yellow]")
        console.print(
            "\n[dim]Register tasks using @Schedule.cron() or @Schedule.every()[/dim]"
        )
        return

    # Create table
    table = Table(title="Scheduled Tasks", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="green")
    table.add_column("Schedule", style="yellow")
    table.add_column("Type", style="blue")
    table.add_column("Description", style="dim")

    for task in tasks:
        schedule_str = (
            task["schedule"] if task["type"] == "cron" else f"{task['schedule']}s"
        )
        description = task["description"] or ""
        if description and len(description) > 50:
            description = description[:47] + "..."

        table.add_row(
            task["name"],
            schedule_str,
            task["type"],
            description,
        )

    console.print(table)
    console.print(f"\n[green]Total:[/green] {len(tasks)} task(s)")


@app.command("dashboard")
def queue_dashboard(
    redis_url: str = typer.Option(
        "redis://localhost:6379", "--redis", help="Redis URL"
    ),
    port: int = typer.Option(8080, "--port", "-p", help="Dashboard port"),
) -> None:
    """
    Start the SAQ monitoring dashboard (like Laravel Horizon).

    This command starts a web UI where you can:
    - Monitor running jobs
    - View job history
    - See queue statistics
    - Retry failed jobs

    The dashboard requires aiohttp to be installed.

    Args:
        redis_url: Redis connection URL (default: redis://localhost:6379)
        port: Port to run the dashboard on (default: 8080)

    Example:
        $ jtc queue dashboard
        🎛️  Dashboard started at http://localhost:8080

        $ jtc queue dashboard --port 9000
        🎛️  Dashboard started at http://localhost:9000
    """
    try:
        # Check if aiohttp is installed
        import aiohttp  # noqa: F401
    except ImportError:
        console.print("[red]✗ aiohttp not installed[/red]")
        console.print(
            "[yellow]Install with:[/yellow] poetry add aiohttp",
        )
        sys.exit(1)

    console.print(f"[green]🎛️  Starting SAQ dashboard...[/green]")
    console.print(f"[dim]📡 Redis:[/dim] {redis_url}")
    console.print(f"[dim]🌐 Port:[/dim] {port}")

    try:
        import saq.web
        from redis.asyncio import Redis

        # Create Redis connection
        redis = Redis.from_url(redis_url, decode_responses=True)

        # Create SAQ queue
        queue = saq.Queue(redis, name="default")

        console.print(f"[green]✓ Dashboard ready![/green]")
        console.print(f"[green]🌐 Visit:[/green] http://localhost:{port}")
        console.print("[dim]Press Ctrl+C to stop[/dim]")

        # Run the dashboard (blocking)
        # SAQ provides a built-in web UI
        asyncio.run(saq.web.create_app(queue).run(host="0.0.0.0", port=port))

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Dashboard stopped by user[/yellow]")
        sys.exit(0)
    except AttributeError:
        console.print("[red]✗ SAQ web UI not available[/red]")
        console.print(
            "[yellow]Note:[/yellow] SAQ dashboard may not be available in this version"
        )
        console.print(
            "[dim]You can monitor jobs with redis-cli or a Redis GUI instead[/dim]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error starting dashboard:[/red] {e}")
        sys.exit(1)
