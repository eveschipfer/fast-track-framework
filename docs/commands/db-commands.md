# Database Commands

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21

This section documents all `db:*` commands used for database operations including migrations, rollbacks, and seeding.

## Overview

Database commands provide essential database management tools similar to Laravel's `php artisan db:*` commands or Django's `manage.py` commands.

**Note**: Sprint 9.0 Modernization - All database commands now use the IoC Container for dependency injection, ensuring consistency between CLI and HTTP application.

---

## db:migrate

Run all pending database migrations.

### Syntax

```bash
jtc db:migrate
```

### Description

Executes all pending Alembic migrations to bring the database schema up to date. This command:
- Reads the database configuration from your config files
- Applies migrations in order from the `workbench/database/migrations` directory
- Uses Alembic as the migration tool

### Prerequisites

- Database connection configured in `config/database.py`
- Alembic configuration file (`alembic.ini`) in project root
- Migration files exist in `workbench/database/migrations`

### Examples

```bash
# Run all pending migrations
jtc db migrate
# Output:
# 🐱 JTC: Sincronizando o banco de dados...
# 📡 Using database: sqlite
# ✅ Banco de dados atualizado com sucesso!
```

### Database Configuration

The command reads configuration from `config/database.py`:

```python
# config/database.py
config = {
    "default": "sqlite",
    "connections": {
        "sqlite": {
            "driver": "sqlite+aiosqlite",
            "database": "workbench/database/app.db"
        },
        "mysql": {
            "driver": "mysql+aiomysql",
            "host": "localhost",
            "port": 3306,
            "database": "fast_track",
            "username": "app_user",
            "password": "secret"
        },
        "postgresql": {
            "driver": "postgresql+asyncpg",
            "host": "localhost",
            "port": 5432,
            "database": "fast_track",
            "username": "app_user",
            "password": "secret"
        }
    }
}
```

### Error Handling

The command will exit with an error if:
- Database connection not found in config
- Migration fails (syntax error, dependency issue, etc.)
- Configuration file is invalid

### Educational Note

Similar to:
- Laravel: `php artisan migrate`
- Django: `python manage.py migrate`

---

## db:rollback

Revert the last database migration(s).

### Syntax

```bash
jtc db:rollback [options]
```

### Options

- `step`: Number of migration steps to rollback (default: 1)

### Description

Reverts database migrations by the specified number of steps. This is useful for:
- Undoing a problematic migration
- Rolling back to test a previous state
- Fixing migration errors

### Examples

```bash
# Rollback the last migration (default: 1 step)
jtc db rollback
# Output:
# ⏪ Revertendo 1 passo(s)...
# 📡 Using database: sqlite
# ✅ Banco de dados revertido com sucesso!

# Rollback 3 migrations
jtc db:rollback --step 3
# Output:
# ⏪ Revertendo 3 passo(s)...
# 📡 Using database: sqlite
# ✅ Banco de dados revertido com sucesso!
```

### Use Cases

```bash
# Undo last migration and reapply
jtc db:rollback
# Edit migration file
jtc db:migrate

# Rollback to specific point
jtc db:rollback --step 5
```

### Educational Note

Similar to:
- Laravel: `php artisan migrate:rollback`
- Django: `python manage.py migrate <app> <migration> --fake`

---

## db:seed

Run database seeders to populate the database with test/initial data.

### Syntax

```bash
jtc db:seed [options]
```

### Options

- `-c, --class`: Seeder class name (default: "DatabaseSeeder")

### Description

Executes a seeder class to populate the database with test or initial data. Seeders are resolved from the IoC Container, allowing dependency injection.

### Prerequisites

- Database migrations have been run
- Seeder class exists in `tests/seeders/` directory
- Seeder class has a `run()` method

### Examples

```bash
# Run default DatabaseSeeder
jtc db seed
# Output:
# Seeding database with DatabaseSeeder...
# ✓ Database seeded successfully

# Run specific seeder
jtc db seed --class UserSeeder
# Output:
# Seeding database with UserSeeder...
# ✓ Database seeded successfully
```

### Creating Seeders

First, create a seeder using the make command:

```bash
jtc make:seeder UserSeeder
```

Then, edit the generated file:

```python
# tests/seeders/user_seeder.py
from fast_query import Seeder, AsyncSession

class UserSeeder(Seeder):
    """Seed users table with test data."""
    
    async def run(self) -> None:
        """Insert test users into database."""
        # Use self.session (injected by Container)
        from app.models import User
        
        user1 = User(name="Alice", email="alice@example.com")
        user2 = User(name="Bob", email="bob@example.com")
        
        self.session.add_all([user1, user2])
        await self.session.commit()
```

### Dependency Injection

**Sprint 9.0**: Seeders are resolved from the IoC Container, allowing:

```python
class UserSeeder(Seeder):
    def __init__(
        self,
        session: AsyncSession,  # Injected by Container
        user_repo: UserRepository  # Injected by Container
    ):
        self.session = session
        self.user_repo = user_repo
    
    async def run(self) -> None:
        # Use injected dependencies
        user = await self.user_repo.create(...)
```

### Multiple Seeders

Create a main `DatabaseSeeder` that calls other seeders:

```python
# tests/seeders/database_seeder.py
from fast_query import Seeder

class DatabaseSeeder(Seeder):
    """Main seeder that runs all seeders."""
    
    async def run(self) -> None:
        """Run all seeders in order."""
        from tests.seeders.user_seeder import UserSeeder
        from tests.seeders.post_seeder import PostSeeder
        
        await UserSeeder(self.session).run()
        await PostSeeder(self.session).run()
```

### Error Handling

The command will fail if:
- Seeder class not found in `tests/seeders/`
- Seeder doesn't inherit from `Seeder` base class
- Seeder doesn't have a `run()` method
- Database errors occur during seeding

### Educational Note

Similar to:
- Laravel: `php artisan db:seed`
- Django: `python manage.py loaddata`

---

## Common Database Workflow

### Typical Development Cycle

```bash
# 1. Create a migration
# (Use Alembic: alembic revision --autogenerate -m "create_users_table")

# 2. Run migrations
jtc db:migrate

# 3. Create a seeder
jtc make:seeder UserSeeder

# 4. Edit the seeder to add test data
# (Edit tests/seeders/user_seeder.py)

# 5. Seed the database
jtc db seed --class UserSeeder

# 6. If something goes wrong, rollback
jtc db:rollback --step 1

# 7. Fix and re-run migration
jtc db:migrate
```

### Database Setup

1. **Configure database** in `config/database.py`
2. **Create initial migration**: `alembic revision --autogenerate -m "init"`
3. **Run migration**: `jtc db:migrate`
4. **Seed database**: `jtc db seed`

### Production Considerations

- Always backup database before running migrations in production
- Test migrations in development/staging first
- Use transactions in migrations for rollback safety
- Review generated migration files before applying

---

## Best Practices

### Migrations

- Use descriptive migration names: `add_email_to_users`, `create_posts_table`
- Keep migrations small and focused
- Never modify existing migration files (create new ones)
- Test migrations in development first

### Seeders

- Make seeders idempotent (can run multiple times safely)
- Use transactions in seeders
- Separate seeders by concern (users, posts, settings)
- Don't seed sensitive data in production

### Rollbacks

- Understand what you're rolling back
- Have a plan for data recovery
- Test rollbacks in development

---

## Troubleshooting

### Migration Errors

```bash
# Error: "Target database is not up to date"
# Solution: Run migration first
jtc db:migrate

# Error: "Connection refused"
# Solution: Check database configuration and ensure database server is running
```

### Seeder Errors

```bash
# Error: "Could not import UserSeeder"
# Solution: Ensure seeder file exists in tests/seeders/
ls tests/seeders/user_seeder.py

# Error: "Class UserSeeder is not defined"
# Solution: Check seeder file has correct class name
cat tests/seeders/user_seeder.py
```

### Container DI Issues (Sprint 9.0)

```bash
# Error: "Could not resolve dependency"
# Solution: Ensure DatabaseServiceProvider is registered
# Check config/app.py has the provider in the list
```

---

## Next Steps

- [Make Commands](make-commands.md) - Generate models, repositories, controllers, etc.
- [Cache Commands](cache-commands.md) - Manage application cache
- [Auth Commands](auth-commands.md) - Authentication utilities
- [Queue Commands](queue-commands.md) - Background job management
- [Test Commands](test-commands.md) - Testing utilities
- [Deploy Commands](deploy-commands.md) - Deployment automation

---

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21
