# 🚀 Fast Track Framework

> **Laravel's Developer Experience + Python's Async Performance** — Production-ready micro-framework built on FastAPI.

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/tests-467%20passed-brightgreen.svg)](https://github.com/eveschipfer/fast-track-framework)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/eveschipfer/fast-track-framework)
[![Sprint](https://img.shields.io/badge/sprint-11.0%20complete-brightgreen.svg)](https://github.com/eveschipfer/fast-track-framework)

---

## 🎯 Vision

Fast Track Framework (FTF) is a **production-ready web framework** built on the philosophy that great developer experience doesn't require sacrificing performance. We combine Laravel's ergonomic conventions with Python's async capabilities.

**Core Philosophy:**
- ✅ **Developer Experience First** — Convention over configuration, intuitive APIs.
- ✅ **Type-Safe** — Strict MyPy, zero `Any` types, full IDE autocomplete.
- ✅ **Async-Native** — Built on `asyncio`, not an afterthought.
- ✅ **Explicit Dependencies** — No magic, IoC Container with type-hint based DI.
- ✅ **Educational** — Every architectural decision documented with "why".

> **Status:** v1.0 Core Architecture Complete — Ready for production applications.

---

## ✨ Features

### 🏗️ Core (v1.0 Ready)

| Feature | Description | Status |
|---------|-------------|--------|
| **IoC Container** | Type-hint based DI (singleton/scoped/transient) | ✅ Production |
| **Service Providers** | Laravel-inspired two-phase boot architecture | ✅ Sprint 5.2 |
| **Type-Safe Config** | Pydantic Settings with runtime validation | ✅ Sprint 7.0 |
| **CLI Modernization** | Full IoC integration with provider boot | ✅ Sprint 9.0 |

### 📊 Data Layer

| Feature | Description | Status |
|---------|-------------|--------|
| **Hybrid Repository** | SQLAlchemy 2.0 syntax + helper methods (`find`, `create`) | ✅ Sprint 8.0 |
| **Query Builder** | Laravel Eloquent-inspired fluent interface | ✅ Sprint 2.3 |
| **Factories & Seeders** | Laravel-inspired test data with Faker | ✅ Sprint 2.8 |
| **Pagination Engine** | Length-aware and cursor pagination | ✅ Sprint 5.5 |

### 🔐 Authentication & Authorization

| Feature | Description | Status |
|---------|-------------|--------|
| **Guard Pattern (Auth 2.0)** | `AuthManager` facade with pluggable guards | ✅ Sprint 10.0 |
| **RBAC Gates System** | Gates, Policies, secure-by-default | ✅ Sprint 5.5 |
| **JWT Tokens** | Built-in `JwtGuard` with token refresh | ✅ Sprint 10.0 |

### ✅ Validation (v1.0 Ready)

| Feature | Description | Status |
|---------|-------------|--------|
| **Validation 2.0** | FormRequests with **Method Injection** (Container integrated) | ✅ Sprint 11.0 |
| **Custom Rules** | Pydantic v2 validators with CLI scaffolding | ✅ Sprint 3.6 |
| **i18n Support** | Multi-language error messages | ✅ Sprint 3.5 |

### 🛠️ DevOps & Infrastructure

| Feature | Description | Status |
|---------|-------------|--------|
| **Job Queue** | SAQ integration with class-based jobs | ✅ Sprint 3.2 |
| **Task Scheduler** | `@Schedule.cron()` decorators | ✅ Sprint 3.8 |
| **Mailer System** | Multi-driver (Log/Array/SMTP) with Jinja2 | ✅ Sprint 4.0 |
| **Storage System** | Local/S3/Memory drivers with async I/O | ✅ Sprint 4.1 |

---

## 🚀 Architecture in Action

### 1. Controller with Dependency Injection

Clean, class-based controllers with automatic dependency injection.

```python
from ftf.http import Controller, Get, Post, Inject
from app.repositories import UserRepository
from app.requests import StoreUserRequest

class UserController(Controller):
    def __init__(self, repo: UserRepository = Inject()):
        self.repo = repo  # Auto-injected by Container

    @Get("/")
    async def index(self):
        return await self.repo.all()

    @Post("/")
    async def store(self, request: StoreUserRequest):
        # Request is already Validated & Authorized
        return await self.repo.create(request.model_dump())
```

### 2. Validation 2.0 (Method Injection) ⚡

The power of Sprint 11: Inject Repositories directly into your validation rules. No more hardcoded sessions!

```python
from ftf.validation import FormRequest, Rule
from app.repositories import UserRepository

class StoreUserRequest(FormRequest):
    name: str
    email: str

    # ✨ Method Injection: The Container injects UserRepository automatically
    async def rules(self, user_repo: UserRepository):
        # Async database check using the injected repo
        await Rule.unique(user_repo, "email", self.email)

        if self.email.endswith("@spam.com"):
            self.stop("Domains from spam.com are not allowed.")
```

### 3. Authentication 2.0 (Guard Pattern) 🔐

The power of Sprint 10: Modular authentication via Facade.

```python
from ftf.auth import AuthManager

@Get("/profile")
async def profile(self):
    # Uses the default configured guard (JWT, Session, etc)
    user = await AuthManager.user()
    return {"id": user.id, "name": user.name}
```

### 4. Task Scheduling

```python
from ftf.jobs import Schedule

@Schedule.cron("0 * * * *")
async def hourly_cleanup():
    await UserRepository.query().where("status", "inactive").delete()
```

---

## 🛣️ Road to v1.0

### ✅ Complete (Core v1.0)
- [x] IoC Container with type-hint DI
- [x] Service Provider architecture
- [x] Hybrid Repository (SQLAlchemy 2.0 + helpers)
- [x] Type-Safe Configuration (Pydantic Settings)
- [x] Validation 2.0 with Method Injection
- [x] Authentication 2.0 (Guard Pattern)
- [x] CLI Modernization
- [x] Job Queue & Task Scheduler
- [x] Mailer & Storage systems

### 🚀 Next Steps (Post-v1.0)
- [ ] API Resources (Transformation Layer)
- [ ] WebSockets / Real-time
- [ ] Horizon Dashboard (Job monitoring)

---

## 🏃 5-Minute Quick Start

### 1. Install

```bash
git clone https://github.com/eveschipfer/fast-track-framework.git
cd fast-track-framework
poetry install
poetry shell
```

### 2. Configure

```bash
cp .env.example .env
# Update database credentials in .env
```

### 3. Run

```bash
poetry run ftf serve
# Visit http://localhost:8000/docs
```

---

## 🧪 Testing Strategy

We maintain a strict 100% Pass Rate policy.

```bash
# Run all tests (467+ tests)
poetry run pytest workbench/tests/ -v

# Run with coverage
poetry run pytest --cov=src
```

**Quality Metrics:**
- ✅ 467 Tests Passing (Sprint 11)
- ✅ 0 Flaky Tests
- ✅ 100% Critical Path Coverage

---

## 📝 License

MIT License — see LICENSE file for details.

---

<div align="center">

**Built with ❤️ for production use**

[Quick Start](docs/guides/quickstart.md) • [IoC Container](docs/guides/container.md) • [Contributing](CONTRIBUTING.md)

</div>
