# Sprint 4.2 - API Resources (Transformation Layer)

**Status**: ✅ Complete
**Date**: February 2026
**Test Count**: 24 new tests (100% passing)
**Coverage**: 82.86% (core.py), 88.24% (collection.py)

---

## Overview

Sprint 4.2 implements a comprehensive API Resource system, inspired by Laravel API Resources, that provides a transformation layer between database models and JSON responses. This decouples the database schema from the API response format, giving developers fine-grained control over what data is exposed and how it's formatted.

**Goal**: Enable developers to transform database models into consistent, controlled JSON responses without exposing internal database structures.

---

## Key Features

### 1. JsonResource Base Class

Generic base class for transforming models to JSON:
```python
class UserResource(JsonResource[User]):
    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        return {
            "id": self.resource.id,
            "name": self.resource.name,
            "created_at": self.resource.created_at.isoformat(),
        }

# Usage
UserResource.make(user).resolve()
# {"data": {"id": 1, "name": "John", "created_at": "2026-02-01T12:00:00"}}
```

### 2. Conditional Attributes

Include fields based on conditions (permissions, user type, etc.):
```python
def to_array(self, request: Request | None = None) -> dict[str, Any]:
    is_admin = request and hasattr(request.state, "user") and request.state.user.is_admin

    return {
        "id": self.resource.id,
        "name": self.resource.name,
        # Only show email for admins
        "email": self.when(is_admin, self.resource.email),
        # Default value for non-admins
        "role": self.when(is_admin, "admin", "user"),
    }
```

### 3. Relationship Loading Control

Only include relationships that were eager-loaded (prevents N+1 queries):
```python
def to_array(self, request: Request | None = None) -> dict[str, Any]:
    posts = self.when_loaded("posts")

    return {
        "id": self.resource.id,
        "name": self.resource.name,
        # Only include if posts were eager-loaded
        "posts": PostResource.collection(posts).resolve()["data"]
                if posts is not MISSING
                else MISSING,
    }
```

### 4. Resource Collections

Transform lists of models consistently:
```python
users = await repo.all()
UserResource.collection(users).resolve()
# {
#   "data": [
#     {"id": 1, "name": "John"},
#     {"id": 2, "name": "Jane"}
#   ]
# }
```

### 5. CLI Scaffolding

Generate resource classes with `make:resource` command:
```bash
$ jtc make resource UserResource
✓ Resource created: src/jtc/resources/user_resource.py

$ jtc make resource PostResource --model Post
✓ Resource created: src/jtc/resources/post_resource.py
```

---

## File Structure

```
src/jtc/resources/
├── __init__.py              # Public API (JsonResource, ResourceCollection, MISSING)
├── core.py                  # JsonResource base class with when() and when_loaded()
└── collection.py            # ResourceCollection for handling lists

src/jtc/cli/
├── commands/make.py         # Added make:resource command
└── templates.py             # Added get_resource_template()

examples/
└── resource_example.py      # Complete examples (7 scenarios)

tests/unit/
└── test_resources.py        # 24 unit tests (100% passing)
```

**Total**: 6 modified/new files, ~1,600 lines of code (including tests and examples)

---

## Architecture & Design Patterns

### Adapter Pattern

Resources adapt database models to API-specific JSON format:

```python
# Database model (internal structure)
class User(Base):
    __tablename__ = "users"
    id: Mapped[int]
    first_name: Mapped[str]
    last_name: Mapped[str]
    password_hash: Mapped[str]
    created_at: Mapped[datetime]

# API Resource (external format)
class UserResource(JsonResource[User]):
    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        return {
            "id": self.resource.id,
            # Combine first_name + last_name
            "name": f"{self.resource.first_name} {self.resource.last_name}",
            # Hide password_hash
            # Format datetime
            "member_since": self.resource.created_at.isoformat(),
        }

# Response
{
    "data": {
        "id": 1,
        "name": "John Doe",          # Computed field
        "member_since": "2026-01-01T12:00:00"  # Formatted
        # No password_hash exposed
    }
}
```

### Template Method Pattern

`to_array()` is the template method that subclasses implement:

```python
class JsonResource(Generic[T]):
    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        """Abstract method - subclasses must implement."""
        raise NotImplementedError()

    def resolve(self, request: Request | None = None) -> dict[str, Any]:
        """Algorithm that uses to_array() - NOT overridden."""
        data = self.to_array(request)
        filtered_data = {k: v for k, v in data.items() if v is not MISSING}
        return {"data": filtered_data}
```

### Builder Pattern

Fluent API for creating resources:

```python
# Factory method
UserResource.make(user).resolve()

# Collection method
UserResource.collection(users).resolve()

# Chaining (future enhancement)
# UserResource.make(user).with_meta({"version": "1.0"}).resolve()
```

### Sentinel Value Pattern

`MISSING` sentinel for conditional attributes:

```python
MISSING: Final = object()

# when() returns MISSING if condition is False
"email": self.when(is_admin, self.resource.email)
# If not admin, email = MISSING

# resolve() filters out MISSING values
filtered_data = {k: v for k, v in data.items() if v is not MISSING}
# MISSING values are removed, so "email" key won't appear
```

---

## Implementation Details

### 1. JsonResource Base Class (core.py)

```python
class JsonResource(Generic[T]):
    """Base class for API Resources."""

    def __init__(self, resource: T) -> None:
        self.resource = resource

    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        """Abstract method - subclasses implement."""
        raise NotImplementedError()

    def resolve(self, request: Request | None = None) -> dict[str, Any]:
        """Resolve with data wrapper, filtering MISSING values."""
        data = self.to_array(request)
        filtered_data = {k: v for k, v in data.items() if v is not MISSING}
        return {"data": filtered_data}

    @classmethod
    def make(cls, resource: T) -> "JsonResource[T]":
        """Factory method."""
        return cls(resource)

    @classmethod
    def collection(cls, resources: Iterable[T]) -> "ResourceCollection[T]":
        """Create collection."""
        from jtc.resources.collection import ResourceCollection
        return ResourceCollection(cls, resources)

    def when(self, condition: bool, value: Any, default: Any = MISSING) -> Any:
        """Conditionally include value."""
        return value if condition else default

    def when_loaded(self, relationship: str) -> Any:
        """Include relationship only if loaded (SQLAlchemy)."""
        if hasattr(self.resource, "__dict__"):
            if relationship in self.resource.__dict__:
                value = getattr(self.resource, relationship)
                return value if value is not None else MISSING
        elif hasattr(self.resource, relationship):
            value = getattr(self.resource, relationship, None)
            if value is not None:
                return value
        return MISSING
```

### 2. ResourceCollection (collection.py)

```python
class ResourceCollection(Generic[T]):
    """Handle collections of resources."""

    def __init__(
        self, resource_class: Type[JsonResource[T]], resources: Iterable[T]
    ) -> None:
        self.resource_class = resource_class
        self.resources = resources

    def resolve(self, request: Request | None = None) -> dict[str, Any]:
        """Resolve collection with data wrapper."""
        # Transform each resource
        data = [
            self.resource_class(resource).to_array(request)
            for resource in self.resources
        ]

        # Filter out MISSING values from each item
        filtered_data = [
            {k: v for k, v in item.items() if v is not MISSING}
            for item in data
        ]

        result: dict[str, Any] = {"data": filtered_data}

        # TODO: Add pagination metadata (bonus feature)
        # if hasattr(self.resources, "total"):
        #     result["meta"] = {...}
        #     result["links"] = {...}

        return result
```

### 3. CLI Command (commands/make.py)

```python
@app.command("resource")
def make_resource(
    name: str,
    model: str = typer.Option(None, "--model", "-m", help="Model name"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """Generate an API Resource for transforming models to JSON."""
    # Auto-detect model name if not specified
    if model is None:
        model = name.replace("Resource", "")

    filename = to_snake_case(name)
    file_path = Path("src/jtc/resources") / f"{filename}.py"
    content = get_resource_template(name, model)

    if create_file(file_path, content, force):
        console.print(f"✓ Resource created: {file_path}")
```

### 4. Resource Template (templates.py)

Generates complete resource class with:
- Proper imports (JsonResource, MISSING, Request, Model)
- Generic type annotation
- to_array() method with TODO comments
- Example usage in docstring
- Commented examples for common patterns

---

## Usage Examples

### Example 1: Basic Resource

```python
class UserResource(JsonResource[User]):
    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        return {
            "id": self.resource.id,
            "name": self.resource.name,
            "email": self.resource.email,
        }

# Single resource
user = await repo.find(1)
return UserResource.make(user).resolve()
# {"data": {"id": 1, "name": "John", "email": "john@example.com"}}

# Collection
users = await repo.all()
return UserResource.collection(users).resolve()
# {"data": [{...}, {...}]}
```

### Example 2: Conditional Fields

```python
class UserResource(JsonResource[User]):
    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        is_admin = request and hasattr(request.state, "user") and request.state.user.is_admin

        return {
            "id": self.resource.id,
            "name": self.resource.name,
            # Only show for admins
            "email": self.when(is_admin, self.resource.email),
            # Show badge for admins
            "admin_badge": self.when(is_admin, "⭐ Admin"),
            # Default value
            "role": self.when(is_admin, "admin", "user"),
        }

# Admin user
{
    "data": {
        "id": 1,
        "name": "John",
        "email": "john@example.com",  # Included
        "admin_badge": "⭐ Admin",      # Included
        "role": "admin"
    }
}

# Regular user
{
    "data": {
        "id": 2,
        "name": "Jane",
        # No email key (filtered out)
        # No admin_badge key (filtered out)
        "role": "user"
    }
}
```

### Example 3: Relationship Loading

```python
class UserResource(JsonResource[User]):
    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        posts = self.when_loaded("posts")

        return {
            "id": self.resource.id,
            "name": self.resource.name,
            "posts": PostResource.collection(posts).resolve()["data"]
                    if posts is not MISSING
                    else MISSING,
        }

# Without eager loading
user = await repo.find(1)  # No joins
UserResource.make(user).resolve()
# {"data": {"id": 1, "name": "John"}}  # No posts key

# With eager loading
user = await repo.query().with_("posts").find(1)
UserResource.make(user).resolve()
# {"data": {"id": 1, "name": "John", "posts": [...]}}
```

### Example 4: Computed Fields

```python
class UserResource(JsonResource[User]):
    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        return {
            "id": self.resource.id,
            "name": self.resource.name,
            # Computed: initials
            "initials": "".join([n[0].upper() for n in self.resource.name.split()]),
            # Computed: member duration
            "member_for_days": (datetime.now() - self.resource.created_at).days,
            # Computed: email domain
            "email_domain": self.resource.email.split("@")[1],
        }

# Response
{
    "data": {
        "id": 1,
        "name": "John Doe",
        "initials": "JD",
        "member_for_days": 30,
        "email_domain": "example.com"
    }
}
```

### Example 5: In FastAPI Routes

```python
from jtc.http import FastTrackFramework, Inject
from jtc.resources import JsonResource

app = FastTrackFramework()

@app.get("/api/users/{id}")
async def get_user(
    id: int,
    repo: UserRepository = Inject(UserRepository)
):
    user = await repo.find_or_fail(id)
    return UserResource.make(user).resolve()

@app.get("/api/users")
async def list_users(
    repo: UserRepository = Inject(UserRepository)
):
    users = await repo.all()
    return UserResource.collection(users).resolve()
```

---

## Testing

### Test Coverage

**Total**: 24 tests (100% passing)

**JsonResource Tests** (9 tests):
- ✅ make() factory method
- ✅ to_array() transformation
- ✅ resolve() wraps data
- ✅ NotImplementedError for missing to_array()

**Conditional Attributes Tests** (6 tests):
- ✅ when(True) returns value
- ✅ when(False) returns MISSING
- ✅ when(False, default) returns default
- ✅ Conditional field included when True
- ✅ Conditional field excluded when False (filtered out)

**Relationship Loading Tests** (4 tests):
- ✅ when_loaded() returns MISSING if not loaded
- ✅ when_loaded() returns value if loaded
- ✅ Resource without loaded relationship
- ✅ Resource with loaded relationship

**ResourceCollection Tests** (4 tests):
- ✅ collection() creates ResourceCollection
- ✅ Collection resolves all resources
- ✅ Empty collection returns empty data array
- ✅ Collection filters MISSING values

**Integration Tests** (2 tests):
- ✅ Full transformation pipeline
- ✅ Collection transformation pipeline

### Running Tests

```bash
# All resource tests
poetry run pytest tests/unit/test_resources.py -v

# With coverage
poetry run pytest tests/unit/test_resources.py --cov=ftf.resources --cov-report=term-missing

# Specific test
poetry run pytest tests/unit/test_resources.py::test_conditional_field_excluded_when_false -v
```

### Test Results

```
============================= test session starts ==============================
collected 24 items

tests/unit/test_resources.py::test_resource_make PASSED                  [  4%]
tests/unit/test_resources.py::test_resource_to_array PASSED              [  8%]
tests/unit/test_resources.py::test_resource_resolve_wraps_data PASSED    [ 12%]
tests/unit/test_resources.py::test_resource_not_implemented_error PASSED [ 16%]
tests/unit/test_resources.py::test_when_true_returns_value PASSED        [ 20%]
tests/unit/test_resources.py::test_when_false_returns_missing PASSED     [ 25%]
tests/unit/test_resources.py::test_when_false_with_default_returns_default PASSED [ 29%]
tests/unit/test_resources.py::test_conditional_field_included_when_true PASSED [ 33%]
tests/unit/test_resources.py::test_conditional_field_excluded_when_false PASSED [ 37%]
tests/unit/test_resources.py::test_when_loaded_not_loaded_returns_missing PASSED [ 41%]
tests/unit/test_resources.py::test_when_loaded_loaded_returns_value PASSED [ 45%]
tests/unit/test_resources.py::test_resource_without_loaded_relationship PASSED [ 50%]
tests/unit/test_resources.py::test_resource_with_loaded_relationship PASSED [ 54%]
tests/unit/test_resources.py::test_resource_collection PASSED            [ 58%]
tests/unit/test_resources.py::test_collection_resolve_transforms_all PASSED [ 62%]
tests/unit/test_resources.py::test_collection_empty_list PASSED          [ 66%]
tests/unit/test_resources.py::test_collection_filters_missing_values PASSED [ 70%]
tests/unit/test_resources.py::test_resource_generic_type PASSED          [ 75%]
tests/unit/test_resources.py::test_collection_generic_type PASSED        [ 79%]
tests/unit/test_resources.py::test_missing_is_singleton PASSED           [ 83%]
tests/unit/test_resources.py::test_missing_not_none PASSED               [ 87%]
tests/unit/test_resources.py::test_missing_not_equal_to_anything PASSED  [ 91%]
tests/unit/test_resources.py::test_full_transformation_pipeline PASSED   [ 95%]
tests/unit/test_resources.py::test_collection_transformation_pipeline PASSED [100%]

============================== 24 passed in 2.01s ==============================
```

---

## Key Learnings

### 1. Decoupling Database from API

Resources solve the problem of tight coupling between database schema and API responses:

**Without Resources:**
```python
@app.get("/users/{id}")
async def get_user(id: int, repo: UserRepository = Inject()):
    user = await repo.find(id)
    return user  # Exposes internal structure, all fields, no formatting
```

**With Resources:**
```python
@app.get("/users/{id}")
async def get_user(id: int, repo: UserRepository = Inject()):
    user = await repo.find(id)
    return UserResource.make(user).resolve()  # Controlled, formatted, secure
```

### 2. Sentinel Values vs Null

Using `MISSING` sentinel instead of `None` allows distinguishing between:
- Field intentionally set to null (`None`)
- Field conditionally excluded (`MISSING`)

```python
# ❌ Ambiguous with None
"email": None if not is_admin else self.resource.email
# Response: {"email": null}  # Key exists with null value

# ✅ Clear with MISSING
"email": self.when(is_admin, self.resource.email)
# Response: {}  # Key doesn't exist
```

### 3. N+1 Query Prevention

`when_loaded()` prevents accidental N+1 queries:

```python
# ❌ Without when_loaded() - triggers lazy load (N+1!)
"posts": [PostResource.make(p).to_array() for p in self.resource.posts]

# ✅ With when_loaded() - only if eager-loaded
posts = self.when_loaded("posts")
"posts": PostResource.collection(posts).resolve()["data"]
        if posts is not MISSING
        else MISSING
```

### 4. Type Safety with Generics

Generic `T` parameter provides type safety:

```python
class JsonResource(Generic[T]):
    def __init__(self, resource: T) -> None:
        self.resource = resource  # T type preserved

resource: JsonResource[User] = UserResource.make(user)
resource.resource.id  # MyPy knows it's User, autocomplete works
```

### 5. Adapter Pattern in Practice

Resources are adapters between two incompatible interfaces:

```python
# Source interface (Database)
user = User(
    id=1,
    first_name="John",
    last_name="Doe",
    password_hash="hashed",
    created_at=datetime(2026, 1, 1)
)

# Target interface (API)
{
    "data": {
        "id": 1,
        "name": "John Doe",  # Adapted: first_name + last_name
        "member_since": "2026-01-01T00:00:00"  # Adapted: formatted datetime
        # password_hash excluded
    }
}
```

---

## Laravel Comparison

### Laravel API Resources

```php
// Laravel
class UserResource extends JsonResource
{
    public function toArray($request)
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'email' => $this->when($request->user()->isAdmin(), $this->email),
            'posts' => PostResource::collection($this->whenLoaded('posts')),
        ];
    }
}

// Usage
return new UserResource($user);
return UserResource::collection($users);
```

### Fast Track Framework (This Sprint)

```python
# FTF
class UserResource(JsonResource[User]):
    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        is_admin = request and hasattr(request.state, "user") and request.state.user.is_admin

        return {
            "id": self.resource.id,
            "name": self.resource.name,
            "email": self.when(is_admin, self.resource.email),
            "posts": PostResource.collection(self.when_loaded("posts")).resolve()["data"]
                    if self.when_loaded("posts") is not MISSING
                    else MISSING,
        }

# Usage
return UserResource.make(user).resolve()
return UserResource.collection(users).resolve()
```

**Key Differences:**
- FTF uses **explicit typing** (`JsonResource[User]`) vs Laravel's magic properties
- FTF uses **MISSING sentinel** instead of excluding keys with null
- FTF requires **explicit resolve()** call (clearer intention)
- FTF returns **dict** (FastAPI JSON serialization) vs Laravel's Response object

---

## What's Next

### Possible Enhancements

1. **Pagination Metadata**: Auto-detect Paginator and add meta/links
2. **Resource Wrapping Control**: Configure "data" wrapper key
3. **Meta Information**: Add custom metadata to responses
4. **Nested Resources**: Better handling of deep nesting
5. **Conditional Resources**: Entire resources based on conditions
6. **Resource Merging**: Combine multiple resources
7. **Response Macros**: Reusable response transformations
8. **Anonymous Resources**: On-the-fly resources without classes

---

## Success Criteria

✅ All 24 tests passing (100%)
✅ MyPy strict mode passes (no errors)
✅ Ruff linting passes (no errors)
✅ Coverage >80% on resources module
✅ JsonResource base class working
✅ ResourceCollection working
✅ Conditional attributes with when()
✅ Relationship loading with when_loaded()
✅ make:resource CLI command
✅ Complete example working
✅ Documentation complete

---

## Statistics

- **Files Added/Modified**: 6
- **Lines of Code**: ~1,600 (including tests and examples)
- **Tests**: 24 (100% passing)
- **Coverage**: 82.86% (core.py), 88.24% (collection.py)
- **CLI Commands**: 1 new (make:resource)
- **Design Patterns**: 4 (Adapter, Template Method, Builder, Sentinel)

---

## Conclusion

Sprint 4.2 delivers a production-ready API Resource system with:
- **Clean Separation**: Database schema vs API format
- **Type Safety**: Full Generic support with MyPy
- **Performance**: N+1 prevention with when_loaded()
- **Security**: Hide sensitive fields
- **Flexibility**: Conditional, computed, nested fields
- **Laravel Parity**: Familiar API for Laravel developers

The resource system is ready for use in production APIs and provides a solid foundation for advanced features like pagination metadata, resource caching, and custom wrappers.
