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
    get_middleware_template,
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


@app.command("middleware")
def make_middleware(
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a Middleware class for HTTP request processing.

    Middleware allows you to filter HTTP requests entering your application.
    This is useful for logging, authentication, CORS, rate limiting, etc.

    Args:
        name: Name of the middleware (e.g., "LogRequests", "RateLimiter")
        force: Overwrite if file already exists

    Example:
        $ ftf make middleware LogRequests
        ✓ Middleware created: src/ftf/http/middleware/log_requests.py

        $ ftf make middleware RateLimiter --force
        ✓ Middleware created: src/ftf/http/middleware/rate_limiter.py (overwritten)

    Educational Note:
        Middleware follows the "onion" pattern: each layer wraps the next.
        Request flows through middleware layers, then to route handler,
        then response flows back through middleware in reverse order.

        Example middleware flow:
            Request → CORS → Auth → Logging → Route Handler
            Response ← CORS ← Auth ← Logging ← Route Handler
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (src/ftf/http/middleware/)
    middleware_dir = Path("src/ftf/http/middleware")
    middleware_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py if it doesn't exist
    init_file = middleware_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""Custom middleware classes."""\n')

    file_path = middleware_dir / f"{filename}.py"

    # Generate content
    content = get_middleware_template(name)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Middleware created:[/green] {file_path}")
        console.print(
            "[yellow]💡 Register with:[/yellow] app.add_middleware({})".format(name)
        )
        console.print(
            "[dim]Or use BaseHTTPMiddleware for async dispatch method[/dim]"
        )
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)


@app.command("auth")
def make_auth(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a complete authentication system (macro command).

    This command creates all files needed for JWT authentication:
    - User model with email and password fields
    - UserRepository extending BaseRepository
    - LoginRequest and RegisterRequest with validation
    - AuthController with /register, /login, /me endpoints

    This is a "macro" command that generates multiple files at once,
    similar to Laravel's `php artisan make:auth`.

    Args:
        force: Overwrite existing files

    Example:
        $ ftf make auth
        🔐 Generating authentication system...
        ✓ User model created: src/ftf/models/user.py
        ✓ UserRepository created: src/ftf/repositories/user_repository.py
        ✓ LoginRequest created: src/ftf/http/requests/auth/login_request.py
        ✓ RegisterRequest created: src/ftf/http/requests/auth/register_request.py
        ✓ AuthController created: src/ftf/http/controllers/auth_controller.py
        🎉 Authentication scaffolding complete!
    """
    # Import here to avoid circular dependency
    from ftf.cli.templates import (
        get_auth_controller_template,
        get_login_request_template,
        get_register_request_template,
        get_user_model_template,
        get_user_repository_template,
    )

    console.print("[bold cyan]🔐 Generating authentication system...[/bold cyan]\n")

    files_created = 0
    files_skipped = 0

    # 1. User model
    console.print("[dim]Creating User model...[/dim]")
    user_model_path = Path("src/ftf/models/user.py")
    if create_file(user_model_path, get_user_model_template(), force):
        console.print(f"[green]  ✓ User model:[/green] {user_model_path}")
        files_created += 1
    else:
        console.print(f"[yellow]  ⊘ Exists:[/yellow] {user_model_path}")
        files_skipped += 1

    # 2. UserRepository
    console.print("[dim]Creating UserRepository...[/dim]")
    user_repo_path = Path("src/ftf/repositories/user_repository.py")
    if create_file(user_repo_path, get_user_repository_template(), force):
        console.print(f"[green]  ✓ UserRepository:[/green] {user_repo_path}")
        files_created += 1
    else:
        console.print(f"[yellow]  ⊘ Exists:[/yellow] {user_repo_path}")
        files_skipped += 1

    # 3. Auth requests directory
    auth_requests_dir = Path("src/ftf/http/requests/auth")
    auth_requests_dir.mkdir(parents=True, exist_ok=True)
    (auth_requests_dir / "__init__.py").write_text('"""Auth validators."""\n')

    # 4. LoginRequest
    console.print("[dim]Creating LoginRequest...[/dim]")
    login_path = auth_requests_dir / "login_request.py"
    if create_file(login_path, get_login_request_template(), force):
        console.print(f"[green]  ✓ LoginRequest:[/green] {login_path}")
        files_created += 1
    else:
        console.print(f"[yellow]  ⊘ Exists:[/yellow] {login_path}")
        files_skipped += 1

    # 5. RegisterRequest
    console.print("[dim]Creating RegisterRequest...[/dim]")
    register_path = auth_requests_dir / "register_request.py"
    if create_file(register_path, get_register_request_template(), force):
        console.print(f"[green]  ✓ RegisterRequest:[/green] {register_path}")
        files_created += 1
    else:
        console.print(f"[yellow]  ⊘ Exists:[/yellow] {register_path}")
        files_skipped += 1

    # 6. AuthController
    console.print("[dim]Creating AuthController...[/dim]")
    controller_path = Path("src/ftf/http/controllers/auth_controller.py")
    if create_file(controller_path, get_auth_controller_template(), force):
        console.print(f"[green]  ✓ AuthController:[/green] {controller_path}")
        files_created += 1
    else:
        console.print(f"[yellow]  ⊘ Exists:[/yellow] {controller_path}")
        files_skipped += 1

    # Summary
    console.print()
    console.print("[bold green]🎉 Authentication scaffolding complete![/bold green]")
    console.print(f"[green]✓ Created {files_created} files[/green]")
    if files_skipped > 0:
        console.print(f"[yellow]⊘ Skipped {files_skipped} existing files (use --force)[/yellow]")

    # Next steps
    console.print("\n[bold cyan]📋 Next Steps:[/bold cyan]")
    console.print("1. Create migration: [dim]ftf make migration create_users_table[/dim]")
    console.print("2. Run migration: [dim]ftf db migrate[/dim]")
    console.print("3. Set JWT secret: [dim]export JWT_SECRET_KEY='your-secret'[/dim]")
    console.print("4. Register routes: [dim]app.include_router(auth_controller.router)[/dim]")


@app.command("cmd")
def make_command(
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a custom CLI command.

    Creates a new Typer command file that can be registered in the main CLI.
    This allows users to extend the ftf CLI with custom commands.

    Args:
        name: Name of the command (e.g., "deploy", "backup")
        force: Overwrite if file already exists

    Example:
        $ ftf make:command deploy
        ✓ Command created: src/ftf/cli/commands/deploy.py

        $ ftf make:command backup --force
        ✓ Command created: src/ftf/cli/commands/backup.py (overwritten)

    Educational Note:
        This allows users to create custom commands for their specific needs:
        - Deployment scripts
        - Database backups
        - Data migrations
        - Custom tooling

        Unlike Laravel (which has auto-discovery), you need to manually
        register the command in src/ftf/cli/main.py for now.
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (src/ftf/cli/commands/)
    file_path = Path("src/ftf/cli/commands") / f"{filename}.py"

    # Generate content from template
    from ftf.cli.templates import get_command_template

    content = get_command_template(name)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Command created:[/green] {file_path}")
        console.print()
        console.print("[bold yellow]⚠️  Manual Registration Required:[/bold yellow]")
        console.print("Add this command to [cyan]src/ftf/cli/main.py[/cyan]:")
        console.print()
        console.print(f"[dim]from ftf.cli.commands.{filename} import app as {filename}_app")
        console.print(f"app.add_typer({filename}_app, name='{name.lower()}')")
        console.print()
        console.print(f"[dim]Then run:[/dim] ftf {name.lower()} --help")
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)


@app.command("lang")
def make_lang(
    locale: str,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a translation file for a new locale.

    Creates a new JSON translation file with default skeleton translations.
    Translation files are stored in src/resources/lang/{locale}.json.

    Args:
        locale: Locale code (e.g., "pt_BR", "es", "fr", "de")
        force: Overwrite if file already exists

    Example:
        $ ftf make:lang pt_BR
        ✓ Translation file created: src/resources/lang/pt_BR.json

        $ ftf make:lang es --force
        ✓ Translation file created: src/resources/lang/es.json (overwritten)

    Educational Note:
        Translation files use JSON format with dot notation keys:

        {
            "auth.failed": "Credenciais inválidas",
            "validation.required": "O campo :field é obrigatório"
        }

        This is similar to Laravel's translation files but using JSON
        instead of PHP arrays for better portability.
    """
    # Create resources/lang directory if it doesn't exist
    lang_dir = Path("src/resources/lang")
    lang_dir.mkdir(parents=True, exist_ok=True)

    # Determine file path
    file_path = lang_dir / f"{locale}.json"

    # Generate content from template
    from ftf.cli.templates import get_lang_template

    content = get_lang_template(locale)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Translation file created:[/green] {file_path}")
        console.print()
        console.print("[bold cyan]💡 Next Steps:[/bold cyan]")
        console.print("1. Edit translation keys in the JSON file")
        console.print("2. Use translations in your code:")
        console.print()
        console.print("[dim]from ftf.i18n import trans, set_locale[/dim]")
        console.print(f"[dim]set_locale('{locale}')[/dim]")
        console.print("[dim]message = trans('auth.failed')[/dim]")
        console.print()
        console.print("[dim]Set default locale:[/dim]")
        console.print(f"[dim]export DEFAULT_LOCALE='{locale}'[/dim]")
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)
