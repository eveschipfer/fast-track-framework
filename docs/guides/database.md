# 📦 Fast Query - Database & ORM Guide

Fast Query is a standalone, framework-agnostic ORM package extracted from Fast Track Framework in Sprint 2.5.

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Core Components](#core-components)
- [Repository Pattern](#repository-pattern)
- [Query Builder](#query-builder)
- [Advanced Query Features (Sprint 2.6)](#advanced-query-features-sprint-26) 🆕
  - [Global Scopes (Soft Deletes)](#global-scopes-soft-deletes-)
  - [Local Scopes](#local-scopes-reusable-query-logic-)
  - [Relationship Filters](#relationship-filters-where_has-)
  - [Combining Advanced Features](#combining-advanced-features)
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

**🆕 Sprint 2.6 Advanced Features:**
✅ **Nested Eager Loading** - Dot notation for deep relationships (`"posts.comments.author"`)
✅ **Global Scopes** - Automatic soft delete filtering with `with_trashed()` and `only_trashed()`
✅ **Local Scopes** - Reusable query logic with `.scope(User.active)`
✅ **Relationship Filters** - Filter by relationship existence with `.where_has("posts")`

---

## Quick Start

### With Fast Track Framework

```python
from jtc.http import FastTrackFramework, Inject
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

### Advanced Eager Loading (Sprint 2.6) 🆕

**Nested relationships with dot notation:**

```python
# Load nested relationships using strings
users = await (
    repo.query()
    .with_("posts.comments", "posts.author")
    .get()
)

# Access deeply nested relationships (all loaded!)
for user in users:
    for post in user.posts:
        print(post.author.name)       # Already loaded!
        for comment in post.comments:
            print(comment.content)     # Already loaded!
```

**Mix object-based and string-based:**

```python
# Combine both syntaxes
users = await (
    repo.query()
    .with_(User.posts, "posts.comments.author")
    .get()
)
```

**Benefits:**
- ✅ More concise for deep nesting
- ✅ Validates relationship paths automatically
- ✅ Backward compatible with object-based loading

---

## Advanced Query Features (Sprint 2.6)

### Global Scopes (Soft Deletes) 🆕

**Automatic soft delete filtering** for models with `SoftDeletesMixin`:

```python
# Default: Excludes soft-deleted records automatically
users = await repo.query().get()
# Only returns users where deleted_at IS NULL

# Include soft-deleted records
all_users = await repo.query().with_trashed().get()
# Returns both active and deleted users

# Only soft-deleted records
deleted_users = await repo.query().only_trashed().get()
# Only returns users where deleted_at IS NOT NULL
```

**Works with all terminal methods:**

```python
# Count active users
active_count = await repo.query().count()

# Count all users (including deleted)
total_count = await repo.query().with_trashed().count()

# Count only deleted users
deleted_count = await repo.query().only_trashed().count()

# First active user
user = await repo.query().first()

# First deleted user
deleted = await repo.query().only_trashed().first()
```

**Note:** Global scope only applies to models with `SoftDeletesMixin`. Models without the mixin (like Post, Comment) are unaffected.

---

### Local Scopes (Reusable Query Logic) 🆕

**Define reusable query methods:**

```python
# Define scopes in your model
class User(Base, TimestampMixin, SoftDeletesMixin):
    # ... columns ...

    @staticmethod
    def active(query):
        """Scope to filter active users."""
        return query.where(User.status == "active")

    @staticmethod
    def verified(query):
        """Scope to filter verified users."""
        return query.where(User.email_verified_at.isnot(None))

    @staticmethod
    def premium(query):
        """Scope to filter premium users."""
        return query.where(User.subscription_tier == "premium")
```

**Use scopes in queries:**

```python
# Single scope
active_users = await repo.query().scope(User.active).get()

# Chain multiple scopes
verified_active_users = await (
    repo.query()
    .scope(User.active)
    .scope(User.verified)
    .get()
)

# Combine scopes with other filters
premium_adults = await (
    repo.query()
    .scope(User.premium)
    .where(User.age >= 18)
    .order_by(User.created_at, "desc")
    .get()
)
```

**Use lambdas for inline scopes:**

```python
# Inline lambda scope
adults = await (
    repo.query()
    .scope(lambda q: q.where(User.age >= 18))
    .get()
)
```

**Benefits:**
- ✅ DRY: Define complex logic once, reuse everywhere
- ✅ Composable: Chain multiple scopes
- ✅ Testable: Each scope can be tested independently
- ✅ Readable: Named scopes make queries self-documenting

---

### Relationship Filters (where_has) 🆕

**Filter records based on relationship existence:**

```python
# Get users who have at least one post
users_with_posts = await (
    repo.query()
    .where_has("posts")
    .get()
)

# Get posts that have at least one comment
posts_with_comments = await (
    post_repo.query()
    .where_has("comments")
    .get()
)

# Combine with other filters
active_authors = await (
    repo.query()
    .where(User.status == "active")
    .where_has("posts")
    .order_by(User.created_at, "desc")
    .get()
)
```

**Works with all relationship types:**

```python
# One-to-many (uses SQLAlchemy's any())
users_with_posts = await repo.query().where_has("posts").get()

# Many-to-one (uses SQLAlchemy's has())
posts_with_author = await post_repo.query().where_has("author").get()

# Many-to-many
users_with_roles = await repo.query().where_has("roles").get()
```

**Error handling:**

```python
# Invalid relationship name
await repo.query().where_has("invalid_rel").get()
# Raises: AttributeError: Model User has no relationship 'invalid_rel'

# Not a relationship (just a column)
await repo.query().where_has("name").get()
# Raises: AttributeError: Attribute 'name' on User is not a relationship
```

---

### Combining Advanced Features

**Real-world example using all Sprint 2.6 features:**

```python
# Complex query: Active users with posts, eager load nested relationships
authors = await (
    user_repo.query()
    .scope(User.active)              # Local scope (reusable logic)
    .scope(User.verified)            # Chain multiple scopes
    .where_has("posts")              # Relationship filter
    .with_("posts.comments.author")  # Nested eager loading
    .order_by(User.created_at, "desc")
    .limit(50)
    .get()
)

# Everything loaded! No N+1 queries, all filters applied
for author in authors:
    print(f"Author: {author.name}")  # Active, verified, has posts
    for post in author.posts:
        print(f"  Post: {post.title}")
        for comment in post.comments:
            # Comment author already loaded (nested eager loading)
            print(f"    Comment by {comment.author.name}: {comment.content}")
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
