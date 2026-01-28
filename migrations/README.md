# Database Migrations

This directory contains Alembic database migrations for the Fast Track Framework.

## Quick Start

### Create a New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add users table"

# Create empty migration (for custom SQL)
alembic revision -m "Add custom index"
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +2

# Upgrade to specific revision
alembic upgrade ae1027a6acf
```

### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade ae1027a6acf

# Rollback all migrations
alembic downgrade base
```

### View Migration Status

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## Migration File Structure

```
migrations/
├── README.md           # This file
├── env.py             # Alembic environment configuration
├── script.py.mako     # Template for new migrations
└── versions/          # Migration files (auto-generated)
    ├── 20260127_1234_ae1027a6acf_add_users_table.py
    └── 20260128_0956_def456789ab_add_email_index.py
```

## How Auto-Discovery Works

Alembic automatically detects model changes by:

1. **Importing Base** from `ftf.database`
2. **Importing all models** from `ftf.models` in `env.py`
3. **Comparing metadata** with current database schema
4. **Generating migration** with detected changes

## Example: Adding a New Model

### 1. Create the Model

```python
# src/ftf/models/product.py
from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from ftf.database import Base

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    price: Mapped[float] = mapped_column(Numeric(10, 2))
```

### 2. Export the Model

```python
# src/ftf/models/__init__.py
from .user import User
from .product import Product  # Add this

__all__ = ["User", "Product"]  # Add Product
```

### 3. Generate Migration

```bash
alembic revision --autogenerate -m "Add products table"
```

### 4. Review and Apply

```bash
# Review the generated migration file
cat migrations/versions/*_add_products_table.py

# Apply the migration
alembic upgrade head
```

## Best Practices

### ✅ DO

- **Review auto-generated migrations** before applying
- **Test migrations** on development database first
- **Use descriptive messages** for migration names
- **Keep migrations small** (one logical change per migration)
- **Commit migrations** to version control

### ❌ DON'T

- **Don't edit applied migrations** (create new ones instead)
- **Don't delete migration files** (breaks migration history)
- **Don't skip migrations** (apply them in order)
- **Don't use raw SQL** unless necessary (use Alembic ops)

## Common Operations

### Add Column

```python
def upgrade() -> None:
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))
```

### Remove Column

```python
def upgrade() -> None:
    op.drop_column('users', 'age')
```

### Add Index

```python
def upgrade() -> None:
    op.create_index('ix_users_email', 'users', ['email'])
```

### Rename Table

```python
def upgrade() -> None:
    op.rename_table('old_name', 'new_name')
```

### Custom SQL

```python
def upgrade() -> None:
    op.execute("CREATE INDEX CONCURRENTLY idx_users_name ON users(name)")
```

## Troubleshooting

### "Target database is not up to date"

This means there are unapplied migrations. Run:

```bash
alembic upgrade head
```

### "Can't locate revision identified by 'xyz'"

The migration file may be missing. Check:

```bash
ls migrations/versions/
alembic history
```

### Auto-generate detects no changes

Make sure:
1. Model is imported in `ftf/models/__init__.py`
2. Model inherits from `Base`
3. Database is up to date (`alembic upgrade head`)

### Offline Mode (SQL Scripts)

Generate SQL without applying:

```bash
alembic upgrade head --sql > migration.sql
```

## Environment-Specific Migrations

### Development (SQLite)

```bash
# alembic.ini
sqlalchemy.url = sqlite+aiosqlite:///./dev.db
```

### Production (PostgreSQL)

```bash
# Override with environment variable
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/prod"
alembic -x dbUrl=$DATABASE_URL upgrade head
```

Or modify `env.py` to read from environment variables.

## Integration with FastTrack Framework

The framework automatically handles:
- ✅ Database engine creation
- ✅ Session management (scoped per request)
- ✅ Repository injection
- ✅ Automatic cleanup

Migrations are separate and run manually:
- During deployment (CI/CD pipeline)
- Local development (before running app)
- Database setup (initial schema creation)

## More Information

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Migrations](https://docs.sqlalchemy.org/en/20/core/metadata.html)
- [FastTrack Database Guide](../SPRINT_2_2_DATABASE_IMPLEMENTATION.md)
