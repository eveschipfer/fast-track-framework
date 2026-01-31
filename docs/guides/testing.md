# 🧪 Testing Guide

Fast Track Framework maintains 64 passing tests with comprehensive coverage of critical functionality.

## Test Structure

```
tests/
├── unit/                          # Isolated component tests
│   ├── test_repository.py         # Repository CRUD (17 tests)
│   ├── test_query_builder.py      # Query Builder (38 tests)
│   └── test_container*.py         # Container tests
├── integration/                   # Multi-component tests
│   └── test_database_integration.py  # Full stack (9 tests)
└── conftest.py                    # Shared fixtures
```

## Running Tests

```bash
# All tests
poetry run pytest tests/ -v

# With coverage
poetry run pytest tests/ -v --cov

# Specific suite
poetry run pytest tests/unit/test_repository.py -v
poetry run pytest tests/integration/ -v

# HTML coverage report
poetry run pytest tests/ --cov --cov-report=html
open htmlcov/index.html
```

## Test Philosophy

- **Unit Tests**: Isolated with mocked dependencies
- **Integration Tests**: Real database (in-memory SQLite)
- **Coverage Target**: >80% for critical paths
- **Type Safety**: All tests pass MyPy strict mode

## Example Tests

### Repository Tests
```python
import pytest
from fast_query import Base, BaseRepository, create_engine

@pytest.mark.asyncio
async def test_create_user(user_repo):
    user = User(name="Alice", email="alice@example.com")
    created = await user_repo.create(user)

    assert created.id is not None
    assert created.name == "Alice"

@pytest.mark.asyncio
async def test_find_or_fail_raises_exception(user_repo):
    from fast_query import RecordNotFound

    with pytest.raises(RecordNotFound) as exc_info:
        await user_repo.find_or_fail(999)

    assert exc_info.value.model_name == "User"
    assert exc_info.value.identifier == 999
```

### Query Builder Tests
```python
@pytest.mark.asyncio
async def test_fluent_query(user_repo):
    # Create test data
    await user_repo.create(User(name="Alice", age=25))
    await user_repo.create(User(name="Bob", age=30))

    # Query with fluent builder
    adults = await (
        user_repo.query()
        .where(User.age >= 18)
        .order_by(User.created_at, "desc")
        .limit(10)
        .get()
    )

    assert len(adults) == 2
```

## Fixtures

### Database Fixtures

```python
# conftest.py
import pytest
from fast_query import create_engine, AsyncSessionFactory

@pytest.fixture
async def engine():
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def session(engine):
    factory = AsyncSessionFactory()
    async with factory() as session:
        yield session

@pytest.fixture
def user_repo(session):
    return UserRepository(session)
```

## Best Practices

### 1. Use Fixtures
```python
# ✅ Good - Reusable fixture
@pytest.fixture
def user_repo(session):
    return UserRepository(session)

def test_something(user_repo):
    # Use fixture
    pass
```

### 2. Async Tests
```python
# ✅ Use pytest-asyncio
@pytest.mark.asyncio
async def test_async_operation(user_repo):
    user = await user_repo.create(User(name="Alice"))
    assert user.id is not None
```

### 3. Mock External Dependencies
```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_with_mock():
    mock_repo = AsyncMock(spec=UserRepository)
    mock_repo.find.return_value = User(id=1, name="Alice")

    service = UserService(mock_repo)
    user = await service.get_user(1)

    assert user.name == "Alice"
    mock_repo.find.assert_called_once_with(1)
```

---

See [Database Guide](database.md) and [Container Guide](container.md) for more details.
