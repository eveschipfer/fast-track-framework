"""
Cache CLI Commands (Sprint 3.7)

Commands for managing the cache system.

Commands:
    - cache:clear: Clear all cached data
    - cache:forget: Remove specific cache key
    - cache:config: Show current cache configuration

Educational Note:
    Laravel Artisan cache commands:
        php artisan cache:clear       # Clear all cache
        php artisan cache:forget key  # Forget specific key
        php artisan config:cache      # Cache config (different)

    Fast Track equivalent:
        ftf cache:clear               # Clear all cache
        ftf cache:forget key          # Forget specific key
        ftf cache:config              # Show cache config
"""

import asyncio
import os

import typer
from rich.console import Console
from rich.table import Table

from jtc.cache import Cache

# Create command group
app = typer.Typer()
console = Console()


@app.command("clear")
def cache_clear() -> None:
    """
    Clear all cached data.

    This removes all cache entries from the active driver.

    Warning:
        This affects ALL cache keys. Use with caution in production.

    Example:
        $ jtc cache:clear
        ✓ Cache cleared successfully!

    Educational Note:
        Laravel:
            php artisan cache:clear

        Fast Track:
            ftf cache:clear

        Use cases:
            - After deployment (clear old cached config)
            - After database changes (clear cached queries)
            - Debugging cache issues
    """
    console.print("[dim]Clearing cache...[/dim]")

    # Run async flush
    asyncio.run(Cache.flush())

    console.print("[bold green]✓ Cache cleared successfully![/bold green]")
    console.print()
    console.print("[dim]Driver:[/dim]", os.getenv("CACHE_DRIVER", "file"))


@app.command("forget")
def cache_forget(key: str) -> None:
    """
    Remove a specific cache key.

    Args:
        key: Cache key to remove

    Example:
        $ jtc cache:forget user:123
        ✓ Cache key 'user:123' removed

        $ jtc cache:forget config:app
        ✓ Cache key 'config:app' removed

    Educational Note:
        This is more surgical than cache:clear.
        Use when you want to invalidate specific cached data.

        Example use cases:
            - User updated: ftf cache:forget user:123
            - Config changed: ftf cache:forget config:app
            - Product updated: ftf cache:forget product:456
    """
    console.print(f"[dim]Removing cache key:[/dim] {key}")

    # Run async forget
    asyncio.run(Cache.forget(key))

    console.print(f"[bold green]✓ Cache key '{key}' removed[/bold green]")


@app.command("config")
def cache_config() -> None:
    """
    Show current cache configuration.

    Displays active driver and configuration from environment variables.

    Example:
        $ jtc cache:config

        Cache Configuration
        ┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃ Setting       ┃ Value                    ┃
        ┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
        │ Driver        │ file                     │
        │ File Path     │ storage/framework/cache  │
        └───────────────┴──────────────────────────┘

    Educational Note:
        This helps debug cache configuration issues.
        Shows which driver is active and its settings.
    """
    console.print("[bold cyan]Cache Configuration[/bold cyan]")
    console.print()

    # Create table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    # Get driver info
    driver = os.getenv("CACHE_DRIVER", "file")
    table.add_row("Driver", driver)

    # Add driver-specific config
    if driver == "file":
        file_path = os.getenv("CACHE_FILE_PATH", "storage/framework/cache")
        table.add_row("File Path", file_path)

    elif driver == "redis":
        table.add_row("Redis Host", os.getenv("REDIS_HOST", "localhost"))
        table.add_row("Redis Port", os.getenv("REDIS_PORT", "6379"))
        table.add_row("Redis DB", os.getenv("REDIS_DB", "0"))
        table.add_row("Redis Prefix", os.getenv("REDIS_CACHE_PREFIX", "ftf_cache:"))
        if os.getenv("REDIS_PASSWORD"):
            table.add_row("Redis Password", "********")

    elif driver == "array":
        table.add_row("Type", "In-memory (testing only)")

    console.print(table)
    console.print()
    console.print("[dim]💡 Change driver in .env:[/dim]")
    console.print("[dim]   CACHE_DRIVER=file|redis|array[/dim]")


@app.command("test")
def cache_test() -> None:
    """
    Test cache functionality.

    Performs basic cache operations to verify the cache is working.

    Example:
        $ jtc cache:test
        Testing cache operations...
        ✓ Put: Stored test value
        ✓ Get: Retrieved test value
        ✓ Increment: Counter works
        ✓ Forget: Removed test value
        ✓ Cache is working correctly!

    Educational Note:
        Use this to verify cache configuration is correct.
        Especially useful after changing drivers or deploying.
    """
    console.print("[bold cyan]Testing cache operations...[/bold cyan]")
    console.print()

    async def run_tests():
        """Run async cache tests."""
        test_key = "test:cache:verification"
        test_value = {"message": "Hello, Cache!", "timestamp": 1234567890}

        try:
            # Test 1: Put
            console.print("[dim]1. Testing put...[/dim]")
            await Cache.put(test_key, test_value, ttl=60)
            console.print("[green]   ✓ Put: Stored test value[/green]")

            # Test 2: Get
            console.print("[dim]2. Testing get...[/dim]")
            retrieved = await Cache.get(test_key)
            if retrieved == test_value:
                console.print("[green]   ✓ Get: Retrieved test value[/green]")
            else:
                console.print("[red]   ✗ Get: Value mismatch[/red]")
                return False

            # Test 3: Increment
            console.print("[dim]3. Testing increment...[/dim]")
            counter_key = "test:cache:counter"
            count1 = await Cache.increment(counter_key)
            count2 = await Cache.increment(counter_key)
            if count2 == count1 + 1:
                console.print("[green]   ✓ Increment: Counter works[/green]")
            else:
                console.print("[red]   ✗ Increment: Counter failed[/red]")
                return False

            # Test 4: Forget
            console.print("[dim]4. Testing forget...[/dim]")
            await Cache.forget(test_key)
            await Cache.forget(counter_key)
            check = await Cache.get(test_key)
            if check is None:
                console.print("[green]   ✓ Forget: Removed test value[/green]")
            else:
                console.print("[red]   ✗ Forget: Failed to remove[/red]")
                return False

            return True

        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            return False

    # Run tests
    success = asyncio.run(run_tests())

    console.print()
    if success:
        console.print("[bold green]✓ Cache is working correctly![/bold green]")
    else:
        console.print("[bold red]✗ Cache tests failed[/bold red]")
        console.print("[dim]Check cache configuration with:[/dim] ftf cache:config")
        raise typer.Exit(code=1)
