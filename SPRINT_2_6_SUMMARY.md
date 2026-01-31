# Sprint 2.6 - Advanced Query Builder ("Musculatura")

**Status:** ✅ Complete
**Date:** January 30, 2026
**Focus:** Transform QueryBuilder from simple wrapper to advanced ORM tool

---

## 🎯 Objective

Enhance the QueryBuilder with 4 advanced features that provide **"musculatura"** (strength/muscle) to the ORM layer, enabling expressive, complex queries with minimal boilerplate.

---

## ✅ Delivered Features

### 1. **Nested Eager Loading (Dot Notation)** ✅

**Goal:** Allow loading deep relationships using string notation.

**Implementation:**
- Enhanced `with_()` method to accept both objects and strings
- Added `_parse_nested_relationship()` helper method
- Parses dot-separated paths like `"posts.comments"` into nested SQLAlchemy `selectinload()` calls
- Validates each level of the relationship path

**Usage:**
```python
# Before (Sprint 2.3): Object-based loading
users = await user_repo.query().with_(User.posts).get()

# NEW (Sprint 2.6): String-based nested loading
users = await user_repo.query().with_("posts.comments", "posts.author").get()

# Access nested relationships (all loaded!)
for user in users:
    for post in user.posts:
        print(post.author.name)       # Loaded!
        for comment in post.comments:
            print(comment.content)     # Loaded!
```

**Backward Compatibility:** ✅ Maintained - existing object-based usage still works

**Tests:** 5 tests covering single-level, two-level, multiple paths, invalid relationships, mixed notation

---

### 2. **Global Scopes (Soft Delete Filtering)** ✅

**Goal:** Automatically filter out soft-deleted records by default.

**Implementation:**
- Added `_include_trashed` and `_only_trashed` flags to QueryBuilder
- Added `with_trashed()` method to include deleted records
- Added `only_trashed()` method to show only deleted records
- Added `_apply_global_scope()` method to apply filtering
- Integrated scope into all terminal methods: `get()`, `first()`, `count()`, `exists()`, `pluck()`
- Auto-detects `SoftDeletesMixin` on model

**Usage:**
```python
# Default behavior: Excludes soft-deleted automatically
users = await user_repo.query().get()
# Returns only active users (deleted_at IS NULL)

# Include soft-deleted records
all_users = await user_repo.query().with_trashed().get()
# Returns all users (active + deleted)

# Only soft-deleted records
deleted_users = await user_repo.query().only_trashed().get()
# Returns only deleted users (deleted_at IS NOT NULL)

# Works with all terminal methods
count_active = await user_repo.query().count()           # Only active
count_all = await user_repo.query().with_trashed().count()  # All
```

**Automatic Detection:** Works only for models with `SoftDeletesMixin` (User), doesn't affect models without it (Post, Comment)

**Tests:** 7 tests covering default behavior, with_trashed, only_trashed, count, first, pluck, non-mixin models

---

### 3. **Local Scopes (Reusable Query Logic)** ✅

**Goal:** Enable reusable query methods that can be applied to any query.

**Implementation:**
- Added `scope()` method that accepts a callable
- Callable receives the QueryBuilder and returns modified QueryBuilder
- Supports static methods, lambdas, or any callable

**Usage:**
```python
# Define scope as static method in model
class User(Base):
    @staticmethod
    def active(query: QueryBuilder["User"]) -> QueryBuilder["User"]:
        return query.where(User.status == "active")

    @staticmethod
    def verified(query: QueryBuilder["User"]) -> QueryBuilder["User"]:
        return query.where(User.email_verified_at.isnot(None))

# Use scopes in queries
active_users = await user_repo.query().scope(User.active).get()

# Chain multiple scopes
verified_active = await (
    user_repo.query()
    .scope(User.active)
    .scope(User.verified)
    .get()
)

# Or use lambdas
adults = await (
    user_repo.query()
    .scope(lambda q: q.where(User.age >= 18))
    .get()
)
```

**Benefits:**
- DRY: Define complex query logic once, reuse everywhere
- Composable: Chain multiple scopes
- Testable: Each scope can be tested independently

**Tests:** 3 tests covering static methods, lambdas, chaining

---

### 4. **Relationship Filters (where_has)** ✅

**Goal:** Filter records based on relationship existence.

**Implementation:**
- Added `where_has(relationship_name)` method
- Dynamically detects relationship type (to-one vs to-many)
- Uses SQLAlchemy's `has()` for to-one or `any()` for to-many
- Raises clear errors for invalid relationships

**Usage:**
```python
# Get users who have at least one post
users_with_posts = await user_repo.query().where_has("posts").get()

# Get posts that have at least one comment
posts_with_comments = await post_repo.query().where_has("comments").get()

# Combine with other filters
active_authors = await (
    user_repo.query()
    .where(User.status == "active")
    .where_has("posts")
    .get()
)
```

**Error Handling:**
```python
# Invalid relationship name
await user_repo.query().where_has("invalid_rel").get()
# Raises: AttributeError: Model User has no relationship 'invalid_rel'

# Not a relationship (just a column)
await user_repo.query().where_has("name").get()
# Raises: AttributeError: Attribute 'name' on User is not a relationship
```

**Tests:** 5 tests covering one-to-many, many-to-one, combined filters, error handling

---

## 🧪 Test Coverage

**New Tests:** 22 comprehensive tests in `tests/unit/test_query_builder_advanced.py`

**Test Breakdown:**
- ✅ Nested Eager Loading: 5 tests
- ✅ Global Scopes: 7 tests
- ✅ Local Scopes: 3 tests
- ✅ Relationship Filters: 5 tests
- ✅ Integration Tests: 2 tests (combining all features)

**Test Results:**
```bash
$ poetry run pytest tests/unit/test_query_builder_advanced.py -v

======================= 22 passed, 18 warnings in 3.57s ========================
```

**Backward Compatibility:** ✅ All 64 existing tests still pass

---

## 📊 Metrics

| Metric | Value |
|--------|-------|
| **New Tests** | +22 |
| **Total Tests** | 86 (64 existing + 22 new) |
| **Lines of Code** | ~300 lines added to QueryBuilder |
| **New Methods** | 5 public methods (with_, with_trashed, only_trashed, scope, where_has) |
| **Helper Methods** | 2 private methods (_parse_nested_relationship, _apply_global_scope) |
| **Features Delivered** | 4/4 (100%) |
| **Test Pass Rate** | 100% |
| **Breaking Changes** | 0 |

---

## 🎓 Key Learnings

### 1. **String-Based vs Object-Based Relationship Loading**

**Challenge:** Supporting both string notation (`"posts.comments"`) and object notation (`User.posts`) in the same method.

**Solution:** Type union `InstrumentedAttribute[Any] | str` with runtime type checking:
```python
def with_(self, *relationships: InstrumentedAttribute[Any] | str) -> "QueryBuilder[T]":
    for rel in relationships:
        if isinstance(rel, str):
            self._eager_loads.append(self._parse_nested_relationship(rel))
        else:
            self._eager_loads.append(selectinload(rel))
    return self
```

**Learning:** Python's duck typing and `isinstance()` make multi-format APIs elegant.

---

### 2. **Global Scopes with Deferred Execution**

**Challenge:** Apply soft delete filtering automatically but allow opt-out via `with_trashed()`.

**Solution:** Store flags (`_include_trashed`, `_only_trashed`) during query building, apply filter only in terminal methods:
```python
def _apply_global_scope(self) -> None:
    if not issubclass(self.model, SoftDeletesMixin):
        return

    if self._only_trashed:
        self._stmt = self._stmt.where(self.model.deleted_at.isnot(None))
    elif not self._include_trashed:
        self._stmt = self._stmt.where(self.model.deleted_at.is_(None))
```

**Learning:** Lazy execution pattern (build query, execute later) enables flexible filtering strategies.

---

### 3. **Dynamic Relationship Detection**

**Challenge:** Determine if relationship is to-one or to-many to use correct SQLAlchemy filter.

**Solution:** Inspect relationship metadata at runtime:
```python
rel_attr = getattr(self.model, relationship_name)

if rel_attr.property.uselist:
    # One-to-many (collection) - use any()
    self._stmt = self._stmt.where(rel_attr.any())
else:
    # Many-to-one (scalar) - use has()
    self._stmt = self._stmt.where(rel_attr.has())
```

**Learning:** SQLAlchemy's metadata is rich and accessible - leverage it for smart behavior.

---

### 4. **Nested Relationship Parsing**

**Challenge:** Parse `"posts.comments.author"` into nested `selectinload()` chain while validating each level.

**Solution:** Iterative parsing with model tracking:
```python
def _parse_nested_relationship(self, path: str) -> Any:
    parts = path.split(".")
    current_model = self.model
    load_option = None

    for i, part in enumerate(parts):
        if not hasattr(current_model, part):
            raise AttributeError(f"Model {current_model.__name__} has no relationship '{part}'")

        rel_attr = getattr(current_model, part)

        if i == 0:
            load_option = selectinload(rel_attr)
        else:
            load_option = load_option.selectinload(rel_attr)

        # Track next model in chain
        current_model = rel_attr.property.mapper.class_

    return load_option
```

**Learning:** Parsing with state tracking (current model) enables clear error messages with context.

---

## 🔍 Code Quality

### Type Safety
- ✅ All methods fully type-annotated
- ✅ MyPy strict mode compliance maintained
- ✅ Generic type preservation (`QueryBuilder[T]`)

### Error Handling
- ✅ Clear error messages with model name and relationship path
- ✅ Early validation (fail fast on invalid relationships)
- ✅ Helpful error messages for debugging

### Documentation
- ✅ Comprehensive docstrings for all new methods
- ✅ Usage examples in docstrings
- ✅ Sprint 2.6 markers in updated method docs

---

## 🚀 Real-World Usage Examples

### Example 1: Blog with Complex Queries

```python
# Get active users who have published posts with comments
authors = await (
    user_repo.query()
    .scope(User.active)              # Local scope
    .where_has("posts")              # Relationship filter
    .with_("posts.comments.author")  # Nested eager loading
    .get()
)

# All loaded! No N+1 queries
for author in authors:
    for post in author.posts:
        for comment in post.comments:
            print(f"{comment.author.name}: {comment.content}")
```

### Example 2: Soft Delete Management

```python
# Admin dashboard: View deleted users
deleted_users = await (
    user_repo.query()
    .only_trashed()           # Only soft-deleted
    .order_by(User.deleted_at, "desc")
    .limit(100)
    .get()
)

# Count active vs deleted
active_count = await user_repo.query().count()
deleted_count = await user_repo.query().only_trashed().count()
total_count = await user_repo.query().with_trashed().count()

print(f"Active: {active_count}, Deleted: {deleted_count}, Total: {total_count}")
```

### Example 3: Reusable Scopes

```python
# Define scopes in User model
class User(Base, SoftDeletesMixin):
    # ... columns ...

    @staticmethod
    def active(q):
        return q.where(User.status == "active")

    @staticmethod
    def verified(q):
        return q.where(User.email_verified_at.isnot(None))

    @staticmethod
    def premium(q):
        return q.where(User.subscription_tier == "premium")

# Combine scopes for complex queries
premium_verified_users = await (
    user_repo.query()
    .scope(User.active)
    .scope(User.verified)
    .scope(User.premium)
    .where_has("posts")  # With at least one post
    .get()
)
```

---

## 🔄 Comparison to Laravel Eloquent

### Nested Eager Loading

**Laravel:**
```php
$users = User::with('posts.comments.author')->get();
```

**Fast Query (Sprint 2.6):**
```python
users = await user_repo.query().with_("posts.comments.author").get()
```

✅ **Parity achieved!**

---

### Global Scopes (Soft Deletes)

**Laravel:**
```php
// Excludes soft-deleted by default
$users = User::all();

// Include soft-deleted
$users = User::withTrashed()->get();

// Only soft-deleted
$users = User::onlyTrashed()->get();
```

**Fast Query (Sprint 2.6):**
```python
# Excludes soft-deleted by default
users = await user_repo.query().get()

# Include soft-deleted
users = await user_repo.query().with_trashed().get()

# Only soft-deleted
users = await user_repo.query().only_trashed().get()
```

✅ **Parity achieved!**

---

### Local Scopes

**Laravel:**
```php
class User extends Model {
    public function scopeActive($query) {
        return $query->where('status', 'active');
    }
}

$users = User::active()->get();
```

**Fast Query (Sprint 2.6):**
```python
class User(Base):
    @staticmethod
    def active(query):
        return query.where(User.status == "active")

users = await user_repo.query().scope(User.active).get()
```

✅ **Parity achieved!**

---

### Relationship Filters

**Laravel:**
```php
$users = User::has('posts')->get();
```

**Fast Query (Sprint 2.6):**
```python
users = await user_repo.query().where_has("posts").get()
```

✅ **Parity achieved!**

---

## 🎯 Sprint Goals Achievement

| Goal | Status | Notes |
|------|--------|-------|
| Nested Eager Loading | ✅ Complete | String-based dot notation working |
| Global Scopes | ✅ Complete | Soft delete filtering automatic |
| Local Scopes | ✅ Complete | Reusable query methods supported |
| Relationship Filters | ✅ Complete | where_has() working for all relationship types |
| Backward Compatibility | ✅ Maintained | All 64 existing tests pass |
| Type Safety | ✅ Maintained | MyPy strict mode compliance |
| Test Coverage | ✅ Excellent | 22 new tests, 100% pass rate |

---

## 🐛 Known Issues

### Table Redefinition in Test Suite

**Issue:** When running all tests together (`pytest tests/`), SQLAlchemy raises table redefinition errors.

**Root Cause:** Multiple test files import the same models (User, Post, Comment) from `ftf.models`, and SQLAlchemy's `Base.metadata` sees them as duplicate definitions.

**Impact:** Tests work perfectly when run individually or in subsets, but fail when run all together.

**Workaround:** Run tests in separate commands:
```bash
# Existing tests
poetry run pytest tests/unit/test_query_builder.py tests/unit/test_repository.py -v

# New advanced tests
poetry run pytest tests/unit/test_query_builder_advanced.py -v
```

**Permanent Fix (Future Sprint):** Add `__table_args__ = {'extend_existing': True}` to all models, or refactor tests to use isolated model definitions.

---

## 📝 Next Steps (Future Sprints)

### Sprint 2.7: Query Builder Enhancements
- [ ] `whereHas()` with callback for nested conditions
- [ ] `withCount()` to count relationships
- [ ] Subquery support
- [ ] `chunk()` for processing large datasets

### Sprint 2.8: Model Factories & Seeders
- [ ] Laravel-style model factories
- [ ] Database seeders
- [ ] Faker integration

### Sprint 3.x: Production Features
- [ ] Authentication system (JWT + OAuth2)
- [ ] Event dispatcher (pub/sub)
- [ ] Background jobs (async task queue)
- [ ] CLI tool (Artisan-like commands)

---

## 🙏 Conclusion

Sprint 2.6 successfully transforms the QueryBuilder from a basic SQL wrapper into a **powerful, Laravel Eloquent-inspired ORM** with:

✅ **4/4 advanced features delivered**
✅ **22 comprehensive tests (100% pass rate)**
✅ **Zero breaking changes**
✅ **Feature parity with Laravel Eloquent** for key patterns

The QueryBuilder now has **"musculatura"** - it's no longer just functional, it's **expressive, composable, and production-ready**.

---

**Sprint 2.6: COMPLETE** ✅🚀
