# Database Migrations Guide

Complete guide for managing database migrations in Fast Track Framework using Alembic.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Creating Migrations](#creating-migrations)
5. [Running Migrations](#running-migrations)
6. [Rolling Back](#rolling-back)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)

## Overview

Fast Track Framework uses **Alembic** for database migrations, providing:

- ✅ **Automatic path resolution**: Works in Docker, local, CI/CD without configuration
- ✅ **Model autodiscovery**: Automatically detects all models (framework + app)
- ✅ **Async support**: Native SQLAlchemy 2.0 async migrations
- ✅ **Zero configuration**: Just run Alembic commands
- ✅ **Production-ready**: Clean code, enterprise-grade error handling

### Architecture

```
larafast/
├── alembic.ini                      # Alembic configuration
├── workbench/
│   ├── database/
│   │   └── migrations/
│   │       ├── env.py              # Environment (dynamic path discovery)
│   │       ├── script.py.mako      # Migration template
│   │       └── versions/           # Migration files
│   └── app/
│       └── models/                 # Application models
├── framework/
│   └── fast_query/                  # Framework models (Base)
```

### Key Components

- **env.py**: Dynamic project root discovery, model imports, async execution
- **alembic.ini**: Configuration file with database URL fallback
- **versions/**: Individual migration files (timestamp + description)

## Quick Start

### Prerequisites

Ensure you have Alembic installed (it's already in pyproject.toml):

```bash
# Verify installation
docker exec fast_track_dev bash -c "cd larafast && poetry show alembic"
```

### First Migration

```bash
# Generate initial migration
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic revision --autogenerate -m 'Initial migration'"

# Run migration
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic upgrade head"
```

## Creating Migrations

### Autogenerate (Recommended)

Alembic can automatically detect changes to your models and generate migration files:

```bash
# Create migration with autogenerate
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic revision --autogenerate -m 'Add users table'"

# Create migration without autogenerate (empty migration)
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic revision -m 'Custom migration script'"
```

### When to Use Autogenerate

✅ **Use autogenerate for**:
- Adding new models
- Adding new columns to existing tables
- Changing column types
- Adding indexes
- Adding foreign keys

❌ **Do NOT use autogenerate for**:
- Data migrations (inserting/updating data)
- Complex column renames (requires manual migration)
- Dropping columns with data loss risk
- Performance optimizations (requires manual SQL)

### Manual Migrations

For complex changes or data migrations, create an empty migration and edit manually:

```bash
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic revision -m 'Add status column to users'"
```

Then edit the generated file in `workbench/database/migrations/versions/`:

```python
def upgrade() -> None:
    # Add status column
    op.add_column('users', sa.Column('status', sa.String(20), nullable=False, server_default='active'))

def downgrade() -> None:
    # Remove status column
    op.drop_column('users', 'status')
```

## Running Migrations

### Run All Pending Migrations

```bash
# Upgrade to latest version
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic upgrade head"
```

### Run Specific Number of Migrations

```bash
# Run next 3 migrations
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic upgrade +3"
```

### Run Specific Migration

```bash
# Upgrade to specific revision (hash)
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic upgrade <revision_hash>"
```

### Check Migration Status

```bash
# Show current revision and pending migrations
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic current"

# Show migration history
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic history"
```

## Rolling Back

### Rollback One Migration

```bash
# Rollback one step
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic downgrade -1"
```

### Rollback Multiple Migrations

```bash
# Rollback 3 migrations
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic downgrade -3"
```

### Rollback to Base

```bash
# Rollback all migrations (empty database)
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic downgrade base"
```

### Rollback to Specific Revision

```bash
# Rollback to specific revision
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic downgrade <revision_hash>"
```

## Advanced Usage

### Database URL Configuration

The database URL is configured in three ways (in order of priority):

#### 1. Environment Variables (Production)

```bash
# For MySQL
DB_CONNECTION=mysql
DB_HOST=production-db.example.com
DB_DATABASE=fast_track
DB_USERNAME=app_user
DB_PASSWORD=secure_password
DB_PORT=3306

# For PostgreSQL
DB_CONNECTION=postgresql
DB_HOST=production-db.example.com
DB_DATABASE=fast_track
DB_USERNAME=app_user
DB_PASSWORD=secure_password
DB_PORT=5432

# For SQLite
DB_CONNECTION=sqlite
DB_DATABASE=./app.db
```

#### 2. config/database.py

```python
# workbench/config/database.py
config = {
    "default": "mysql",
    "connections": {
        "mysql": {
            "driver": "mysql+aiomysql",
            "host": "production-db.example.com",
            "port": 3306,
            "database": "fast_track",
            "username": "app_user",
            "password": "secure_password",
        }
    }
}
```

#### 3. alembic.ini Fallback

```ini
# larafast/alembic.ini
sqlalchemy.url = sqlite+aiosqlite:///./app.db
```

### Model Discovery

The `env.py` automatically discovers all models:

#### Framework Models

```python
# fast_query Base is automatically imported
from fast_query import Base
```

#### Application Models

```python
# All models in workbench/app/models/ are imported
from workbench.app.models.user import User
from workbench.app.models.post import Post
from workbench.app.models.comment import Comment
from workbench.app.models.role import Role
from workbench.app.models.product import Product
```

#### Adding New Models

When you create a new model, just import it in `env.py`:

```python
# workbench/app/models/order.py
from fast_query import Base
from sqlalchemy.orm import Mapped, mapped_column

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    total: Mapped[float] = mapped_column()
```

```python
# workbench/database/migrations/env.py
from workbench.app.models.order import Order  # Add this line
```

### Async Migration Support

The framework uses SQLAlchemy 2.0 with async support:

- **SQLite**: `sqlite+aiosqlite:///./app.db`
- **MySQL**: `mysql+aiomysql://user:pass@host:port/database`
- **PostgreSQL**: `postgresql+asyncpg://user:pass@host:port/database`

The `run_async_migrations()` function handles all async operations automatically.

### Offline Mode (SQL Generation)

Generate SQL scripts without connecting to the database:

```bash
# Generate migration SQL (offline mode)
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic upgrade head --sql > migration.sql"
```

This is useful for:
- CI/CD pipelines with no database access
- Code review before applying migrations
- Manual database administration

### Migration Best Practices

#### DO ✅

- Write descriptive migration messages
- Review auto-generated migrations before committing
- Test migrations in development first
- Keep migrations reversible (always implement downgrade())
- Run migrations during deployment, not before
- Use transactions in complex migrations
- Add indexes for frequently queried columns

#### DON'T ❌

- Don't edit existing migration files after they're deployed
- Don't include data migrations in schema migrations (separate them)
- Don't use autogenerate for complex refactors
- Don't hardcode database URLs in migration files
- Don't skip writing downgrade() methods
- Don't commit migration files without testing

### Complex Migration Patterns

#### Column Rename

```python
def upgrade() -> None:
    # Rename column using PostgreSQL-specific syntax
    op.execute("ALTER TABLE users RENAME COLUMN name TO full_name")

def downgrade() -> None:
    op.execute("ALTER TABLE users RENAME COLUMN full_name TO name")
```

#### Data Migration

```python
from sqlalchemy import orm

def upgrade() -> None:
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    # Migrate data from status to status_code
    for user in session.execute("SELECT id, status FROM users"):
        status_map = {'active': 'ACT', 'inactive': 'INA'}
        session.execute(
            "UPDATE users SET status_code = :code WHERE id = :id",
            {"code": status_map[user.status], "id": user.id}
        )

    session.commit()

def downgrade() -> None:
    # Reverse data migration
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    for user in session.execute("SELECT id, status_code FROM users"):
        status_map = {'ACT': 'active', 'INA': 'inactive'}
        session.execute(
            "UPDATE users SET status = :status WHERE id = :id",
            {"status": status_map[user.status_code], "id": user.id}
        )

    session.commit()
```

#### Batch Operations

```python
def upgrade() -> None:
    # Batch operations for large tables
    op.execute("""
        ALTER TABLE orders
        ADD COLUMN status VARCHAR(20) DEFAULT 'pending';

        UPDATE orders SET status = 'completed' WHERE paid_at IS NOT NULL;
    """)

def downgrade() -> None:
    op.drop_column('orders', 'status')
```

## Troubleshooting

### ModuleNotFoundError: No module named 'framework'

**Problem**: Alembic can't find the framework or workbench modules.

**Solution**: The new `env.py` handles this automatically with dynamic path discovery. If it still fails:

```bash
# Check current directory
docker exec fast_track_dev bash -c "cd larafast && pwd"

# Ensure you're running from project root
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic upgrade head"
```

### Target Database Not Found

**Problem**: Database doesn't exist or connection string is wrong.

**Solution**: Check database configuration:

```bash
# Check .env file
cat .env | grep DB_

# Check config/database.py
cat workbench/config/database.py
```

### Migration Already Applied

**Problem**: Trying to run a migration that's already been applied.

**Solution**: Check current migration status:

```bash
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic current"
```

### Foreign Key Errors

**Problem**: Migration fails due to foreign key constraints.

**Solution**: Drop foreign keys before renaming tables/columns:

```python
def upgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_posts_author_id', 'posts', type_='foreignkey')
    # Rename column
    op.alter_column('posts', 'author_id', new_column_name='user_id')
    # Recreate foreign key
    op.create_foreign_key('fk_posts_user_id', 'posts', 'users', ['user_id'], ['id'])
```

### SQLite Lock Errors

**Problem**: SQLite database is locked during migration.

**Solution**: Ensure no other process is using the database:

```bash
# Find processes using the database
lsof app.db

# Kill the process if necessary
kill -9 <PID>
```

### Testing Migrations

```bash
# Create test database
export DB_DATABASE=test_app.db

# Run migrations
docker exec fast_track_dev bash -c "cd larafast && poetry run alembic upgrade head"

# Verify tables
sqlite3 test_app.db ".schema"

# Cleanup
rm test_app.db
```

### Migration Conflicts

**Problem**: Two developers create migrations with the same timestamp.

**Solution**: Rename one of the migration files:

```bash
# Rename conflicting migration
mv 20250207_1430_add_users_table.py 20250207_1431_add_users_table.py
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Run Migrations

on:
  push:
    branches: [main]

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run migrations
        env:
          DB_CONNECTION: postgresql
          DB_HOST: ${{ secrets.DB_HOST }}
          DB_DATABASE: ${{ secrets.DB_DATABASE }}
          DB_USERNAME: ${{ secrets.DB_USERNAME }}
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
        run: |
          poetry run alembic upgrade head
```

## Summary

✅ **Dynamic path resolution**: Works everywhere without configuration
✅ **Model autodiscovery**: Automatically detects all models
✅ **Async support**: Native SQLAlchemy 2.0 async migrations
✅ **Production-ready**: Enterprise-grade error handling
✅ **Clean code**: Well-documented, maintainable migration system

For more information:
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Fast Track Framework Documentation](../README.md)
