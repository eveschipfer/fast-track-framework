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

from jtc.cli.templates import (
    get_controller_template,
    get_event_template,
    get_factory_template,
    get_job_template,
    get_listener_template,
    get_mailable_template,
    get_middleware_template,
    get_model_template,
    get_provider_template,
    get_repository_template,
    get_request_template,
    get_resource_template,
    get_rule_template,
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


def to_pascal_case(name: str) -> str:
    """
    Convert snake_case or any string to PascalCase.

    Args:
        name: Input string (e.g., "cpf_is_valid", "CpfIsValid")

    Returns:
        PascalCase string (e.g., "CpfIsValid")

    Example:
        >>> to_pascal_case("cpf_is_valid")
        'CpfIsValid'
        >>> to_pascal_case("CpfIsValid")
        'CpfIsValid'
    """
    # If already in PascalCase (no underscores/hyphens, starts with capital), return as-is
    if "_" not in name and "-" not in name and name and name[0].isupper():
        return name

    # Split by underscores/hyphens and capitalize each word (preserve uppercase letters)
    words = name.replace("-", "_").split("_")
    return "".join(word[0].upper() + word[1:] if word else "" for word in words)


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
        $ jtc make:model User
        ✓ Model created: src/jtc/models/user.py

        $ jtc make:model Post --force
        ✓ Model created: src/jtc/models/post.py (overwritten)
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)
    table_name = pluralize(filename)

    # Determine file path (workbench/app/models/)
    file_path = Path("workbench/app/models") / f"{filename}.py"

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
        $ jtc make:repository UserRepository
        ✓ Repository created: src/jtc/repositories/user_repository.py

        $ jtc make:repository PostRepo --model Post
        ✓ Repository created: src/jtc/repositories/post_repo.py
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Auto-detect model name if not provided
    if model is None:
        # Remove "Repository" suffix if present
        model = name.replace("Repository", "").replace("Repo", "")

    # Determine file path (workbench/app/repositories/)
    file_path = Path("workbench/app/repositories") / f"{filename}.py"

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
        $ jtc make:request StoreUserRequest
        ✓ Request created: src/jtc/requests/store_user_request.py

        $ jtc make:request UpdatePostRequest --force
        ✓ Request created: src/jtc/requests/update_post_request.py (overwritten)
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (src/jtc/requests/)
    file_path = Path("src/jtc/requests") / f"{filename}.py"

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


@app.command("resource")
def make_resource(
    name: str,
    model: str = typer.Option(None, "--model", "-m", help="Model name"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate an API Resource for transforming models to JSON.

    This command generates a resource class that transforms database models
    into JSON responses, decoupling your database schema from API format.

    Args:
        name: Name of the resource (e.g., "UserResource", "PostResource")
        model: Name of the model (auto-detected from resource name if not specified)
        force: Overwrite if file already exists

    Example:
        $ jtc make:resource UserResource
        ✓ Resource created: src/jtc/resources/user_resource.py

        $ jtc make:resource PostResource --model Post
        ✓ Resource created: src/jtc/resources/post_resource.py

        $ jtc make:resource UserResource --force
        ✓ Resource created: src/jtc/resources/user_resource.py (overwritten)
    """
    # Auto-detect model name if not specified
    # UserResource -> User, PostResource -> Post
    if model is None:
        # Remove "Resource" suffix if present
        model = name.replace("Resource", "")
        if not model:
            console.print("[red]✗ Cannot auto-detect model name[/red]")
            console.print(
                "[dim]Use --model to specify: jtc make:resource MyResource --model MyModel[/dim]"
            )
            raise typer.Exit(code=1)

    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (src/jtc/resources/)
    file_path = Path("src/jtc/resources") / f"{filename}.py"

    # Generate content
    content = get_resource_template(name, model)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Resource created:[/green] {file_path}")
        console.print(
            f"[dim]Transform {model} models to JSON responses[/dim]"
        )
        console.print(
            f"[dim]Usage: {name}.make({model.lower()}).resolve()[/dim]"
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
        $ jtc make:factory UserFactory
        ✓ Factory created: tests/factories/user_factory.py

        $ jtc make:factory PostFactory --model Post
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
        $ jtc make:seeder UserSeeder
        ✓ Seeder created: tests/seeders/user_seeder.py

        $ jtc make:seeder DatabaseSeeder --force
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

@app.command("controller")
def make_controller(
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a Controller class.

    Args:
        name: Name of the controller (e.g., "UserController")
        force: Overwrite if file already exists

    Example:
        $ jtc make:controller UserController
        ✓ Controller created: workbench/http/controllers/user_controller.py

        $ jtc make:controller User
        ✓ Controller created: workbench/http/controllers/user_controller.py
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)
    resource_name = name.replace("Controller", "").lower() + "s"

    # Determine file path (workbench/http/controllers/)
    file_path = Path("workbench/http/controllers") / f"{filename}.py"

    # Generate content
    content = get_controller_template(name)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Controller created:[/green] {file_path}")
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)


@app.command("provider")
def make_provider(
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a Service Provider.

    Args:
        name: Name of the provider (e.g., "PaymentServiceProvider")
        force: Overwrite if file already exists

    Example:
        $ jtc make:provider PaymentServiceProvider
        ✓ Provider created: workbench/app/providers/payment_service_provider.py

        $ jtc make:provider Analytics --force
        ✓ Provider created: workbench/app/providers/analytics_service_provider.py (overwritten)
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (workbench/app/providers/)
    file_path = Path("workbench/app/providers") / f"{filename}.py"

    # Generate content
    content = get_provider_template(name)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Provider created:[/green] {file_path}")
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
        $ jtc make event UserRegistered
        ✓ Event created: src/jtc/events/user_registered.py

        $ jtc make event OrderPlaced --force
        ✓ Event created: src/jtc/events/order_placed.py (overwritten)
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (src/jtc/events/)
    file_path = Path("src/jtc/events") / f"{filename}.py"

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
        $ jtc make listener SendWelcomeEmail --event UserRegistered
        ✓ Listener created: src/jtc/listeners/send_welcome_email.py

        $ jtc make listener LogUserActivity -e UserRegistered
        ✓ Listener created: src/jtc/listeners/log_user_activity.py
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (src/jtc/listeners/)
    file_path = Path("src/jtc/listeners") / f"{filename}.py"

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
        $ jtc make job SendWelcomeEmail
        ✓ Job created: src/jtc/jobs/send_welcome_email.py

        $ jtc make job ProcessPayment --force
        ✓ Job created: src/jtc/jobs/process_payment.py (overwritten)
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (src/jtc/jobs/)
    file_path = Path("src/jtc/jobs") / f"{filename}.py"

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
        $ jtc make middleware LogRequests
        ✓ Middleware created: src/jtc/http/middleware/log_requests.py

        $ jtc make middleware RateLimiter --force
        ✓ Middleware created: src/jtc/http/middleware/rate_limiter.py (overwritten)

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

    # Determine file path (src/jtc/http/middleware/)
    middleware_dir = Path("src/jtc/http/middleware")
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


@app.command("mail")
def make_mail(
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a Mailable class for sending emails.

    Mailables are responsible for building email content using templates
    or plain text/HTML. They use the Builder Pattern for fluent composition.

    Args:
        name: Name of the mailable (e.g., "WelcomeEmail", "InvoiceEmail")
        force: Overwrite if file already exists

    Example:
        $ jtc make mail WelcomeEmail
        ✓ Mailable created: src/mail/welcome_email.py

        $ jtc make mail InvoiceEmail --force
        ✓ Mailable created: src/mail/invoice_email.py (overwritten)

    Educational Note:
        Mailables combine several design patterns:
        - Builder Pattern: Fluent API for email composition
        - Template Method: Abstract build() method for subclasses
        - Strategy Pattern: Different ways to set content (view/text/html)

        Usage in code:
            ```python
            from mail.welcome_email import WelcomeEmail
            from jtc.mail import Mail

            # Send immediately
            await Mail.send(WelcomeEmail(user))

            # Fluent API
            await Mail.to(user.email).send(WelcomeEmail(user))

            # Queue for background
            await Mail.to(user.email).queue(WelcomeEmail(user))
            ```
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (src/mail/)
    file_path = Path("src/mail") / f"{filename}.py"

    # Generate content
    content = get_mailable_template(name)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Mailable created:[/green] {file_path}")
        console.print()
        console.print("[bold cyan]💡 Usage Example:[/bold cyan]")
        console.print()
        console.print(f"[dim]from mail.{filename} import {name}[/dim]")
        console.print("[dim]from jtc.mail import Mail[/dim]")
        console.print()
        console.print("[dim]# Send immediately[/dim]")
        console.print(f"[dim]await Mail.send({name}(...))[/dim]")
        console.print()
        console.print("[dim]# Queue for background[/dim]")
        console.print(f'[dim]await Mail.to("user@example.com").queue({name}(...))[/dim]')
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
        $ jtc make auth
        🔐 Generating authentication system...
        ✓ User model created: src/jtc/models/user.py
        ✓ UserRepository created: src/jtc/repositories/user_repository.py
        ✓ LoginRequest created: src/jtc/http/requests/auth/login_request.py
        ✓ RegisterRequest created: src/jtc/http/requests/auth/register_request.py
        ✓ AuthController created: src/jtc/http/controllers/auth_controller.py
        🎉 Authentication scaffolding complete!
    """
    # Import here to avoid circular dependency
    from jtc.cli.templates import (
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
    user_model_path = Path("src/jtc/models/user.py")
    if create_file(user_model_path, get_user_model_template(), force):
        console.print(f"[green]  ✓ User model:[/green] {user_model_path}")
        files_created += 1
    else:
        console.print(f"[yellow]  ⊘ Exists:[/yellow] {user_model_path}")
        files_skipped += 1

    # 2. UserRepository
    console.print("[dim]Creating UserRepository...[/dim]")
    user_repo_path = Path("src/jtc/repositories/user_repository.py")
    if create_file(user_repo_path, get_user_repository_template(), force):
        console.print(f"[green]  ✓ UserRepository:[/green] {user_repo_path}")
        files_created += 1
    else:
        console.print(f"[yellow]  ⊘ Exists:[/yellow] {user_repo_path}")
        files_skipped += 1

    # 3. Auth requests directory
    auth_requests_dir = Path("src/jtc/http/requests/auth")
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
    controller_path = Path("src/jtc/http/controllers/auth_controller.py")
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
    console.print("1. Create migration: [dim]jtc make migration create_users_table[/dim]")
    console.print("2. Run migration: [dim]jtc db migrate[/dim]")
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
    This allows users to extend the jtc CLI with custom commands.

    Args:
        name: Name of the command (e.g., "deploy", "backup")
        force: Overwrite if file already exists

    Example:
        $ jtc make:command deploy
        ✓ Command created: src/jtc/cli/commands/deploy.py

        $ jtc make:command backup --force
        ✓ Command created: src/jtc/cli/commands/backup.py (overwritten)

    Educational Note:
        This allows users to create custom commands for their specific needs:
        - Deployment scripts
        - Database backups
        - Data migrations
        - Custom tooling

        Unlike Laravel (which has auto-discovery), you need to manually
        register the command in src/jtc/cli/main.py for now.
    """
    # Convert to snake_case for filename
    filename = to_snake_case(name)

    # Determine file path (src/jtc/cli/commands/)
    file_path = Path("src/jtc/cli/commands") / f"{filename}.py"

    # Generate content from template
    from jtc.cli.templates import get_command_template

    content = get_command_template(name)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Command created:[/green] {file_path}")
        console.print()
        console.print("[bold yellow]⚠️  Manual Registration Required:[/bold yellow]")
        console.print("Add this command to [cyan]src/jtc/cli/main.py[/cyan]:")
        console.print()
        console.print(f"[dim]from jtc.cli.commands.{filename} import app as {filename}_app")
        console.print(f"app.add_typer({filename}_app, name='{name.lower()}')")
        console.print()
        console.print(f"[dim]Then run:[/dim] jtc {name.lower()} --help")
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
        $ jtc make:lang pt_BR
        ✓ Translation file created: src/resources/lang/pt_BR.json

        $ jtc make:lang es --force
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
    from jtc.cli.templates import get_lang_template

    content = get_lang_template(locale)

    # Create file
    if create_file(file_path, content, force):
        console.print(f"[green]✓ Translation file created:[/green] {file_path}")
        console.print()
        console.print("[bold cyan]💡 Next Steps:[/bold cyan]")
        console.print("1. Edit translation keys in the JSON file")
        console.print("2. Use translations in your code:")
        console.print()
        console.print("[dim]from jtc.i18n import trans, set_locale[/dim]")
        console.print(f"[dim]set_locale('{locale}')[/dim]")
        console.print("[dim]message = trans('auth.failed')[/dim]")
        console.print()
        console.print("[dim]Set default locale:[/dim]")
        console.print(f"[dim]export DEFAULT_LOCALE='{locale}'[/dim]")
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)


@app.command("rule")
def make_rule(
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """
    Generate a new Validation Rule class (Pydantic AfterValidator).

    Creates a custom validation rule that can be used with Pydantic v2's
    AfterValidator pattern. The rule is a callable class that validates
    field values and can raise ValueError for validation failures.

    Args:
        name: Name of the validation rule (e.g., "CpfIsValid", "MinAge")
        force: Overwrite if file already exists

    Example:
        $ jtc make:rule CpfIsValid
        ✓ Validation Rule created: src/rules/cpf_is_valid.py

        $ jtc make:rule MinAge --force
        ✓ Validation Rule created: src/rules/min_age.py (overwritten)

    Educational Note:
        This follows Pydantic v2's pattern for custom validators:

        1. The validator is a callable class (implements __call__)
        2. It returns the value if valid (can transform)
        3. It raises ValueError if validation fails
        4. It uses ftf.i18n for multi-language error messages

        Comparison with Laravel:
            Laravel:
                php artisan make:rule Uppercase
                // Implements Rule interface with passes() method

            Fast Track:
                jtc make:rule CpfIsValid
                // Callable class used with Pydantic AfterValidator
    """
    # 1. Prepare naming
    snake_name = to_snake_case(name)
    class_name = to_pascal_case(name)

    # 2. Define path (Default: src/rules)
    directory = Path("src/rules")
    file_path = directory / f"{snake_name}.py"

    # 3. Check existence
    if file_path.exists() and not force:
        console.print(f"[bold red]❌ Rule already exists:[/bold red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)

    # 4. Create directory structure
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "__init__.py").touch(exist_ok=True)  # Ensure it's a package

    # 5. Generate content
    content = get_rule_template(class_name)

    # 6. Write file
    if create_file(file_path, content, force):
        console.print(f"[bold green]✓ Validation Rule created:[/bold green] {file_path}")
        console.print()
        console.print("[bold cyan]💡 Usage Example:[/bold cyan]")
        console.print()
        console.print("[dim]from typing import Annotated[/dim]")
        console.print("[dim]from pydantic import AfterValidator, BaseModel[/dim]")
        console.print(f"[dim]from rules.{snake_name} import {class_name}[/dim]")
        console.print()
        console.print("[dim]class MyModel(BaseModel):[/dim]")
        console.print(f"[dim]    field: Annotated[str, AfterValidator({class_name}())][/dim]")
        console.print()
        console.print("[bold cyan]📚 Learn More:[/bold cyan]")
        console.print("[dim]https://docs.pydantic.dev/latest/concepts/validators/#annotated-validators[/dim]")
    else:
        console.print(f"[red]✗ File already exists:[/red] {file_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(code=1)
