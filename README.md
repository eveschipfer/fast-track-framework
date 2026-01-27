# 🚀 Fast Track Framework

> A Laravel-inspired micro-framework built on top of FastAPI, designed as an educational deep-dive into modern Python architecture patterns.

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-green.svg)](https://fastapi.tiangolo.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://img.shields.io/badge/coverage-97.42%25-brightgreen.svg)](https://github.com/eveschipfer/fast-track-framework)

---

## 🎯 **Project Vision**

Fast Track Framework bridges the gap between FastAPI's async performance and Laravel's developer experience. Built from scratch as a learning journey, this project demonstrates:

- 🏗️ **Modern Python architecture** with strict type safety (MyPy strict mode)
- ⚡ **Async-first design** leveraging Python 3.13+ features
- 🎨 **Laravel-inspired DX** with IoC Container and dependency injection
- 🧪 **Test-driven development** with 97.42% coverage
- 📚 **Educational documentation** explaining every design decision
- 🚀 **Production-ready tooling** (Poetry, Black, Ruff, pre-commit hooks)

---

## ✨ **Features**

### 🔥 Current (Sprint 2.1 - FastAPI Integration)

- [x] **IoC Container** - Dependency injection with automatic resolution
- [x] **FastAPI Integration** - Seamless DI with `Inject()` parameter
- [x] **Request Scoping** - Per-request dependency lifecycle management
- [x] **Async-first** - Built on asyncio with proper context management
- [x] **Type-safe** - Strict MyPy compliance, 97.42% test coverage
- [x] **Production tooling** - Poetry, pre-commit hooks, Black, Ruff, MyPy

### 🚧 In Progress (Sprint 2.x - Database & ORM)

- [ ] **Eloquent-inspired ORM** - SQLModel wrapper with fluent query builder
- [ ] **Database migrations** - Alembic with simplified API
- [ ] **Service Providers** - Laravel-style application bootstrapping
- [ ] **Artisan-like CLI** - Code generation and migration tools

### 🗺️ Roadmap (Sprint 2.x+)

- [ ] **SQLModel ORM** - Eloquent-inspired query builder
- [ ] **Database migrations** - Alembic with simplified API
- [ ] **Service Providers** - Laravel-style bootstrapping
- [ ] **Middleware System** - Built-in auth, CORS, rate limiting
- [ ] **CLI Tool** - Code generation (models, controllers, migrations)
- [ ] **Authentication system** - JWT + OAuth2 patterns
- [ ] **Event dispatcher** - Pub/sub for decoupled architecture
- [ ] **Background jobs** - Async task queue integration
- [ ] **Validation** - Enhanced Pydantic integration

---

## 🏃 **Quick Start**

### Prerequisites

- Python 3.13 or higher
- Poetry (package manager)

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
poetry run mypy src/ftf/http/ src/ftf/core/ src/ftf/main.py

# Code formatting
poetry run black src/ tests/

# Import sorting
poetry run isort src/ tests/

# Linting
poetry run ruff check src/ tests/

# Run all checks
poetry run black src/ tests/ && \
poetry run isort src/ tests/ && \
poetry run ruff check src/ tests/ && \
poetry run mypy src/ftf/http/ src/ftf/core/ src/ftf/main.py
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

---

## 🧠 **Core Concepts**

### 1. Dependency Injection Container

Fast Track Framework features a custom IoC container that uses Python type hints for automatic dependency resolution:

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

**Example with nested dependencies:**
```python
class Database:
    def __init__(self):
        self.connection = "postgresql://..."

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
```

### 2. FastAPI Integration with Inject()

Seamlessly inject dependencies into FastAPI routes using the `Inject()` function:

```python
from ftf.http import FastTrackFramework, Inject
from ftf.http.params import Inject

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

### 3. Request-Scoped Dependencies

Use scoped dependencies for per-request state (database sessions, auth context):

```python
from ftf.http import FastTrackFramework, ScopedMiddleware

app = FastTrackFramework()

# Add scoped middleware to manage request lifecycle
app.add_middleware(ScopedMiddleware)

# Register scoped dependency
app.register(DatabaseSession, scope="scoped")

@app.get("/users")
def list_users(session: DatabaseSession = Inject(DatabaseSession)):
    # Same session instance within this request
    # Automatically cleaned up after request completes
    return session.query(User).all()
```

**Benefits:**
- ✅ One instance per request (not per injection)
- ✅ Automatic cleanup after request
- ✅ Async-safe with ContextVars
- ✅ No memory leaks

### Eloquent-inspired ORM (Coming Soon)
```python
from ftf.orm import Model

class User(Model):
    __tablename__ = "users"
    
    name: str
    email: str
    created_at: datetime

# Fluent query builder
users = await User.query()\
    .where("status", "active")\
    .order_by("created_at", "desc")\
    .limit(10)\
    .get()

# Relationships
class Post(Model):
    user_id: int
    
    def user(self):
        return self.belongs_to(User)
```

### CLI Tool (Coming Soon)
```bash
# Generate models
ftf make:model User --migration

# Run migrations
ftf migrate

# Generate controllers
ftf make:controller UserController --resource

# Seed database
ftf db:seed
```

---

## 🏗️ **Architecture**

### Project Structure
```
larafast/
├── src/ftf/
│   ├── core/                          # IoC Container (Sprint 1.2) ✅
│   │   ├── container.py               # Main DI container
│   │   ├── exceptions.py              # DI-specific exceptions
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
│   │   └── sprint_1_2_active_record_trap.py
│   ├── main.py                        # Application entry point ✅
│   └── __init__.py
├── tests/
│   ├── unit/                          # Unit tests (24 tests) ✅
│   │   └── test_container.py
│   ├── integration/                   # Integration tests (13 tests) ✅
│   │   ├── test_http_integration.py
│   │   └── test_welcome_controller.py
│   └── conftest.py
├── pyproject.toml                     # Poetry + tooling config ✅
├── README.md                          # This file
├── SPRINT_SUMMARY.md                  # Sprint 1.x learnings
├── SPRINT_2_1_SUMMARY.md              # Sprint 2.1 complete guide ✅
└── CONTRIBUTING.md

✅ = Complete    🚧 = In Progress    ⏳ = Planned
```

### Design Principles

1. **Explicit over Implicit** - Following the Zen of Python
2. **Async-Native** - No sync fallbacks, pure asyncio
3. **Type Safety First** - Leveraging Python's type system
4. **Test-Driven** - Every feature starts with tests
5. **Educational** - Code comments explain "why", not just "what"

---

## 🧪 **Testing**

We maintain **97.42% test coverage** with comprehensive unit and integration tests:

```bash
# Run all tests with coverage
poetry run pytest tests/ -v --cov

# Run specific test suites
poetry run pytest tests/unit/ -v           # Unit tests (24 tests)
poetry run pytest tests/integration/ -v    # Integration tests (13 tests)

# Run with markers
poetry run pytest -m "not slow" -v         # Skip slow tests
poetry run pytest -m integration -v        # Only integration tests
```

### Test Results (Sprint 2.1)

```
========================= test session starts ==========================
collected 37 items

tests/integration/test_http_integration.py ........... PASSED [ 69%]
tests/integration/test_welcome_controller.py ....     PASSED [ 79%]
tests/unit/test_container.py ....................     PASSED [100%]

======================= 36 passed, 1 skipped in 3.20s ==================

Coverage: 97.42%
- src/ftf/core/container.py:    97.18%
- src/ftf/http/app.py:          95.12%
- src/ftf/http/params.py:       100%
- src/ftf/http/controllers/*:   100%
- src/ftf/main.py:              100%
```

### Test Philosophy

- **Unit Tests**: Test components in isolation (Container, DI resolution)
- **Integration Tests**: Test FastAPI + Container integration end-to-end
- **Async Tests**: All async code tested with pytest-asyncio
- **Type Safety**: Tests verify type-safe dependency resolution
- **Fixtures**: Shared setup via conftest.py for DRY tests
- **Real Scenarios**: Tests simulate actual HTTP requests with TestClient

---

## 📚 **Documentation**

### Learning Resources

This project is built as an educational journey. Each sprint has detailed documentation:

- ✅ [**SPRINT_SUMMARY.md**](SPRINT_SUMMARY.md) - Sprints 1.1 & 1.2 learnings
- ✅ [**SPRINT_2_1_SUMMARY.md**](SPRINT_2_1_SUMMARY.md) - Complete Sprint 2.1 guide
- ✅ [**CONTRIBUTING.md**](CONTRIBUTING.md) - Contribution guidelines
- 📝 Exercises in `src/ftf/exercises/` - Hands-on learning examples

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
poetry run mypy src/ftf/http/ src/ftf/core/ src/ftf/main.py
poetry run pytest tests/ -v --cov
```

### Contribution Guidelines

1. **Fork & Branch** - Create feature branches from `main`
2. **Write Tests** - Maintain >95% coverage (current: 97.42%)
3. **Type Hints** - All functions must be type-annotated (strict MyPy)
4. **Conventional Commits** - Use semantic commit messages
5. **Documentation** - Update relevant docs and docstrings
6. **Code Quality** - Ensure Black, isort, Ruff, and MyPy pass

### Quality Standards

- ✅ **Type Safety**: MyPy strict mode must pass
- ✅ **Test Coverage**: >95% coverage required
- ✅ **Code Style**: Black formatting (line length: 88)
- ✅ **Import Order**: isort with Black profile
- ✅ **Linting**: Ruff with 30+ rule categories
- ✅ **Docstrings**: Google-style docstrings for public APIs

---

## 🎓 **Learning Journey**

### Sprint Progress

| Sprint | Focus | Status | Coverage | Tests |
|--------|-------|--------|----------|-------|
| 1.1 | Async Python Basics | ✅ Complete | - | Educational |
| 1.2 | IoC Container | ✅ Complete | ~87% | 24 unit tests |
| 1.3 | Tooling & CI/CD | ✅ Complete | - | Config only |
| **2.1** | **FastAPI Integration** | ✅ **Complete** | **97.42%** | **37 tests** |
| 2.2 | Database & ORM | ⏳ Planned | - | - |
| 2.3 | Advanced Patterns | ⏳ Planned | - | - |
| 3.1 | ORM Deep Dive | ⏳ Planned | - | - |
| 3.2 | Migration System | ⏳ Planned | - | - |
| 3.3 | CLI Tool | ⏳ Planned | - | - |
| 4.1 | Documentation | ⏳ Planned | - | - |
| 4.2 | Example Project | ⏳ Planned | - | - |

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

#### Coming Soon
- ⏳ **Async SQLAlchemy** - Session management patterns
- ⏳ **Pydantic V2** - Performance optimizations
- ⏳ **Query Builder Design** - Fluent interface implementation

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
| **ORM** | SQLModel | Coming | Pydantic + SQLAlchemy unified |
| **Migrations** | Alembic | Coming | Industry standard migrations |
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

## 📝 **License**

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **Sebastian Ramirez** - Creator of FastAPI, SQLModel, and Typer
- **Taylor Otwell** - Creator of Laravel

---

## 🌟 **Star History**

If this project helps your learning journey, consider giving it a star! ⭐

---

## 📬 **Contact**

- **GitHub Issues**: [Report bugs or request features](https://github.com/eveschipfer/fast-track-framework/issues)
- **Discussions**: [Ask questions or share ideas](https://github.com/eveschipfer/fast-track-framework/discussions)

---

<div align="center">

**Built with ❤️ for learning**

[Documentation](https://eveschipfer.github.io/fast-track-framework) • [Contributing](CONTRIBUTING.md) • [Changelog](CHANGELOG.md)

</div>