"""
Scaffolding Commands (Sprint 3.0)

This module provides make:* commands for generating framework components.
These commands automate the creation of models, repositories, form requests,
factories, and seeders with proper structure and imports.

Commands:
    - make:model: Generate a model with mixins
    - make:repository: Generate a repository
    - make:request: Generate a FormRequest with validation
    - make:factory: Generate a factory for test data
    - make:seeder: Generate a seeder

Educational Note:
    These commands enforce architectural standards (e.g., warning docstrings
    in FormRequest.rules()) and reduce boilerplate, making the framework
    feel more like Laravel or Django.
"""

import re
from pathlib import Path

import typer
from rich.console import Console

from ftf.cli.templates import (
    get_event_template,
    get_factory_template,
    get_job_template,
    get_listener_template,
    get_model_template,
    get_repository_template,
    get_request_template,
    get_seeder_template,
)

# Create command group
app = typer.Typer()
console = Console()


def to_snake_case(name: str) -> str:
    """
    Convert PascalCase to snake_case.

    Args:
        name: PascalCase string (e.g., "UserRepository")

    Returns:
        snake_case string (e.g., "user_repository")

    Example:
        >>> to_snake_case("UserRepository")
        'user_repository'
        >>> to_snake_case("StoreUserRequest")
        'store_user_request'
    """
    # Insert underscore before uppercase letters (except first)
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscore before uppercase letters preceded by lowercase
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def pluralize(name: str) -> str:
    """
    Simple pluralization for table names.

    Args:
        name: Singular name (e.g., "user", "post")

    Returns:
        Plural name (e.g., "users", "posts")

    Educational Note:
        This is a very simple implementation. For production, use a library
        like 'inflect'. We keep it simple for the educational framework.

    Example:
        >>> pluralize("user")
        'users'
        >>> pluralize("post")
        'posts'
    """
    if name.endswith("y"):
        return name[:-1] + "ies"
    if name.endswith("s"):
        return name + "es"
    return name + "s"


def create_file(path: Path, content: str, force: bool = False) -> bool:
    """
    Create a file with given content.

    Args:
        path: Path to the file
        content: File content
        force: Overwrite if file exists

    Returns:
        bool: True if file was created, False if it already exists

    Raises:
        OSError: If directory creation fails
    """
    # Create directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file exists
    if path.exists() and not force:
        return False

    # Write file
    path.write_text(content)
    return True


@app.command("model")
def make_model(
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a model with TimestampMixin and SoftDeletesMixin.

    Args:
        name: Name of the model (e.g., "User", "Post")
        force: Overwrite if file already exists

    Example:
        $ ftf make:model User
        ✓ Model created: src/ftf/models/user.py

        $ ftf make:model Post --force
        ✓ Model created: src/ftf/models/post.py (overwritten)
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)
    table_name = pluralize(filename)

    # Determine file path (src/ftf/models/)
    file_path = Path("src/ftf/models") / f"{filename}.py"

    # Generate content
    content = get_model_template(name, table_name)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Model created:[/green] {file_path}")
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)


@app.command("repository")
def make_repository(
    name: str,
    model: str = typer.Option(None, "--model", "-m", help="Model name"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a repository inheriting BaseRepository.

    Args:
        name: Name of the repository (e.g., "UserRepository")
        model: Model name (auto-detected from repository name if not provided)
        force: Overwrite if file already exists

    Example:
        $ ftf make:repository UserRepository
        ✓ Repository created: src/ftf/repositories/user_repository.py

        $ ftf make:repository PostRepo --model Post
        ✓ Repository created: src/ftf/repositories/post_repo.py
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Auto-detect model name if not provided
    if model is None:
        # Remove "Repository" suffix if present
        model = name.replace("Repository", "").replace("Repo", "")

    # Determine file path (src/ftf/repositories/)
    file_path = Path("src/ftf/repositories") / f"{filename}.py"

    # Generate content
    content = get_repository_template(name, model)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Repository created:[/green] {file_path}")
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)


@app.command("request")
def make_request(
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a FormRequest with validation methods.

    This command generates a request with the GOVERNANCE WARNING about
    side effects in rules().

    Args:
        name: Name of the request (e.g., "StoreUserRequest")
        force: Overwrite if file already exists

    Example:
        $ ftf make:request StoreUserRequest
        ✓ Request created: src/ftf/requests/store_user_request.py

        $ ftf make:request UpdatePostRequest --force
        ✓ Request created: src/ftf/requests/update_post_request.py (overwritten)
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (src/ftf/requests/)
    file_path = Path("src/ftf/requests") / f"{filename}.py"

    # Generate content (includes governance warning)
    content = get_request_template(name)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Request created:[/green] {file_path}")
        console.print(
            "[yellow]⚠️  Remember: rules() is for validation only![/yellow]"
        )
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)


@app.command("factory")
def make_factory(
    name: str,
    model: str = typer.Option(None, "--model", "-m", help="Model name"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a factory for test data generation.

    Args:
        name: Name of the factory (e.g., "UserFactory")
        model: Model name (auto-detected from factory name if not provided)
        force: Overwrite if file already exists

    Example:
        $ ftf make:factory UserFactory
        ✓ Factory created: tests/factories/user_factory.py

        $ ftf make:factory PostFactory --model Post
        ✓ Factory created: tests/factories/post_factory.py
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Auto-detect model name if not provided
    if model is None:
        # Remove "Factory" suffix if present
        model = name.replace("Factory", "")

    # Determine file path (tests/factories/)
    file_path = Path("tests/factories") / f"{filename}.py"

    # Generate content
    content = get_factory_template(name, model)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Factory created:[/green] {file_path}")
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)


@app.command("seeder")
def make_seeder(
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a seeder for database seeding.

    Args:
        name: Name of the seeder (e.g., "UserSeeder")
        force: Overwrite if file already exists

    Example:
        $ ftf make:seeder UserSeeder
        ✓ Seeder created: tests/seeders/user_seeder.py

        $ ftf make:seeder DatabaseSeeder --force
        ✓ Seeder created: tests/seeders/database_seeder.py (overwritten)
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (tests/seeders/)
    file_path = Path("tests/seeders") / f"{filename}.py"

    # Generate content
    content = get_seeder_template(name)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Seeder created:[/green] {file_path}")
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)


@app.command("event")
def make_event(
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate an Event class (DTO).

    Events are data containers that represent something that happened in the
    system. They are dispatched through the Event Bus and handled by Listeners.

    Args:
        name: Name of the event (e.g., "UserRegistered", "OrderPlaced")
        force: Overwrite if file already exists

    Example:
        $ ftf make event UserRegistered
        ✓ Event created: src/ftf/events/user_registered.py

        $ ftf make event OrderPlaced --force
        ✓ Event created: src/ftf/events/order_placed.py (overwritten)
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (src/ftf/events/)
    file_path = Path("src/ftf/events") / f"{filename}.py"

    # Generate content
    content = get_event_template(name)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Event created:[/green] {file_path}")
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)


@app.command("listener")
def make_listener(
    name: str,
    event: str = typer.Option(None, "--event", "-e", help="Event name"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a Listener class for handling events.

    Listeners handle specific events and are resolved from the IoC Container,
    allowing dependency injection.

    Args:
        name: Name of the listener (e.g., "SendWelcomeEmail")
        event: Event name this listener handles (e.g., "UserRegistered")
        force: Overwrite if file already exists

    Example:
        $ ftf make listener SendWelcomeEmail --event UserRegistered
        ✓ Listener created: src/ftf/listeners/send_welcome_email.py

        $ ftf make listener LogUserActivity -e UserRegistered
        ✓ Listener created: src/ftf/listeners/log_user_activity.py
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (src/ftf/listeners/)
    file_path = Path("src/ftf/listeners") / f"{filename}.py"

    # Generate content
    event_name = event if event else "Event"
    content = get_listener_template(name, event_name)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Listener created:[/green] {file_path}")
        if event:
            console.print(
                f"[yellow]Remember to register this listener for {event}![/yellow]"
            )
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)


@app.command("job")
def make_job(
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a Job class for background processing.

    Jobs are class-based units of work that can be dispatched to a queue and
    executed asynchronously by workers. Jobs support dependency injection
    through the IoC Container.

    Args:
        name: Name of the job (e.g., "SendWelcomeEmail", "ProcessPayment")
        force: Overwrite if file already exists

    Example:
        $ ftf make job SendWelcomeEmail
        ✓ Job created: src/ftf/jobs/send_welcome_email.py

        $ ftf make job ProcessPayment --force
        ✓ Job created: src/ftf/jobs/process_payment.py (overwritten)
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (src/ftf/jobs/)
    file_path = Path("src/ftf/jobs") / f"{filename}.py"

    # Generate content
    content = get_job_template(name)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Job created:[/green] {file_path}")
        console.print(
            "[yellow]💡 Dispatch with:[/yellow] await {}.dispatch(...)".format(name)
        )
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)
