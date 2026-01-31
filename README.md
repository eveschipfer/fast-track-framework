# 🚀 Fast Track Framework

> **A Laravel-inspired micro-framework built on FastAPI** — Combining Laravel's developer experience with Python's async performance.

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-green.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/tests-193%20passed-success.svg)](https://github.com/eveschipfer/fast-track-framework)
[![Sprint](https://img.shields.io/badge/sprint-3.2%20complete-success.svg)](https://github.com/eveschipfer/fast-track-framework)
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
| **✅ Form Requests** | Async validation with Pydantic + database rules | ✅ Sprint 2.9 |
| **⚡ CLI Tooling** | Scaffolding commands (make:*) and db operations | ✅ Sprint 3.0 |
| **📡 Event Bus** | Observer Pattern with async listeners and DI | ✅ Sprint 3.1 |
| **⚙️ Job Queue** | Laravel-style background jobs with SAQ & DI | ✅ Sprint 3.2 |
| **🧪 193 Tests** | 100% passing, comprehensive coverage | ✅ Complete |
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
- 📜 [**Sprint 3.2 Summary**](docs/history/SPRINT_3_2_SUMMARY.md) — Job Queue & Workers (NEW!)
- 📜 [**Sprint 3.1 Summary**](docs/history/SPRINT_3_1_SUMMARY.md) — Event Bus & Observer Pattern
- 📜 [**Sprint 3.0 Summary**](docs/history/SPRINT_3_0_SUMMARY.md) — CLI Tooling & Scaffolding
- 📜 [**Sprint 2.9 Summary**](docs/history/SPRINT_2_9_SUMMARY.md) — Form Requests & Async Validation
- 📜 [**Sprint 2.8 Summary**](docs/history/SPRINT_2_8_SUMMARY.md) — Factory & Seeder System
- 📜 [**Sprint 2.7 Summary**](docs/history/SPRINT_2_7_SUMMARY.md) — Contract Tests & Semantic Regression
- 📜 [**Sprint 2.6 Summary**](docs/history/SPRINT_2_6_SUMMARY.md) — Advanced Query Builder Features
- 📜 [**Sprint 2.5 Summary**](docs/history/sprint-2-5-summary.md) — Fast Query extraction (framework-agnostic ORM)
- 📜 [**All Sprint Documentation**](docs/history/) — Complete sprint history

### Quality Reports
- 🔬 [**Testing Guide**](docs/guides/testing.md) — Comprehensive testing documentation
- 🛡️ [**Quality Reports**](docs/quality/) — Validation reports and technical debt resolution

---

## 🆕 What's New in Sprint 3.2?

### **Job Queue & Workers** — Background Processing with SAQ

Implemented a Laravel-style background job system using SAQ (Simple Async Queue) with full dependency injection support through a clever Bridge Pattern:

```python
from ftf.jobs import Job

# Define jobs with DI
class SendWelcomeEmail(Job):
    def __init__(self, mailer: MailerService, user_repo: UserRepository):
        self.mailer = mailer
        self.user_repo = user_repo
        self.user_id: int = 0  # Set by payload

    async def handle(self) -> None:
        user = await self.user_repo.find(self.user_id)
        await self.mailer.send(user.email, "Welcome!")

# Dispatch to background queue
await SendWelcomeEmail.dispatch(user_id=123)
```

**Key Features:**
- ✅ **Class-Based Jobs** — Laravel-style API (not function-based like SAQ native)
- ✅ **Dependency Injection** — Jobs resolved from IoC Container
- ✅ **Bridge Pattern** — Universal `runner()` wraps SAQ's function API
- ✅ **CLI Commands** — `ftf queue work`, `ftf queue dashboard`, `ftf make job`
- ✅ **Async Native** — Built on SAQ (not Celery!)
- ✅ **Dashboard UI** — Built-in monitoring like Laravel Horizon
- ✅ **91.94% Coverage** — 13 new tests, comprehensive validation

**Example CLI Usage:**
```bash
$ ftf make job SendWelcomeEmail
✓ Job created: src/ftf/jobs/send_welcome_email.py
💡 Dispatch with: await SendWelcomeEmail.dispatch(...)

$ ftf queue work
🚀 Worker started for queue: default
📡 Listening for jobs on redis://localhost:6379

$ ftf queue dashboard
🎛️  Dashboard started at http://localhost:8080
```

**Learn more:** [Sprint 3.2 Summary](docs/history/SPRINT_3_2_SUMMARY.md)

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
| **2.8** | Factory & Seeder System | Test data generation with Faker |
| **2.9** | Form Requests & Validation | Async validation with Pydantic + DB rules |
| **3.0** | CLI Tooling & Scaffolding | Typer + Rich, make:* commands, db:seed |
| **3.1** | Event Bus & Observers | Observer Pattern, async listeners, IoC integration |
| **3.2** ✨ | **Job Queue & Workers** | **SAQ, class-based jobs, Bridge Pattern, dashboard** |

**Status:** 193 tests passing | ~48% coverage | Sprint 3.2 complete ✅

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
- 167 tests passing (100% pass rate, 1 skipped)
  - 143 unit tests (91 + 21 factory + 16 validation + 15 CLI)
  - 13 integration tests
  - 20 contract tests (SQL generation)
  - 9 semantic regression tests (O(1) complexity)
- ~47% overall coverage
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
    ├── validation/          # Form Requests & Validation (Sprint 2.9)
    ├── events/              # Event Bus & Observers (Sprint 3.1)
    ├── jobs/                # 🆕 Job Queue & Workers (Sprint 3.2)
    ├── cli/                 # CLI Tooling (Sprint 3.0)
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
