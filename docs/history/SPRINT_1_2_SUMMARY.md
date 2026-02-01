# Sprint 1.2 Summary - IoC Container & Dependency Injection

**Sprint Duration**: Early Development Phase
**Sprint Goal**: Build type-hint based IoC container with three lifetime scopes
**Status**: ✅ Complete

---

## 📋 Overview

Sprint 1.2 implemented the core IoC (Inversion of Control) Container that powers dependency injection throughout the Fast Track Framework. Unlike Laravel's name-based resolution, this container uses Python's type hints for automatic dependency resolution.

### Objectives

1. ✅ Implement type-hint based dependency resolution
2. ✅ Support three lifetime scopes (Singleton, Scoped, Transient)
3. ✅ Detect and prevent circular dependencies
4. ✅ Support constructor injection with nested dependencies
5. ✅ Create educational examples showing Active Record anti-pattern

---

## 🎯 What Was Built

### 1. Core IoC Container

**File**: `src/ftf/core/container.py`

**Key Features**:
- Type-hint based resolution (not name-based)
- Three lifetime scopes
- Circular dependency detection
- Automatic nested dependency resolution

**Implementation**:
```python
from typing import Type, TypeVar, get_type_hints

T = TypeVar('T')

class Container:
    """IoC Container with type-hint based dependency injection."""

    def __init__(self):
        self._registrations: Dict[Type, Registration] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_cache: Dict[Type, Any] = {}

    def register(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        scope: Literal["singleton", "scoped", "transient"] = "transient"
    ) -> None:
        """
        Register a service with the container.

        Args:
            service_type: Type to resolve
            implementation: Concrete implementation (optional)
            scope: Lifetime scope (singleton/scoped/transient)
        """
        if implementation is None:
            implementation = service_type

        self._registrations[service_type] = Registration(
            service_type=service_type,
            implementation=implementation,
            scope=scope
        )

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service from the container.

        Args:
            service_type: Type to resolve

        Returns:
            Instance of requested type

        Raises:
            DependencyResolutionError: If type not registered
            CircularDependencyError: If circular dependency detected
        """
        # Check for circular dependencies
        if service_type in self._resolution_stack:
            raise CircularDependencyError(
                f"Circular dependency detected: {service_type}"
            )

        # Get registration
        registration = self._get_registration(service_type)

        # Singleton: return cached instance
        if registration.scope == "singleton":
            if service_type not in self._singletons:
                instance = self._create_instance(registration)
                self._singletons[service_type] = instance
            return self._singletons[service_type]

        # Scoped: return cached instance for current scope
        elif registration.scope == "scoped":
            if service_type not in self._scoped_cache:
                instance = self._create_instance(registration)
                self._scoped_cache[service_type] = instance
            return self._scoped_cache[service_type]

        # Transient: always create new instance
        else:
            return self._create_instance(registration)

    def _create_instance(self, registration: Registration) -> Any:
        """Create instance with automatic dependency injection."""
        implementation = registration.implementation

        # Get constructor parameters via type hints
        hints = get_type_hints(implementation.__init__)

        # Resolve dependencies
        dependencies = {}
        for param_name, param_type in hints.items():
            if param_name == "return":
                continue
            dependencies[param_name] = self.resolve(param_type)

        # Create instance with injected dependencies
        return implementation(**dependencies)
```

### 2. Lifetime Scopes

**Three Scopes**:

1. **Singleton** - Application Lifetime
```python
# Database engine: shared across entire application
container.register(AsyncEngine, scope="singleton")

# One instance for app lifetime
engine1 = container.resolve(AsyncEngine)
engine2 = container.resolve(AsyncEngine)
assert engine1 is engine2  # Same instance
```

2. **Scoped** - Request Lifetime
```python
# Database session: one per HTTP request
container.register(AsyncSession, scope="scoped")

# Same instance within request
session1 = container.resolve(AsyncSession)
session2 = container.resolve(AsyncSession)
assert session1 is session2  # Same within scope

# Clear scope (end of request)
container.clear_scoped_cache()

# New instance in new scope
session3 = container.resolve(AsyncSession)
assert session1 is not session3  # Different scope
```

3. **Transient** - Always New
```python
# Repository: new instance every time
container.register(UserRepository, scope="transient")

# Always different instances
repo1 = container.resolve(UserRepository)
repo2 = container.resolve(UserRepository)
assert repo1 is not repo2  # Different instances
```

### 3. Automatic Dependency Resolution

**Nested Dependencies**:
```python
class Database:
    def __init__(self):
        self.connected = True

class UserRepository:
    def __init__(self, db: Database):
        self.db = db

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

# Register
container.register(Database, scope="singleton")
container.register(UserRepository)
container.register(UserService)

# Resolve - automatically injects Database into Repository into Service
service = container.resolve(UserService)
# UserService → UserRepository → Database (auto-injected)
```

### 4. Circular Dependency Detection

**Problem**:
```python
class ServiceA:
    def __init__(self, b: 'ServiceB'):
        self.b = b

class ServiceB:
    def __init__(self, a: ServiceA):
        self.a = a

# This would cause infinite recursion!
container.register(ServiceA)
container.register(ServiceB)
```

**Solution**: Container detects and raises error
```python
try:
    service = container.resolve(ServiceA)
except CircularDependencyError as e:
    print(f"Circular dependency: {e}")
    # "Circular dependency detected: ServiceA -> ServiceB -> ServiceA"
```

---

## 🎓 Key Learnings

### 1. Why NOT Active Record in Async Python?

**File**: `src/ftf/exercises/sprint_1_2_active_record_trap.py`

**The Problem**:
```python
# Laravel Active Record (works in PHP)
class User(Model):
    # ...

user = User.find(123)  # How does this get DB connection?
user.save()  # Magic global connection!

# Python Async (doesn't work well)
class User(Base):
    async def save(self):
        # Where does session come from?
        # Global state? ContextVar? 🤔
        await session.commit()
```

**Why It Fails**:
- Async Python needs explicit async context
- Global state breaks testability
- ContextVars are complex and error-prone
- Explicit is better than implicit (Zen of Python)

**Solution**: Repository Pattern with DI
```python
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session  # Explicit dependency

    async def save(self, user: User) -> None:
        self.session.add(user)
        await self.session.commit()

# Clear dependency flow
repo = UserRepository(session)
await repo.save(user)
```

### 2. Type Hints vs Name-Based Resolution

**Laravel (Name-Based)**:
```php
class UserController {
    public function __construct(UserRepository $repo) {
        // Resolved by class name string
    }
}
```

**Fast Track (Type-Hint Based)**:
```python
class UserController:
    def __init__(self, repo: UserRepository):
        # Resolved by type hint (Type[UserRepository])
        self.repo = repo
```

**Benefits**:
- ✅ Type-safe (MyPy validates)
- ✅ IDE autocomplete works
- ✅ Refactoring-friendly
- ✅ No string-based magic

### 3. Scoped Lifetime for Request Context

**Problem**: Database sessions must be request-scoped

**Wrong** (Singleton):
```python
# ❌ Shared session across all requests (bad!)
container.register(AsyncSession, scope="singleton")

# Request 1 and Request 2 share same session
# Transactions get mixed up! 💥
```

**Right** (Scoped):
```python
# ✅ New session per request
container.register(AsyncSession, scope="scoped")

# Request lifecycle:
# 1. Request starts → create session
# 2. Request processes → use session
# 3. Request ends → clear_scoped_cache() → session closed
```

---

## 📊 Files Created

1. **`src/ftf/core/container.py`** - Core IoC container
2. **`src/ftf/core/exceptions.py`** - DI exceptions
3. **`src/ftf/core/__init__.py`** - Public API
4. **`src/ftf/exercises/sprint_1_2_demo.py`** - DI examples
5. **`src/ftf/exercises/sprint_1_2_active_record_trap.py`** - Educational anti-pattern

---

## 🔄 Comparison with Laravel

| Feature | Laravel | Fast Track |
|---------|---------|------------|
| **Resolution** | Name-based (`UserRepository::class`) | Type-hint based (`UserRepository`) |
| **Lifetimes** | Singleton, Bind, Scoped | Singleton, Scoped, Transient |
| **Registration** | `$app->bind(Repo::class, RepoImpl::class)` | `container.register(Repo, RepoImpl)` |
| **Resolution** | `$app->make(Repo::class)` | `container.resolve(Repo)` |
| **Circular** | Runtime error | Detected and fails fast |
| **Type Safety** | Runtime (PHP) | Compile-time (MyPy) |

---

## 📈 Sprint Metrics

```
Files Created:     5 (container + exceptions + examples)
Lines of Code:     ~800
Tests:             37 (Sprint 1.3 added comprehensive tests)
Key Concepts:      3 (Singleton, Scoped, Transient)
Patterns:          IoC, DI, Strategy Pattern
Status:            ✅ Complete
```

---

## 🚀 Real-World Usage in Framework

This container powers all dependency injection:

### FastAPI Integration (Sprint 2.1)
```python
from ftf.http import Inject

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    repo: UserRepository = Inject(UserRepository)
):
    # Container automatically injects UserRepository
    return await repo.find_or_fail(user_id)
```

### Database Layer (Sprint 2.2+)
```python
# Register database components
container.register(AsyncEngine, scope="singleton")
container.register(AsyncSession, scope="scoped")
container.register(UserRepository, scope="transient")

# Automatic injection chain:
# UserRepository → AsyncSession → AsyncEngine
```

---

## 🎯 Sprint Success Criteria

- ✅ **Type-Hint Resolution**: Use Python type hints for DI
- ✅ **Three Scopes**: Singleton, Scoped, Transient
- ✅ **Nested Dependencies**: Automatic recursive resolution
- ✅ **Circular Detection**: Fail fast on circular dependencies
- ✅ **Educational**: Document why not Active Record
- ✅ **Foundation**: Ready for framework integration

---

## 🏆 Sprint Completion

**Status**: ✅ Complete
**Next Sprint**: Sprint 1.3 - Container Hardening (Async, Lifecycle, Override)

**Sprint 1.2 delivered**:
- ✅ Core IoC Container implementation
- ✅ Three lifetime scopes
- ✅ Type-hint based resolution
- ✅ Circular dependency detection
- ✅ Educational anti-pattern examples
- ✅ Foundation for framework DI

**Impact**: Every dependency injection in the framework uses this container.

---

**Built with ❤️ for understanding Dependency Injection**
