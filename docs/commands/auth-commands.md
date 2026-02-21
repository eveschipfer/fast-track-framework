# Auth Commands

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21

This section documents authentication-related commands.

## Overview

The framework provides a powerful `make:auth` command that scaffolds a complete JWT-based authentication system in one command. This is a "macro" command that generates all necessary files for user authentication.

**Note**: The authentication command is part of the `make` command group. For the full documentation, see [Make Commands](make-commands.md#makeauth).

---

## make:auth

Generate a complete JWT-based authentication system.

### Syntax

```bash
jtc make auth [options]
```

### Options

- `-f, --force`: Overwrite existing files

### Description

This macro command generates all files needed for JWT authentication in a single operation, similar to Laravel's `php artisan make:auth`.

### What's Generated

The command creates 5 files:

1. **User Model** (`src/jtc/models/user.py`)
   - Email field (unique, indexed)
   - Password field
   - Timestamps and soft deletes

2. **UserRepository** (`src/jtc/repositories/user_repository.py`)
   - Extends BaseRepository
   - Type-hinted for User model
   - Ready for dependency injection

3. **LoginRequest** (`src/jtc/http/requests/auth/login_request.py`)
   - Validates email and password
   - Proper error messages
   - FormRequest validation pattern

4. **RegisterRequest** (`src/jtc/http/requests/auth/register_request.py`)
   - Validates name, email, password
   - Checks for unique email (requires session)
   - Password confirmation

5. **AuthController** (`src/jtc/http/controllers/auth_controller.py`)
   - `/register` endpoint (POST)
   - `/login` endpoint (POST)
   - `/me` endpoint (GET - authenticated)

### Examples

```bash
# Generate authentication scaffolding
jtc make auth
# Output:
# 🔐 Generating authentication system...
# 
# Creating User model...
#   ✓ User model created: src/jtc/models/user.py
# Creating UserRepository...
#   ✓ UserRepository created: src/jtc/repositories/user_repository.py
# Creating LoginRequest...
#   ✓ LoginRequest created: src/jtc/http/requests/auth/login_request.py
# Creating RegisterRequest...
#   ✓ RegisterRequest created: src/jtc/http/requests/auth/register_request.py
# Creating AuthController...
#   ✓ AuthController created: src/jtc/http/controllers/auth_controller.py
# 
# ============================================================
# 🎉 Authentication scaffolding complete!
# ✓ Created 5 files
# ============================================================
```

### Next Steps After Generation

#### 1. Create Database Migration

```bash
# Create migration for users table
alembic revision --autogenerate -m "create_users_table"
```

#### 2. Add Fields to Migration

Edit the generated migration file (`workbench/database/migrations/versions/*.py`):

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique index on email
    op.create_index('ix_users_email', 'users', ['email'])
```

#### 3. Run Migration

```bash
jtc db:migrate
```

#### 4. Register Routes

In your main application file (`workbench/main.py` or `src/app.py`):

```python
from jtc.http.controllers.auth_controller import router

# Register auth routes
app.include_router(router)
```

This will expose:
- `POST /register` - User registration
- `POST /login` - User login (returns JWT)
- `GET /me` - Get current authenticated user

#### 5. Set JWT Secret Key

```bash
# In .env file
export JWT_SECRET_KEY="your-secret-key-here-make-it-long-and-random"

# Or set in environment before running
JWT_SECRET_KEY="your-secret" jtc run
```

### API Endpoints

After setup, these endpoints are available:

#### POST /register

Register a new user account.

**Request Body:**
```json
{
  "name": "Alice Smith",
  "email": "alice@example.com",
  "password": "securepassword123",
  "password_confirmation": "securepassword123"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "name": "Alice Smith",
    "email": "alice@example.com"
  }
}
```

#### POST /login

Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "email": "alice@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### GET /me

Get current authenticated user's information.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200):**
```json
{
  "id": 1,
  "name": "Alice Smith",
  "email": "alice@example.com",
  "created_at": "2026-02-21T12:00:00Z",
  "updated_at": "2026-02-21T12:00:00Z"
}
```

### Using the JWT Token

```python
import httpx

# After login, you get an access_token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Use it in subsequent requests
headers = {
    "Authorization": f"Bearer {token}"
}

response = httpx.get("http://localhost:8000/me", headers=headers)
user_data = response.json()
```

### Customization

You can customize the generated files:

#### User Model

```python
# src/jtc/models/user.py
class User(Base, TimestampMixin, SoftDeletesMixin):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    
    # Add custom fields
    is_active: Mapped[bool] = mapped_column(default=True)
    role: Mapped[str] = mapped_column(String(50))
```

#### Auth Controller

```python
# src/jtc/http/controllers/auth_controller.py

# Customize password hashing
# Add email verification
# Add rate limiting
# Add password reset functionality
```

### Security Considerations

- **Password Hashing**: The generated code uses `passlib.bcrypt` for secure password hashing
- **JWT Tokens**: Short-lived tokens (recommended: 15-60 minutes)
- **HTTPS Required**: Never send credentials over HTTP
- **Password Strength**: Enforce strong passwords in RegisterRequest validation
- **Rate Limiting**: Add rate limiting to login endpoint

### Troubleshooting

#### Email Already Exists Error

```bash
# Error: "Email already registered"
# Solution: This is expected - RegisterRequest validates uniqueness
# Use a different email or delete existing user
```

#### Invalid Credentials

```bash
# Error: "Invalid credentials"
# Solution: Check email and password
# Verify user exists in database
# Check password hash comparison logic
```

#### JWT Token Not Working

```bash
# Error: "Could not validate credentials" (401)
# Solutions:
# 1. Check JWT_SECRET_KEY is set
echo $JWT_SECRET_KEY

# 2. Verify token format (should be "Bearer <token>")
# 3. Check token expiration
# 4. Ensure headers are sent correctly
```

### Educational Note

This command is inspired by Laravel's authentication scaffolding:

**Laravel**:
```bash
php artisan make:auth
# Generates: views, controllers, routes, migrations
```

**Fast Track**:
```bash
jtc make auth
# Generates: models, repositories, requests, controller
```

Both provide a complete authentication system in one command, but Fast Track focuses on API-first approach (no views, returns JSON).

### Related Commands

- [Make Commands](make-commands.md#makeauth) - Full `make:auth` documentation
- [Database Commands](db-commands.md) - Run migrations for user table
- [Test Commands](test-commands.md) - Test authentication endpoints

---

## Authentication Workflow Example

### Complete User Registration Flow

```bash
# 1. Generate authentication system
jtc make auth

# 2. Create migration
alembic revision --autogenerate -m "create_users_table"

# 3. Edit migration (add email index)

# 4. Run migration
jtc db:migrate

# 5. Register routes in app
# Edit workbench/main.py to include auth_controller

# 6. Set JWT secret
export JWT_SECRET_KEY="super-secret-key-123"

# 7. Start application
jtc run

# 8. Test registration
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "password123",
    "password_confirmation": "password123"
  }'

# 9. Test login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# 10. Test /me endpoint
curl http://localhost:8000/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Best Practices

### Password Security

- Always hash passwords (done by default in generated code)
- Use bcrypt (used by default)
- Enforce strong password requirements
- Never store plain-text passwords

### Token Management

- Use short-lived access tokens (15-60 minutes)
- Implement refresh tokens for long sessions
- Store tokens securely (httpOnly cookies recommended)
- Include token expiration validation

### User Management

- Soft delete users instead of hard delete
- Implement email verification for registration
- Add password reset functionality
- Store user activity logs

---

## Comparison with Laravel

| Laravel | Fast Track | Purpose |
|---------|-------------|----------|
| `php artisan make:auth` | `jtc make auth` | Generate complete auth system |
| `php artisan migrate` | `jtc db:migrate` | Run database migrations |
| Laravel Views + Controllers | Controllers + API JSON | API-first vs traditional web |

---

## Next Steps

- [Make Commands](make-commands.md) - Generate other components
- [Database Commands](db-commands.md) - Database migrations and seeding
- [Cache Commands](cache-commands.md) - Cache management
- [Queue Commands](queue-commands.md) - Background job management
- [Test Commands](test-commands.md) - Testing utilities
- [Deploy Commands](deploy-commands.md) - Deployment automation

---

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21
