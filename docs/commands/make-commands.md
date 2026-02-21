# Make Commands

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21

This section documents all `make:*` commands used to generate framework components. These commands automate the creation of models, repositories, controllers, and other components with proper structure and imports.

## Overview

Make commands follow the pattern: `jtc make:<command>`

These commands enforce architectural standards and reduce boilerplate, making the framework feel more like Laravel or Django.

---

## make:model

Generate a SQLAlchemy model with TimestampMixin and SoftDeletesMixin.

### Syntax

```bash
jtc make:model <name> [options]
```

### Arguments

- `name`: Name of the model (e.g., "User", "Post")

### Options

- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create a User model
jtc make:model User
# Output: ✓ Model created: workbench/app/models/user.py

# Create a Post model with force flag
jtc make:model Post --force
# Output: ✓ Model created: workbench/app/models/post.py (overwritten)
```

### Generated Code

The command generates a SQLAlchemy 2.0 model with:

- `TimestampMixin`: Adds `created_at` and `updated_at` fields
- `SoftDeletesMixin`: Adds `deleted_at` field for soft deletes
- Primary key `id`
- Name field placeholder
- Placeholder comments for adding more fields and relationships

### Template Reference

See `framework/jtc/cli/templates.py::get_model_template()` for the code template.

---

## make:repository

Generate a repository class inheriting from BaseRepository.

### Syntax

```bash
jtc make:repository <name> [options]
```

### Arguments

- `name`: Name of the repository (e.g., "UserRepository", "PostRepository")

### Options

- `-m, --model`: Model name (auto-detected from repository name if not provided)
- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create UserRepository (auto-detects User model)
jtc make:repository UserRepository
# Output: ✓ Repository created: workbench/app/repositories/user_repository.py

# Create PostRepo with explicit model
jtc make:repository PostRepo --model Post
# Output: ✓ Repository created: workbench/app/repositories/post_repo.py
```

### Model Auto-Detection

The command automatically detects the model name by removing common suffixes:
- `UserRepository` → `User`
- `PostRepo` → `Post`

### Generated Code

Generates a repository class extending `BaseRepository` with type hints for CRUD operations.

### Template Reference

See `framework/jtc/cli/templates.py::get_repository_template()` for the code template.

---

## make:request

Generate a FormRequest with validation methods.

### Syntax

```bash
jtc make:request <name> [options]
```

### Arguments

- `name`: Name of the request (e.g., "StoreUserRequest", "UpdatePostRequest")

### Options

- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create StoreUserRequest
jtc make:request StoreUserRequest
# Output: ✓ Request created: src/jtc/requests/store_user_request.py

# Create UpdatePostRequest with force
jtc make:request UpdatePostRequest --force
# Output: ✓ Request created: src/jtc/requests/update_post_request.py (overwritten)
```

### Important Note

⚠️ **Remember**: The `rules()` method is for validation only! Do not add side effects (database queries, external API calls) in the validation logic. The command generates a governance warning about this.

### Generated Code

Generates a `FormRequest` class with:
- `authorize()` method for permission checks
- `rules()` method for validation rules
- Proper type hints and docstrings

### Template Reference

See `framework/jtc/cli/templates.py::get_request_template()` for the code template.

---

## make:resource

Generate an API Resource class for transforming models to JSON.

### Syntax

```bash
jtc make:resource <name> [options]
```

### Arguments

- `name`: Name of the resource (e.g., "UserResource", "PostResource")

### Options

- `-m, --model`: Model name (auto-detected from resource name if not specified)
- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create UserResource (auto-detects User model)
jtc make:resource UserResource
# Output: ✓ Resource created: src/jtc/resources/user_resource.py

# Create PostResource with explicit model
jtc make:resource PostResource --model Post
# Output: ✓ Resource created: src/jtc/resources/post_resource.py
```

### Usage

```python
from app.resources.user_resource import UserResource
from app.models import User

# Transform User model to JSON
user = await repo.find(1)
json_data = UserResource.make(user).resolve()
```

### Purpose

Resources decouple your database schema from API response format, allowing you to:
- Filter sensitive fields
- Transform data structures
- Include related data
- Format dates and numbers

### Template Reference

See `framework/jtc/cli/templates.py::get_resource_template()` for the code template.

---

## make:factory

Generate a factory class for test data generation.

### Syntax

```bash
jtc make:factory <name> [options]
```

### Arguments

- `name`: Name of the factory (e.g., "UserFactory", "PostFactory")

### Options

- `-m, --model`: Model name (auto-detected from factory name if not provided)
- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create UserFactory (auto-detects User model)
jtc make:factory UserFactory
# Output: ✓ Factory created: tests/factories/user_factory.py

# Create PostFactory with explicit model
jtc make:factory PostFactory --model Post
# Output: ✓ Factory created: tests/factories/post_factory.py
```

### Generated Code

Generates a factory class that:
- Uses the Faker library for fake data
- Defines default values for each field
- Can create single instances or bulk data

### Template Reference

See `framework/jtc/cli/templates.py::get_factory_template()` for the code template.

---

## make:seeder

Generate a seeder class for database seeding.

### Syntax

```bash
jtc make:seeder <name> [options]
```

### Arguments

- `name`: Name of the seeder (e.g., "UserSeeder", "DatabaseSeeder")

### Options

- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create UserSeeder
jtc make:seeder UserSeeder
# Output: ✓ Seeder created: tests/seeders/user_seeder.py

# Create DatabaseSeeder with force
jtc make:seeder DatabaseSeeder --force
# Output: ✓ Seeder created: tests/seeders/database_seeder.py (overwritten)
```

### Generated Code

Generates a seeder class with a `run()` method where you can populate the database with initial data.

### Template Reference

See `framework/jtc/cli/templates.py::get_seeder_template()` for the code template.

---

## make:controller

Generate a Controller class.

### Syntax

```bash
jtc make:controller <name> [options]
```

### Arguments

- `name`: Name of the controller (e.g., "UserController", "PostController")

### Options

- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create UserController
jtc make:controller UserController
# Output: ✓ Controller created: workbench/http/controllers/user_controller.py

# Create Post (auto-adds "Controller" suffix)
jtc make:controller Post
# Output: ✓ Controller created: workbench/http/controllers/post_controller.py
```

### Generated Code

Generates a controller class with:
- FastAPI router
- Placeholder methods (index, show, store, update, destroy)
- Proper resource naming (pluralized)

### Template Reference

See `framework/jtc/cli/templates.py::get_controller_template()` for the code template.

---

## make:provider

Generate a Service Provider.

### Syntax

```bash
jtc make:provider <name> [options]
```

### Arguments

- `name`: Name of the provider (e.g., "PaymentServiceProvider", "Analytics")

### Options

- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create PaymentServiceProvider
jtc make:provider PaymentServiceProvider
# Output: ✓ Provider created: workbench/app/providers/payment_service_provider.py

# Create Analytics (auto-adds "ServiceProvider" suffix)
jtc make:provider Analytics --force
# Output: ✓ Provider created: workbench/app/providers/analytics_service_provider.py (overwritten)
```

### Purpose

Service providers are the central place to register bindings in the IoC Container. Use them to:
- Register services
- Register event listeners
- Register middleware
- Configure framework features

### Generated Code

Generates a provider class with:
- `register()` method for service bindings
- `boot()` method for logic that needs all services loaded

### Template Reference

See `framework/jtc/cli/templates.py::get_provider_template()` for the code template.

---

## make:event

Generate an Event class (Data Transfer Object).

### Syntax

```bash
jtc make:event <name> [options]
```

### Arguments

- `name`: Name of the event (e.g., "UserRegistered", "OrderPlaced")

### Options

- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create UserRegistered event
jtc make event UserRegistered
# Output: ✓ Event created: src/jtc/events/user_registered.py

# Create OrderPlaced event with force
jtc make event OrderPlaced --force
# Output: ✓ Event created: src/jtc/events/order_placed.py (overwritten)
```

### Purpose

Events are data containers that represent something that happened in the system. They are dispatched through the Event Bus and handled by Listeners.

### Generated Code

Generates an event class with attributes for the event data.

### Template Reference

See `framework/jtc/cli/templates.py::get_event_template()` for the code template.

---

## make:listener

Generate a Listener class for handling events.

### Syntax

```bash
jtc make:listener <name> [options]
```

### Arguments

- `name`: Name of the listener (e.g., "SendWelcomeEmail", "LogUserActivity")

### Options

- `-e, --event`: Event name this listener handles (e.g., "UserRegistered")
- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create SendWelcomeEmail listener
jtc make listener SendWelcomeEmail --event UserRegistered
# Output: ✓ Listener created: src/jtc/listeners/send_welcome_email.py

# Create LogUserActivity listener
jtc make listener LogUserActivity -e UserRegistered
# Output: ✓ Listener created: src/jtc/listeners/log_user_activity.py
```

### Important Note

⚠️ **Remember to register this listener** for the event you specified in your event configuration!

### Generated Code

Generates a listener class that:
- Handles a specific event
- Supports dependency injection through the IoC Container
- Has a `handle()` method for event processing

### Template Reference

See `framework/jtc/cli/templates.py::get_listener_template()` for the code template.

---

## make:job

Generate a Job class for background processing.

### Syntax

```bash
jtc make:job <name> [options]
```

### Arguments

- `name`: Name of the job (e.g., "SendWelcomeEmail", "ProcessPayment")

### Options

- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create SendWelcomeEmail job
jtc make job SendWelcomeEmail
# Output: ✓ Job created: src/jtc/jobs/send_welcome_email.py

# Create ProcessPayment job with force
jtc make job ProcessPayment --force
# Output: ✓ Job created: src/jtc/jobs/process_payment.py (overwritten)
```

### Usage

```python
from app.jobs.send_welcome_email import SendWelcomeEmail

# Dispatch to queue
await SendWelcomeEmail(user).dispatch()
```

### Purpose

Jobs are class-based units of work that can be dispatched to a queue and executed asynchronously by workers. They support dependency injection through the IoC Container.

### Generated Code

Generates a job class with:
- `handle()` method for job logic
- Support for async operations
- Dependency injection support

### Template Reference

See `framework/jtc/cli/templates.py::get_job_template()` for the code template.

---

## make:middleware

Generate a Middleware class for HTTP request processing.

### Syntax

```bash
jtc make:middleware <name> [options]
```

### Arguments

- `name`: Name of the middleware (e.g., "LogRequests", "RateLimiter")

### Options

- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create LogRequests middleware
jtc make middleware LogRequests
# Output: ✓ Middleware created: src/jtc/http/middleware/log_requests.py

# Create RateLimiter middleware with force
jtc make middleware RateLimiter --force
# Output: ✓ Middleware created: src/jtc/http/middleware/rate_limiter.py (overwritten)
```

### Registration

```python
# Register with FastAPI
app.add_middleware(LogRequests)

# Or use BaseHTTPMiddleware for async dispatch method
```

### Purpose

Middleware allows you to filter HTTP requests entering your application. This is useful for:
- Logging
- Authentication
- CORS
- Rate limiting
- Request/response modification

### Onion Pattern

Middleware follows the "onion" pattern:
- **Request flows**: `CORS → Auth → Logging → Route Handler`
- **Response flows**: `CORS ← Auth ← Logging ← Route Handler`

### Template Reference

See `framework/jtc/cli/templates.py::get_middleware_template()` for the code template.

---

## make:mail

Generate a Mailable class for sending emails.

### Syntax

```bash
jtc make:mail <name> [options]
```

### Arguments

- `name`: Name of the mailable (e.g., "WelcomeEmail", "InvoiceEmail")

### Options

- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create WelcomeEmail mailable
jtc make mail WelcomeEmail
# Output: ✓ Mailable created: src/mail/welcome_email.py

# Create InvoiceEmail mailable with force
jtc make mail InvoiceEmail --force
# Output: ✓ Mailable created: src/mail/invoice_email.py (overwritten)
```

### Usage Examples

```python
from mail.welcome_email import WelcomeEmail
from jtc.mail import Mail

# Send immediately
await Mail.send(WelcomeEmail(user))

# Fluent API
await Mail.to(user.email).send(WelcomeEmail(user))

# Queue for background
await Mail.to(user.email).queue(WelcomeEmail(user))
```

### Design Patterns

Mailables combine several design patterns:
- **Builder Pattern**: Fluent API for email composition
- **Template Method**: Abstract `build()` method for subclasses
- **Strategy Pattern**: Different ways to set content (view/text/html)

### Template Reference

See `framework/jtc/cli/templates.py::get_mailable_template()` for the code template.

---

## make:auth

Generate a complete authentication system (macro command).

### Syntax

```bash
jtc make auth [options]
```

### Options

- `-f, --force`: Overwrite existing files

### Examples

```bash
# Generate authentication scaffolding
jtc make auth
# Output:
# 🔐 Generating authentication system...
# ✓ User model created: src/jtc/models/user.py
# ✓ UserRepository created: src/jtc/repositories/user_repository.py
# ✓ LoginRequest created: src/jtc/http/requests/auth/login_request.py
# ✓ RegisterRequest created: src/jtc/http/requests/auth/register_request.py
# ✓ AuthController created: src/jtc/http/controllers/auth_controller.py
# 🎉 Authentication scaffolding complete!
```

### What's Generated

This "macro" command creates all files needed for JWT authentication:

1. **User model**: With email and password fields
2. **UserRepository**: Extending BaseRepository
3. **LoginRequest**: FormRequest with validation
4. **RegisterRequest**: FormRequest with validation
5. **AuthController**: With `/register`, `/login`, `/me` endpoints

### Next Steps

```bash
# 1. Create migration
jtc make migration create_users_table

# 2. Run migration
jtc db migrate

# 3. Set JWT secret
export JWT_SECRET_KEY='your-secret'

# 4. Register routes
app.include_router(auth_controller.router)
```

### Comparison

Similar to Laravel's `php artisan make:auth` - generates a complete authentication scaffolding in one command.

---

## make:cmd

Generate a custom CLI command.

### Syntax

```bash
jtc make:cmd <name> [options]
```

### Arguments

- `name`: Name of the command (e.g., "deploy", "backup")

### Options

- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create deploy command
jtc make:command deploy
# Output: ✓ Command created: src/jtc/cli/commands/deploy.py

# Create backup command with force
jtc make:command backup --force
# Output: ✓ Command created: src/jtc/cli/commands/backup.py (overwritten)
```

### Registration Required

⚠️ **Manual Registration Required**: Unlike Laravel (which has auto-discovery), you need to manually register the command in `src/jtc/cli/main.py`:

```python
from jtc.cli.commands.deploy import app as deploy_app
app.add_typer(deploy_app, name='deploy')
```

Then run: `jtc deploy --help`

### Use Cases

Custom commands for:
- Deployment scripts
- Database backups
- Data migrations
- Custom tooling

### Template Reference

See `framework/jtc/cli/templates.py::get_command_template()` for the code template.

---

## make:lang

Generate a translation file for a new locale.

### Syntax

```bash
jtc make:lang <locale> [options]
```

### Arguments

- `locale`: Locale code (e.g., "pt_BR", "es", "fr", "de")

### Options

- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create Brazilian Portuguese translation
jtc make:lang pt_BR
# Output: ✓ Translation file created: src/resources/lang/pt_BR.json

# Create Spanish translation with force
jtc make:lang es --force
# Output: ✓ Translation file created: src/resources/lang/es.json (overwritten)
```

### File Format

Translation files use JSON format with dot notation keys:

```json
{
  "auth.failed": "Credenciais inválidas",
  "validation.required": "O campo :field é obrigatório"
}
```

### Usage

```python
from jtc.i18n import trans, set_locale

# Set locale
set_locale('pt_BR')

# Use translation
message = trans('auth.failed')
```

### Set Default Locale

```bash
export DEFAULT_LOCALE='pt_BR'
```

### Template Reference

See `framework/jtc/cli/templates.py::get_lang_template()` for the code template.

---

## make:rule

Generate a new Validation Rule class (Pydantic AfterValidator).

### Syntax

```bash
jtc make:rule <name> [options]
```

### Arguments

- `name`: Name of the validation rule (e.g., "CpfIsValid", "MinAge")

### Options

- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create CpfIsValid rule
jtc make:rule CpfIsValid
# Output: ✓ Validation Rule created: src/rules/cpf_is_valid.py

# Create MinAge rule with force
jtc make:rule MinAge --force
# Output: ✓ Validation Rule created: src/rules/min_age.py (overwritten)
```

### Usage Example

```python
from typing import Annotated
from pydantic import AfterValidator, BaseModel
from rules.cpf_is_valid import CpfIsValid

class MyModel(BaseModel):
    cpf: Annotated[str, AfterValidator(CpfIsValid())]
```

### Pydantic v2 Pattern

The validator follows Pydantic v2's pattern:
1. The validator is a callable class (implements `__call__`)
2. It returns the value if valid (can transform)
3. It raises `ValueError` if validation fails
4. It uses `ftf.i18n` for multi-language error messages

### Comparison with Laravel

**Laravel**:
```php
php artisan make:rule Uppercase
// Implements Rule interface with passes() method
```

**Fast Track**:
```bash
jtc make:rule CpfIsValid
// Callable class used with Pydantic AfterValidator
```

### Learn More

https://docs.pydantic.dev/latest/concepts/validators/#annotated-validators

### Template Reference

See `framework/jtc/cli/templates.py::get_rule_template()` for the code template.

---

## make:k6

Generate a k6 load testing script.

### Syntax

```bash
jtc make:k6 <name> [options]
```

### Arguments

- `name`: Name of the load test (e.g., "user_login", "api_stress")

### Options

- `-v, --vus`: Number of virtual users (default: 10)
- `-d, --duration`: Duration of load test (default: "30s")
- `-f, --force`: Overwrite file if it already exists

### Examples

```bash
# Create user_login load test (defaults: 10 VUs, 30s)
jtc make:k6 user_login
# Output: ✓ Load test created: workbench/tests/load/user_login.js

# Create api_stress test with custom settings
jtc make:k6 api_stress --vus 50 --duration 2m
# Output: ✓ Load test created: workbench/tests/load/api_stress.js
```

### Running Load Tests

```bash
# Run with defaults from file
k6 run workbench/tests/load/user_login.js

# Override VUs and duration
k6 run --vus 100 --duration 5m workbench/tests/load/api_stress.js

# Use custom base URL
BASE_URL=https://api.example.com k6 run workbench/tests/load/user_login.js
```

### Generated Features

The generated k6 script includes:
- Configurable VUs and duration
- Ramp up/down stages
- Performance thresholds (p95 < 500ms, errors < 1%)
- Environment variable support for `BASE_URL`

### Important

⚠️ **Remember**: Update the endpoint URL in the generated script to match your actual API!

### Template Reference

See `framework/jtc/cli/templates.py::get_k6_template()` for the code template.

---

## Common Options

Most make commands support these common options:

- `-f, --force`: Overwrite existing files without prompting

### Common Workflow

1. Generate a component: `jtc make:model User`
2. Add your fields and logic
3. Test the component
4. Commit to version control

### Best Practices

- Use descriptive names: `UserRepository`, `StoreUserRequest`, `WelcomeEmail`
- Follow naming conventions (PascalCase for classes)
- Review generated code and customize as needed
- Keep generated code under version control

## Next Steps

- [Database Commands](db-commands.md) - Migrate, rollback, and seed databases
- [Cache Commands](cache-commands.md) - Clear, forget, and test cache
- [Auth Commands](auth-commands.md) - Authentication-related commands
- [Queue Commands](queue-commands.md) - Background job management
- [Test Commands](test-commands.md) - Testing utilities
- [Deploy Commands](deploy-commands.md) - Deployment automation

---

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21
