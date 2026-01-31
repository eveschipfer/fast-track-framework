"""
Fast Track Framework CLI (Sprint 3.0)

This module provides the main entry point for the FTF command-line interface.
It uses Typer for command parsing and Rich for beautiful terminal output.

Educational Note:
    This CLI follows the Laravel Artisan and Django manage.py pattern, providing
    scaffolding commands (make:*) and operational commands (db:*). Unlike those
    frameworks which use custom command classes, we use Typer's decorator-based
    approach which is more Pythonic and type-safe.

Usage:
    poetry run ftf --help
    poetry run ftf make:model User
    poetry run ftf make:repository UserRepository
    poetry run ftf db:seed

Architecture:
    - Typer: CLI framework with automatic help generation
    - Rich: Terminal formatting (colors, tables, progress bars)
    - Command Groups: make, db (extensible for future commands)
"""

import typer
from rich.console import Console

# Create Rich console for beautiful output
console = Console()

# Create main Typer app
app = typer.Typer(
    name="ftf",
    help="Fast Track Framework - Laravel-inspired CLI for Python",
    add_completion=False,  # Disable shell completion for now
    pretty_exceptions_enable=False,  # Disable rich formatting (compatibility issue)
    rich_markup_mode=None,  # Disable rich markup
)


@app.command()
def version() -> None:
    """
    Show the Fast Track Framework version.

    Example:
        $ ftf version
        Fast Track Framework v0.1.0 (Sprint 3.0)
    """
    console.print("[bold green]Fast Track Framework[/bold green] v0.1.0")
    console.print("[dim]Sprint 3.0 - CLI Tooling & Scaffolding[/dim]")


@app.callback()
def main() -> None:
    """
    Fast Track Framework CLI.

    A Laravel-inspired micro-framework built on FastAPI with focus on
    developer experience and educational value.
    """
    pass


# Import and register command groups
# Note: Imports are done here to avoid circular dependencies
def register_commands() -> None:
    """
    Register all command groups.

    This function is called automatically when the CLI is imported.
    It registers the make:* and db:* command groups.

    Educational Note:
        We register commands lazily to avoid circular imports and to
        make the CLI modular. Each command group is in its own file
        and can be developed independently.
    """
    from ftf.cli.commands import db, make

    # Register make:* commands (scaffolding)
    app.add_typer(make.app, name="make", help="Generate framework components")

    # Register db:* commands (database operations)
    app.add_typer(db.app, name="db", help="Database operations")


# Register commands when module is imported
register_commands()


# Educational Note: Entry Point
# When you run `poetry run ftf`, Poetry looks for [tool.poetry.scripts] in
# pyproject.toml which points to this module's `app` object. Typer then
# parses sys.argv and routes to the appropriate command.

if __name__ == "__main__":
    # This allows running the CLI directly with: python -m ftf.cli.main
    app()
