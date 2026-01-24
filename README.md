# 🚀 Fast Track Framework

> A Laravel-inspired micro-framework built on top of FastAPI, designed as an educational deep-dive into modern Python architecture patterns.

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 **Project Vision**

Fast Track Framework bridges the gap between FastAPI's async performance and Laravel's developer experience. Built from scratch as a learning journey, this project demonstrates:

- 🏗️ **Modern Python architecture** with strict type safety
- ⚡ **Async-first design** leveraging Python 3.11+ features
- 🎨 **Laravel-inspired DX** (Eloquent-like ORM, Artisan-like CLI)
- 🧪 **Test-driven development** with >80% coverage
- 📚 **Educational documentation** explaining every design decision

---

## ✨ **Features**

### 🔥 Current (Sprint 1.x - Foundation)

- [x] **IoC Container** - Dependency injection with automatic resolution
- [x] **Async-first** - Built on asyncio with proper context management
- [x] **Type-safe** - Strict MyPy compliance, zero `Any` types
- [x] **Production tooling** - Poetry, pre-commit hooks, CI/CD

### 🚧 In Progress (Sprint 2.x - FastAPI Integration)

- [ ] **Eloquent-inspired ORM** - SQLModel wrapper with fluent query builder
- [ ] **Artisan-like CLI** - Code generation and migration tools
- [ ] **Service Providers** - Laravel-style application bootstrapping
- [ ] **Middleware Stack** - Request lifecycle management

### 🗺️ Roadmap (Sprint 3.x+)

- [ ] **Database migrations** - Alembic with simplified API
- [ ] **Authentication system** - JWT + OAuth2 patterns
- [ ] **Event dispatcher** - Pub/sub for decoupled architecture
- [ ] **Background jobs** - Async task queue integration

---

## 🏃 **Quick Start**

### Prerequisites

- Python 3.11 or higher
- Poetry (package manager)

### Installation
```bash
# Clone the repository
git clone https://github.com/eveschipfer/fast-track-framework.git
cd fast-track-framework

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run tests
pytest tests/ -v --cov

# Type checking
mypy src/ --strict
```

### Hello World Example
```python
from ftf import Application, Container
from ftf.http import Router, get

# Setup DI container
container = Container()
container.register(Database, singleton=True)
container.register(UserRepository)

# Create application
app = Application(container)

# Define route with automatic dependency injection
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    repo: UserRepository  # Auto-injected!
):
    user = await repo.find(user_id)
    return {"user": user.to_dict()}

# Run with Uvicorn
# uvicorn main:app --reload
```

---

## 🧠 **Core Concepts**

### Dependency Injection Container

Fast Track Framework features a custom IoC container that uses Python type hints for automatic dependency resolution:
```python
from ftf.core import Container

# Register dependencies
container = Container()
container.register(Database, singleton=True)
container.register(UserService)

# Automatic resolution with nested dependencies
# UserService(__init__) requires Database → auto-injected
service = container.resolve(UserService)
```

**Key Features:**
- ✅ Type-hint based resolution
- ✅ Singleton, Scoped, and Transient lifetimes
- ✅ Circular dependency detection
- ✅ Async-safe with ContextVars

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
fast-track-framework/
├── src/ftf/
│   ├── core/                 # IoC container, context management
│   │   ├── container.py
│   │   ├── context.py
│   │   └── exceptions.py
│   ├── orm/                  # SQLModel wrapper, query builder
│   │   ├── model.py
│   │   ├── query.py
│   │   └── relationships.py
│   ├── http/                 # FastAPI extensions
│   │   ├── app.py
│   │   ├── middleware.py
│   │   └── routing.py
│   ├── cli/                  # Typer-based commands
│   │   ├── commands/
│   │   └── templates/
│   └── __init__.py
├── tests/
│   ├── unit/                 # Isolated component tests
│   ├── integration/          # Multi-component tests
│   └── conftest.py          # Shared fixtures
├── docs/                     # Documentation site
├── examples/                 # Sample projects
├── pyproject.toml           # Poetry configuration
└── README.md
```

### Design Principles

1. **Explicit over Implicit** - Following the Zen of Python
2. **Async-Native** - No sync fallbacks, pure asyncio
3. **Type Safety First** - Leveraging Python's type system
4. **Test-Driven** - Every feature starts with tests
5. **Educational** - Code comments explain "why", not just "what"

---

## 🧪 **Testing**

We maintain >80% test coverage with a mix of unit and integration tests:
```bash
# Run all tests with coverage
pytest tests/ -v --cov --cov-report=html

# Run specific test suites
pytest tests/unit/ -v           # Unit tests only
pytest tests/integration/ -v    # Integration tests only

# Run with markers
pytest -m "not slow" -v        # Skip slow tests
```

### Test Philosophy

- **Unit Tests**: Test components in isolation with mocked dependencies
- **Integration Tests**: Test component interactions with real DB (in-memory SQLite)
- **Async Tests**: All async code tested with pytest-asyncio
- **Fixtures**: Shared setup via conftest.py for DRY tests

---

## 📚 **Documentation**

### Learning Resources

This project is built as an educational journey. Each sprint has detailed documentation:

- [**Sprint 1.1**: Async Python Fundamentals](docs/sprints/1.1-async-basics.md)
- [**Sprint 1.2**: IoC Container Deep Dive](docs/sprints/1.2-ioc-container.md)
- [**Sprint 2.1**: FastAPI Integration](docs/sprints/2.1-fastapi-core.md)
- [**Architecture Decisions**: ADRs](docs/architecture/)

### API Documentation

Once running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🤝 **Contributing**

This is primarily an educational project, but contributions are welcome!

### Development Setup
```bash
# Install with dev dependencies
poetry install

# Setup pre-commit hooks
pre-commit install

# Run quality checks
mypy src/ --strict
black src/ tests/ --check
ruff check src/ tests/
pytest tests/ -v --cov
```

### Contribution Guidelines

1. **Fork & Branch** - Create feature branches from `develop`
2. **Write Tests** - Maintain >80% coverage
3. **Type Hints** - All functions must be type-annotated
4. **Conventional Commits** - Use semantic commit messages
5. **Documentation** - Update relevant docs

---

## 🎓 **Learning Journey**

### Sprint Progress

| Sprint | Focus | Status | Duration |
|--------|-------|--------|----------|
| 1.1 | Async Python Basics | ✅ Complete | 1 week |
| 1.2 | IoC Container | ✅ Complete | 1 week |
| 1.3 | Tooling & CI/CD | 🔄 In Progress | 3 days |
| 2.1 | FastAPI Core | ⏳ Planned | 1 week |
| 2.2 | Database & ORM | ⏳ Planned | 2 weeks |
| 2.3 | Advanced Patterns | ⏳ Planned | 1 week |
| 3.1 | ORM Deep Dive | ⏳ Planned | 2 weeks |
| 3.2 | Migration System | ⏳ Planned | 1 week |
| 3.3 | CLI Tool | ⏳ Planned | 1 week |
| 4.1 | Documentation | ⏳ Planned | 1 week |
| 4.2 | Example Project | ⏳ Planned | 1 week |
| 4.3 | PyPI Release | ⏳ Planned | 3 days |

### Key Learnings

- ✅ **Active Record vs Data Mapper** - Why SQLAlchemy uses Data Mapper
- ✅ **ContextVars** - Thread-safe global state in async Python
- ✅ **Type Hints Introspection** - Using `get_type_hints()` for DI
- ⏳ **Async SQLAlchemy** - Session management patterns
- ⏳ **Pydantic V2** - Performance optimizations

---

## 🔗 **Tech Stack**

| Category | Technology | Why? |
|----------|-----------|------|
| **Web Framework** | FastAPI 0.115+ | Modern, async-first, type-safe |
| **ORM** | SQLModel | Pydantic + SQLAlchemy unified |
| **Database** | PostgreSQL/SQLite | Production/testing databases |
| **Migrations** | Alembic | Industry standard for SQLAlchemy |
| **CLI** | Typer | FastAPI's cousin for CLI apps |
| **Testing** | Pytest + pytest-asyncio | Best-in-class testing tools |
| **Type Checking** | MyPy (strict) | Catch bugs before runtime |
| **Code Quality** | Black, Ruff, Pre-commit | Consistent, quality code |
| **CI/CD** | GitHub Actions | Automated testing & deployment |

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