# 🏗️ IoC Container - Dependency Injection Guide

The Fast Track Framework features a production-grade IoC (Inversion of Control) container with automatic dependency resolution.

## Overview

**Key Features:**
- ✅ **Type-hint based resolution** (not name-based)
- ✅ **Three lifetime scopes**: Singleton, Scoped, Transient
- ✅ **Circular dependency detection**
- ✅ **Async-safe** (using ContextVars)
- ✅ **Resource lifecycle management**
- ✅ **Dependency override** for testing

---

## Lifetime Scopes

### Singleton
Created once for the entire application lifetime.

**Use for:**
- Database engines
- Connection pools
- Configuration objects
- Heavy resources

```python
from ftf import Container

container = Container()
container.register(DatabaseEngine, scope="singleton")

# Same instance every time
db1 = container.resolve(DatabaseEngine)
db2 = container.resolve(DatabaseEngine)
assert db1 is db2  # True
```

### Scoped
Created once per request, shared within that request.

**Use for:**
- Database sessions
- Request context
- User authentication state

```python
# Register session as scoped
app.register(AsyncSession, implementation=session_factory, scope="scoped")

# Within a request, same instance
session1 = container.resolve(AsyncSession)
session2 = container.resolve(AsyncSession)
assert session1 is session2  # True (within same request)

# Different request = different instance
# Automatically cleaned up after request ends
```

### Transient
Created every time it's resolved.

**Use for:**
- Repositories
- Services
- Stateless components

```python
app.register(UserRepository, scope="transient")

# New instance every time
repo1 = container.resolve(UserRepository)
repo2 = container.resolve(UserRepository)
assert repo1 is not repo2  # True
```

---

## Basic Usage

### 1. Register Dependencies

```python
from ftf.http import FastTrackFramework

app = FastTrackFramework()

# Simple registration (transient by default)
app.register(UserService)

# With explicit scope
app.register(DatabaseEngine, scope="singleton")

# With custom implementation
app.register(ICache, implementation=RedisCache, scope="singleton")

# With factory function
def create_session() -> AsyncSession:
    return AsyncSessionFactory()()

app.register(AsyncSession, implementation=create_session, scope="scoped")
```

### 2. Auto-Injection in Routes

```python
from ftf.http import Inject

@app.get("/users")
async def list_users(
    repo: UserRepository = Inject(UserRepository),  # Auto-injected!
    cache: ICache = Inject(ICache)                  # Auto-injected!
):
    # repo and cache are automatically resolved from container
    users = await repo.all(limit=10)
    return users
```

### 3. Manual Resolution

```python
# Direct resolution
service = app.container.resolve(UserService)

# With nested dependencies
# UserService depends on UserRepository
# UserRepository depends on AsyncSession
# All automatically resolved!
service = app.container.resolve(UserService)
```

---

## Automatic Dependency Resolution

The container inspects type hints and automatically resolves dependencies:

```python
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

class UserService:
    def __init__(self, repo: UserRepository, cache: ICache):
        self.repo = repo
        self.cache = cache

# Register all
app.register(AsyncSession, scope="scoped")
app.register(UserRepository, scope="transient")
app.register(ICache, implementation=RedisCache, scope="singleton")
app.register(UserService, scope="transient")

# Resolve UserService
# Container automatically:
# 1. Resolves AsyncSession (scoped)
# 2. Creates UserRepository(session)
# 3. Resolves ICache (singleton)
# 4. Creates UserService(repo, cache)
service = app.container.resolve(UserService)
```

---

## Request-Scoped Dependencies

Scoped dependencies are created once per request and automatically cleaned up:

```python
from ftf.http import FastTrackFramework

app = FastTrackFramework()

# Register scoped session
app.register(AsyncSession, implementation=session_factory, scope="scoped")
app.register(UserRepository, scope="transient")

@app.get("/users")
async def list_users(
    repo: UserRepository = Inject(UserRepository)
):
    # repo.session is the same AsyncSession for this entire request
    users = await repo.all()

    # After response is sent:
    # - Session is automatically committed
    # - Connection returned to pool
    # - Resources cleaned up

    return users
```

**How it works:**

1. **Request starts** → Scoped cache created (ContextVar)
2. **Dependencies resolved** → Scoped instances cached
3. **Request ends** → `clear_scoped_cache_async()` called
4. **Cleanup** → Resources disposed, cache cleared

---

## Circular Dependency Detection

The container detects circular dependencies and fails fast:

```python
class ServiceA:
    def __init__(self, b: ServiceB):
        self.b = b

class ServiceB:
    def __init__(self, a: ServiceA):
        self.a = a

app.register(ServiceA)
app.register(ServiceB)

# Raises CircularDependencyError
try:
    app.container.resolve(ServiceA)
except CircularDependencyError as e:
    print(e)  # "Circular dependency detected: ServiceA -> ServiceB -> ServiceA"
```

---

## Dependency Override (Testing)

Override dependencies for testing:

```python
from ftf import Container

# Production code
container = Container()
container.register(IDatabase, implementation=PostgresDB, scope="singleton")

# In tests
class MockDatabase(IDatabase):
    async def query(self, sql: str):
        return [{"id": 1, "name": "Test"}]

# Override for testing
container.override(IDatabase, MockDatabase())

# Now resolves to mock
db = container.resolve(IDatabase)
assert isinstance(db, MockDatabase)

# Clear override after test
container.clear_overrides()
```

---

## Resource Lifecycle Management

Automatically cleanup resources with async context managers:

```python
from contextlib import asynccontextmanager

class DatabaseSession:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.session = None

    async def __aenter__(self):
        self.session = AsyncSessionFactory()()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()

# Register as scoped
app.register(DatabaseSession, scope="scoped")

# Automatically cleaned up after request
@app.get("/users")
async def list_users(db: DatabaseSession = Inject(DatabaseSession)):
    users = await db.session.execute(select(User))
    return users.scalars().all()
    # Session automatically committed and closed!
```

---

## Advanced Patterns

### Factory Pattern

```python
def create_cache_client() -> ICache:
    if os.getenv("REDIS_URL"):
        return RedisCache(os.getenv("REDIS_URL"))
    else:
        return MemoryCache()

app.register(ICache, implementation=create_cache_client, scope="singleton")
```

### Interface-based Registration

```python
from abc import ABC, abstractmethod

class IEmailService(ABC):
    @abstractmethod
    async def send(self, to: str, body: str):
        pass

class SendGridEmail(IEmailService):
    async def send(self, to: str, body: str):
        # Implementation
        pass

# Register interface → implementation
app.register(IEmailService, implementation=SendGridEmail, scope="singleton")

# Inject by interface
@app.post("/send-email")
async def send_email(
    email_service: IEmailService = Inject(IEmailService)
):
    await email_service.send("user@example.com", "Hello!")
```

### Multiple Implementations

```python
# Register with names
app.container.register(IStorage, implementation=S3Storage, scope="singleton")
app.container._singletons[IStorage] = S3Storage()

# Or use factory to choose at runtime
def storage_factory() -> IStorage:
    storage_type = os.getenv("STORAGE_TYPE", "local")
    if storage_type == "s3":
        return S3Storage()
    else:
        return LocalStorage()

app.register(IStorage, implementation=storage_factory, scope="singleton")
```

---

## Best Practices

### 1. Follow Lifetime Guidelines

```python
# ✅ Correct
app.register(AsyncEngine, scope="singleton")      # Heavy, reusable
app.register(AsyncSession, scope="scoped")        # Request-bound
app.register(UserRepository, scope="transient")   # Stateless, cheap

# ❌ Incorrect
app.register(AsyncSession, scope="singleton")     # Session shared across requests!
app.register(UserRepository, scope="singleton")   # Repository holds stale session!
```

### 2. Use Type Hints

```python
# ✅ Type hints enable auto-resolution
class UserService:
    def __init__(self, repo: UserRepository, cache: ICache):
        self.repo = repo
        self.cache = cache

# ❌ No type hints = manual wiring required
class UserService:
    def __init__(self, repo, cache):
        self.repo = repo
        self.cache = cache
```

### 3. Explicit Dependencies

```python
# ✅ Explicit (testable, clear)
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

# ❌ Implicit global (hard to test, hidden dependency)
class UserService:
    def get_user(self, user_id: int):
        return User.find(user_id)  # Global state!
```

### 4. Test with Overrides

```python
def test_user_service():
    container = Container()

    # Use mock
    mock_repo = MockUserRepository()
    container.override(UserRepository, mock_repo)

    service = container.resolve(UserService)
    # service.repo is now mock_repo

    container.clear_overrides()
```

---

## Troubleshooting

### UnregisteredDependencyError
```python
# Error: UserService not registered
service = container.resolve(UserService)

# Fix: Register it
app.register(UserService)
```

### CircularDependencyError
```python
# Error: A → B → A
# Fix: Use factory or property injection
class ServiceA:
    def __init__(self):
        self._b = None

    @property
    def b(self) -> ServiceB:
        if not self._b:
            self._b = container.resolve(ServiceB)
        return self._b
```

### Scoped Dependency Outside Request
```python
# Error: Trying to resolve scoped dependency without request context
# Fix: Use get_session() manually or ensure inside request
async with get_session() as session:
    repo = UserRepository(session)
    users = await repo.all()
```

---

## See Also

- [Database Guide](database.md) - Using repositories with DI
- [Testing Guide](testing.md) - Testing with mocks and overrides
- [Architecture Decisions](../architecture/decisions.md) - Why IoC?

---

**Next:** Explore the [Database & ORM Guide](database.md)! 🚀
