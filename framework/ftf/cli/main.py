"""
Fast Track Framework CLI (Sprint 9.0 - Modernized)

This module provides the main entry point for the FTF command-line interface.
It uses Typer for command parsing and Rich for beautiful terminal output.

Sprint 9.0 Changes:
- CLI now operates within Container IoC context
- Loads AppSettings from Pydantic (Sprint 7.0)
- Boots Service Providers (DatabaseServiceProvider, etc.)
- Ensures consistency between CLI and HTTP server

Architecture:
    - Typer: CLI framework with automatic help generation
    - Rich: Terminal formatting (colors, tables, progress bars)
    - Container: IoC container for dependency injection
    - Service Providers: Two-phase boot (register → boot)

Usage:
    poetry run ftf --help
    poetry run ftf db:seed
    poetry run ftf make:model User
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
        Fast Track Framework v1.0.0 (Sprint 9.0)
    """
    console.print("[bold green]Fast Track Framework[/bold green] v1.0.0")
    console.print("[dim]Sprint 9.0 - CLI Modernization & Core Integration[/dim]")


def _boot_framework() -> None:
    """
    Boot the Fast Track Framework with Container and Service Providers.

    This function ensures the CLI operates with the same database connections,
    configuration, and services as the HTTP server.

    Sprint 9.0 Architecture:
        1. Load AppSettings (Pydantic) - Environment configuration
        2. Initialize Container (Singleton) - Dependency injection
        3. Register Service Providers - Two-phase boot (register → boot)
        4. DatabaseServiceProvider configures AsyncEngine/AsyncSession

    Educational Note:
        This creates a "framework client" that operates exactly like the HTTP
        application. Both CLI and HTTP share:
        - Same Container instance
        - Same AppSettings (Pydantic)
        - Same AsyncEngine/AsyncSession from DatabaseServiceProvider
        - Same Service Providers
    """
    from ftf.core import Container
    from workbench.config.settings import AppSettings, settings

    # Step 1: Create/Get Container singleton
    container = Container()
    container._singletons[Container] = container

    # Step 2: Register AppSettings (Sprint 7.0)
    # This makes settings available for DI throughout the framework
    container.register(AppSettings, scope="singleton")
    container._singletons[AppSettings] = settings

    # Step 3: Load and execute Service Providers
    # Providers are registered in config/app.py
    from ftf.config import config

    providers = config("app.providers", [])
    if not providers:
        console.print("[yellow]⚠️  No providers configured in config/app.py[/yellow]")
        console.print("   Using minimal configuration...")
    else:
        console.print(f"[cyan]📦 Booting {len(providers)} service provider(s)...[/cyan]")

        # Import and register each provider
        for provider_spec in providers:
            # Sprint 5.7: Handle string paths (e.g., "ftf.providers.database.DatabaseServiceProvider")
            if isinstance(provider_spec, str):
                provider_class = _import_provider_class(provider_spec)
            else:
                # Backward compatibility: Direct class reference
                provider_class = provider_spec

            # Create provider instance and register in container
            provider = provider_class(container)
            container.register(provider.__class__, scope="singleton")
            container._singletons[provider.__class__] = provider

            # Execute register phase
            console.print(f"[dim]   → {provider.__class__.__name__}: Registering...[/dim]")
            provider.register()

        # Execute boot phase on all providers
        console.print("[cyan]🔧 Bootstrapping service providers...[/cyan]")
        for provider_spec in providers:
            if isinstance(provider_spec, str):
                provider_class = _import_provider_class(provider_spec)
            else:
                provider_class = provider_spec

            # Get provider instance from container
            provider = container.resolve(provider.__class__)
            provider.boot()
            console.print(f"[green]✓ {provider.__class__.__name__}: Booted[/green]")


def _import_provider_class(provider_path: str) -> type:
    """
    Dynamically import a provider class from a string path.

    Args:
        provider_path: Dot-notation path to provider class
                     (e.g., "ftf.providers.database.DatabaseServiceProvider")

    Returns:
        type: The provider class

    Raises:
        ImportError: If provider cannot be imported

    Example:
        >>> _import_provider_class("ftf.providers.database.DatabaseServiceProvider")
        <class 'ftf.providers.database.DatabaseServiceProvider'>
    """
    import importlib
    import sys

    # Split path into module and class name
    parts = provider_path.split(".")
    module_path = ".".join(parts[:-1])
    class_name = parts[-1]

    # Import module
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise ImportError(
            f"Provider module not found: {module_path}\n"
            f"Make sure the provider exists and is installed."
        ) from e

    # Get class from module
    if not hasattr(module, class_name):
        raise ImportError(
            f"Provider class '{class_name}' not found in module '{module_path}'"
        )

    return getattr(module, class_name)


@app.callback()
def main() -> None:
    """
    Fast Track Framework CLI (Sprint 9.0).

    This callback ensures the framework is booted before any command executes.
    
    Boot process:
        1. Load AppSettings (Pydantic configuration)
        2. Initialize Container (Singleton)
        3. Register Service Providers (register → boot)
        4. Providers configure AsyncEngine/AsyncSession

    After booting:
        - Commands can resolve services from Container
        - Commands have access to same database as HTTP server
        - Configuration is consistent across CLI and HTTP

    Educational Note:
        This makes the CLI a "framework client" that operates exactly
        like the HTTP application. The CLI is no longer an isolated
        tool - it's part of the framework.
    """
    # Boot the framework
    _boot_framework()

    console.print("[green]✓ Framework booted successfully![/green]")


# Import and register command groups
# Note: Imports are done here to avoid circular dependencies
def register_commands() -> None:
    """
    Register all command groups.

    This function is called automatically when the CLI is imported.
    It registers the make:*, db:*, queue:*, and cache:* command groups.

    Sprint 9.0: Commands now have access to Container and AppSettings.
    """
    from ftf.cli.commands import cache, db, make, queue

    # Register make:* commands (scaffolding)
    app.add_typer(make.app, name="make", help="Generate framework components")

    # Register db:* commands (database operations)
    app.add_typer(db.app, name="db", help="Database operations")

    # Register queue:* commands (background jobs)
    app.add_typer(queue.app, name="queue", help="Queue worker and dashboard")

    # Register cache:* commands (cache management)
    app.add_typer(cache.app, name="cache", help="Cache management operations")


# Register commands when module is imported
register_commands()


# Educational Note: Entry Point
# When you run `poetry run ftf`, Poetry looks for [tool.poetry.scripts] in
# pyproject.toml which points to this module's `app` object. Typer then
# parses sys.argv and routes to the appropriate command.
if __name__ == "__main__":
    # This allows running the CLI directly with: python -m ftf.cli.main
    app()
