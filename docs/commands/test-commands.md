# Test Commands

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21

This section documents testing-related commands and practices.

## Overview

The Fast Track Framework uses **pytest** as its testing framework, not CLI-based test commands like Laravel. However, the framework includes example commands (`test` and `test_deploy`) that demonstrate how to create custom CLI commands for project-specific testing needs.

---

## Running Tests

The framework uses pytest for all testing. Tests are located in the `workbench/tests/` directory.

### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_repository.py

# Run specific test function
pytest tests/unit/test_repository.py::test_create_user

# Run tests matching pattern
pytest -k "user"
```

### Docker Environment

Since the framework runs in Docker, run tests inside the container:

```bash
# Run all tests in Docker
docker exec fast_track_dev bash -c "cd larafast && pytest workbench/tests/ -v"

# Run specific test file
docker exec fast_track_dev bash -c "cd larafast && pytest tests/unit/test_container.py -v"

# Run with coverage
docker exec fast_track_dev bash -c "cd larafast && pytest workbench/tests/ --cov"
```

### Common pytest Options

```bash
# Verbose output
pytest -v

# Show local variables (useful for debugging)
pytest -vv

# Stop on first failure
pytest -x

# Run only specific markers (unit, integration, slow)
pytest -m unit

# Exclude slow tests
pytest -m "not slow"

# Parallel execution (requires pytest-xdist)
pytest -n auto
```

---

## Example CLI Commands

The framework includes example custom commands that demonstrate how to extend the CLI:

### test

A custom command example showing how to create CLI commands.

#### Registration

The command must be manually registered in `src/jtc/cli/main.py`:

```python
from jtc.cli.commands.test import app as test_app
app.add_typer(test_app, name="test")
```

#### Usage

```bash
# Run the test command
jtc test

# With options
jtc test --option value

# With flag
jtc test --flag
```

#### What It Does

This is a placeholder/example command. In a real project, you would customize it to:
- Run test suites
- Generate test reports
- Set up test databases
- Clear test caches
- Other testing-related automation

### testdeploy

Another example command showing deployment-related testing.

#### Registration

```python
from jtc.cli.commands.test_deploy import app as test_deploy_app
app.add_typer(test_deploy_app, name="testdeploy")
```

#### Usage

```bash
jtc testdeploy
```

#### What It Does

Placeholder example for deployment testing commands. Customize to:
- Run deployment tests
- Verify production readiness
- Run health checks
- Rollback if tests fail

---

## Creating Custom Test Commands

### Step 1: Generate Command

```bash
jtc make:cmd runtests
```

This creates `src/jtc/cli/commands/runtests.py` with boilerplate code.

### Step 2: Implement Command Logic

Edit the generated file:

```python
"""
Run Tests Command

Custom CLI command to run project test suite.
"""
import subprocess
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def main(
    coverage: bool = typer.Option(False, "--coverage", "-c", help="Run with coverage"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    parallel: bool = typer.Option(False, "--parallel", "-p", help="Parallel execution"),
) -> None:
    """Run test suite with various options."""
    console.print("[bold cyan]Running test suite...[/bold cyan]")
    
    # Build pytest command
    cmd = ["pytest", "workbench/tests/"]
    
    if coverage:
        cmd.append("--cov")
    
    if verbose:
        cmd.append("-vv")
    
    if parallel:
        cmd.append("-n")
        cmd.append("auto")
    
    # Run tests
    console.print(f"[dim]Executing: {' '.join(cmd)}[/dim]")
    console.print()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        console.print(result.stdout)
        
        if result.returncode == 0:
            console.print("[bold green]✓ Tests passed![/bold green]")
        else:
            console.print("[bold red]✗ Tests failed[/bold red]")
            raise typer.Exit(code=result.returncode)
    
    except Exception as e:
        console.print(f"[red]✗ Error running tests:[/red] {e}")
        raise typer.Exit(code=1)
```

### Step 3: Register Command

Add to `src/jtc/cli/main.py`:

```python
from jtc.cli.commands.runtests import app as runtests_app

# Register custom command
app.add_typer(runtests_app, name="runtests")
```

### Step 4: Run Custom Command

```bash
jtc runtests

# With options
jtc runtests --coverage --parallel

# Verbose mode
jtc runtests -vv
```

---

## Test Organization

### Directory Structure

```
workbench/tests/
├── unit/              # Unit tests (isolated, fast)
│   ├── test_container.py
│   ├── test_repository.py
│   └── test_query_builder.py
├── integration/         # Integration tests (real database, services)
│   ├── test_api.py
│   └── test_auth.py
├── contract/           # Contract tests (verify interface contracts)
├── benchmarks/         # Performance benchmarks
│   └── benchmark_*.py
├── factories/          # Test data factories
│   └── user_factory.py
└── seeders/           # Database seeders
    └── database_seeder.py
```

### Test Categories

#### Unit Tests

```python
# workbench/tests/unit/test_repository.py
import pytest
from app.models import User
from app.repositories import UserRepository

@pytest.mark.unit
def test_create_user():
    """Test creating a user in database."""
    user = User(name="Alice", email="alice@example.com")
    assert user.name == "Alice"
```

**Characteristics**:
- No external dependencies
- Use mocks/fakes
- Fast execution
- Test specific functionality

#### Integration Tests

```python
# workbench/tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.mark.integration
async def test_register_user():
    """Test user registration through API."""
    response = client.post("/register", json={
        "name": "Alice",
        "email": "alice@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
```

**Characteristics**:
- Real database
- Real HTTP client
- Test component interaction
- Slower than unit tests

#### Contract Tests

```python
# workbench/tests/contract/test_sql_contract.py
import pytest

@pytest.mark.contract
def test_repository_contract():
    """Verify Repository follows interface contract."""
    # Test all required methods exist
    assert hasattr(UserRepository, 'create')
    assert hasattr(UserRepository, 'find')
    assert hasattr(UserRepository, 'update')
    assert hasattr(UserRepository, 'delete')
```

**Characteristics**:
- Verify interfaces
- Test architecture contracts
- Language-agnostic (Python, TypeScript, etc.)

#### Benchmarks

```python
# workbench/tests/benchmarks/test_query_performance.py
import pytest

@pytest.mark.benchmark
def test_query_performance(benchmark):
    """Benchmark query execution time."""
    result = benchmark(repo.query().execute)
    assert len(result) > 0
```

**Characteristics**:
- Measure performance
- Compare implementations
- Profile bottlenecks

---

## Test Markers

The framework uses pytest markers to categorize tests:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run all except slow tests
pytest -m "not slow"

# Run multiple markers
pytest -m "unit or integration"
```

### Available Markers

- `unit`: Unit tests (isolated, fast)
- `integration`: Integration tests (real DB/services)
- `contract`: Contract tests (interface verification)
- `slow`: Slow tests (skip by default)
- `benchmark`: Performance benchmarks

### Running Marked Tests

```bash
# Run fast tests only (skip slow)
pytest -m "not slow" -v

# Run all integration tests
pytest -m integration -v

# Run only benchmarks
pytest -m benchmark -v
```

---

## Coverage

### Running with Coverage

```bash
# Generate coverage report
pytest --cov=framework/jtc --cov=workbench/app --cov-report=html

# Show coverage in terminal
pytest --cov=framework/jtc --cov=workbench/app --cov-report=term-missing

# Docker environment
docker exec fast_track_dev bash -c "cd larafast && pytest workbench/tests/ --cov"
```

### Coverage Report

After running, coverage reports are generated:
- `htmlcov/index.html` - HTML report
- Terminal output shows missing lines
- Target: 60% coverage

### Improving Coverage

```bash
# See coverage by file
pytest --cov-report=html

# Open HTML report
open htmlcov/index.html

# Find uncovered lines
grep -r "class=\"miss\"" htmlcov/
```

---

## Best Practices

### Test Structure

1. **Arrange-Act-Assert Pattern**:
   ```python
   def test_create_user():
       # Arrange: Set up test data
       user_data = {"name": "Alice"}
       
       # Act: Execute code
       user = repo.create(user_data)
       
       # Assert: Verify results
       assert user.name == "Alice"
   ```

2. **Descriptive Test Names**:
   ```python
   def test_create_user_returns_user_with_id():  # Good
   def test_user():  # Bad - too vague
   ```

3. **One Assertion Per Test**:
   ```python
   def test_user_name():  # One assertion
       assert user.name == "Alice"
   
   def test_user_properties():  # Multiple assertions
       assert user.name == "Alice"
       assert user.email == "alice@example.com"
   ```

### Isolation

- **Use Fixtures**: Shared test setup/teardown
- **Transaction Rollback**: Undo database changes after test
- **Mock External Services**: Don't make real API calls
- **Independent Files**: Each test file should run independently

### Maintenance

- **Keep Tests Fast**: Unit tests should run in < 1 second
- **Flaky Tests**: Fix unstable tests rather than mark as flaky
- **Clean Up**: Delete test data after test completes
- **Update Tests**: Keep tests in sync with production code

---

## Troubleshooting

### Tests Not Found

```bash
# Error: No tests collected
# Solution: Check test file location
ls workbench/tests/

# Verify test file names
# Should be test_*.py
```

### Import Errors

```bash
# Error: Module not found
# Solution: Check PYTHONPATH
export PYTHONPATH=/path/to/larafast:$PYTHONPATH

# Or run from project root
cd /path/to/larafast
pytest
```

### Database Connection Issues

```bash
# Error: Could not connect to database
# Solution: Check test database configuration
# Test database uses in-memory SQLite by default
cat workbench/tests/conftest.py

# Verify database URL
docker exec fast_track_dev bash -c "echo \$TEST_DATABASE_URL"
```

### Coverage Issues

```bash
# Coverage not generating
# Solution: Install coverage
poetry add pytest-cov

# Or specify coverage explicitly
pytest --cov=framework/jtc --cov=workbench/app
```

---

## Comparison with Laravel

| Laravel | Fast Track | Purpose |
|---------|-------------|----------|
| `php artisan test` | `pytest workbench/tests/` | Run test suite |
| `php artisan test --filter=UserTest` | `pytest tests/unit/test_user.py` | Run specific tests |
| `php artisan test --coverage` | `pytest --cov` | Coverage reporting |
| `php artisan make:test` | `jtc make:cmd` + pytest | Custom test commands |

---

## Related Commands

- [Make Commands](make-commands.md#makecmd) - Create custom CLI commands
- [Database Commands](db-commands.md) - Run database migrations for tests
- [Queue Commands](queue-commands.md) - Queue-related testing

---

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21
