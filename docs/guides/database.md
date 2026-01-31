# 📦 Fast Query - Database & ORM Guide

Fast Query is a standalone, framework-agnostic ORM package extracted from Fast Track Framework in Sprint 2.5.

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Core Components](#core-components)
- [Repository Pattern](#repository-pattern)
- [Query Builder](#query-builder)
- [Mixins](#mixins)
- [Smart Delete](#smart-delete)
- [Standalone Usage](#standalone-usage)

---

## Overview

**Fast Query** provides Laravel Eloquent-inspired ORM functionality for Python with:

✅ **Framework-Agnostic** - Works with FastAPI, Flask, Django, CLI tools
✅ **Repository Pattern** - Type-safe data access without Active Record anti-patterns
✅ **Fluent Query Builder** - Method chaining like Laravel Eloquent
✅ **Auto-Timestamps** - Automatically managed `created_at`/`updated_at`
✅ **Smart Deletes** - Auto-detects soft vs hard delete
✅ **Type-Safe** - Full MyPy support with Generic types

---

## Quick Start

### With Fast Track Framework

```python
from ftf.http import FastTrackFramework, Inject
from fast_query import (
    create_engine, AsyncSessionFactory,
    Base, BaseRepository,
    TimestampMixin, SoftDeletesMixin
)
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

# Create app
app = FastTrackFramework()

# 1. Setup database engine
engine = create_engine("sqlite+aiosqlite:///./app.db")
app.container.register(AsyncEngine, scope="singleton")
app.container._singletons[AsyncEngine] = engine

# 2. Register session factory (scoped per request)
def session_factory() -> AsyncSession:
    return AsyncSessionFactory()()

app.register(AsyncSession, implementation=session_factory, scope="scoped")

# 3. Define model with mixins
class User(Base, TimestampMixin, SoftDeletesMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    # created_at, updated_at, deleted_at automatically added!

# 4. Create repository
class UserRepository(BaseRepository[User]):
    pass

app.register(UserRepository, scope="transient")

# 5. Use in routes with auto-injection
@app.post("/users")
async def create_user(
    name: str,
    email: str,
    repo: UserRepository = Inject(UserRepository)
):
    user = User(name=name, email=email)
    return await repo.create(user)
    # created_at and updated_at automatically set!

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    repo: UserRepository = Inject(UserRepository)
):
    return await repo.find_or_fail(user_id)
    # Auto 404 if not found!

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    repo: UserRepository = Inject(UserRepository)
):
    user = await repo.find_or_fail(user_id)
    await repo.delete(user)
    # Soft delete! Sets deleted_at, record stays in DB
    return {"message": "User soft-deleted"}
```

---

## Core Components

### Engine & Session

**AsyncEngine** - Singleton connection pool
```python
from fast_query import create_engine, get_engine

# Create at startup
engine = create_engine("postgresql+asyncpg://user:pass@localhost/db")

# Get existing engine
engine = get_engine()

# Cleanup on shutdown
await engine.dispose()
```

**AsyncSession** - Request-scoped database session
```python
from fast_query import AsyncSessionFactory, get_session

# Factory for DI integration
factory = AsyncSessionFactory()
session = factory()

# Manual session (for CLI/scripts)
async with get_session() as session:
    # Auto-commit on success, auto-rollback on exception
    user = User(name="Alice")
    session.add(user)
    # Committed automatically
```

---

## Repository Pattern

Generic CRUD repository with type safety:

```python
from fast_query import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    # Add custom query methods
    async def find_by_email(self, email: str) -> User | None:
        return await (
            self.query()
            .where(User.email == email)
            .first()
        )
```

### Built-in Methods

```python
# Create
user = User(name="Alice", email="alice@example.com")
created = await repo.create(user)

# Read
user = await repo.find(123)              # Returns None if not found
user = await repo.find_or_fail(123)      # Raises RecordNotFound
users = await repo.all(limit=10, offset=0)

# Update
user.name = "Bob"
updated = await repo.update(user)

# Delete
await repo.delete(user)                  # Smart delete (soft if mixin present)

# Count
total = await repo.count()
```

---

## Query Builder

Laravel Eloquent-inspired fluent interface:

### Filtering

```python
# Where clauses
users = await (
    repo.query()
    .where(User.age >= 18)
    .where(User.status == "active")
    .get()
)

# OR conditions
users = await (
    repo.query()
    .or_where(
        User.email == "alice@test.com",
        User.email == "bob@test.com"
    )
    .get()
)

# IN / NOT IN
users = await repo.query().where_in(User.id, [1, 2, 3]).get()
users = await repo.query().where_not_in(User.status, ["banned"]).get()

# NULL checks
users = await repo.query().where_null(User.deleted_at).get()
users = await repo.query().where_not_null(User.email_verified_at).get()

# LIKE
users = await repo.query().where_like(User.name, "%alice%").get()

# BETWEEN
users = await repo.query().where_between(User.age, 18, 65).get()
```

### Ordering & Pagination

```python
# Order by
users = await repo.query().order_by(User.created_at, "desc").get()

# Latest / Oldest (uses created_at by default)
users = await repo.query().latest().get()
users = await repo.query().oldest().get()

# Limit & Offset
users = await repo.query().limit(10).offset(20).get()

# Pagination
users = await repo.query().paginate(page=2, per_page=20).get()
```

### Terminal Methods

```python
# Get all results
users = await repo.query().where(User.active == True).get()

# Get first
user = await repo.query().where(User.email == "alice@example.com").first()

# Get first or fail (raises RecordNotFound)
user = await repo.query().where(User.id == 123).first_or_fail()

# Count
count = await repo.query().where(User.status == "active").count()

# Exists
has_users = await repo.query().exists()

# Pluck (extract single column)
emails = await repo.query().pluck(User.email)
# ['alice@example.com', 'bob@example.com', ...]
```

### Eager Loading

Prevent N+1 queries:

```python
# Load relationships
users = await (
    repo.query()
    .with_(User.posts, User.roles)  # selectinload (separate queries)
    .get()
)

# Or use JOINs
users = await (
    repo.query()
    .with_joined(User.posts)  # joinedload (single query)
    .get()
)
```

---

## Mixins

### TimestampMixin

Auto-managed UTC timestamps:

```python
from fast_query import TimestampMixin

class Post(Base, TimestampMixin):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    # created_at and updated_at automatically added!

# Usage
post = Post(title="My Post")
await repo.create(post)
print(post.created_at)  # 2026-01-30 22:30:15.123456+00:00
print(post.updated_at)  # 2026-01-30 22:30:15.123456+00:00

# On update
post.title = "Updated"
await repo.update(post)
print(post.updated_at)  # 2026-01-30 22:35:20.789012+00:00 (updated!)
```

### SoftDeletesMixin

Soft delete functionality:

```python
from fast_query import SoftDeletesMixin

class User(Base, SoftDeletesMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    # deleted_at and is_deleted automatically added!

# Soft delete
user = await repo.find(123)
await repo.delete(user)
# Sets deleted_at = now(), record stays in database

# Check if deleted
if user.is_deleted:
    print("User was soft-deleted")

# Restore
user.deleted_at = None
await repo.update(user)

# Query excluding soft-deleted
active_users = await (
    repo.query()
    .where(User.deleted_at.is_(None))
    .get()
)

# Query only soft-deleted
deleted_users = await (
    repo.query()
    .where(User.deleted_at.isnot(None))
    .get()
)
```

---

## Smart Delete

Repository automatically detects if model has `SoftDeletesMixin`:

```python
# Model WITHOUT soft deletes
class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)

await repo.delete(tag)  # Hard delete (DELETE FROM tags WHERE id = ?)

# Model WITH soft deletes
class User(Base, SoftDeletesMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)

await repo.delete(user)  # Soft delete (UPDATE users SET deleted_at = NOW() WHERE id = ?)
```

**Implementation** (inside `BaseRepository.delete()`):
```python
if isinstance(instance, SoftDeletesMixin):
    # Soft delete
    instance.deleted_at = datetime.now(timezone.utc)
    await self.session.commit()
else:
    # Hard delete
    await self.session.delete(instance)
    await self.session.commit()
```

---

## Standalone Usage

Fast Query works without any web framework:

```python
from fast_query import (
    create_engine, get_session,
    Base, BaseRepository,
    TimestampMixin, SoftDeletesMixin
)

# 1. Create engine
engine = create_engine("sqlite+aiosqlite:///./myapp.db")

# 2. Define model
class User(Base, TimestampMixin, SoftDeletesMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

# 3. Create repository
class UserRepository(BaseRepository[User]):
    pass

# 4. Use in script/CLI/background job
async def main():
    async with get_session() as session:
        repo = UserRepository(session)

        # Create
        user = User(name="Alice")
        await repo.create(user)

        # Query
        active = await (
            repo.query()
            .where(User.deleted_at.is_(None))
            .latest()
            .limit(10)
            .get()
        )

        # Soft delete
        await repo.delete(user)

import asyncio
asyncio.run(main())
```

**Use Cases:**
- 📝 CLI tools and scripts
- ⚙️ Background jobs (Celery, RQ)
- 🔄 ETL pipelines
- 🧪 Data migration scripts
- 🌐 Flask, Django, Starlette apps

---

## Exception Handling

Fast Query uses framework-agnostic exceptions:

```python
from fast_query import RecordNotFound

try:
    user = await repo.find_or_fail(999)
except RecordNotFound as e:
    print(f"Model: {e.model_name}")     # "User"
    print(f"ID: {e.identifier}")        # 999
    print(f"Message: {e.message}")      # "User not found: 999"
```

**With Fast Track Framework**, `RecordNotFound` is automatically converted to HTTP 404:

```python
@app.get("/users/{user_id}")
async def get_user(user_id: int, repo: UserRepository = Inject(UserRepository)):
    return await repo.find_or_fail(user_id)
    # Raises RecordNotFound → Auto-converted to 404 JSON response
```

---

## Best Practices

### 1. Use Type Hints
```python
from typing import Optional

class UserRepository(BaseRepository[User]):
    async def find_by_email(self, email: str) -> Optional[User]:
        return await self.query().where(User.email == email).first()
```

### 2. Custom Repository Methods
```python
class UserRepository(BaseRepository[User]):
    async def find_active_adults(self) -> list[User]:
        return await (
            self.query()
            .where(User.age >= 18)
            .where(User.deleted_at.is_(None))
            .order_by(User.created_at, "desc")
            .get()
        )
```

### 3. Eager Load Relationships
```python
# Bad (N+1 query problem)
users = await repo.all()
for user in users:
    print(user.posts)  # New query for each user!

# Good (2 queries total)
users = await repo.query().with_(User.posts).get()
for user in users:
    print(user.posts)  # Already loaded!
```

### 4. Exclude Soft Deleted by Default
```python
class UserRepository(BaseRepository[User]):
    def query_active(self):
        return self.query().where(User.deleted_at.is_(None))

# Usage
active_users = await repo.query_active().get()
```

---

## See Also

- [IoC Container Guide](container.md) - Dependency Injection integration
- [Testing Guide](testing.md) - Testing repositories and queries
- [Architecture Decisions](../architecture/decisions.md) - Why Repository Pattern?

---

**Next Steps:** Learn about the [IoC Container](container.md) for seamless dependency injection! 🚀
