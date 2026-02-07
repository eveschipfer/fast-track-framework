# 📋 Sprint 2.8 Summary - Factory & Seeder System

**Sprint Goal:** Implement a Laravel-inspired Factory & Seeder system for generating test data

**Status:** ✅ Complete
**Date:** January 31, 2026
**Tests:** 21/21 passing (100%)
**New Features:** Model Factories, Database Seeders, Faker Integration

---

## 🎯 Objective

Create a comprehensive system for generating test data that is:
- **Async-first** - Full async/await support for database operations
- **Type-safe** - Strict type hints with MyPy compliance
- **Laravel-inspired** - Familiar API for Laravel developers
- **Integrated** - Works seamlessly with fast_query ORM
- **Faker-powered** - Realistic fake data using the Faker library

---

## ✨ Features Implemented

### 1. Factory Base Class (`src/fast_query/factories.py`)

A generic `Factory[T]` class that provides:

```python
from fast_query import Factory
from fast_query import get_session

class UserFactory(Factory[User]):
    _model_class = User

    def definition(self) -> dict[str, Any]:
        return {
            "name": self.faker.name(),
            "email": self.faker.email(),
        }

# Usage
async with get_session() as session:
    factory = UserFactory(session)

    # Create unpersisted instance
    user = factory.make()

    # Create and persist
    user = await factory.create()

    # Create multiple
    users = await factory.create_batch(10)
```

**Key Methods:**
- ✅ `definition()` - Abstract method defining default attributes
- ✅ `make(**kwargs)` - Creates unpersisted instance
- ✅ `create(**kwargs)` - Creates and persists instance
- ✅ `create_batch(count, **kwargs)` - Creates multiple instances
- ✅ `state(modifier)` - Applies state transformations
- ✅ `after_create(hook)` - Registers post-creation hooks
- ✅ `reset()` - Clears all states and hooks

### 2. State Management

Factories support state transformations via method chaining:

```python
# Create admin user
admin = await factory.state(
    lambda attrs: {**attrs, "is_admin": True}
).create()

# Chain multiple states
user = await (
    factory
    .state(lambda a: {**a, "name": "Admin"})
    .state(lambda a: {**a, "email": "admin@test.com"})
    .create()
)
```

**Features:**
- ✅ Immutable pattern (returns new factory instance)
- ✅ Method chaining support
- ✅ Multiple states can be stacked
- ✅ States applied in order

### 3. Relationship Hooks

"Magic methods" for creating related models:

```python
# Create user with 5 posts
user = await factory.has_posts(5).create()

# Create post with 10 comments
post = await factory.has_comments(10).create(user_id=user.id)

# Works with batch creation
users = await factory.has_posts(3).create_batch(10)
# Creates 10 users, each with 3 posts (30 posts total)
```

**Implementation:**
- ✅ Generic `has_relationship()` helper
- ✅ Supports additional attributes via **kwargs
- ✅ Async hooks execute after model creation
- ✅ Works with `create()` and `create_batch()`

### 4. Seeder Base Class (`src/fast_query/seeding.py`)

Abstract base class for database seeders:

```python
from fast_query.seeding import Seeder

class UserSeeder(Seeder):
    async def run(self) -> None:
        factory = UserFactory(self.session)
        await factory.create_batch(10)

class DatabaseSeeder(Seeder):
    async def run(self) -> None:
        await self.call(UserSeeder)
        await self.call(PostSeeder)

# Run seeders
async with get_session() as session:
    seeder = DatabaseSeeder(session)
    await seeder.run()
```

**Key Features:**
- ✅ Abstract `run()` method for seeding logic
- ✅ `call(seeder_class)` for orchestrating other seeders
- ✅ Helper functions: `run_seeder()`, `run_seeders()`
- ✅ Full async support

### 5. Faker Integration

Built-in Faker instance for realistic fake data:

```python
def definition(self) -> dict[str, Any]:
    return {
        "name": self.faker.name(),            # "John Doe"
        "email": self.faker.email(),           # "john@example.com"
        "bio": self.faker.paragraph(),         # Random paragraph
        "age": self.faker.random_int(18, 80),  # Random age
    }
```

**Benefits:**
- ✅ Unique data for each instance
- ✅ Realistic test data
- ✅ No manual data generation
- ✅ Hundreds of faker providers available

---

## 📦 Implementation Files

### Core Implementation

1. **`src/fast_query/factories.py`** (419 lines)
   - Generic `Factory[T]` base class
   - State management system
   - Relationship hook system
   - `has_relationship()` helper

2. **`src/fast_query/seeding.py`** (165 lines)
   - `Seeder` abstract base class
   - `run_seeder()` helper function
   - `run_seeders()` helper for multiple seeders

### Example Implementations

3. **`tests/factories/model_factories.py`** (210 lines)
   - `UserFactory` - User model factory
   - `PostFactory` - Post model factory
   - `CommentFactory` - Comment model factory
   - Demonstrates relationship hooks

4. **`tests/seeders/database_seeder.py`** (150 lines)
   - `UserSeeder` - Seeds users with posts
   - `DatabaseSeeder` - Master seeder
   - `AdminSeeder` - Example specialized seeder
   - `DevelopmentDataSeeder` - Rich dev dataset

### Tests

5. **`tests/unit/test_factories.py`** (500 lines)
   - 21 comprehensive test cases
   - Tests all factory features
   - Tests seeder orchestration
   - Integration tests for complex scenarios

---

## 🧪 Test Coverage

**Total Tests:** 21/21 passing (100%)

### Factory Tests (15 tests)

**Basic Operations:**
- ✅ `make()` creates unpersisted instance
- ✅ `make()` accepts attribute overrides
- ✅ `create()` persists to database
- ✅ `create()` accepts attribute overrides
- ✅ `create_batch()` creates multiple records
- ✅ `create_batch()` applies shared attributes

**State Management:**
- ✅ `state()` modifies attributes
- ✅ Multiple states can be chained
- ✅ `state()` doesn't mutate original factory
- ✅ `reset()` clears all states

**Relationship Hooks:**
- ✅ `has_posts()` creates related posts
- ✅ Relationship hooks work with `create_batch()`

**Complex Scenarios:**
- ✅ Models with required foreign keys work
- ✅ Nested relationships (user -> posts -> comments)
- ✅ Faker generates unique data per instance

### Seeder Tests (5 tests)

- ✅ `Seeder.run()` executes seeding logic
- ✅ `Seeder.call()` orchestrates other seeders
- ✅ `run_seeder()` helper function works
- ✅ `run_seeders()` runs multiple seeders
- ✅ Realistic blog dataset creation

### Error Handling Tests (1 test)

- ✅ Factory raises error without `_model_class`

---

## 📊 Test Results

```bash
$ poetry run pytest tests/unit/test_factories.py -v

======================= 21 passed, 68 warnings in 6.05s ========================

tests/unit/test_factories.py::test_factory_make_creates_unpersisted_instance PASSED
tests/unit/test_factories.py::test_factory_make_accepts_attribute_overrides PASSED
tests/unit/test_factories.py::test_factory_create_persists_to_database PASSED
tests/unit/test_factories.py::test_factory_create_accepts_attribute_overrides PASSED
tests/unit/test_factories.py::test_factory_create_batch_creates_multiple_records PASSED
tests/unit/test_factories.py::test_factory_create_batch_accepts_shared_attributes PASSED
tests/unit/test_factories.py::test_factory_state_modifies_attributes PASSED
tests/unit/test_factories.py::test_factory_state_can_chain_multiple_modifiers PASSED
tests/unit/test_factories.py::test_factory_state_does_not_mutate_original_factory PASSED
tests/unit/test_factories.py::test_factory_reset_clears_states PASSED
tests/unit/test_factories.py::test_factory_has_posts_creates_related_posts PASSED
tests/unit/test_factories.py::test_factory_relationship_hooks_work_with_batch PASSED
tests/unit/test_factories.py::test_factory_with_required_foreign_keys PASSED
tests/unit/test_factories.py::test_factory_nested_relationships PASSED
tests/unit/test_factories.py::test_factory_faker_generates_unique_data PASSED
tests/unit/test_factories.py::test_seeder_run_method_executes PASSED
tests/unit/test_factories.py::test_seeder_call_runs_other_seeders PASSED
tests/unit/test_factories.py::test_run_seeder_helper_function PASSED
tests/unit/test_factories.py::test_run_seeders_helper_runs_multiple_seeders PASSED
tests/unit/test_factories.py::test_factory_raises_error_without_model_class PASSED
tests/unit/test_factories.py::test_realistic_blog_dataset_creation PASSED
```

---

## 🔧 Dependencies Added

**Development Dependency:**
```toml
faker = "^20.0.0"  # Fake data generation for factories
```

**Rationale:**
- Faker is the industry-standard library for generating fake data
- Version 20.x provides stable API with Python 3.13 support
- Development-only dependency (not needed in production)

---

## 🎓 Educational Highlights

### 1. Async-First Design

Unlike Laravel's factories which use synchronous database operations, our factories are **fully async**:

```python
# Laravel (synchronous)
User::factory()->count(10)->create();

# Fast Track Framework (async)
users = await factory.create_batch(10)
```

**Why this matters:**
- Maintains async context throughout the stack
- No blocking operations in async code
- Better performance with concurrent operations

### 2. Dependency Injection vs. Static Methods

Laravel uses static methods and facades. We use **explicit dependency injection**:

```python
# Laravel (static, implicit dependencies)
User::factory()->create();

# Fast Track (DI, explicit dependencies)
factory = UserFactory(session)  # Session injected explicitly
user = await factory.create()
```

**Benefits:**
- Testable (easy to mock session)
- Clear dependencies (no hidden global state)
- Follows "Explicit over Implicit" (Zen of Python)

### 3. Type Safety

Factories are **fully type-safe** with Generic[T]:

```python
class UserFactory(Factory[User]):  # Type parameter enforces User type
    _model_class = User

    def definition(self) -> dict[str, Any]:  # Return type enforced
        return {"name": "..."}

# MyPy knows this returns User, not Any!
user: User = await factory.create()
```

**Benefits:**
- Catch errors at development time (not runtime)
- IDE autocomplete works perfectly
- Refactoring is safer

### 4. Immutable State Pattern

State modifiers return **new factory instances**:

```python
factory1 = UserFactory(session)
factory2 = factory1.state(lambda a: {**a, "admin": True})

# factory1 is unchanged!
user1 = await factory1.create()  # Not admin
user2 = await factory2.create()  # Is admin
```

**Why immutable:**
- Prevents accidental mutations
- Makes factories reusable
- Easier to reason about
- Follows functional programming principles

### 5. Relationship Hook Pattern

The "magic methods" pattern is **just syntax sugar**:

```python
# This:
user = await factory.has_posts(5).create()

# Is equivalent to:
async def create_posts(user: User) -> None:
    factory = PostFactory(session)
    await factory.create_batch(5, user_id=user.id)

user = await factory.after_create(create_posts).create()
```

**Educational note:**
- There's no actual "magic" - just clean abstractions
- Users can create their own relationship methods
- The pattern is extensible and composable

---

## 📖 Usage Examples

### Example 1: Simple Factory

```python
from fast_query import get_session, Factory
from jtc.models import User

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

    # Create one user
    user = await factory.create()
    print(f"Created {user.name}")

    # Create batch
    users = await factory.create_batch(10)
    print(f"Created {len(users)} users")
```

### Example 2: State Modifiers

```python
# Create different types of users
admin = await factory.state(
    lambda a: {**a, "role": "admin"}
).create()

# Create suspended user
suspended = await factory.state(
    lambda a: {**a, "status": "suspended", "suspended_at": datetime.now()}
).create()

# Create verified user
verified = await factory.state(
    lambda a: {**a, "email_verified_at": datetime.now()}
).create()
```

### Example 3: Relationship Hooks

```python
# Create user with posts
user = await user_factory.has_posts(5).create()
# User now has 5 posts

# Create user with posts, each post with comments
# (This requires PostFactory to have has_comments method)
user = await user_factory.has_posts(5).create()
# Then create comments for each post separately
```

### Example 4: Database Seeder

```python
from fast_query.seeding import Seeder
from fast_query import get_session

class DatabaseSeeder(Seeder):
    async def run(self) -> None:
        print("🌱 Seeding database...")

        # Create users with posts
        factory = UserFactory(self.session)
        users = await factory.has_posts(5).create_batch(10)
        print(f"✅ Created {len(users)} users with posts")

        print("✅ Database seeding complete!")

# Run seeder
async with get_session() as session:
    seeder = DatabaseSeeder(session)
    await seeder.run()
```

### Example 5: Testing with Factories

```python
@pytest.mark.asyncio
async def test_user_can_create_post(session: AsyncSession) -> None:
    # Arrange: Create user using factory
    user_factory = UserFactory(session)
    user = await user_factory.create()

    # Act: Create post
    post_factory = PostFactory(session)
    post = await post_factory.create(
        user_id=user.id,
        title="Test Post"
    )

    # Assert
    assert post.user_id == user.id
    assert post.title == "Test Post"
```

---

## 🚀 Integration with fast_query

The Factory and Seeder system is now part of the **fast_query** package public API:

```python
# Available from fast_query
from fast_query import (
    # Existing ORM components
    Base, BaseRepository, QueryBuilder,
    create_engine, get_session,
    TimestampMixin, SoftDeletesMixin,

    # New in Sprint 2.8
    Factory,   # Base class for factories
    Seeder,    # Base class for seeders
)
```

**Package Philosophy:**
- ✅ Framework-agnostic (works with any Python framework)
- ✅ Zero dependencies on web frameworks
- ✅ Can be used in CLI tools, scripts, background jobs
- ✅ Factories and seeders follow the same philosophy

---

## 🔄 Comparison with Laravel

| Feature | Laravel | Fast Track Framework |
|---------|---------|---------------------|
| **Basic Factory** | `User::factory()` | `UserFactory(session)` |
| **Create One** | `->create()` | `await factory.create()` |
| **Create Many** | `->count(10)->create()` | `await factory.create_batch(10)` |
| **States** | `->admin()->create()` | `->state(lambda a: {...}).create()` |
| **Relationships** | `->hasPosts(5)->create()` | `->has_posts(5).create()` |
| **Seeders** | `php artisan db:seed` | `await run_seeder(DatabaseSeeder, session)` |
| **Async** | No | Yes (fully async) |
| **Type Safety** | No | Yes (Generic[T]) |
| **DI** | Static methods | Explicit injection |

**Key Differences:**
- **Async-first**: All operations are async/await
- **Explicit dependencies**: Session is injected, not global
- **Type-safe**: Factories are Generic[T] with MyPy support
- **Immutable**: State modifiers return new instances

---

## 📝 Design Decisions

### Why Generic[T] instead of subclassing per model?

**Decision:** Use `Factory[T]` with `_model_class` attribute

**Rationale:**
- Type safety: MyPy knows `UserFactory` returns `User`
- Reusable base class with all functionality
- Explicit model class declaration
- Follows Repository Pattern established in Sprint 2.2

### Why explicit session injection?

**Decision:** Require `AsyncSession` in factory constructor

**Rationale:**
- No global state (follows Zen of Python)
- Testable (easy to mock session)
- Clear dependencies (no hidden database connections)
- Consistent with Repository Pattern

### Why immutable state pattern?

**Decision:** `state()` returns new factory instance

**Rationale:**
- Prevents accidental mutations
- Makes factories reusable
- Easier to reason about code
- Follows functional programming principles

### Why relationship hooks instead of automatic relationships?

**Decision:** Require explicit `has_posts()` calls

**Rationale:**
- Explicit over implicit (Zen of Python)
- User controls what relationships to create
- Avoids performance issues from automatic loading
- More flexible for complex scenarios

---

## 🎯 Sprint Metrics

**Development Time:** ~4 hours
**Lines of Code:**
- Core Implementation: 584 lines (factories.py + seeding.py)
- Example Factories: 210 lines
- Example Seeders: 150 lines
- Tests: 500 lines
- **Total:** ~1,444 lines

**Test Coverage:**
- 21 new tests (100% passing)
- All factory features covered
- All seeder features covered
- Integration tests for complex scenarios

**Dependencies Added:**
- faker (^20.0.0) - Development only

---

## 🔜 Next Steps

### Potential Enhancements (Future Sprints)

1. **Sequence Support**
   ```python
   factory.sequence(lambda n: f"user{n}@test.com")
   ```

2. **Trait System** (like Laravel)
   ```python
   factory.trait("admin", lambda a: {**a, "role": "admin"})
   factory.with_traits("admin", "verified").create()
   ```

3. **Factory Callbacks**
   ```python
   factory.before_create(lambda model: ...)
   factory.after_making(lambda model: ...)
   ```

4. **CLI Commands**
   ```bash
   python manage.py seed  # Run DatabaseSeeder
   python manage.py factory:make UserFactory
   ```

5. **Factory Discovery**
   - Auto-discover factories in `tests/factories/`
   - Register globally for easier access

---

## ✅ Sprint Completion Checklist

- ✅ Generic `Factory[T]` base class implemented
- ✅ `make()`, `create()`, `create_batch()` methods working
- ✅ State management with `state()` working
- ✅ Relationship hooks with `has_*()` methods working
- ✅ `Seeder` base class implemented
- ✅ Faker integration working
- ✅ Example factories created (User, Post, Comment)
- ✅ Example seeders created (User, Database)
- ✅ 21 comprehensive tests passing
- ✅ Documentation written
- ✅ Dependencies added to pyproject.toml
- ✅ Public API exported from fast_query

---

## 🎓 Key Learnings

1. **Async Factories**: Factory pattern works well with async Python when designed from the ground up for async

2. **Type Safety Matters**: Generic[T] provides excellent IDE support and catches errors early

3. **Explicit > Implicit**: Requiring session injection makes dependencies clear and testable

4. **Relationship Complexity**: Creating related models requires careful handling of foreign keys and dependencies

5. **Faker Integration**: Faker makes test data generation trivial and realistic

---

## 📚 Documentation

**Created:**
- This sprint summary
- Inline documentation in `factories.py` (comprehensive docstrings)
- Inline documentation in `seeding.py`
- Example implementations with educational comments

**Updated:**
- `fast_query/__init__.py` - Added Factory and Seeder exports
- `pyproject.toml` - Added faker dependency

**To Do:**
- Update main README.md with factory examples
- Update database guide with factory usage
- Create CLI documentation for future commands

---

**Sprint 2.8 Status:** ✅ **COMPLETE**

All objectives met. Factory & Seeder system is production-ready and fully tested. The framework now has a complete testing toolkit for generating realistic test data.
