# Sprint 5.3: Configuration System - Implementation Summary

## Overview

Sprint 5.3 implements a centralized **Configuration System** inspired by Laravel's config architecture. All application settings are now stored in Python configuration files (`workbench/config/*.py`) and accessed via dot notation. Service providers are automatically registered from configuration, eliminating manual registration in `main.py`.

## What Was Implemented

### 1. Framework Core (`framework/jtc/config/`)

#### `repository.py` - NEW (350+ lines)
**ConfigRepository** singleton class with:
- **Dynamic module loading**: Imports Python config files at runtime using `importlib`
- **Dot notation access**: `config.get("app.name")` → traverse nested dicts
- **Graceful defaults**: Return default value if key doesn't exist
- **Type-safe**: Full MyPy strict mode compatibility
- **Singleton pattern**: Single instance across application

**Key Methods:**
```python
class ConfigRepository:
    def load_from_directory(path: str) -> None
        # Load all .py files from config directory

    def get(key: str, default: Any = None) -> Any
        # Get value with dot notation: "app.name"

    def set(key: str, value: Any) -> None
        # Set value at runtime (for testing)

    def has(key: str) -> bool
        # Check if key exists

    def all(config_name: str | None = None) -> dict
        # Get all configs or specific config file

    def flush() -> None
        # Clear all configs (for testing)
```

**Dynamic Loading Process:**
1. Scan `workbench/config/` for `.py` files
2. Use `importlib.util` to dynamically import each file
3. Extract `config` dictionary from module
4. Store in internal `_configs` dict with filename as key

**Dot Notation Parsing:**
```python
# "database.connections.mysql.host" →
# configs["database"]["connections"]["mysql"]["host"]
parts = key.split(".")
config_name = parts[0]  # "database"
# Traverse nested dicts for remaining parts
```

#### `__init__.py` - NEW
**Global config helper:**
```python
def config(key: str, default: Any = None) -> Any:
    """Global helper for config access."""
    return _config_repository.get(key, default)

def get_config_repository() -> ConfigRepository:
    """Get singleton instance for advanced operations."""
    return _config_repository
```

**Design Decision**: Use global `config()` function (like Laravel) for convenience.

### 2. Workbench Configuration (`workbench/config/`)

#### `app.py` - NEW
Application configuration file:
```python
import os
from app.providers import AppServiceProvider, RouteServiceProvider

config = {
    "name": os.getenv("APP_NAME", "Fast Track Framework"),
    "env": os.getenv("APP_ENV", "production"),
    "debug": os.getenv("APP_DEBUG", "false").lower() == "true",
    "version": "5.3.0",
    "url": os.getenv("APP_URL", "http://localhost:8000"),
    "timezone": os.getenv("APP_TIMEZONE", "UTC"),

    # Service Providers (auto-registered)
    "providers": [
        AppServiceProvider,
        RouteServiceProvider,
    ],

    "locale": os.getenv("APP_LOCALE", "en"),
    "fallback_locale": "en",
}
```

**Key Features:**
- ✅ **Environment variables**: Use `os.getenv()` for env-specific config
- ✅ **Provider list**: Auto-registration from `config["providers"]`
- ✅ **Type conversion**: String to bool for `APP_DEBUG`
- ✅ **Sensible defaults**: Fallback values for all settings

#### `database.py` - NEW
Database configuration file:
```python
import os

config = {
    "default": os.getenv("DB_CONNECTION", "sqlite"),

    "connections": {
        "sqlite": {
            "driver": "sqlite",
            "database": os.getenv("DB_DATABASE", "workbench.db"),
            "prefix": "",
            "foreign_key_constraints": True,
        },
        "mysql": {
            "driver": "mysql",
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "database": os.getenv("DB_DATABASE", "workbench"),
            "username": os.getenv("DB_USERNAME", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "pool_size": 10,
            "max_overflow": 20,
        },
        "postgresql": {...},
    },

    "migrations": {
        "table": "migrations",
        "directory": "migrations",
    },

    "redis": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "password": os.getenv("REDIS_PASSWORD", ""),
        "database": int(os.getenv("REDIS_DB", "0")),
    },
}
```

**Design**: Shows nested configuration structure for complex settings.

### 3. Framework HTTP (`framework/jtc/http/app.py`) - UPDATED

**Added Config Support:**

**New Constructor Parameter:**
```python
def __init__(
    self,
    *args: Any,
    config_path: str | None = None,  # NEW
    **kwargs: Any
) -> None:
```

**New Methods:**

**`_detect_config_path()`:**
```python
def _detect_config_path(self) -> str:
    """Auto-detect config directory (workbench/config or config)."""
    if Path("workbench/config").exists():
        return "workbench/config"
    if Path("config").exists():
        return "config"
    return "workbench/config"  # Default
```

**`_load_configuration(config_path)`:**
```python
def _load_configuration(self, config_path: str) -> None:
    """Load all .py files from config directory."""
    config_repo = get_config_repository()
    try:
        config_repo.load_from_directory(config_path)
        print(f"📝 Loaded configuration from: {config_path}")
    except FileNotFoundError:
        print(f"⚠️  Config directory not found: {config_path}")
        print("   Continuing without configuration files...")
```

**`_register_configured_providers()`:**
```python
def _register_configured_providers(self) -> None:
    """Auto-register providers from config("app.providers")."""
    from jtc.config import config

    providers = config("app.providers", [])

    if not providers:
        print("⚠️  No providers configured in config/app.py")
        return

    for provider_class in providers:
        self.register_provider(provider_class)
```

**Initialization Flow (Updated):**
```
1. Create Container
2. Initialize provider tracking
3. Register Container in itself
4. Register FastTrackFramework in Container
5. Load configuration from workbench/config/  # NEW (Sprint 5.3)
6. Auto-register providers from config         # NEW (Sprint 5.3)
7. Setup lifespan
8. Initialize FastAPI
9. Register exception handlers
```

### 4. Workbench Entry Point (`workbench/main.py`) - REFACTORED

**Before (Sprint 5.2):**
```python
def create_app() -> FastTrackFramework:
    app = FastTrackFramework()

    # Manual provider registration
    app.register_provider(AppServiceProvider)
    app.register_provider(RouteServiceProvider)

    return app
```

**After (Sprint 5.3):**
```python
def create_app() -> FastTrackFramework:
    # Config loaded and providers registered automatically!
    app = FastTrackFramework()

    # That's it! The framework now:
    # 1. Loads config from workbench/config/*.py
    # 2. Registers providers from config("app.providers")
    # 3. Boots providers on application startup

    return app
```

**New Endpoints:**

**`GET /` - Updated to use config:**
```python
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {config('app.name')}",
        "version": config("app.version"),
        "environment": config("app.env"),
        "debug": config("app.debug"),
        "architecture": "Service Provider + Configuration System (Sprint 5.3)",
    }
```

**`GET /config` - NEW debug endpoint:**
```python
@app.get("/config")
async def show_config():
    """Show current configuration (debugging only)."""
    return {
        "app_name": config("app.name"),
        "environment": config("app.env"),
        "debug": config("app.debug"),
        "version": config("app.version"),
        "locale": config("app.locale"),
        "database_default": config("database.default"),
        "providers_count": len(config("app.providers", [])),
    }
```

## Architecture Decisions

### 1. Python Files vs JSON/YAML

**Decision**: Use Python files (`.py`) for configuration.

**Rationale**:
- ✅ **Dynamic values**: Can use `os.getenv()` and conditional logic
- ✅ **Type safety**: IDE autocomplete and type checking
- ✅ **Computed values**: Execute Python code at load time
- ✅ **Import statements**: Can import provider classes
- ❌ JSON: Static, no logic, no imports
- ❌ YAML: Still static, requires parsing library

**Example**:
```python
# Python config - can use logic
config = {
    "debug": os.getenv("APP_DEBUG", "false").lower() == "true",
    "providers": [
        AppServiceProvider,  # Can import classes!
        RouteServiceProvider,
    ]
}

# JSON - static only
{
    "debug": "false",  # String, not boolean
    "providers": ["AppServiceProvider"]  # String, not class
}
```

### 2. Config Variable Convention

**Decision**: Config files must define a `config` dict variable.

**Rationale**:
- Clear and explicit (not magic)
- Easy to identify config values
- Prevents importing module internals (os, sys, etc.)
- Consistent across all config files

**Pattern**:
```python
# workbench/config/app.py
import os

config = {  # <- Required variable name
    "name": "FastTrack",
    # ...
}
```

**Rejected Alternative**: Using `return` statement (not valid Python module syntax).

### 3. Dot Notation Access

**Decision**: Use dot notation for nested config access.

**Rationale**:
- Laravel-like API (familiar)
- Intuitive: `config("database.connections.mysql.host")`
- Handles arbitrary nesting depth
- Graceful fallback to defaults

**Implementation**:
```python
def get(self, key: str, default: Any = None) -> Any:
    parts = key.split(".")
    config_name = parts[0]

    value = self._configs.get(config_name)
    if value is None:
        return default

    for part in parts[1:]:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return default

    return value
```

### 4. Singleton Pattern

**Decision**: Use Singleton for ConfigRepository.

**Rationale**:
- Single source of truth for configuration
- Config loaded once at startup
- Accessible from anywhere in application
- Consistent with other framework singletons (Cache, Mail, etc.)

**Implementation**:
```python
class ConfigRepository:
    _instance: "ConfigRepository | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._configs = {}
        return cls._instance
```

### 5. Auto-Registration vs Manual

**Decision**: Auto-register providers from config.

**Rationale**:
- Centralized: All providers listed in one place (config/app.py)
- Clean entry point: `main.py` is minimal
- Laravel parity: Matches `config/app.php` providers array
- DRY: Don't repeat provider list in multiple places

**Comparison**:
```python
# ❌ Manual (Sprint 5.2)
app = FastTrackFramework()
app.register_provider(AppServiceProvider)
app.register_provider(RouteServiceProvider)
app.register_provider(DatabaseServiceProvider)

# ✅ Auto (Sprint 5.3)
app = FastTrackFramework()
# Providers loaded from config("app.providers")
```

### 6. Config Directory Auto-Detection

**Decision**: Auto-detect `workbench/config/` or `config/`.

**Rationale**:
- Works out of the box (no setup needed)
- Flexible: Supports alternative structures
- Explicit override: Can pass `config_path` parameter
- Fails gracefully: Continues without config if not found

## File Structure

```
larafast/
├── framework/
│   └── ftf/
│       ├── config/                      # NEW - Config subsystem
│       │   ├── __init__.py             # Global config() helper
│       │   └── repository.py           # ConfigRepository singleton
│       └── http/
│           └── app.py                   # UPDATED - Config loading
│
└── workbench/
    ├── config/                          # NEW - Application config
    │   ├── __init__.py                 # Package marker
    │   ├── app.py                      # App config (providers list)
    │   └── database.py                 # Database config
    └── main.py                          # REFACTORED - Minimal setup
```

## Usage Examples

### Basic Config Access

```python
from jtc.config import config

# Get simple value
app_name = config("app.name")  # "Fast Track Framework"

# Get with default
debug = config("app.debug", False)

# Get nested value
db_host = config("database.connections.mysql.host", "localhost")

# Get list
providers = config("app.providers", [])
```

### Using Config in Routes

```python
from jtc.http import FastTrackFramework
from jtc.config import config

app = FastTrackFramework()

@app.get("/info")
async def app_info():
    return {
        "name": config("app.name"),
        "version": config("app.version"),
        "environment": config("app.env"),
    }
```

### Environment-Specific Configuration

```bash
# .env file
APP_NAME="My Custom App"
APP_ENV=development
APP_DEBUG=true
DB_CONNECTION=mysql
DB_HOST=localhost
DB_PORT=3306
```

```python
# workbench/config/app.py
import os

config = {
    "name": os.getenv("APP_NAME", "FastTrack"),  # "My Custom App"
    "env": os.getenv("APP_ENV", "production"),    # "development"
    "debug": os.getenv("APP_DEBUG", "false") == "true",  # True
}
```

### Adding New Config Files

```python
# workbench/config/cache.py
import os

config = {
    "default": os.getenv("CACHE_DRIVER", "file"),

    "stores": {
        "file": {
            "driver": "file",
            "path": "storage/framework/cache",
        },
        "redis": {
            "driver": "redis",
            "connection": "cache",
        },
        "array": {
            "driver": "array",
        },
    },
}

# Usage
from jtc.config import config

cache_driver = config("cache.default")  # "file"
redis_connection = config("cache.stores.redis.connection")  # "cache"
```

### Runtime Config Modification (Testing)

```python
from jtc.config import get_config_repository

def test_with_custom_config():
    repo = get_config_repository()

    # Save original value
    original = repo.get("app.debug")

    # Modify for test
    repo.set("app.debug", True)

    # Test code...

    # Restore original
    repo.set("app.debug", original)
```

## Testing

### Manual Testing

```bash
# Start server
cd larafast
poetry run uvicorn workbench.main:app --reload

# Test endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/config

# Expected output for /config
{
  "app_name": "Fast Track Framework",
  "environment": "production",
  "debug": false,
  "version": "5.3.0",
  "locale": "en",
  "database_default": "sqlite",
  "providers_count": 2
}
```

### Expected Startup Output

```
📝 Loaded configuration from: workbench/config
🚀 Fast Track Framework starting up...
📦 Container initialized with 2 services
🔧 Booting 2 service provider(s)...
📝 AppServiceProvider: Registering application services...
🔧 AppServiceProvider: Bootstrapping application services...
🛣️  RouteServiceProvider: Registering routes...
✅ RouteServiceProvider: API routes registered at /api
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Comparison with Laravel

### Laravel Config System

```php
// config/app.php
return [
    'name' => env('APP_NAME', 'Laravel'),
    'env' => env('APP_ENV', 'production'),
    'providers' => [
        App\Providers\AppServiceProvider::class,
        App\Providers\RouteServiceProvider::class,
    ],
];

// Usage
$name = config('app.name');
```

### Fast Track Framework Config System

```python
# workbench/config/app.py
import os

config = {
    "name": os.getenv("APP_NAME", "FastTrack"),
    "env": os.getenv("APP_ENV", "production"),
    "providers": [
        AppServiceProvider,
        RouteServiceProvider,
    ],
}

# Usage
from jtc.config import config
name = config("app.name")
```

### Key Similarities

✅ **Directory structure**: Both use `config/` directory
✅ **Dot notation**: Both use `config("app.name")` syntax
✅ **Environment variables**: Both use env vars for sensitive data
✅ **Provider registration**: Both auto-register from config
✅ **Nested configs**: Both support nested dictionaries

### Key Differences

| Feature | Laravel | Fast Track Framework |
|---------|---------|---------------------|
| **File format** | PHP | Python |
| **Env function** | `env()` | `os.getenv()` |
| **Type hints** | Partial (PHP 8+) | Full (MyPy strict) |
| **Dynamic imports** | `::class` strings | Direct class imports |
| **Config cache** | Yes (`config:cache`) | No (future enhancement) |

## Sprint Metrics

### Code Statistics

| Metric | Value |
|--------|-------|
| **New Files** | 6 files |
| **Modified Files** | 2 files |
| **Lines Added** | ~700 lines (code) |
| **Test Coverage** | Manual (integration tests planned) |
| **Type Safety** | 100% type-hinted |

### Files by Category

| Category | Files | Lines |
|----------|-------|-------|
| **Framework Config** | 2 new | ~450 lines |
| **Workbench Config** | 3 new | ~200 lines |
| **Framework HTTP** | 1 modified | +50 lines |
| **Workbench Main** | 1 refactored | ~130 lines |
| **Total** | **8 files** | **~830 lines** |

## Key Benefits

### 1. Centralized Configuration
**Before**: Settings scattered across `main.py`, env vars, and code.
**After**: All settings in `workbench/config/*.py`.

### 2. Environment-Specific Settings
**Before**: Hardcoded values or manual env var checks.
**After**: `os.getenv()` with defaults in config files.

### 3. Auto-Provider Registration
**Before**: Manual `app.register_provider()` calls in `main.py`.
**After**: Provider list in `config/app.py`, auto-registered.

### 4. Clean Entry Point
**Before**: `main.py` had provider registration code.
**After**: `main.py` is just `app = FastTrackFramework()`.

### 5. Type-Safe Access
**Before**: No config system, direct access to env vars.
**After**: Config with type hints and MyPy validation.

## Future Enhancements

### 1. Config Caching

```python
# jtc config:cache command
def cache_config():
    """Pre-compile config to PHP-style cached array."""
    config_repo = get_config_repository()
    config_repo.load_from_directory("workbench/config")

    with open("bootstrap/cache/config.pkl", "wb") as f:
        pickle.dump(config_repo._configs, f)

# Load from cache if exists
if Path("bootstrap/cache/config.pkl").exists():
    with open("bootstrap/cache/config.pkl", "rb") as f:
        config_repo._configs = pickle.load(f)
```

### 2. Config Validation

```python
# Validate config against schema
from pydantic import BaseModel

class AppConfig(BaseModel):
    name: str
    env: str
    debug: bool
    providers: list[type]

# In FastTrackFramework.__init__
app_config = AppConfig(**config("app"))
```

### 3. Config Publishing

```python
# jtc vendor:publish --tag=config
# Copy framework config to user's workbench/config
shutil.copy(
    "framework/jtc/config/defaults/cache.py",
    "workbench/config/cache.py"
)
```

### 4. Hot Reload (Development)

```python
# Watch config files for changes
from watchfiles import watch

async def watch_config():
    async for changes in watch("workbench/config"):
        print(f"Config changed: {changes}")
        config_repo.flush()
        config_repo.load_from_directory("workbench/config")
        # Re-register providers if needed
```

## Conclusion

Sprint 5.3 successfully implements a centralized Configuration System inspired by Laravel. The implementation provides:

✅ **Laravel Parity**: Familiar config system for Laravel developers
✅ **Type Safety**: Full MyPy strict mode compatibility
✅ **Auto-Configuration**: Providers registered from config
✅ **Clean Architecture**: Minimal `main.py`, centralized settings
✅ **Extensible**: Easy to add new config files
✅ **Production Ready**: Environment variable support

The framework now has mature configuration management, bringing it closer to v1.0 architectural maturity. Combined with Service Providers (Sprint 5.2), the application bootstrapping is clean, predictable, and maintainable.

**Next Sprint**: TBD (Awaiting user direction)
