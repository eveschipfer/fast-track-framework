# 🚀 Fast Track Framework

> **A Laravel-inspired micro-framework built on FastAPI** — Combining Laravel's developer experience with Python's async performance.

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-green.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/tests-425%20passed-success.svg)](https://github.com/eveschipfer/fast-track-framework)
[![Sprint](https://img.shields.io/badge/sprint-4.1%20complete-success.svg)](https://github.com/eveschipfer/fast-track-framework)
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
| **🔐 Authentication** | JWT tokens, bcrypt passwords, route guards | ✅ Sprint 3.3 |
| **🛡️ HTTP Kernel** | Global exception handling, CORS, GZip, middleware | ✅ Sprint 3.4 |
| **🌍 i18n System** | Multi-language support, JSON translations, CLI tools | ✅ Sprint 3.5 |
| **✅ Custom Validation** | Pydantic v2 rules with ftf make rule command | ✅ Sprint 3.6 |
| **💾 Multi-Driver Cache** | File/Redis/Array drivers, rate limiting middleware | ✅ Sprint 3.7 |
| **⏰ Task Scheduler** | Cron expressions & intervals with @Schedule decorators | ✅ Sprint 3.8 |
| **📧 Mailer System** | Multi-driver emails (Log/Array/SMTP), Jinja2 templates, queue integration | ✅ Sprint 4.0 |
| **📁 Storage System** | Multi-driver file storage (Local/Memory/S3), async I/O, unified API | ✅ Sprint 4.1 |
| **🧪 425 Tests** | 100% passing, comprehensive coverage | ✅ Complete |
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
- 📜 [**Sprint 4.0 Summary**](docs/history/SPRINT_4_0_SUMMARY.md) — Mailer System with Multi-Driver Support (NEW!)
- 📜 [**Sprint 3.8 Summary**](docs/history/SPRINT_3_8_SUMMARY.md) — Async Jobs & Task Scheduler
- 📜 [**Sprint 3.7 Summary**](docs/history/SPRINT_3_7_SUMMARY.md) — Multi-Driver Caching & Rate Limiting
- 📜 [**Sprint 3.6 Summary**](docs/history/SPRINT_3_6_SUMMARY.md) — Custom Validation Rules CLI
- 📜 [**Sprint 3.5 Summary**](docs/history/SPRINT_3_5_SUMMARY.md) — i18n System & CLI Extensibility
- 📜 [**Sprint 3.4 Summary**](docs/history/SPRINT_3_4_SUMMARY.md) — HTTP Kernel & Exception Handler
- 📜 [**Sprint 3.3 Summary**](docs/history/SPRINT_3_3_SUMMARY.md) — Authentication & JWT
- 📜 [**Sprint 3.2 Summary**](docs/history/SPRINT_3_2_SUMMARY.md) — Job Queue & Workers
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

## 🆕 What's New in Sprint 4.0?

### **Mailer System** — Laravel-Inspired Email with Multi-Driver Support

Implemented comprehensive email system with template rendering, multiple drivers, and queue integration. Send beautiful emails with just a few lines of code:

```python
from ftf.mail import Mail, Mailable

# Define your email
class WelcomeEmail(Mailable):
    def __init__(self, user: User):
        super().__init__()
        self.user = user

    async def build(self) -> None:
        self.subject("Welcome to Fast Track!")
        self.from_("noreply@app.com", "Fast Track")
        self.view("mail.welcome", {"user": self.user})

# Send immediately
await Mail.send(WelcomeEmail(user))

# Fluent API with recipients
await Mail.to("user@example.com", "John").send(WelcomeEmail(user))

# Queue for background processing
await Mail.to("user@example.com").queue(WelcomeEmail(user))
```

**Multi-Driver Support:**
```bash
# Development (logs to console)
MAIL_DRIVER=log

# Testing (stores in memory)
MAIL_DRIVER=array

# Production (sends via SMTP)
MAIL_DRIVER=smtp
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_ENCRYPTION=tls
```

**CLI Scaffolding:**
```bash
$ ftf make mail WelcomeEmail
✓ Mailable created: src/mail/welcome_email.py

# Generated with complete documentation and examples
│ health_check     │ 60s          │ interval │ Check health        │
│ daily_report     │ 0 0 * * *    │ cron     │ Generate report     │
└──────────────────┴──────────────┴──────────┴─────────────────────┘

Total: 3 task(s)
```

**Background Jobs (from Sprint 3.2):**
```python
from ftf.jobs import Job

class ProcessOrderJob(Job):
    def __init__(self, order_service: OrderService):
        self.order_service = order_service  # Auto-injected
        self.order_id: int = 0  # Set from payload

    async def handle(self):
        await self.order_service.process(self.order_id)

# Dispatch from anywhere
await ProcessOrderJob.dispatch(order_id=123)
```

**Key Features:**
- ✅ **Cron Expressions**: Full 5-field cron syntax support
- ✅ **Simple Intervals**: Run tasks every N seconds
- ✅ **Auto-Discovery**: Worker finds all @Schedule tasks
- ✅ **Redis Verification**: Checks connection before starting
- ✅ **QueueProvider**: Unified Jobs + Schedules initialization
- ✅ **IoC Integration**: Tasks can access services
- ✅ **21 Tests**: 100% coverage on schedule module
- ✅ **No Separate Process**: Unlike Celery beat, no extra daemon

**Learn more:** [Sprint 3.8 Summary](docs/history/SPRINT_3_8_SUMMARY.md) | [Schedule Guide](docs/guides/schedule.md)

---

## 🔙 Previous: Sprint 3.7

### **Multi-Driver Caching & Rate Limiting** — Laravel-Inspired Cache Facade

Production-ready caching system with multi-driver architecture (File/Redis/Array):

```python
from ftf.cache import Cache

# Simple cache operations
user = await Cache.get("user:123")
await Cache.put("user:123", user, ttl=3600)

# Remember pattern
user = await Cache.remember("user:123", 3600, lambda: fetch_user(123))

# Rate limiting
from ftf.http.middleware.throttle import ThrottleMiddleware
app.add_middleware(ThrottleMiddleware, max_requests=60, window_seconds=60)

💡 Usage Example:

from typing import Annotated
from pydantic import AfterValidator, BaseModel
from rules.cpf_is_valid import CpfIsValid

class MyModel(BaseModel):
    cpf: Annotated[str, AfterValidator(CpfIsValid())]
```

**Generated Validation Rule**:
```python
from typing import Any
from ftf.i18n import trans

class CpfIsValid:
    """Validate Brazilian CPF format."""

    def __init__(self, allow_masked: bool = True) -> None:
        self.allow_masked = allow_masked

    def __call__(self, value: str) -> str:
        """Validate and return the value."""
        if not is_valid_cpf(value):
            raise ValueError(trans("validation.invalid_cpf"))
        return value
```

**Key Features:**
- ✅ **Pydantic v2 Pattern** — Callable classes with `__call__` method
- ✅ **Stateful Validators** — Initialize with parameters via `__init__`
- ✅ **i18n Integration** — Auto-imports ftf.i18n for multi-language errors
- ✅ **Type-Safe** — Full MyPy support with strict type hints
- ✅ **Reusable** — Use across multiple models with Annotated
- ✅ **Smart Naming** — Converts PascalCase/snake_case automatically

**Example CLI Usage:**
```bash
$ ftf make rule MinAge
✓ Validation Rule created: src/rules/min_age.py

$ ftf make rule CpfIsValid --force
✓ Validation Rule created: src/rules/cpf_is_valid.py (overwritten)
```

**Learn more:** [Sprint 3.6 Summary](docs/history/SPRINT_3_6_SUMMARY.md)

---

## 🔙 Previous: Sprint 3.5

### **i18n System & CLI Extensibility** — Global Multi-Language Support

Lightweight internationalization system with JSON-based translations:

```python
from ftf.i18n import trans, t, set_locale, has

# Simple translation
message = trans("auth.failed")  # "These credentials do not match our records."

# With placeholders
message = trans("validation.min", field="Password", min=8)
# "The Password must be at least 8 characters."

# Switch language
set_locale("pt_BR")  # Portuguese (Brazil)
message = trans("auth.failed")
# "Essas credenciais não correspondem aos nossos registros."

# Check if translation exists
if has("auth.throttle"):
    message = trans("auth.throttle", seconds=60)
```

**Key Features:**
- ✅ **JSON Translations** — Portable, non-executable format (en, pt_BR)
- ✅ **Dot Notation Keys** — Hierarchical organization (auth.failed, validation.required)
- ✅ **Placeholder Replacement** — Simple :field, :min, :max syntax
- ✅ **Translator Singleton** — Single instance, hot-swappable locales
- ✅ **Cascade Loading** — User translations override framework defaults
- ✅ **CLI Commands** — make:cmd, make:lang for extensibility
- ✅ **26 Tests** — 100% passing, 96.83% coverage

**Example CLI Usage:**
```bash
$ ftf make:cmd deploy
✓ Command created: src/ftf/cli/commands/deploy.py

$ ftf make:lang de
✓ Translation file created: src/resources/lang/de.json
```

**Learn more:** [Sprint 3.5 Summary](docs/history/SPRINT_3_5_SUMMARY.md)

---

## 🔙 Previous: Sprint 3.4

### **HTTP Kernel & Exception Handler** — Production-Ready Error Handling

Centralized exception handling and middleware configuration:

```python
from ftf.http import FastTrackFramework, Inject, AuthenticationError, AuthorizationError
from ftf.http.middleware import MiddlewareManager

# Create app - exception handling auto-configured!
app = FastTrackFramework()

# One-line middleware setup
MiddlewareManager.configure_all(app)  # CORS + GZip + Security

# Exceptions auto-convert to JSON
@app.get("/users/{user_id}")
async def get_user(user_id: int, repo: UserRepository = Inject()):
    return await repo.find_or_fail(user_id)
    # RecordNotFound → 404: {"detail": "User not found: 123"}

@app.get("/admin")
async def admin_panel(user: CurrentUser):
    if not user.is_admin:
        raise AuthorizationError("Admins only")
        # → 403: {"detail": "Admins only"}
```

**Key Features:**
- ✅ **Global Exception Handling** — Auto-converts exceptions to JSON (never HTML)
- ✅ **Standard HTTP Errors** — 404, 401, 403, 422 with consistent format
- ✅ **CORS Middleware** — Environment-based config (`CORS_ORIGINS`)
- ✅ **GZip Compression** — 70-90% reduction for JSON responses
- ✅ **TrustedHost Security** — Prevents Host header attacks
- ✅ **make:middleware CLI** — Generate custom middleware classes
- ✅ **93% Coverage** — 25 new tests, all passing

**Example CLI Usage:**
```bash
$ ftf make:middleware LogRequests
✓ Middleware created: src/ftf/http/middleware/log_requests.py
💡 Register with: app.add_middleware(LogRequests)
```

**Environment Configuration:**
```bash
# .env file
CORS_ORIGINS="http://localhost:3000,https://myapp.com"
ALLOWED_HOSTS="localhost,myapp.com,*.myapp.com"
```

**Learn more:** [Sprint 3.4 Summary](docs/history/SPRINT_3_4_SUMMARY.md)

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
| **3.2** | Job Queue & Workers | SAQ, class-based jobs, Bridge Pattern, dashboard |
| **3.3** | Authentication & JWT | JWT tokens, bcrypt, AuthGuard, CurrentUser |
| **3.4** | HTTP Kernel | Global exceptions, CORS, GZip, middleware |
| **3.5** | i18n & CLI | JSON translations, multi-language, make:cmd/lang |
| **3.6** | Custom Validation | Pydantic v2 rules, make:rule, i18n errors |
| **3.7** ✨ | **Multi-Driver Cache** | **File/Redis/Array, rate limiting, CLI** |

**Status:** 381 tests passing | ~67% coverage | Sprint 3.8 complete ✅

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
- 360 tests passing (100% pass rate)
  - Unit tests: 235 (91 container + 21 factory + 16 validation + 15 CLI + 13 events + 13 jobs + 15 auth + 25 http_kernel + 26 i18n)
  - Integration tests: 13
  - Contract tests: 20 (SQL generation)
  - Semantic regression tests: 9 (O(1) complexity)
- ~66% overall coverage
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
    │   ├── exceptions.py    # 🆕 Global exception handling (Sprint 3.4)
    │   └── middleware/      # 🆕 CORS, GZip, TrustedHost (Sprint 3.4)
    ├── validation/          # Form Requests & Validation (Sprint 2.9)
    ├── events/              # Event Bus & Observers (Sprint 3.1)
    ├── jobs/                # Job Queue & Workers (Sprint 3.2)
    ├── auth/                # Authentication & JWT (Sprint 3.3)
    ├── i18n/                # 🆕 Internationalization (Sprint 3.5)
    ├── cli/                 # CLI Tooling (Sprint 3.0)
    ├── models/              # Database models
    ├── resources/           # 🆕 Framework resources (Sprint 3.5)
    │   └── lang/            # Framework translations (en, pt_BR)
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
