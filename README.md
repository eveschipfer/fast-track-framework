# 🚀 Fast Track Framework

> **A Laravel-inspired micro-framework built on FastAPI** — Combining Laravel's developer experience with Python's async performance.

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-green.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/tests-136%20passed-success.svg)](https://github.com/eveschipfer/fast-track-framework)
[![Sprint](https://img.shields.io/badge/sprint-2.8%20complete-success.svg)](https://github.com/eveschipfer/fast-track-framework)
[![Fast Query](https://img.shields.io/badge/fast__query-standalone-blue.svg)](https://github.com/eveschipfer/fast-track-framework)

---

## 🎯 Vision

Fast Track Framework is an **educational deep-dive** into building production-grade Python frameworks. It demonstrates modern architecture patterns while maintaining Laravel's approachable developer experience.

**Key Philosophy:**
- ✅ **Type-safe first** — Strict MyPy, zero `Any` types
- ✅ **Async-native** — Built on Python 3.13+ asyncio
- ✅ **Framework-agnostic ORM** — Works with FastAPI, Flask, Django, CLI
- ✅ **Explicit over implicit** — No magic, clear dependencies
- ✅ **Educational** — Every decision documented with "why"

> **Note:** This is a learning project designed for experimentation, not a drop-in replacement for mature frameworks.

---

## ✨ Features

| Feature | Description | Status |
|---------|-------------|--------|
| **🏗️ IoC Container** | Type-hint based DI with 3 lifetime scopes (singleton, scoped, transient) | ✅ Production |
| **📦 Fast Query** | Standalone ORM package (zero framework dependencies) | ✅ Sprint 2.5 |
| **🔍 Query Builder** | Laravel Eloquent-inspired fluent interface (22 methods) | ✅ Sprint 2.3 |
| **🗄️ Repository Pattern** | Explicit database access (NOT Active Record) | ✅ Sprint 2.2 |
| **⚡ Smart Features** | Auto-timestamps, soft deletes, smart delete detection | ✅ Sprint 2.5 |
| **🔗 Relationships** | One-to-many, many-to-many with eager loading | ✅ Sprint 2.3 |
| **🏭 Factories & Seeders** | Laravel-inspired test data generation with Faker | ✅ Sprint 2.8 |
| **🧪 136 Tests** | 100% passing, comprehensive coverage | ✅ Complete |
| **🛠️ Alembic** | Auto-migrations with async support | ✅ Sprint 2.2 |

---

## 🏃 5-Minute Quick Start

### 1. Install

```bash
git clone https://github.com/eveschipfer/fast-track-framework.git
cd fast-track-framework/larafast
poetry install
poetry shell
```

### 2. Run

```bash
poetry run uvicorn ftf.main:app --reload
# Visit http://localhost:8000/docs
```

### 3. Your First API

```python
from ftf.http import FastTrackFramework, Inject
from fast_query import Base, BaseRepository, TimestampMixin

app = FastTrackFramework()

# Define model with auto-timestamps
class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

# Create repository
class UserRepository(BaseRepository[User]):
    pass

app.register(UserRepository, scope="transient")

# Auto-inject repository
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    repo: UserRepository = Inject(UserRepository)
):
    return await repo.find_or_fail(user_id)  # Auto 404!
```

**See full setup:** [Quick Start Guide](docs/guides/quickstart.md)

---

## 📚 Documentation

### Getting Started
- 📖 [**Quick Start Guide**](docs/guides/quickstart.md) — Installation, hello world, first API
- 🗄️ [**Database & ORM Guide**](docs/guides/database.md) — Fast Query package, repository pattern, query builder
- 🧪 [**Testing Guide**](docs/guides/testing.md) — Writing tests, fixtures, best practices

### Core Concepts
- 🏗️ [**IoC Container**](docs/guides/container.md) — Dependency injection, scopes, lifecycle management
- 🧠 [**Architecture Decisions**](docs/architecture/decisions.md) — Why Repository Pattern? Why type-hints?

### Sprint History
- 📜 [**Sprint 2.8 Summary**](docs/history/SPRINT_2_8_SUMMARY.md) — Factory & Seeder System (NEW!)
- 📜 [**Sprint 2.7 Summary**](docs/history/SPRINT_2_7_SUMMARY.md) — Contract Tests & Semantic Regression
- 📜 [**Sprint 2.6 Summary**](docs/history/SPRINT_2_6_SUMMARY.md) — Advanced Query Builder Features
- 📜 [**Sprint 2.5 Summary**](docs/history/sprint-2-5-summary.md) — Fast Query extraction (framework-agnostic ORM)
- 📜 [**Sprint 2.4 Summary**](docs/history/SPRINT_2_4_SUMMARY.md) — Relationship Stress Tests
- 📜 [**All Sprint Documentation**](docs/history/) — Complete sprint history

### Quality Reports
- 🔬 [**Testing Guide**](docs/guides/testing.md) — Comprehensive testing documentation
- 🛡️ [**Quality Reports**](docs/quality/) — Validation reports and technical debt resolution

---

## 🆕 What's New in Sprint 2.8?

### **Factory & Seeder System** — Laravel-Inspired Test Data Generation

Implemented a complete factory and seeder system for generating realistic test data with **Faker integration**:

```python
# Define a factory
from fast_query import Factory

class UserFactory(Factory[User]):
    _model_class = User

    def definition(self) -> dict[str, Any]:
        return {
            "name": self.faker.name(),
            "email": self.faker.email(),
        }

# Use it
async with get_session() as session:
    factory = UserFactory(session)

    # Create one
    user = await factory.create()

    # Create many
    users = await factory.create_batch(10)

    # With relationships
    user = await factory.has_posts(5).create()

    # With state modifiers
    admin = await factory.state(lambda a: {**a, "is_admin": True}).create()
```

**Key Features:**
- ✅ **Async-first** — Full async/await support for database operations
- ✅ **Type-safe** — Generic Factory[T] with strict type hints
- ✅ **Laravel-inspired** — Familiar API for Laravel developers
- ✅ **Faker integration** — Realistic fake data out of the box
- ✅ **Relationship hooks** — Create related models with `.has_posts(5)`
- ✅ **State management** — Chain state transformations with `.state()`
- ✅ **Database seeders** — Orchestrate data generation with seeders

**Learn more:** [Sprint 2.8 Summary](docs/history/SPRINT_2_8_SUMMARY.md)

---

## 🎓 Learning Journey

This project is built **sprint-by-sprint** as an educational deep-dive:

| Sprint | Focus | Highlights |
|--------|-------|------------|
| **1.1** | Async Python | asyncio, gather, semaphores |
| **1.2** | IoC Container | Type-hint based DI, 3 scopes |
| **2.1** | FastAPI Integration | `Inject()`, middleware, request scoping |
| **2.2** | Database Foundation | Repository Pattern, Alembic migrations |
| **2.3** | Query Builder | Fluent API (22 methods), relationships |
| **2.4** | Stress Testing | N+1 prevention, cascade deletes |
| **2.5** | Fast Query Extraction | Standalone ORM package |
| **2.6** | Advanced Query Builder | Nested eager loading, scopes, where_has |
| **2.7** | Quality Engineering | Contract tests, semantic regression |
| **2.8** ✨ | **Factory & Seeder System** | **Test data generation with Faker** |

**Status:** 136 tests passing | ~45% coverage | Sprint 2.8 complete ✅

---

## 🧪 Testing

```bash
# Run all tests
poetry run pytest tests/ -v --cov

# Test fast_query standalone
poetry run pytest tests/unit/test_repository.py -v
poetry run pytest tests/unit/test_query_builder.py -v

# Verify zero framework dependencies
cd larafast && PYTHONPATH=src poetry run python -c "import fast_query; print('✅ Works!')"
```

**Test Results:**
- 136 tests passing (100% pass rate)
  - 112 unit tests (including 21 factory tests)
  - 13 integration tests
  - 20 contract tests (SQL generation)
  - 9 semantic regression tests (O(1) complexity)
- ~45% overall coverage
- Zero framework coupling verified ✅

**Learn more:** [Testing Guide](docs/guides/testing.md)

---

## 🏗️ Architecture

```
src/
├── fast_query/              # Standalone ORM Package
│   ├── engine.py            # AsyncEngine singleton
│   ├── session.py           # AsyncSession factory
│   ├── repository.py        # Generic CRUD with smart delete
│   ├── query_builder.py     # Fluent query builder
│   ├── mixins.py            # TimestampMixin, SoftDeletesMixin
│   ├── factories.py         # 🆕 Factory system (Sprint 2.8)
│   ├── seeding.py           # 🆕 Seeder system (Sprint 2.8)
│   └── exceptions.py        # RecordNotFound, FastQueryError
│
└── ftf/
    ├── core/                # IoC Container (Sprint 1.2)
    ├── http/                # FastAPI integration (Sprint 2.1)
    ├── models/              # Database models
    └── main.py              # Application entry point
```

**Design Principles:**
1. **Explicit over Implicit** — Following Zen of Python
2. **Async-Native** — No sync fallbacks, pure asyncio
3. **Type Safety First** — Strict MyPy, zero `Any` types
4. **Framework-Agnostic** — ORM works everywhere

**Learn more:** [Architecture Decisions](docs/architecture/decisions.md)

---

## 🤝 Contributing

Contributions welcome! This project maintains **strict quality standards**:

```bash
# Run quality checks
poetry run black src/ tests/
poetry run isort src/ tests/
poetry run ruff check src/ tests/ --fix
poetry run mypy src/
poetry run pytest tests/ -v --cov
```

**Requirements:**
- ✅ Type hints (strict MyPy)
- ✅ >80% test coverage
- ✅ Black formatting
- ✅ Google-style docstrings

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## 💡 Inspiration

- **Laravel** — Developer experience and conventions
- **FastAPI** — Modern async patterns
- **NestJS** — Dependency injection architecture
- **SQLAlchemy** — Production-grade ORM

---

## 📝 License

MIT License — see [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for learning and production use**

[Quick Start](docs/guides/quickstart.md) • [Database Guide](docs/guides/database.md) • [IoC Container](docs/guides/container.md) • [Testing](docs/guides/testing.md)

</div>
