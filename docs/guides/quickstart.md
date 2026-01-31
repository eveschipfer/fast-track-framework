# 🚀 Quick Start Guide

Get up and running with Fast Track Framework in less than 5 minutes.

## Prerequisites

- **Python 3.13** or higher
- **Poetry** (package manager)
- **Docker** (optional, for development environment)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/eveschipfer/fast-track-framework.git
cd fast-track-framework/larafast
```

### 2. Install Dependencies

```bash
# Install all dependencies with Poetry
poetry install

# Activate virtual environment
poetry shell
```

### 3. Run the Application

```bash
# Start development server
poetry run uvicorn ftf.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
poetry run python -m ftf.main
```

### 4. Verify Installation

Open your browser and visit:
- **API Docs**: http://localhost:8000/docs
- **Root Endpoint**: http://localhost:8000/

You should see: `{"message":"Welcome to Fast Track Framework! 🚀"}`

---

## Hello World Example

Create your first route with automatic dependency injection:

```python
from fastapi import APIRouter
from ftf.http import FastTrackFramework, Inject

# Create application with built-in IoC Container
app = FastTrackFramework(
    title="My API",
    version="1.0.0"
)

# Define a service
class UserService:
    def get_user(self, user_id: int):
        return {"id": user_id, "name": "John Doe"}

# Register service in container
app.register(UserService, scope="transient")

# Create router
router = APIRouter()

# Define route with automatic dependency injection
@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    service: UserService = Inject(UserService)  # Auto-injected!
):
    return service.get_user(user_id)

# Include router
app.include_router(router)

# Run with: uvicorn main:app --reload
```

**Test it:**
```bash
# Root endpoint
curl http://localhost:8000/
# {"message":"Welcome to Fast Track Framework! 🚀"}

# Your new endpoint
curl http://localhost:8000/users/123
# {"id": 123, "name": "John Doe"}

# API docs (Swagger UI)
open http://localhost:8000/docs
```

---

## Run Tests

```bash
# All tests with coverage
poetry run pytest tests/ -v --cov

# Only unit tests
poetry run pytest tests/unit/ -v

# Only integration tests
poetry run pytest tests/integration/ -v

# Generate HTML coverage report
poetry run pytest tests/ --cov --cov-report=html
```

---

## Code Quality Checks

Fast Track Framework enforces strict code quality standards:

```bash
# Type checking (strict mode)
poetry run mypy src/

# Code formatting
poetry run black src/ tests/

# Import sorting
poetry run isort src/ tests/

# Linting
poetry run ruff check src/ tests/

# Run all checks at once
poetry run black src/ tests/ && \
poetry run isort src/ tests/ && \
poetry run ruff check src/ tests/ --fix && \
poetry run mypy src/
```

---

## Docker Development (Optional)

If you prefer using Docker:

```bash
# Start container
docker-compose up -d

# Enter container
docker exec -it fast_track_dev bash

# Inside container
cd larafast
poetry install
poetry run pytest tests/ -v
```

---

## Next Steps

Now that you have Fast Track Framework running, explore:

1. **[Database & ORM](database.md)** - Learn about Fast Query and Repository Pattern
2. **[IoC Container](container.md)** - Deep dive into Dependency Injection
3. **[Testing Guide](testing.md)** - Write tests with QueryCounter

---

## Troubleshooting

### Poetry not found
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

### Python version mismatch
```bash
# Check Python version
python --version

# Use pyenv to install Python 3.13
pyenv install 3.13.0
pyenv local 3.13.0
```

### Port 8000 already in use
```bash
# Use a different port
poetry run uvicorn ftf.main:app --reload --port 8001
```

---

**Ready to build?** Check out the [Database Guide](database.md) next! 🚀
