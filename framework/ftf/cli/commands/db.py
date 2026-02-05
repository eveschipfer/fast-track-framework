"""
Database Commands (Sprint 9.0 - Modernized)

This module provides db:* commands for database operations like seeding.

Sprint 9.0 Changes:
- Removed manual session creation (now uses Container DI)
- Seeds resolved via container.resolve()
- Consistent with HTTP server (same database/engine)

Commands:
    - db:seed: Run database seeders using Container DI

Educational Note:
    These commands wrap async database operations in a sync CLI interface,
    similar to Laravel's php artisan db:seed or Django's manage.py loaddata.

    Sprint 9.0: All commands now use Container for DI, ensuring
    consistency between CLI and HTTP application.
"""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console

# Create command group
app = typer.Typer()
console = Console()


@app.command("seed")
def seed(
    seeder: str = typer.Option(
        "DatabaseSeeder",
        "--class",
        "-c",
        help="Seeder class name"
    ),
) -> None:
    """
    Run the database seeder using Container DI.

    This command executes the specified seeder to populate the database
    with test/initial data. The seeder is resolved from the IoC Container,
    allowing dependencies to be injected via __init__.

    Args:
        seeder: Name of seeder class (default: "DatabaseSeeder")

    Example:
        $ ftf db seed
        Seeding database...
        ✓ Database seeded successfully

        $ ftf db seed --class UserSeeder
        Seeding database with UserSeeder...
        ✓ Database seeded successfully
    """
    console.print(f"[cyan]Seeding database with {seeder}...[/cyan]")

    try:
        # Run async seeding with Container DI
        asyncio.run(_run_seeder(seeder))
        console.print("[green]✓ Database seeded successfully[/green]")
    except Exception as e:
        console.print(f"[red]✗ Seeding failed:[/red] {e}")
        raise typer.Exit(code=1)


async def _run_seeder(seeder_name: str) -> None:
    """
    Run the seeder using Container dependency injection.

    This function imports the seeder dynamically and executes it.
    The seeder is resolved from the Container, allowing dependencies
    to be injected via __init__.

    Args:
        seeder_name: Name of seeder class

    Raises:
        ImportError: If seeder module/class not found
        Exception: If seeding fails

    Educational Note:
        Sprint 9.0: The seeder is resolved from Container, allowing:
        - Dependency injection (UserRepository, etc.)
        - Consistent database access (same AsyncSession)
        - Testability (mock dependencies in tests)

        Before (Sprint 3.0):
            from fast_query import get_session  # Manual session creation
            async with get_session() as session:
                seeder = seeder_class(session)
                await seeder.run()

        After (Sprint 9.0):
            from ftf.core import Container  # Container DI
            container = Container()
            seeder_class = _import_seeder_class(seeder_name)
            # Container resolves the seeder and injects dependencies
            seeder = container.resolve(seeder_class)
            await seeder.run()
    """
    # Import Container for dependency injection
    from ftf.core import Container

    # Create Container singleton
    container = Container()
    container._singletons[Container] = container

    # Import required dependencies
    from sqlalchemy.ext.asyncio import AsyncSession

    # Add tests/seeders to path if not already there
    seeders_path = Path("tests/seeders")
    if seeders_path not in sys.path:
        sys.path.insert(0, str(seeders_path))

    # Try to import the seeder class
    try:
        # Assume seeder is in tests/seeders/<snake_case_name>.py
        module_name = _to_snake_case(seeder_name)

        # Import the module
        if seeders_path.exists():
            module = __import__(module_name, fromlist=[seeder_name])
        else:
            raise ImportError(
                f"Seeders directory not found: {seeders_path}\n"
                f"Create it with: ftf make seeder {seeder_name}"
            )

        # Get the seeder class
        seeder_class = getattr(module, seeder_name)

    except (ImportError, AttributeError) as e:
        raise ImportError(
            f"Could not import {seeder_name}. Make sure:\n"
            f"1. File exists: tests/seeders/{_to_snake_case(seeder_name)}.py\n"
            f"2. Class {seeder_name} is defined in that file\n"
            f"3. Class inherits from Seeder\n\n"
            f"Create it with: ftf make seeder {seeder_name}"
        ) from e

    # Register AsyncSession in Container (for seeder injection)
    # Sprint 9.0: DatabaseServiceProvider has already registered AsyncSession
    # This ensures it's available for DI in seeders

    # Create seeder instance (Container DI!)
    # Note: The seeder __init__ will receive AsyncSession if it has a type hint
    seeder = container.resolve(seeder_class)

    # Run the seeder
    await seeder.run()


def _to_snake_case(name: str) -> str:
    """
    Convert PascalCase to snake_case.

    Args:
        name: PascalCase string

    Returns:
        snake_case string

    Example:
        >>> _to_snake_case("DatabaseSeeder")
        'database_seeder'
    """
    import re

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
