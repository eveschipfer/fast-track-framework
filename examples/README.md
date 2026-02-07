# Fast Track Framework - Examples

This directory contains practical examples demonstrating the framework's features.

## Available Examples

### 1. Database Example (`database_example.py`)

Complete CRUD API demonstrating:
- ✅ FastAPI + IoC Container integration
- ✅ SQLAlchemy AsyncEngine (singleton)
- ✅ AsyncSession (scoped per request)
- ✅ Repository Pattern (NOT Active Record)
- ✅ Dependency injection with `Inject()`
- ✅ Automatic session cleanup
- ✅ Custom repository methods
- ✅ Pydantic validation

**Run:**
```bash
python examples/database_example.py
```

**Test:**
```bash
# Create user
curl -X POST http://localhost:8000/users \
     -H "Content-Type: application/json" \
     -d '{"name":"Alice","email":"alice@example.com"}'

# List users
curl http://localhost:8000/users

# Get user by ID
curl http://localhost:8000/users/1

# Update user
curl -X PUT http://localhost:8000/users/1 \
     -H "Content-Type: application/json" \
     -d '{"name":"Alice Updated"}'

# Delete user
curl -X DELETE http://localhost:8000/users/1

# Find by email
curl http://localhost:8000/users/email/alice@example.com

# Get stats
curl http://localhost:8000/stats
```

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Concepts Demonstrated

### Dependency Injection
```python
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    repo: UserRepository = Inject(UserRepository)  # ← Automatic injection
):
    return await repo.find_or_fail(user_id)
```

### Repository Pattern
```python
class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    # Add custom methods
    async def find_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
```

### Container Registration
```python
# Singleton: App-wide shared instance
app.container.register(AsyncEngine, instance=engine)

# Scoped: One per HTTP request
app.register(AsyncSession, implementation=session_factory, scope="scoped")

# Transient: New instance every time
app.register(UserRepository, scope="transient")
```

### Automatic Cleanup
```python
# Middleware handles session lifecycle
set_scoped_cache({})          # Request start
response = await call_next()   # Process request
await clear_scoped_cache_async()  # Cleanup (calls session.close())
```

## Comparison: Eloquent vs Repository Pattern

### Laravel (Active Record)
```php
// Laravel - NOT possible in async Python!
$user = User::find(1);
$user->name = "Updated";
$user->save();  // ❌ Where does session come from?
```

### FastTrack (Repository Pattern)
```python
# FastTrack - Explicit and testable
repo = UserRepository(session)  # ✅ Explicit dependency
user = await repo.find(1)
user.name = "Updated"
await repo.update(user)  # ✅ Clear transaction control
```

**Why Repository?**
- ✅ Explicit session dependency (testable)
- ✅ Works everywhere (HTTP, CLI, jobs, tests)
- ✅ Manual transaction control
- ✅ Type-safe with MyPy
- ✅ No ContextVar global state

## Testing Examples

Each example can be tested with:

```bash
# Install dependencies
poetry install

# Run tests
pytest tests/integration/test_database_integration.py -v

# Run example
python examples/database_example.py
```

## Adding Your Own Examples

1. Create new file: `examples/my_example.py`
2. Import framework: `from jtc.http import FastTrackFramework`
3. Follow patterns from existing examples
4. Add documentation to this README

## More Information

- [Sprint 2.2 Implementation](../SPRINT_2_2_DATABASE_IMPLEMENTATION.md)
- [Database Module](../src/jtc/database/)
- [Models Module](../src/jtc/models/)
- [Integration Tests](../tests/integration/)
