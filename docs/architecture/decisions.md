# 🧠 Architecture Decisions

Key design decisions and trade-offs in Fast Track Framework.

## Why Repository Pattern (NOT Active Record)?

### The Problem with Active Record in Async Python

```python
# Active Record (Laravel/Django style)
user = User.find(1)
user.name = "Bob"
user.save()
```

**Issues in async Python:**
- Requires global database connection (ContextVar)
- Hidden dependencies (where does `find()` get the session?)
- Hard to test (global state)
- Breaks in background jobs, CLI tools

### Repository Pattern Solution

```python
# Repository Pattern (FTF style)
user = await repo.find(1)
user.name = "Bob"
await repo.update(user)
```

**Benefits:**
- ✅ Explicit dependencies (`repo` passed to function)
- ✅ Testable (mock the repository)
- ✅ Works everywhere (HTTP, CLI, jobs, tests)
- ✅ Type-safe (MyPy can verify)

See: `src/ftf/exercises/sprint_1_2_active_record_trap.py` for detailed explanation.

---

## Framework-Agnostic ORM (Fast Query)

### Decision: Extract Database Layer

**Sprint 2.5** extracted all ORM functionality into `fast_query` package.

**Rationale:**
- ORM should NOT depend on web framework
- Enables reuse across Flask, Django, CLI
- Clean separation of concerns
- Easier to test independently

**Result:**
```python
# fast_query has ZERO imports from fastapi or ftf
from fast_query import BaseRepository  # ✅ Works anywhere

# ftf integrates with fast_query
from ftf.http import FastTrackFramework  # Web framework layer
```

---

## Type-Hint Based DI (NOT Name-Based)

### Why Type Hints?

```python
# ✅ FTF (type-hint based)
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

# Container uses type hint to resolve

# ❌ Laravel (name-based)
class UserService:
    def __init__(self, userRepository):  # Must match binding name
        self.repo = userRepository
```

**Benefits:**
- IDE autocomplete works
- MyPy validates dependencies
- Refactoring is safer (rename tracking)
- No magic strings

---

## Design Principles

1. **Explicit over Implicit** - Following Zen of Python
2. **Async-Native** - No sync fallbacks, pure asyncio
3. **Type Safety First** - Leverage Python's type system
4. **Test-Driven** - Every feature starts with tests
5. **Educational** - Code comments explain "why", not just "what"

---

See [Sprint 2.5 Summary](../history/sprint-2-5-summary.md) for implementation details.
