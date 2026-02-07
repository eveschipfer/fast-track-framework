"""
Authentication Scaffolding Command (Sprint 3.3)

This module provides the make:auth command - a "macro" command that generates
a complete authentication system with a single command.

Educational Note:
    This is similar to Laravel's `php artisan make:auth` which scaffolds
    authentication controllers, views, and routes. We generate:
    - User model with email and password fields
    - UserRepository for database operations
    - LoginRequest and RegisterRequest with validation
    - AuthController with /register, /login, /me endpoints

Usage:
    $ jtc make auth
    ✓ User model created: src/jtc/models/user.py
    ✓ UserRepository created: src/jtc/repositories/user_repository.py
    ✓ LoginRequest created: src/jtc/http/requests/auth/login_request.py
    ✓ RegisterRequest created: src/jtc/http/requests/auth/register_request.py
    ✓ AuthController created: src/jtc/http/controllers/auth_controller.py

    🎉 Authentication scaffolding complete!

    Next steps:
    1. Create migration: ftf make migration create_users_table
    2. Run migrations: ftf db migrate
    3. Register routes in your FastAPI app
"""

from pathlib import Path

import typer
from rich.console import Console

from jtc.cli.commands.make import create_file
from jtc.cli.templates import (
    get_auth_controller_template,
    get_login_request_template,
    get_register_request_template,
    get_user_model_template,
    get_user_repository_template,
)

# Create command group
app = typer.Typer()
console = Console()


@app.command("auth")
def make_auth(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
) -> None:
    """
    Generate a complete authentication system.

    This command creates all the files needed for JWT authentication:
    - User model (with email, password fields)
    - UserRepository (extends BaseRepository)
    - LoginRequest (validates email/password)
    - RegisterRequest (validates registration with unique email check)
    - AuthController (handles /register, /login, /me endpoints)

    Args:
        force: Overwrite existing files if they exist

    Example:
        $ jtc make auth
        ✓ Generated 5 files for authentication

        $ jtc make auth --force
        ✓ Generated 5 files (overwritten)
    """
    console.print("[bold cyan]🔐 Generating authentication system...[/bold cyan]\n")

    files_created = 0
    files_skipped = 0

    # 1. Create User model
    console.print("[dim]Creating User model...[/dim]")
    user_model_path = Path("src/jtc/models/user.py")
    user_model_content = get_user_model_template()

    if create_file(user_model_path, user_model_content, force):
        console.print(f"[green]  ✓ User model created:[/green] {user_model_path}")
        files_created += 1
    else:
        console.print(f"[yellow]  ⊘ File exists:[/yellow] {user_model_path}")
        files_skipped += 1

    # 2. Create UserRepository
    console.print("[dim]Creating UserRepository...[/dim]")
    user_repo_path = Path("src/jtc/repositories/user_repository.py")
    user_repo_content = get_user_repository_template()

    if create_file(user_repo_path, user_repo_content, force):
        console.print(f"[green]  ✓ UserRepository created:[/green] {user_repo_path}")
        files_created += 1
    else:
        console.print(f"[yellow]  ⊘ File exists:[/yellow] {user_repo_path}")
        files_skipped += 1

    # 3. Create auth requests directory
    auth_requests_dir = Path("src/jtc/http/requests/auth")
    auth_requests_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py in auth requests dir
    auth_init_path = auth_requests_dir / "__init__.py"
    if not auth_init_path.exists():
        auth_init_path.write_text('"""Auth request validators."""\n')

    # 4. Create LoginRequest
    console.print("[dim]Creating LoginRequest...[/dim]")
    login_request_path = auth_requests_dir / "login_request.py"
    login_request_content = get_login_request_template()

    if create_file(login_request_path, login_request_content, force):
        console.print(f"[green]  ✓ LoginRequest created:[/green] {login_request_path}")
        files_created += 1
    else:
        console.print(f"[yellow]  ⊘ File exists:[/yellow] {login_request_path}")
        files_skipped += 1

    # 5. Create RegisterRequest
    console.print("[dim]Creating RegisterRequest...[/dim]")
    register_request_path = auth_requests_dir / "register_request.py"
    register_request_content = get_register_request_template()

    if create_file(register_request_path, register_request_content, force):
        console.print(
            f"[green]  ✓ RegisterRequest created:[/green] {register_request_path}"
        )
        files_created += 1
    else:
        console.print(f"[yellow]  ⊘ File exists:[/yellow] {register_request_path}")
        files_skipped += 1

    # 6. Create AuthController
    console.print("[dim]Creating AuthController...[/dim]")
    auth_controller_path = Path("src/jtc/http/controllers/auth_controller.py")
    auth_controller_content = get_auth_controller_template()

    if create_file(auth_controller_path, auth_controller_content, force):
        console.print(
            f"[green]  ✓ AuthController created:[/green] {auth_controller_path}"
        )
        files_created += 1
    else:
        console.print(f"[yellow]  ⊘ File exists:[/yellow] {auth_controller_path}")
        files_skipped += 1

    # Summary
    console.print()
    console.print("[bold green]" + "=" * 60 + "[/bold green]")
    console.print(
        f"[bold green]🎉 Authentication scaffolding complete![/bold green]"
    )
    console.print(f"[green]✓ Created {files_created} files[/green]")
    if files_skipped > 0:
        console.print(f"[yellow]⊘ Skipped {files_skipped} existing files[/yellow]")
        console.print("[dim]Use --force to overwrite existing files[/dim]")
    console.print("[bold green]" + "=" * 60 + "[/bold green]")

    # Next steps
    console.print()
    console.print("[bold cyan]📋 Next Steps:[/bold cyan]\n")
    console.print("[bold]1. Create database migration:[/bold]")
    console.print("   [dim]$[/dim] ftf make migration create_users_table\n")
    console.print("[bold]2. Add these fields to the migration:[/bold]")
    console.print("   [dim]•[/dim] name (String, 100)")
    console.print("   [dim]•[/dim] email (String, 255, unique, indexed)")
    console.print("   [dim]•[/dim] password (String, 255)\n")
    console.print("[bold]3. Run migrations:[/bold]")
    console.print("   [dim]$[/dim] ftf db migrate\n")
    console.print("[bold]4. Register routes in your app:[/bold]")
    console.print("[dim]   from jtc.http.controllers.auth_controller import router")
    console.print("   app.include_router(router)[/dim]\n")
    console.print("[bold]5. Set JWT secret key:[/bold]")
    console.print('   [dim]$[/dim] export JWT_SECRET_KEY="your-secret-key-here"\n')
    console.print("[bold cyan]📖 Documentation:[/bold cyan]")
    console.print("   See docs/guides/authentication.md for usage examples")
