# CLI Commands Reference

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21

Welcome to the Fast Track Framework CLI Commands Reference. This documentation covers all available CLI commands for generating components, managing databases, caching, authentication, queues, testing, and deployment.

---

## Quick Reference

| Command Group | Description | Commands |
|--------------|-------------|----------|
| **[Make Commands](make-commands.md)** | Scaffolding for framework components | 18 commands |
| **[Database Commands](db-commands.md)** | Database migrations and seeding | 3 commands |
| **[Cache Commands](cache-commands.md)** | Cache management | 4 commands |
| **[Auth Commands](auth-commands.md)** | Authentication scaffolding | 1 command |
| **[Queue Commands](queue-commands.md)** | Background job processing | 3 commands |
| **[Test Commands](test-commands.md)** | Testing framework | pytest-based |
| **[Deploy Commands](deploy-commands.md)** | Deployment automation | Custom commands |

---

## Command Groups

### Make Commands

Scaffolding commands to generate framework components with proper structure and imports.

**Commands:**
- `make:model` - Generate SQLAlchemy models
- `make:repository` - Generate repository classes
- `make:request` - Generate FormRequest validators
- `make:resource` - Generate API resources
- `make:factory` - Generate test data factories
- `make:seeder` - Generate database seeders
- `make:controller` - Generate controller classes
- `make:provider` - Generate service providers
- `make:event` - Generate event classes
- `make:listener` - Generate event listeners
- `make:job` - Generate background jobs
- `make:middleware` - Generate HTTP middleware
- `make:mail` - Generate email mailables
- `make:auth` - Generate complete auth system
- `make:cmd` - Generate custom CLI commands
- `make:lang` - Generate translation files
- `make:rule` - Generate validation rules
- `make:k6` - Generate k6 load test scripts

**Quick Start:**
```bash
# Generate a model
jtc make:model User

# Generate complete authentication
jtc make auth

# See full documentation
[Make Commands](make-commands.md)
```

### Database Commands

Database management commands for migrations, rollbacks, and seeding.

**Commands:**
- `db:migrate` - Run database migrations
- `db:rollback` - Revert migrations
- `db:seed` - Populate database with test data

**Quick Start:**
```bash
# Run all pending migrations
jtc db:migrate

# Seed database
jtc db:seed

# See full documentation
[Database Commands](db-commands.md)
```

### Cache Commands

Cache management commands for clearing, forgetting, and testing cache.

**Commands:**
- `cache:clear` - Clear all cached data
- `cache:forget` - Remove specific cache key
- `cache:config` - Show cache configuration
- `cache:test` - Test cache functionality

**Quick Start:**
```bash
# Clear all cache
jtc cache:clear

# Show configuration
jtc cache:config

# See full documentation
[Cache Commands](cache-commands.md)
```

### Auth Commands

Authentication scaffolding command for generating complete JWT-based authentication system.

**Commands:**
- `make:auth` - Generate complete authentication system

**Quick Start:**
```bash
# Generate authentication scaffolding
jtc make auth

# See full documentation
[Auth Commands](auth-commands.md)
```

### Queue Commands

Background job processing and scheduled task management.

**Commands:**
- `queue:work` - Start queue worker
- `queue:list` - List scheduled tasks
- `queue:dashboard` - Start monitoring UI

**Quick Start:**
```bash
# Start queue worker
jtc queue work

# List scheduled tasks
jtc queue list

# See full documentation
[Queue Commands](queue-commands.md)
```

### Test Commands

Testing framework and test-related automation.

**Commands:**
- `test` - Example custom command
- `testdeploy` - Example deployment command

**Framework Testing:**
The framework uses **pytest** for testing, not CLI commands. See [Test Commands](test-commands.md) for comprehensive testing documentation.

**Quick Start:**
```bash
# Run all tests
pytest workbench/tests/

# Run with coverage
pytest --cov=framework/jtc --cov=workbench/app

# See full documentation
[Test Commands](test-commands.md)
```

### Deploy Commands

Deployment automation and commands.

**Commands:**
- `deploy` - Example deployment command

**Quick Start:**
```bash
# Run deployment (customize first)
jtc deploy

# See full documentation
[Deploy Commands](deploy-commands.md)
```

---

## Getting Help

Each command includes built-in help documentation.

```bash
# Show help for specific command
jtc make:model --help

# Show help for entire command group
jtc make --help

# Show help for all commands
jtc --help
```

---

## Common Options

Many commands support these common options:

### Force Option

```bash
# Overwrite existing files
jtc make:model User --force
jtc db:migrate
```

### Verbose Option

```bash
# Show detailed output
pytest -v

# Very verbose output
pytest -vv
```

### Environment Options

```bash
# Specify environment
jtc deploy --env production

# Use custom Redis
jtc queue work --redis redis://production:6380
```

---

## Configuration

### Environment Variables

The framework uses environment variables for configuration. Create a `.env` file in your project root:

```bash
# Database Configuration
DB_CONNECTION=sqlite
DB_DATABASE=workbench/database/app.db

# For MySQL/PostgreSQL
# DB_HOST=localhost
# DB_PORT=3306
# DB_DATABASE=fast_track
# DB_USERNAME=app_user
# DB_PASSWORD=secret

# Cache Configuration
CACHE_DRIVER=file
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
DEFAULT_LOCALE=en

# Queue Configuration
REDIS_URL=redis://localhost:6379
```

### Configuration Files

The framework reads configuration from Python files in the `config/` directory:

```
workbench/config/
├── app.py          # Application settings, providers list
├── database.py     # Database connections
├── cache.py        # Cache configuration
└── ...
```

Access configuration:

```python
from jtc.config import config

# Get database connection
db_default = config("database.default", "sqlite")
db_config = config(f"database.connections.{db_default}", {})

# Get cache driver
cache_driver = config("cache.driver", "file")
```

---

## Best Practices

### Command Usage

- **Use Help First**: Try `--help` before using new commands
- **Check Configuration**: Ensure environment variables are set
- **Test Locally**: Run commands in development before production
- **Read Documentation**: Refer to these docs for examples

### Development Workflow

1. **Generate Components**: Use `make:*` commands
2. **Write Tests**: Create tests alongside components
3. **Run Migrations**: Use `db:migrate` before seeding
4. **Clear Cache**: Use `cache:clear` when updating code
5. **Seed Data**: Use `db:seed` for test data
6. **Run Tests**: Verify everything works before committing

### Production Considerations

- **Backup First**: Always backup database before migrations
- **Test Staging**: Run migrations on staging first
- **Monitor**: Watch logs after deployment
- **Rollback Ready**: Have rollback plan ready
- **Health Checks**: Implement `/health` endpoint

---

## Troubleshooting

### Common Issues

#### Command Not Found

```bash
# Error: Command not found
# Solution: Check command syntax
jtc --help

# Verify command exists
jtc make:  # Press Tab to see available commands
```

#### Configuration Errors

```bash
# Error: Configuration not found
# Solution: Check .env file
cat .env

# Verify config file exists
ls workbench/config/

# Check for syntax errors
python -m py_compile workbench/config/*.py
```

#### Database Connection Issues

```bash
# Error: Could not connect to database
# Solution: Check database is running
# SQLite
ls -la workbench/database/app.db

# Redis
redis-cli ping

# MySQL/PostgreSQL
psql -h localhost -U app_user
```

---

## Comparison with Other Frameworks

### Laravel

| Laravel | Fast Track | Notes |
|---------|-------------|--------|
| `php artisan make:model` | `jtc make:model` | Similar functionality |
| `php artisan migrate` | `jtc db:migrate` | Uses Alembic vs Laravel migrations |
| `php artisan cache:clear` | `jtc cache:clear` | Same purpose |
| `php artisan queue:work` | `jtc queue work` | Both use Redis |
| `php artisan make:auth` | `jtc make auth` | Both scaffold auth system |
| `php artisan test` | `pytest` | Laravel uses PHPUnit, Fast Track uses pytest |

### Django

| Django | Fast Track | Notes |
|--------|-------------|--------|
| `python manage.py startapp` | `jtc make:controller` | Django app vs framework controller |
| `python manage.py migrate` | `jtc db:migrate` | Different ORM (Django ORM vs SQLAlchemy) |
| `python manage.py test` | `pytest` | Django uses test command, Fast Track uses pytest |

---

## Learning Resources

### Framework Documentation

- **[Main README](../README.md)** - Framework overview and features
- **[Architecture](../architecture/)** - Design decisions and patterns
- **[Guides](../guides/)** - Getting started guides
- **[Sprint History](../history/)** - Sprint summaries and implementation details

### External Resources

- **[Typer Documentation](https://typer.tiangolo.com/)** - CLI framework
- **[FastAPI Documentation](https://fastapi.tiangolo.com/)** - Web framework
- **[SQLAlchemy Documentation](https://docs.sqlalchemy.org/)** - ORM
- **[Alembic Documentation](https://alembic.sqlalchemy.org/)** - Migrations
- **[Pytest Documentation](https://docs.pytest.org/)** - Testing
- **[SAQ Documentation](https://saq.readthedocs.io/)** - Queue

---

## Contributing

If you find issues with the documentation or want to add new commands:

1. **Report Issues**: Open an issue on GitHub
2. **Submit PR**: Improve documentation with examples
3. **Add Commands**: Contribute new commands to the framework
4. **Update Examples**: Keep examples current with framework changes

---

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21
