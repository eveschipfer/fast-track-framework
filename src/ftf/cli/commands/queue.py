"""
Queue Worker Commands (Sprint 3.2)

This module provides commands for managing the background job queue:
    - queue:work: Start the SAQ worker to process jobs
    - queue:dashboard: Start the monitoring UI (Laravel Horizon-like)

Educational Note:
    These commands initialize the IoC Container and SAQ worker. The worker
    must have access to the container so that jobs can be resolved with
    their dependencies.

Commands:
    $ ftf queue work                    # Start worker (default queue)
    $ ftf queue work --queue high       # Start worker for specific queue
    $ ftf queue dashboard               # Start monitoring UI at http://localhost:8080
"""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console

from ftf.core import Container
from ftf.jobs import JobManager, runner, set_container

# Create command group
app = typer.Typer()
console = Console()


@app.command("work")
def queue_work(
    queue_name: str = typer.Option("default", "--queue", "-q", help="Queue name"),
    redis_url: str = typer.Option(
        "redis://localhost:6379", "--redis", help="Redis URL"
    ),
) -> None:
    """
    Start the queue worker to process background jobs.

    This command:
    1. Initializes the IoC Container
    2. Sets up the SAQ worker with the runner function
    3. Starts processing jobs from the queue

    The worker will run indefinitely until stopped with Ctrl+C.

    Args:
        queue_name: Name of the queue to process (default: "default")
        redis_url: Redis connection URL (default: redis://localhost:6379)

    Example:
        $ ftf queue work
        🚀 Worker started for queue: default
        📡 Listening for jobs on redis://localhost:6379

        $ ftf queue work --queue high --redis redis://localhost:6380
        🚀 Worker started for queue: high
    """
    console.print(f"[green]🚀 Starting worker for queue:[/green] {queue_name}")
    console.print(f"[dim]📡 Redis:[/dim] {redis_url}")

    try:
        # Initialize IoC Container
        container = Container()
        set_container(container)

        # Initialize JobManager
        JobManager.initialize(redis_url)

        # Import the runner function
        # SAQ needs the function to be importable, so we register it
        import saq
        from redis.asyncio import Redis

        # Create Redis connection
        redis = Redis.from_url(redis_url, decode_responses=True)

        # Create SAQ queue with the runner function
        queue = saq.Queue(redis, name=queue_name)

        # Create worker with settings
        settings = {
            "queue": queue,
            "functions": [runner],  # Register the universal runner
            "concurrency": 10,  # Process up to 10 jobs concurrently
        }

        # Create and run worker
        worker = saq.Worker(**settings)

        console.print(f"[green]✓ Worker ready![/green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")

        # Run the worker (blocking)
        asyncio.run(worker.start())

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Worker stopped by user[/yellow]")
        sys.exit(0)
    except ImportError as e:
        console.print(f"[red]✗ Import error:[/red] {e}")
        console.print("[yellow]Make sure SAQ is installed:[/yellow] poetry add saq")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error starting worker:[/red] {e}")
        sys.exit(1)


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
        $ ftf queue dashboard
        🎛️  Dashboard started at http://localhost:8080

        $ ftf queue dashboard --port 9000
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
