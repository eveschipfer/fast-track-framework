# 🚀 Fast Track Framework

> A Laravel-inspired micro-framework built on top of FastAPI, designed as an educational deep-dive into modern Python architecture patterns.
> This project is an educational deep dive into building production-grade frameworks.
It is safe to experiment with, but not intended as a drop-in replacement for mature frameworks.

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-green.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)](https://www.sqlalchemy.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://img.shields.io/badge/coverage-models%20100%25-brightgreen.svg)](https://github.com/eveschipfer/fast-track-framework)
[![Tests](https://img.shields.io/badge/tests-149%20passed-success.svg)](https://github.com/eveschipfer/fast-track-framework)
[![Sprint](https://img.shields.io/badge/sprint-2.4%20complete-success.svg)](https://github.com/eveschipfer/fast-track-framework)

---

## 🎯 **Project Vision**

Fast Track Framework bridges the gap between FastAPI's async performance and Laravel's developer experience. Built from scratch as a learning journey, this project demonstrates:

- 🏗️ **Modern Python architecture** with strict type safety (MyPy strict mode)
- ⚡ **Async-first design** leveraging Python 3.13+ features
- 🎨 **Laravel-inspired DX** with production-ready IoC Container
- 🗄️ **Repository Pattern** for database access (NOT Active Record)
- 🔍 **Query Builder** with Laravel Eloquent-inspired fluent interface
- 🔗 **Relationships** proven under pressure (N+1 prevention, cascade deletes)
- 🧪 **Test-driven development** with 100% model coverage (149 tests passing)
- 📚 **Educational documentation** explaining every design decision
- 🚀 **Production-ready tooling** (Poetry, Black, Ruff, pre-commit hooks)
- ✅ **Battle-tested** - Relationships validated with stress tests

---

## ✨ **Features**

### 🔥 Current (Sprint 2.4 - Battle-Tested Relationships)

**Core Container:**
- [x] **IoC Container** - Production-grade dependency injection with automatic resolution
- [x] **FastAPI Integration** - Seamless DI with `Inject()` parameter
- [x] **Request Scoping** - Per-request dependency lifecycle with automatic cleanup
- [x] **Lifecycle Management** - Resource cleanup with async context managers
- [x] **Dependency Override** - Full mocking support for testing (15 patterns)
- [x] **Async Concurrency** - Validated isolation under high parallelism

**Database Layer:**
- [x] **SQLAlchemy AsyncEngine** - Connection pooling with automatic driver detection
- [x] **Repository Pattern** - Generic CRUD without Active Record anti-pattern
- [x] **AsyncSession** - Scoped per-request with automatic cleanup
- [x] **Alembic Migrations** - Async migration support with auto-discovery
- [x] **Type-safe Models** - SQLAlchemy 2.0 with Mapped[] types
- [x] **Complete CRUD** - BaseRepository[T] with pagination, filtering, custom queries

**Query Builder (NEW ✨):**
- [x] **Fluent Interface** - Laravel Eloquent-inspired method chaining
- [x] **Filtering Methods** - where, or_where, where_in, where_like, where_between, etc.
- [x] **Ordering** - order_by, latest, oldest with defaults
- [x] **Pagination** - limit, offset, paginate with page/per_page
- [x] **Terminal Methods** - get, first, first_or_fail, count, exists, pluck
- [x] **Eager Loading** - with_() (selectinload) and with_joined() (joinedload)
- [x] **Type Safety** - Generic[T] preserves model type through chain
- [x] **Debug Support** - to_sql() for query inspection

**Relationships (NEW ✨):**
- [x] **One-to-Many** - User has many Posts, Post has many Comments
- [x] **Many-to-Many** - Users belong to many Roles via pivot table
- [x] **Eager Loading** - Prevents N+1 queries with lazy="raise"
- [x] **Cascade Deletes** - Automatic cleanup of child records
- [x] **Type Safety** - Full TYPE_CHECKING support for circular imports

**Quality:**
- [x] **Type-safe** - Strict MyPy compliance (0 errors)
- [x] **149 tests passing** - 38 QueryBuilder + 26 database + 12 relationship stress tests
- [x] **100% model coverage** - All relationships tested under pressure
- [x] **Production tooling** - Poetry, pre-commit hooks, Black, Ruff, MyPy
- [x] **Query Counter** - Validates exact SQL query counts (N+1 prevention proof)

### 🆕 Sprint 2.4 Highlights (Relationship Stress Tests)

- [x] **12 Integration Tests** - Prove relationships work under pressure
- [x] **N+1 Prevention Validated** - 50 posts load in EXACTLY 2 queries (not 51!)
- [x] **Cascade Deletes Proven** - Post deletion cascades to 100 comments correctly
- [x] **QueryCounter Utility** - SQLAlchemy event hooks for exact query counting
- [x] **100% Model Coverage** - All 4 models (User, Post, Comment, Role) fully tested
- [x] **Zero Bugs Found** - All "failures" were correct behavior (IntegrityError protection)

### 🏆 Sprint 2.3 Highlights (Query Builder & Relationships)

- [x] **QueryBuilder[T]** - 22 methods (8 filtering + 3 ordering + 3 pagination + 2 eager loading + 6 terminal)
- [x] **38 New Tests** - All passing with 87% coverage on QueryBuilder
- [x] **4 New Models** - Post, Comment, Role with relationships
- [x] **Alembic Migration** - Auto-generated with foreign keys and pivot table
- [x] **Blog Example** - Complete CRUD API with relationships (`examples/blog_example.py`)
- [x] **Zero Breaking Changes** - 100% backward compatible

### 🗺️ Roadmap (Sprint 2.5+)

**Completed in Sprints 2.2-2.4:**
- [x] ~~SQLModel ORM~~ → **SQLAlchemy 2.0 Native** (bare metal, more powerful)
- [x] ~~Database migrations~~ → **Alembic** (fully integrated)
- [x] ~~Query Builder~~ → **Fluent QueryBuilder[T]** (22 methods)
- [x] ~~Relationships~~ → **One-to-Many, Many-to-Many** (battle-tested)

**Next (Sprint 2.5+):**
- [ ] **Advanced Query Features** - whereHas(), withCount(), subqueries
- [ ] **Service Providers** - Laravel-style bootstrapping
- [ ] **Middleware System** - Built-in auth, CORS, rate limiting
- [ ] **CLI Tool (Artisan-like)** - Code generation (make:model, make:migration, db:seed)
- [ ] **Model Factories & Seeders** - Test data generation
- [ ] **Authentication system** - JWT + OAuth2 patterns
- [ ] **Event dispatcher** - Pub/sub for decoupled architecture
- [ ] **Background jobs** - Async task queue integration
- [ ] **Soft Deletes** - Logical deletion with restore capability

---

## 🏃 **Quick Start**

### Prerequisites

- Python 3.13 or higher
- Poetry (package manager)
- Docker (optional, for development environment)

### Installation

```bash
# Clone the repository
git clone https://github.com/eveschipfer/fast-track-framework.git
cd fast-track-framework/larafast

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Run the Application

```bash
# Start development server
poetry run uvicorn ftf.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
poetry run python -m ftf.main
```

### Run Tests

```bash
# All tests with coverage
poetry run pytest tests/ -v --cov

# Only unit tests
poetry run pytest tests/unit/ -v

# Only integration tests
poetry run pytest tests/integration/ -v

# Generate HTML coverage report
poetry run pytest tests/ --cov --cov-report=html
```

### Code Quality Checks

```bash
# Type checking (strict mode)
poetry run mypy src/

# Code formatting
poetry run black src/ tests/

# Import sorting
poetry run isort src/ tests/

# Linting
poetry run ruff check src/ tests/

# Run all checks at once
poetry run black src/ tests/ && \
poetry run isort src/ tests/ && \
poetry run ruff check src/ tests/ --fix && \
poetry run mypy src/
```

### Hello World Example
```python
from fastapi import APIRouter
from ftf.http import FastTrackFramework, Inject

# Create application with built-in IoC Container
app = FastTrackFramework(
    title="My API",
    version="1.0.0"
)

# Define a service
class UserService:
    def get_user(self, user_id: int):
        return {"id": user_id, "name": "John Doe"}

# Register service in container
app.register(UserService, scope="transient")

# Create router
router = APIRouter()

# Define route with automatic dependency injection
@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    service: UserService = Inject(UserService)  # Auto-injected!
):
    return service.get_user(user_id)

# Include router
app.include_router(router)

# Run with: uvicorn main:app --reload
```

**Test it:**
```bash
# Root endpoint
curl http://localhost:8000/
# {"message":"Welcome to Fast Track Framework! 🚀"}

# API docs
open http://localhost:8000/docs
```

### Database CRUD Example (NEW ✨)

```python
from ftf.http import FastTrackFramework, Inject
from ftf.database import create_engine, AsyncSessionFactory, BaseRepository, Base
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

# Create app
app = FastTrackFramework(title="My CRUD API")

# 1. Setup database
engine = create_engine("sqlite+aiosqlite:///./app.db")
app.container.register(AsyncEngine, scope="singleton")
app.container._singletons[AsyncEngine] = engine

# 2. Register session (scoped per request)
def session_factory() -> AsyncSession:
    factory = AsyncSessionFactory()
    return factory()

app.register(AsyncSession, implementation=session_factory, scope="scoped")

# 3. Define model (SQLAlchemy 2.0 style)
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)

# 4. Create repository
class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

app.register(UserRepository, scope="transient")

# 5. Define routes with automatic injection
@app.post("/users")
async def create_user(
    name: str,
    email: str,
    repo: UserRepository = Inject(UserRepository)  # Auto-injected!
):
    user = User(name=name, email=email)
    return await repo.create(user)

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    repo: UserRepository = Inject(UserRepository)
):
    return await repo.find_or_fail(user_id)  # Auto 404 if not found

@app.get("/users")
async def list_users(
    limit: int = 10,
    repo: UserRepository = Inject(UserRepository)
):
    return await repo.all(limit=limit)

# Run with: poetry run python examples/database_example.py
```

**Test the CRUD API:**
```bash
# Create user
curl -X POST http://localhost:8000/users -d "name=Alice&email=alice@example.com"

# Get user
curl http://localhost:8000/users/1

# List users
curl http://localhost:8000/users

# Complete example: poetry run python examples/database_example.py
```

---

## 🧠 **Core Concepts**

### 1. Dependency Injection Container

Fast Track Framework features a **production-grade IoC container** with automatic dependency resolution:

```python
from ftf.core import Container

# Create container
container = Container()

# Register dependencies with different scopes
container.register(Database, scope="singleton")      # App-wide instance
container.register(UserRepository, scope="transient") # New instance each time
container.register(RequestContext, scope="scoped")    # Per-request instance

# Automatic resolution with nested dependencies
# UserService requires Database and UserRepository → auto-injected
service = container.resolve(UserService)
```

**Key Features:**
- ✅ Type-hint based resolution (no name-based lookups)
- ✅ Three lifetime scopes: `singleton`, `scoped`, `transient`
- ✅ Circular dependency detection with fail-fast errors
- ✅ Async-safe with ContextVars for request scoping
- ✅ Nested dependency resolution
- ✅ **Resource lifecycle management** (automatic cleanup)
- ✅ **Dependency override** (full mocking support)
- ✅ **Async concurrency validated** (100 concurrent requests tested)

**Example with nested dependencies:**
```python
class Database:
    async def close(self):
        # Cleanup connection
        pass

class UserRepository:
    def __init__(self, db: Database):  # Database auto-injected
        self.db = db

class UserService:
    def __init__(self, repo: UserRepository):  # Repository auto-injected
        self.repo = repo

# Just resolve the top-level service
# Container automatically resolves: UserService → UserRepository → Database
container = Container()
container.register(Database, scope="singleton")
container.register(UserRepository)
container.register(UserService)

service = container.resolve(UserService)  # Fully wired!

# Cleanup on shutdown
await container.dispose_all()  # Calls Database.close() automatically
```

### 2. Resource Lifecycle Management (New!)

**Automatic cleanup** of scoped and singleton resources:

```python
from ftf.core import Container

container = Container()
container.register(DatabaseConnection, scope="scoped")

# Pattern 1: Context Manager (Recommended)
async with container.scoped_context():
    db = container.resolve(DatabaseConnection)
    # Use db...
# db.close() called automatically

# Pattern 2: Manual Cleanup
from ftf.core import set_scoped_cache, clear_scoped_cache_async

set_scoped_cache({})
db = container.resolve(DatabaseConnection)
# Use db...
await clear_scoped_cache_async()  # Calls close() on all scoped instances

# Pattern 3: Application Shutdown
await container.dispose_all()  # Cleanup all singletons
```

**Supported cleanup methods:**
- `async def close(self)` - Async cleanup (preferred)
- `def close(self)` - Sync cleanup
- `async def dispose(self)` - Alternative async
- `def dispose(self)` - Alternative sync

### 3. Dependency Override for Testing (New!)

**Complete mocking support** with multiple patterns:

```python
from ftf.core import Container

container = Container()

# Production registration
container.register(Database, PostgresDatabase, scope="singleton")
container.register(UserService)

# Test Pattern 1: Override with Type
container.override(Database, FakeDatabase)
service = container.resolve(UserService)  # Uses FakeDatabase

# Test Pattern 2: Override with Instance (for mocks)
from unittest.mock import Mock

mock_db = Mock(spec=Database)
container.override_instance(Database, mock_db)
service = container.resolve(UserService)  # Uses mock_db

# Test Pattern 3: Temporary Override (Context Manager)
async with container.override_context(Database, FakeDatabase):
    service = container.resolve(UserService)  # Uses FakeDatabase
# Automatic revert to PostgresDatabase

# Test Pattern 4: Cleanup
container.reset_overrides()  # Reset all overrides
container.reset_override(Database)  # Reset specific override
```

**Override priority:**
```
Instance Override (highest)
    ↓
Type Override
    ↓
Registration
    ↓
Fallback Instantiation (lowest)
```

### 4. FastAPI Integration with Inject()

Seamlessly inject dependencies into FastAPI routes:

```python
from ftf.http import FastTrackFramework, Inject

app = FastTrackFramework()
app.register(UserService, scope="transient")

@app.get("/users/{user_id}")
def get_user(
    user_id: int,
    service: UserService = Inject(UserService)  # Magic happens here!
):
    return service.get_user(user_id)
```

**How it works:**
1. `Inject(UserService)` creates a FastAPI `Depends()` resolver
2. Resolver extracts the container from `request.app`
3. Container resolves `UserService` with all dependencies
4. Fully resolved instance is passed to your route handler

### 5. Request-Scoped Dependencies with Automatic Cleanup

Use scoped dependencies for per-request state with **automatic cleanup**:

```python
from ftf.http import FastTrackFramework

app = FastTrackFramework()

# Register scoped dependency
app.register(DatabaseSession, scope="scoped")

# Middleware handles lifecycle automatically
@app.middleware("http")
async def scoped_lifecycle(request, call_next):
    async with app.container.scoped_context():
        response = await call_next(request)
        return response
    # All scoped resources cleaned up here

@app.get("/users")
def list_users(session: DatabaseSession = Inject(DatabaseSession)):
    # Same session instance within this request
    # Automatically cleaned up after request completes
    return session.query(User).all()
```

**Benefits:**
- ✅ One instance per request (not per injection)
- ✅ **Automatic cleanup** after request (close() called)
- ✅ Async-safe with ContextVars
- ✅ No memory leaks
- ✅ Validated under high concurrency

### 6. Repository Pattern (Database Access) - NEW ✨

**WHY NOT ACTIVE RECORD?** Active Record (`user.save()`) requires ContextVar global state and breaks testability in async Python. We use **explicit Repository Pattern** instead.

```python
from ftf.database import create_engine, AsyncSessionFactory, BaseRepository, Base
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

# 1. Define model (SQLAlchemy 2.0 style - type-safe!)
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)

# 2. Create repository (Generic CRUD)
class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):  # Explicit dependency!
        super().__init__(session, User)

    # Add custom queries
    async def find_by_email(self, email: str) -> User | None:
        from sqlalchemy import select
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

# 3. Setup in app
app = FastTrackFramework()

# Register engine (singleton - connection pool)
engine = create_engine("postgresql+asyncpg://user:pass@localhost/db")
app.container.register(AsyncEngine, scope="singleton")
app.container._singletons[AsyncEngine] = engine

# Register session (scoped - one per request)
def session_factory() -> AsyncSession:
    factory = AsyncSessionFactory()
    return factory()

app.register(AsyncSession, implementation=session_factory, scope="scoped")
app.register(UserRepository, scope="transient")

# 4. Use in routes (automatic injection + cleanup)
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    repo: UserRepository = Inject(UserRepository)  # Session auto-injected!
):
    return await repo.find_or_fail(user_id)  # Auto 404 if not found

@app.post("/users")
async def create_user(
    name: str,
    email: str,
    repo: UserRepository = Inject(UserRepository)
):
    user = User(name=name, email=email)
    return await repo.create(user)  # Auto-commit + refresh
```

**BaseRepository provides:**
- ✅ `create(instance)` - Insert with auto-commit
- ✅ `find(id)` - Get by primary key
- ✅ `find_or_fail(id)` - Get or raise 404
- ✅ `all(limit, offset)` - List with pagination
- ✅ `update(instance)` - Update with auto-commit
- ✅ `delete(instance)` - Delete with auto-commit
- ✅ `count()` - Count total records

**Comparison:**

```python
# ❌ Laravel/Eloquent (Active Record) - NOT possible in async Python!
user = User.find(1)        # Where does session come from?
user.name = "Updated"
user.save()                # ContextVar global state required

# ✅ FastTrack (Repository Pattern) - Explicit and testable
repo = UserRepository(session)  # Explicit dependency
user = await repo.find(1)
user.name = "Updated"
await repo.update(user)         # Manual transaction control

# Benefits:
# + Explicit dependencies (testable)
# + Works everywhere (HTTP, CLI, jobs, tests)
# + Manual transaction control
# + Type-safe with MyPy
# + No ContextVar global state
```

**Database Migrations with Alembic:**
```bash
# Create migration
alembic revision --autogenerate -m "Add users table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# See migrations/README.md for complete guide
```

---

## 🏗️ **Architecture**

### Project Structure
```
larafast/
├── src/ftf/
│   ├── core/                          # IoC Container (Sprint 1.2) ✅
│   │   ├── container.py               # Main DI container (152 lines, lifecycle, override)
│   │   ├── exceptions.py              # DI-specific exceptions
│   │   └── __init__.py
│   ├── database/                      # Database Layer (Sprint 2.2) ✅ NEW
│   │   ├── engine.py                  # AsyncEngine singleton (SQLite/PostgreSQL)
│   │   ├── session.py                 # AsyncSession factory (scoped)
│   │   ├── base.py                    # SQLAlchemy declarative base
│   │   ├── repository.py              # Generic CRUD repository
│   │   └── __init__.py
│   ├── models/                        # Database Models (Sprint 2.2) ✅ NEW
│   │   ├── user.py                    # Example User model
│   │   └── __init__.py
│   ├── http/                          # FastAPI Integration (Sprint 2.1) ✅
│   │   ├── app.py                     # FastTrackFramework kernel
│   │   ├── params.py                  # Inject() dependency bridge
│   │   ├── controllers/
│   │   │   ├── welcome_controller.py  # Example controller
│   │   │   └── __init__.py
│   │   ├── middleware/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── exercises/                     # Sprint learning exercises
│   │   ├── sprint_1_1_async_ingestor.py
│   │   ├── sprint_1_2_demo.py
│   │   └── sprint_1_2_active_record_trap.py  # Why NOT Active Record
│   ├── main.py                        # Application entry point ✅
│   └── __init__.py
├── tests/
│   ├── unit/                          # Unit tests (91 tests) ✅
│   │   ├── test_container.py          # Core container tests (37 tests)
│   │   ├── test_container_async.py    # Concurrency tests (12 tests)
│   │   ├── test_container_lifecycle.py # Lifecycle tests (10 tests)
│   │   ├── test_container_override.py  # Override tests (15 tests)
│   │   ├── test_repository.py         # Database CRUD tests (17 tests) ✨ NEW
│   │   └── __init__.py
│   ├── integration/                   # Integration tests (22 tests) ✅
│   │   ├── test_http_integration.py
│   │   ├── test_welcome_controller.py
│   │   ├── test_database_integration.py  # HTTP + DB tests (9 tests) ✨ NEW
│   │   └── __init__.py
│   └── conftest.py
├── examples/                          # Working Examples ✨ NEW
│   ├── database_example.py            # Complete CRUD API (runnable)
│   └── README.md                      # Examples documentation
├── migrations/                        # Alembic Migrations ✨ NEW
│   ├── env.py                         # Alembic environment
│   ├── script.py.mako                 # Migration template
│   ├── versions/                      # Migration files
│   └── README.md                      # Migration guide
├── alembic.ini                        # Alembic configuration ✨ NEW
├── pyproject.toml                     # Poetry + tooling config ✅
├── README.md                          # This file
├── SPRINT_SUMMARY.md                  # Sprint 1.x learnings
├── SPRINT_2_1_SUMMARY.md              # Sprint 2.1 complete guide ✅
├── ASYNC_CONCURRENCY_VALIDATION.md    # Concurrency analysis 🆕
├── LIFECYCLE_MANAGEMENT_VALIDATION.md # Lifecycle analysis 🆕
├── DEPENDENCY_OVERRIDE_VALIDATION.md  # Override analysis 🆕
├── TECHNICAL_DEBT_RESOLUTION.md       # Complete quality report 🆕
└── CONTRIBUTING.md

✅ = Complete    🆕 = New    🚧 = In Progress    ⏳ = Planned
```

### Design Principles

1. **Explicit over Implicit** - Following the Zen of Python
2. **Async-Native** - No sync fallbacks, pure asyncio
3. **Type Safety First** - Leveraging Python's type system
4. **Test-Driven** - Every feature starts with tests
5. **Educational** - Code comments explain "why", not just "what"
6. **Production-Ready** - All critical technical debt resolved

---

## 🧪 **Testing**

We maintain **149 passing tests** with comprehensive unit and integration coverage:

```bash
# Run all tests with coverage
poetry run pytest tests/ -v --cov

# Run specific test suites
poetry run pytest tests/unit/ -v           # Unit tests (91 tests)
poetry run pytest tests/integration/ -v    # Integration tests (58 tests)

# Run Sprint 2.3/2.4 tests
poetry run pytest tests/unit/test_query_builder.py -v              # QueryBuilder (38 tests)
poetry run pytest tests/integration/test_relationships_*.py -v     # Relationships (12 tests)

# Run container test suites
poetry run pytest tests/unit/test_container_async.py -v      # Async tests (12 tests)
poetry run pytest tests/unit/test_container_lifecycle.py -v  # Lifecycle tests (10 tests)
poetry run pytest tests/unit/test_container_override.py -v   # Override tests (15 tests)

# Run with markers
poetry run pytest -m "not slow" -v         # Skip slow tests
poetry run pytest -m integration -v        # Only integration tests
```

### Test Results (Sprint 2.4)

```
========================= 149 tests passed ==========================

Test Breakdown:
- Container tests:        74 tests (core, async, lifecycle, override)
- QueryBuilder tests:     38 tests (filtering, ordering, pagination, eager loading)
- Database tests:         17 tests (CRUD operations)
- Relationship tests:     12 tests (N+1 prevention, cascade deletes)
- HTTP integration:        8 tests (FastAPI + DB)

Coverage Highlights:
- Overall Project:        43.03% (growing with each sprint)
- Models (User/Post/Comment/Role): 100% ✅ (battle-tested)
- QueryBuilder:           87% (production-ready)
- Container:              84.21% (production-ready)
- HTTP Layer:             95.12% (excellent)
```

### Test Philosophy

- **Unit Tests**: Test components in isolation (Container, DI resolution)
- **Integration Tests**: Test FastAPI + Container integration end-to-end
- **Async Tests**: All async code tested with pytest-asyncio (**12 new tests**)
- **Lifecycle Tests**: Resource cleanup validated (**10 new tests**)
- **Override Tests**: Mocking patterns validated (**15 new tests**)
- **Type Safety**: Tests verify type-safe dependency resolution
- **Fixtures**: Shared setup via conftest.py for DRY tests
- **Real Scenarios**: Tests simulate actual HTTP requests with TestClient

### Test Suite Breakdown

| Suite | Tests | Focus | Status |
|-------|-------|-------|--------|
| **Container Tests** |
| `test_container.py` | 37 | Core DI functionality | ✅ Complete |
| `test_container_async.py` | 12 | Concurrency & isolation | ✅ Complete |
| `test_container_lifecycle.py` | 10 | Resource cleanup | ✅ Complete |
| `test_container_override.py` | 15 | Mocking & testing | ✅ Complete |
| **Database Tests (Sprint 2.2)** |
| `test_repository.py` | 17 | CRUD operations | ✅ Complete |
| `test_database_integration.py` | 9 | HTTP + DB integration | ✅ Complete |
| **QueryBuilder Tests (Sprint 2.3)** |
| `test_query_builder.py` | 38 | Fluent interface | ✅ Complete |
| `test_blog_example.py` | 8 | Real-world usage | ✅ Complete |
| **Relationship Tests (Sprint 2.4)** |
| `test_relationships_n_plus_one.py` | 6 | N+1 prevention | ✅ Complete |
| `test_relationships_cascade.py` | 6 | Cascade deletes | ✅ Complete |
| **HTTP Tests** |
| `test_http_integration.py` | 5 | FastAPI routes | ✅ Complete |
| `test_welcome_controller.py` | 4 | Controllers | ✅ Complete |
| **Total** | **149** | **All aspects** | **✅ 100% pass** |

---

## 📚 **Documentation**

### Learning Resources

This project is built as an educational journey. Each sprint has detailed documentation:

**Core Documentation:**
- ✅ [**README.md**](README.md) - This file (quick start & overview)
- ✅ [**SPRINT_SUMMARY.md**](SPRINT_SUMMARY.md) - Sprints 1.1 & 1.2 learnings
- ✅ [**SPRINT_2_1_SUMMARY.md**](SPRINT_2_1_SUMMARY.md) - Complete Sprint 2.1 guide
- ✅ [**CONTRIBUTING.md**](CONTRIBUTING.md) - Contribution guidelines
- 📝 Exercises in `src/ftf/exercises/` - Hands-on learning examples

**Quality Hardening Reports (New!):**
- ✅ [**ASYNC_CONCURRENCY_VALIDATION.md**](ASYNC_CONCURRENCY_VALIDATION.md) - Async isolation analysis
- ✅ [**LIFECYCLE_MANAGEMENT_VALIDATION.md**](LIFECYCLE_MANAGEMENT_VALIDATION.md) - Resource cleanup guide
- ✅ [**DEPENDENCY_OVERRIDE_VALIDATION.md**](DEPENDENCY_OVERRIDE_VALIDATION.md) - Testing patterns guide
- ✅ [**TECHNICAL_DEBT_RESOLUTION.md**](TECHNICAL_DEBT_RESOLUTION.md) - Complete quality report

### API Documentation

Once the application is running:
- **Interactive API docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Root endpoint**: http://localhost:8000/
- **Health check**: http://localhost:8000/health

### Code Examples

Explore working examples in the codebase:
- **Container Usage**: `src/ftf/exercises/sprint_1_2_demo.py`
- **Active Record Anti-pattern**: `src/ftf/exercises/sprint_1_2_active_record_trap.py`
- **Async Patterns**: `src/ftf/exercises/sprint_1_1_async_ingestor.py`
- **FastAPI Integration**: `src/ftf/http/controllers/welcome_controller.py`

---

## 🎓 **Learning Journey**

### Sprint Progress

| Sprint | Focus | Status | Coverage | Tests | Highlights |
|--------|-------|--------|----------|-------|------------|
| 1.1 | Async Python Basics | ✅ Complete | - | Educational | asyncio, gather, semaphores |
| 1.2 | IoC Container | ✅ Complete | 87% | 74 tests | Type-based DI, scopes |
| 1.3 | Tooling & CI/CD | ✅ Complete | - | Config | Poetry, MyPy, Ruff, pre-commit |
| **2.1** | **FastAPI Integration** | ✅ **Complete** | **95%** | **13 tests** | **Inject(), middleware** |
| **2.2** | **Database Foundation** | ✅ **Complete** | **70%** | **26 tests** | **Repository, Alembic** |
| **2.3** | **Query Builder & Relations** | ✅ **Complete** | **87%** | **46 tests** | **Fluent API, Models** |
| **2.4** | **Relationship Stress Tests** | ✅ **Complete** | **100%** | **12 tests** | **N+1 proven, 100% models** |
| 2.5 | Advanced Query Features | ⏳ Planned | - | - | whereHas(), withCount() |
| 3.x | Production Features | ⏳ Planned | - | - | Auth, jobs, CLI |

**Total**: 149 tests passing, 43% overall coverage, models at 100% ✅

### Key Learnings

#### Sprint 1.x - Foundation
- ✅ **Active Record vs Data Mapper** - Why explicit DI beats magic globals
- ✅ **ContextVars** - Async-safe request-scoped state
- ✅ **Type Hints Introspection** - Using `get_type_hints()` for DI
- ✅ **Circular Dependency Detection** - Fail-fast with clear error messages

#### Sprint 2.1 - FastAPI Integration
- ✅ **FastAPI Depends() Bridge** - Integrating custom DI with FastAPI
- ✅ **Request Lifecycle Management** - Scoped dependencies with middleware
- ✅ **Type-Safe DI** - Maintaining type safety with dynamic resolution
- ✅ **Inheritance vs Composition** - When to extend vs wrap frameworks
- ✅ **TestClient Patterns** - Integration testing for web apps

#### Quality Hardening Sprint
- ✅ **Async Concurrency Validation** - ContextVar isolation under load
- ✅ **Resource Lifecycle Management** - Automatic cleanup patterns
- ✅ **Dependency Override** - Complete mocking strategies
- ✅ **Test-Driven Quality** - 37 new tests, zero bugs found
- ✅ **Production Readiness** - All critical technical debt resolved

#### Sprint 2.2-2.4 (Database & Relationships)
- ✅ **SQLAlchemy 2.0 Native** - Async session management (NOT SQLModel)
- ✅ **Repository Pattern** - Explicit DI over Active Record
- ✅ **Fluent Query Builder** - Laravel Eloquent-inspired (22 methods)
- ✅ **Relationship Strategy** - lazy="raise" forces explicit eager loading
- ✅ **N+1 Prevention Proof** - QueryCounter validates EXACT query counts
- ✅ **Stress Testing Philosophy** - "Code that compiles ≠ Code that works"

#### Coming Soon (Sprint 2.5+)
- ⏳ **Advanced Queries** - whereHas(), withCount(), subqueries
- ⏳ **Model Factories** - Test data generation patterns
- ⏳ **Artisan CLI** - make:model, make:migration, db:seed
- ⏳ **Pydantic V2** - Performance optimizations

---

## 🤝 **Contributing**

This is primarily an educational project, but contributions are welcome!

### Development Setup
```bash
# Clone and install
git clone https://github.com/eveschipfer/fast-track-framework.git
cd fast-track-framework/larafast
poetry install

# Setup pre-commit hooks (optional)
poetry run pre-commit install

# Run quality checks before committing
poetry run black src/ tests/
poetry run isort src/ tests/
poetry run ruff check src/ tests/ --fix
poetry run mypy src/
poetry run pytest tests/ -v --cov
```

### Contribution Guidelines

1. **Fork & Branch** - Create feature branches from `main`
2. **Write Tests** - Maintain >85% coverage (current: 88.98%)
3. **Type Hints** - All functions must be type-annotated (strict MyPy)
4. **Conventional Commits** - Use semantic commit messages
5. **Documentation** - Update relevant docs and docstrings
6. **Code Quality** - Ensure Black, isort, Ruff, and MyPy pass

### Quality Standards

- ✅ **Type Safety**: MyPy strict mode must pass
- ✅ **Test Coverage**: >85% coverage required (current: 88.98%)
- ✅ **Code Style**: Black formatting (line length: 88)
- ✅ **Import Order**: isort with Black profile
- ✅ **Linting**: Ruff with 30+ rule categories
- ✅ **Docstrings**: Google-style docstrings for public APIs

---

## 🔗 **Tech Stack**

| Category | Technology | Version | Why? |
|----------|-----------|---------|------|
| **Language** | Python | 3.13+ | Latest features, performance |
| **Web Framework** | FastAPI | 0.128+ | Modern, async-first, type-safe |
| **Package Manager** | Poetry | 1.8+ | Reproducible dependency management |
| **Testing** | Pytest + pytest-asyncio | Latest | Best-in-class testing tools |
| **HTTP Client** | httpx | 0.28+ | TestClient for integration tests |
| **Type Checking** | MyPy (strict mode) | 1.13+ | Zero `Any` types, catch bugs early |
| **Code Formatting** | Black | 24.10+ | Uncompromising code formatter |
| **Import Sorting** | isort | 5.13+ | Consistent import organization |
| **Linting** | Ruff | 0.8+ | Fast Python linter (30+ rules) |
| **Pre-commit** | pre-commit | 4.0+ | Automated quality checks |
| **ORM** | SQLAlchemy | 2.0+ | Native async ORM (bare metal) |
| **Migrations** | Alembic | 1.13+ | ✅ Async migrations (integrated) |
| **CLI** | Typer | Coming | FastAPI's cousin for CLI apps |

---

## 💡 **Inspiration**

This project draws inspiration from:

- **Laravel** - Developer experience and conventions
- **FastAPI** - Modern Python async patterns
- **NestJS** - Dependency injection architecture
- **Ruby on Rails** - Convention over configuration
- **ASP.NET Core** - Scoped service lifetimes

---

## 📊 **Project Metrics**

### Quality Metrics (Sprint 2.4)

| Metric | Value | Status |
|--------|-------|--------|
| **Overall Coverage** | 43.03% | 🟡 Growing (models 100%) |
| **Model Coverage** | 100% | ✅ Battle-tested |
| **Total Tests** | 149 | ✅ Comprehensive |
| **Pass Rate** | 100% | ✅ Perfect |
| **Container Coverage** | 84.21% | ✅ Production-ready |
| **QueryBuilder Coverage** | 87% | ✅ Production-ready |
| **Type Safety** | Strict MyPy | ✅ Enforced |
| **Code Style** | Black + Ruff | ✅ Enforced |
| **Documentation** | 8 guides | ✅ Complete |

### Code Metrics

| Metric | Value |
|--------|-------|
| **Production Code** | ~2,000 lines |
| Container | 152 lines |
| QueryBuilder | 550 lines |
| Repository | 180 lines |
| Models | 110 lines |
| **Test Code** | ~4,200 lines |
| **Documentation** | ~3,500 lines |
| **Test:Code Ratio** | 2.1:1 (excellent) |

---

## 📝 **License**

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **Sebastian Ramirez** - Creator of FastAPI, SQLModel, and Typer
- **Taylor Otwell** - Creator of Laravel
- **Python Community** - For amazing tools and libraries

---

## 🌟 **Star History**

If this project helps your learning journey, consider giving it a star! ⭐

---

## 📬 **Contact**

- **GitHub Issues**: [Report bugs or request features](https://github.com/eveschipfer/fast-track-framework/issues)
- **Discussions**: [Ask questions or share ideas](https://github.com/eveschipfer/fast-track-framework/discussions)

---

<div align="center">

**Built with ❤️ for learning and production use**

[Documentation](SPRINT_2_1_SUMMARY.md) • [Contributing](CONTRIBUTING.md) • [Quality Reports](TECHNICAL_DEBT_RESOLUTION.md)

</div>
