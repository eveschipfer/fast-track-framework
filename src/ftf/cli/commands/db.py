"""
Database Commands (Sprint 3.0)

This module provides db:* commands for database operations like seeding.

Commands:
    - db:seed: Run database seeders

Educational Note:
    These commands wrap async database operations in a sync CLI interface,
    similar to Laravel's php artisan db:seed or Django's manage.py loaddata.
    We use asyncio.run() to execute async code from synchronous CLI commands.
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
        "DatabaseSeeder", "--class", "-c", help="Seeder class name"
    ),
) -> None:
    """
    Run the database seeder.

    This command executes the specified seeder to populate the database
    with test/initial data.

    Args:
        seeder: Name of the seeder class (default: "DatabaseSeeder")

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
        # Run async seeding
        asyncio.run(_run_seeder(seeder))
        console.print("[green]✓ Database seeded successfully[/green]")
    except Exception as e:
        console.print(f"[red]✗ Seeding failed:[/red] {e}")
        raise typer.Exit(code=1)


async def _run_seeder(seeder_name: str) -> None:
    """
    Run the seeder asynchronously.

    This function imports the seeder dynamically and executes it.

    Args:
        seeder_name: Name of the seeder class

    Raises:
        ImportError: If seeder module/class not found
        Exception: If seeding fails

    Educational Note:
        We use dynamic imports here to avoid coupling the CLI to specific
        seeder implementations. This allows users to create custom seeders
        without modifying the CLI code.
    """
    # Import required dependencies
    from fast_query import get_session

    # Add tests/seeders to path if not already there
    seeders_path = Path("tests/seeders")
    if seeders_path not in sys.path:
        sys.path.insert(0, str(seeders_path))

    # Try to import the seeder
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

    # Run the seeder
    async with get_session() as session:
        seeder = seeder_class(session)
        await seeder.run()
        await session.commit()


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
