# 📚 Fast Track Framework - Documentation Hub

Complete documentation for the Fast Track Framework and Fast Query ORM.

---

## 🚀 Getting Started

**New to the project? Start here:**

1. **[Quick Start Guide](guides/quickstart.md)** — Get up and running in 5 minutes
2. **[Database & ORM Guide](guides/database.md)** — Learn Fast Query and Repository Pattern
3. **[IoC Container Guide](guides/container.md)** — Master dependency injection

---

## 📖 Guides

### Core Guides
- 📖 [**Quick Start**](guides/quickstart.md) — Installation, hello world, first API
- 🗄️ [**Database & ORM**](guides/database.md) — Fast Query package, repositories, query builder
- 🏗️ [**IoC Container**](guides/container.md) — Dependency injection, scopes, lifecycle
- 🧪 [**Testing**](guides/testing.md) — Writing tests, fixtures, best practices

---

## 🧠 Architecture

### Design Decisions
- 🧠 [**Architecture Decisions**](architecture/decisions.md) — Why Repository Pattern? Why type-hints?

**Key Concepts:**
- Repository Pattern vs Active Record
- Framework-agnostic ORM design
- Type-hint based dependency injection
- Async-first architecture

---

## 📜 Sprint History

### Recent Sprints

**Sprint 16.1 - Cleanup, Modernization & Fixes** (Latest! 🧹✨)
- 📜 [Summary](history/SPRINT_16_1_SUMMARY.md)
- Focus: Eliminate warnings, modernize to Pydantic V2, fix skipped pagination tests
- Added: Pydantic V2 `model_config`, renamed test helper classes, fixed pagination tests with in-memory SQLite
- Features: Clean test output, timezone-aware datetime, pytest warning filters
- Achievement: **All pagination tests passing!** Pydantic V2 modernized, helper classes renamed ✅
- Tests: 445 passing (100%), 5 pagination tests unskipped, 43.18% coverage ✅

**Sprint 13.0 - Deferred Service Providers (JIT Loading)** ⏱️⚡
- 📜 [Summary](history/SPRINT_13_0_SUMMARY.md)
- Focus: Just-In-Time loading of service providers for serverless optimization
- Added: Container deferred support, DeferredServiceProvider validation, JIT loading logic
- Features: O(1) deferred lookup, async boot support, 10x faster cold starts (~50ms vs ~500ms)
- Achievement: **Deferred providers working!** 40% memory reduction, serverless optimized ✅
- Tests: 477 passing (100%), 10 new deferred provider tests ✅

**Sprint 12.0 - Service Provider Hardening (Method Injection + Priority System)** ⚙️🔌
- 📜 [Summary](history/SPRINT_9_0_SUMMARY.md)
- Focus: CLI operates within Container IoC context, loads AppSettings (Sprint 7), executes Service Providers
- Added: Container boot (_boot_framework), AppSettings Pydantic integration, Container DI in db:seed
- Features: Framework client pattern, zero manual sessions, same database/engine as HTTP app
- Achievement: **CLI is framework client!** Full integration with Container & Providers ✅
- Tests: N/A (CLI refactoring, existing commands working) ✅

**Sprint 8.0 - Hybrid Async Repository (Power Mode)** 🔷⚡
- 📜 [Summary](history/SPRINT_8_0_SUMMARY.md)
- Focus: Expose SQLAlchemy 2.0's native AsyncSession, resolving "Leaky Abstraction"
- Added: Public `.session` property in BaseRepository, proof test for hybrid pattern
- Features: Helper methods + full session access (CTEs, Window Functions, Bulk Operations)
- Achievement: **Power Mode enabled!** Best of both worlds ✅
- Tests: 3/3 passing (100%) - Prova de conceito ✅

**Sprint 7.0 - Type-Safe Configuration** 🔷🔒
- 📜 [Summary](history/SPRINT_5_7_SUMMARY.md)
- Focus: Auto-configure database layer through Convention over Configuration
- Added: DatabaseServiceProvider (255 lines), string-based provider loading
- Features: Reads config/database.py, creates AsyncEngine/async_sessionmaker, registers in container
- Achievement: **Zero database boilerplate in main.py!** Convention over Configuration working ✅
- Tests: 536 passing (100%), 68.25% coverage on DatabaseServiceProvider

**Sprint 5.6 - Ultimate QueryBuilder (Pagination & Cursors)** 🔍📄
- 📜 [Summary](history/SPRINT_5_6_SUMMARY.md)
- Focus: Move pagination to QueryBuilder as terminal methods, add cursor pagination
- Added: paginate() and cursor_paginate() terminal methods in QueryBuilder
- Features: Filtered pagination, O(1) cursor-based pagination, query cloning for COUNT
- Achievement: 536 tests passing (100%), zero regression, production-ready ✅

**Sprint 5.5 - Pagination Engine & RBAC Gates System** 📄🔐
- 📜 [Summary](history/SPRINT_5_5_SUMMARY.md)
- Focus: Enterprise-grade pagination and authorization systems
- Added: 7 files (LengthAwarePaginator, Gate, Policy, Authorize, 2 test suites)
- Features: Laravel-style pagination metadata, Gates/Policies authorization, FastAPI integration
- Tests: 76 new tests (27 pagination + 49 RBAC, all passing)
- Achievement: 516 tests passing (100%), production-ready enterprise features ✅

**Sprint 5.4 - Architectural Hardening & Public API Cleanup** 🛡️
- 📜 [Summary](history/SPRINT_5_4_SUMMARY.md)
- Focus: API boundaries, stability guarantees, public/private separation, Hyrum's Law prevention
- Enhanced: 3 docstrings (fast_query stability, HTTP adapter boundary, Auth educational warning)
- Audit: Core module, CLI imports, __all__ completeness, driver encapsulation
- Achievement: 440 tests passing (100%), zero code changes needed, architecture already clean ✅

**Sprint 5.3 - Configuration System** ⚙️
- 📜 [Summary](history/SPRINT_5_3_SUMMARY.md)
- Focus: Centralized configuration management with Laravel-like config system
- Added: 6 files (ConfigRepository, global config() helper, app.py, database.py configs)
- Features: Dot notation access, auto-provider registration, environment variables, type-safe
- Achievement: 440 tests passing (100%), config-driven application, minimal main.py ✅

**Sprint 5.2 - Service Provider Architecture** 🔧
- 📜 [Summary](history/SPRINT_5_2_SUMMARY.md)
- Focus: Laravel-inspired service provider pattern for clean application bootstrapping
- Added: 9 files (ServiceProvider base, AppServiceProvider, RouteServiceProvider, routes/api.py)
- Features: Two-phase boot (register→boot), route organization, factory pattern, provider auto-boot
- Achievement: Clean separation of concerns, extensible architecture ✅

**Sprint 5.1 - The Bug Bash** 🎉
- 📜 [Summary](history/SPRINT_5_1_SUMMARY.md)
- Focus: Achieve 100% test pass rate after Sprint 5.0 monorepo refactor
- Fixed: 20 tests across 4 modules (Auth, Welcome Controller, CLI, Jobs)
- Achievement: **440 passed, 0 failed** (100% pass rate) ✅

**Sprint 5.0 - Monorepo Refactor**
- 📜 [Summary](history/SPRINT_5_0_SUMMARY.md)
- Focus: Separate framework code from application code (vendor vs app)
- Fixed: SQLAlchemy metadata conflicts, import paths, lazy loading
- Achievement: 420/440 tests passing (95.5%), monorepo structure

**Sprint 3.8 - Async Jobs & Task Scheduler**
- 📜 [Summary](history/SPRINT_3_8_SUMMARY.md)
- Focus: Task scheduling with cron expressions and intervals using SAQ + Redis
- Added: 9 files (schedule system, providers, CLI), 21 tests (100% coverage)
- Features: @Schedule.cron(), @Schedule.every(), QueueProvider, Redis verification, queue:list

**Sprint 3.7 - Multi-Driver Caching & Rate Limiting**
- 📜 [Summary](history/SPRINT_3_7_SUMMARY.md)
- Focus: Production-ready caching with multi-driver architecture and rate limiting
- Added: 9 files (cache drivers, middleware, CLI), 4 commands
- Features: File/Redis/Array drivers, ThrottleMiddleware, pickle serialization, atomic operations

**Sprint 3.6 - Custom Validation Rules CLI**
- 📜 [Summary](history/SPRINT_3_6_SUMMARY.md)
- Focus: Generate Pydantic v2 validation rules with ftf make rule command
- Added: ftf make rule command, to_pascal_case function, get_rule_template
- Features: Pydantic AfterValidator pattern, i18n integration, stateful validators

**Sprint 3.5 - i18n System & CLI Extensibility**
- 📜 [Summary](history/SPRINT_3_5_SUMMARY.md)
- Focus: Multi-language support with JSON translations and CLI extensibility
- Added: 26 tests (100% passing, 96.83% coverage on i18n module)
- Features: Translator singleton, dot notation keys, placeholders, make:cmd, make:lang

**Sprint 3.4 - HTTP Kernel & Exception Handler**
- 📜 [Summary](history/SPRINT_3_4_SUMMARY.md)
- Focus: Centralized exception handling and middleware configuration
- Added: 25 tests (100% passing, 93%+ coverage)
- Features: Global exception handlers, CORS, GZip, TrustedHost, make:middleware

**Sprint 3.3 - Authentication & JWT**
- 📜 [Summary](history/SPRINT_3_3_SUMMARY.md)
- Focus: Stateless authentication with JWT and bcrypt
- Added: 22 tests (15 passing - JWT + AuthGuard 100%)
- Features: JWT tokens, bcrypt passwords, AuthGuard, CurrentUser, make:auth scaffolding

**Sprint 3.2 - Job Queue & Workers**
- 📜 [Summary](history/SPRINT_3_2_SUMMARY.md)
- Focus: Background processing with SAQ and Bridge Pattern
- Added: 13 tests for Job, runner, JobManager
- Features: Class-based jobs, DI support, queue:work/dashboard commands, 91.94% coverage

**Sprint 3.1 - Event Bus & Observer Pattern**
- 📜 [Summary](history/SPRINT_3_1_SUMMARY.md)
- Focus: Async event-driven architecture with IoC integration
- Added: 13 tests for Event, Listener, EventDispatcher
- Features: Observer Pattern, generic Listener[E], concurrent execution, CLI scaffolding

**Sprint 3.0 - CLI Tooling & Scaffolding**
- 📜 [Summary](history/SPRINT_3_0_SUMMARY.md)
- Focus: Transform from library to framework with scaffolding CLI
- Added: 15 tests for CLI commands
- Features: make:* commands (model, repository, request, factory, seeder), db:seed

**Sprint 2.9 - Form Requests & Async Validation**
- 📜 [Summary](history/SPRINT_2_9_SUMMARY.md)
- Focus: Laravel-inspired validation with async DB checks
- Added: 16 tests for FormRequest and validation rules
- Features: Async authorization, database validation (unique, exists)

**Sprint 2.8 - Factory & Seeder System**
- 📜 [Summary](history/SPRINT_2_8_SUMMARY.md)
- Focus: Laravel-inspired test data generation
- Added: 21 tests for factories and seeders
- Features: Model factories, database seeders, Faker integration

**Sprint 2.7 - Contract Tests & Semantic Regression**
- 📜 [Summary](history/SPRINT_2_7_SUMMARY.md)
- Focus: Quality engineering, performance as correctness
- Added: 29 tests (20 contract + 9 semantic)
- Tests SQL generation and O(1) query complexity

**Sprint 2.6 - Advanced Query Builder**
- 📜 [Summary](history/SPRINT_2_6_SUMMARY.md)
- Focus: Nested eager loading, global scopes, local scopes, where_has
- Added: 22 advanced feature tests

**Sprint 2.5 - Fast Query Package**
- 📜 [Summary](history/sprint-2-5-summary.md)
- Focus: Extract ORM to standalone package
- Result: Framework-agnostic fast_query package

**Sprint 2.4 - Relationship Stress Tests**
- 📜 [Summary](history/SPRINT_2_4_SUMMARY.md)
- Focus: N+1 prevention validation
- Added: 12 integration tests

**Sprint 2.3 - Query Builder & Relationships**
- 📜 [Summary](history/SPRINT_2_3_SUMMARY.md)
- Focus: Fluent query builder, model relationships
- Added: 38 query builder tests

**Sprint 2.2 - Database Foundation**
- 📜 [Summary](history/SPRINT_2_2_SUMMARY.md)
- 📜 [Implementation Guide](history/SPRINT_2_2_DATABASE_IMPLEMENTATION.md)
- 📜 [Test Results](history/SPRINT_2_2_TEST_RESULTS.md)
- Focus: SQLAlchemy, Repository Pattern, Alembic

**Sprint 2.1 - FastAPI Integration**
- 📜 [Summary](history/SPRINT_2_1_SUMMARY.md)
- Focus: HTTP integration, routing, middleware

### All Sprints
- 📂 [**Complete Sprint History**](history/) — All sprint summaries and reports

---

## 📐 Implementation Guides

**Detailed implementation guides for major sprints:**

These guides provide comprehensive technical details, architecture decisions, and implementation patterns for major framework features. Perfect for understanding the "how" and "why" behind each sprint.

### Recent Implementations

- 📐 [**Sprint 5.3 Implementation**](SPRINT_5_3_IMPLEMENTATION.md) — Configuration System
  - ConfigRepository singleton with dot notation
  - Dynamic Python module loading
  - Auto-provider registration
  - Environment variable support
  - 500+ lines of detailed implementation guide

- 📐 [**Sprint 5.2 Implementation**](SPRINT_5_2_IMPLEMENTATION.md) — Service Provider Architecture
  - ServiceProvider base class design
  - Two-phase initialization (register → boot)
  - Provider auto-registration system
  - Route organization patterns
  - 500+ lines of detailed implementation guide

**When to use these guides:**
- 🔍 **Deep Dive**: Understanding implementation details beyond sprint summaries
- 🏗️ **Architecture**: Learning design patterns and decisions
- 🧪 **Testing**: Seeing how features were tested and validated
- 🎓 **Education**: Learning modern Python framework architecture

---

## 🔬 Quality Reports

### Validation Reports
- 🔬 [**Async Concurrency Validation**](quality/ASYNC_CONCURRENCY_VALIDATION.md) — Async isolation analysis
- 🛡️ [**Lifecycle Management Validation**](quality/LIFECYCLE_MANAGEMENT_VALIDATION.md) — Resource cleanup guide
- 🧪 [**Dependency Override Validation**](quality/DEPENDENCY_OVERRIDE_VALIDATION.md) — Testing patterns guide
- 📊 [**Technical Debt Resolution**](quality/TECHNICAL_DEBT_RESOLUTION.md) — Complete quality report
- 🟡 [**Async Boot in Sync Context (TD-001)**](quality/ASYNC_BOOT_SYNC_CONTEXT.md) — Serverless async boot risk analysis

### Testing Documentation
- 🧪 [**Testing Guide**](guides/testing.md) — How to write and run tests
- 🔬 [**Contract Tests**](../tests/contract/) — SQL generation contracts
- 📊 [**Benchmark Tests**](../tests/benchmarks/) — Semantic regression tests

---

## 📊 Test Metrics

**Current Status (Sprint 13.0):**
- **Total Tests:** 496 (100% critical passing, 19 skipped)
  - Unit Tests: 433 (91 container + 21 factory + 16 validation + 15 CLI + 13 events + 13 jobs + 15 auth + 25 http_kernel + 26 i18n + 21 schedule + 10 deferred providers + 147 query builder + 17 repository + 23 pagination)
  - Integration Tests: 46
  - Contract Tests: 20
  - Semantic/Benchmark Tests: 9
  - Advanced Query Builder: 22

- **Coverage:**
  - Overall: ~49%
  - Models: 100%
  - Query Builder: 87%
  - Container: 86%
  - Factories: 100%
  - Validation: 71-94%
  - CLI: 85%
  - Events: 100%
  - Jobs: 91.94%
  - Auth: 92.11% (JWT), 78.12% (Guard)
  - HTTP Kernel: 93.62% (Exceptions), 85.29% (Middleware)
  - i18n: 96.83% (Core), 100% (Helpers)
  - Schedule: 100% (Core)
  - Deferred Providers: 100%

---

## 🗂️ Documentation Structure

```
docs/
├── README.md                    # This file (documentation hub)
├── guides/                      # User guides
│   ├── quickstart.md           # Quick start guide
│   ├── database.md             # Database & ORM guide
│   ├── container.md            # IoC Container guide
│   └── testing.md              # Testing guide
├── architecture/                # Architecture & design
│   └── decisions.md            # Design decisions & rationale
├── history/                     # Sprint summaries
│   ├── SPRINT_13_0_SUMMARY.md  # Deferred Service Providers (latest)
│   ├── SPRINT_12_0_SUMMARY.md  # Service Provider Hardening
│   ├── SPRINT_11_0_SUMMARY.md  # Validation Engine 2.0
│   ├── SPRINT_10_0_SUMMARY.md  # Authentication 2.0
│   ├── SPRINT_9_0_SUMMARY.md   # CLI Modernization
│   ├── SPRINT_5_7_SUMMARY.md   # Database Service Provider
│   ├── SPRINT_5_6_SUMMARY.md   # Ultimate QueryBuilder
│   ├── SPRINT_5_5_SUMMARY.md   # Pagination & RBAC
│   ├── SPRINT_5_4_SUMMARY.md   # Architectural Hardening
│   ├── SPRINT_5_3_SUMMARY.md   # Configuration System
│   ├── SPRINT_5_2_SUMMARY.md   # Service Provider Architecture
│   ├── SPRINT_3_8_SUMMARY.md   # Async Jobs & Scheduler
│   ├── SPRINT_3_7_SUMMARY.md   # Multi-Driver Caching
│   ├── SPRINT_3_6_SUMMARY.md   # Custom Validation Rules
│   ├── SPRINT_3_5_SUMMARY.md   # i18n & CLI
│   ├── SPRINT_3_4_SUMMARY.md   # HTTP Kernel
│   ├── SPRINT_3_3_SUMMARY.md   # Authentication
│   ├── SPRINT_3_2_SUMMARY.md   # Job Queue
│   ├── SPRINT_3_1_SUMMARY.md   # Event Bus
│   ├── SPRINT_3_0_SUMMARY.md   # CLI Tooling
│   ├── SPRINT_2_9_SUMMARY.md   # Form Requests
│   ├── SPRINT_2_8_SUMMARY.md   # Factories & Seeders
│   └── ... (earlier sprints)
└── quality/                     # Quality reports
    ├── ASYNC_CONCURRENCY_VALIDATION.md
    ├── LIFECYCLE_MANAGEMENT_VALIDATION.md
    ├── DEPENDENCY_OVERRIDE_VALIDATION.md
    └── TECHNICAL_DEBT_RESOLUTION.md
```

---

## 🎯 Quick Links

### For New Developers
1. [Quick Start](guides/quickstart.md) → Install and run
2. [Database Guide](guides/database.md) → Build your first CRUD API
3. [Testing Guide](guides/testing.md) → Write tests

### For Contributors
1. [Architecture Decisions](architecture/decisions.md) → Understand design choices
2. [Quality Reports](quality/) → See validation reports
3. [Sprint History](history/) → Understand evolution

### For Advanced Users
1. [IoC Container Deep Dive](guides/container.md) → Master DI
2. [Advanced Query Features](guides/database.md#advanced-query-features-sprint-26) → Nested loading, scopes
3. [Contract Testing](../tests/contract/) → Prevent regressions

---

## 📈 Framework Evolution

### Phase 1: Foundation (Sprints 1.x)
- Async Python fundamentals
- IoC Container with DI
- Type safety and testing

### Phase 2: Database Layer (Sprints 2.1-2.5)
- FastAPI integration
- SQLAlchemy 2.0 with Repository Pattern
- Query Builder with relationships
- Framework-agnostic ORM extraction

### Phase 3: Advanced Features (Sprints 2.6-2.7)
- Nested eager loading with dot notation
- Global scopes (soft deletes)
- Local scopes and relationship filters
- Contract tests and semantic regression prevention

### Phase 4: Production Ready (Sprints 2.8+)
- CLI tools (Artisan-like)
- Authentication system
- Event dispatcher
- Background jobs

---

## 🔍 Find What You Need

### "I want to..."

**...learn the basics**
→ [Quick Start Guide](guides/quickstart.md)

**...build a CRUD API**
→ [Database Guide](guides/database.md)

**...understand dependency injection**
→ [IoC Container Guide](guides/container.md)

**...write tests**
→ [Testing Guide](guides/testing.md)

**...prevent N+1 queries**
→ [Database Guide - Eager Loading](guides/database.md#eager-loading)

**...understand design decisions**
→ [Architecture Decisions](architecture/decisions.md)

**...see how the framework evolved**
→ [Sprint History](history/)

**...review code quality**
→ [Quality Reports](quality/)

---

## 📝 Documentation Standards

All documentation in this project follows these principles:

1. **Educational First** — Explain "why", not just "what"
2. **Code Examples** — Show, don't just tell
3. **Progressive Disclosure** — Simple first, advanced later
4. **Cross-Referenced** — Link related concepts
5. **Up-to-Date** — Updated with each sprint

---

## 🤝 Contributing to Docs

Found a typo? Have a suggestion? Documentation improvements are welcome!

1. Documentation source: `docs/`
2. Follow existing structure and style
3. Include code examples
4. Test code examples work
5. Update this index if adding new docs

---

**Last Updated:** Sprint 13.0 (February 2026)
**Total Documentation:** 29 files
**Lines of Documentation:** ~22,650 lines
