# Sprint 3.4: HTTP Kernel & Exception Handler

**Status**: ✅ Complete
**Date**: 2026-01-31
**Tests**: 25 new tests (100% passing)
**Coverage**: 93.62% (exceptions.py), 85.29% (middleware/__init__.py)

## Overview

Sprint 3.4 implements the **HTTP Kernel layer** for centralized exception handling and middleware configuration, inspired by Laravel's `app/Exceptions/Handler.php` and `app/Http/Kernel.php`. This sprint transforms our "raw" HTTP layer into a production-ready system with standardized error responses and essential middleware (CORS, GZip, TrustedHost).

### Key Achievement

**Before Sprint 3.4:**
- Exceptions crashed the app or returned generic 500 errors
- No standardized error response format
- Manual middleware configuration
- Each exception handler registered separately

**After Sprint 3.4:**
- Global exception handling with automatic JSON responses
- Standardized error format (404, 401, 403, 422)
- One-line middleware configuration
- Production-ready CORS, GZip, and security headers

## Motivation

The "Orça Já" frontend needs a robust backend that:

1. **Returns consistent JSON errors** (never HTML error pages)
2. **Supports CORS** for cross-origin API calls
3. **Provides security headers** (TrustedHost)
4. **Compresses responses** (GZip) for better performance

Without Sprint 3.4, every route would need manual error handling, and middleware would require complex Starlette configuration. This sprint provides a **Laravel-like developer experience** while maintaining FastAPI's async performance.

## What We Built

### 1. Exception System (`src/ftf/http/exceptions.py`)

**Architecture:**

```python
AppException (base)
├── AuthenticationError (401)
├── AuthorizationError (403)
└── ValidationException (422)

ExceptionHandler (registry)
├── handle_app_exception
├── handle_authentication_error
├── handle_authorization_error
├── handle_validation_exception
├── handle_record_not_found (fast_query)
└── handle_validation_error (FormRequest)
```

**Key Features:**

1. **AppException Base Class**
   - All framework exceptions inherit from this
   - Includes HTTP status code and headers
   - Automatic conversion to JSON responses

2. **Specific Exception Types**
   - `AuthenticationError`: 401 with WWW-Authenticate header
   - `AuthorizationError`: 403 Forbidden
   - `ValidationException`: 422 with validation errors

3. **ExceptionHandler Registry**
   - `register_all(app)`: Auto-register all handlers
   - `register(app, exc, handler)`: Custom exception handlers
   - Integrated into `FastTrackFramework.__init__`

4. **Clean Separation**
   - ORM layer (fast_query) remains HTTP-agnostic
   - HTTP layer converts exceptions to responses
   - Follows Single Responsibility Principle

**Example Usage:**

```python
# Raise exceptions anywhere in your code
raise AuthenticationError("Invalid token")
# Auto-converts to: {"detail": "Invalid token"} with status 401

raise AuthorizationError("Admins only")
# Auto-converts to: {"detail": "Admins only"} with status 403

raise RecordNotFound("User", 123)
# Auto-converts to: {"detail": "User not found: 123"} with status 404
```

### 2. Middleware System (`src/ftf/http/middleware/__init__.py`)

**Architecture:**

```python
MiddlewareManager
├── configure_cors()
├── configure_gzip()
├── configure_trusted_host()
└── configure_all()  # Setup all at once
```

**Components:**

1. **CORS Middleware**
   - Reads from `CORS_ORIGINS` environment variable
   - Defaults to `["*"]` for development
   - Production: specify exact allowed origins
   - Auto-configures: credentials, methods, headers

2. **GZip Compression**
   - Compresses responses > 1000 bytes
   - Compression level 5 (balanced)
   - ~70-90% reduction for JSON responses
   - Transparent to client (auto-decompression)

3. **TrustedHost Security**
   - Validates Host header against whitelist
   - Prevents Host header attacks
   - Reads from `ALLOWED_HOSTS` env var
   - Opt-in (disabled by default to avoid breaking dev)

4. **MiddlewareManager**
   - One-line configuration: `MiddlewareManager.configure_all(app)`
   - Enable/disable individual middleware
   - Laravel-like API

**Example Usage:**

```python
from ftf.http import FastTrackFramework
from ftf.http.middleware import MiddlewareManager

app = FastTrackFramework()

# Option 1: Configure all middleware at once
MiddlewareManager.configure_all(app)

# Option 2: Configure individually
from ftf.http.middleware import configure_cors, configure_gzip
configure_cors(app)  # Reads from CORS_ORIGINS env var
configure_gzip(app)  # Compression level 5, min size 1000 bytes

# Option 3: Custom configuration
configure_cors(
    app,
    allow_origins=["https://myapp.com"],
    allow_credentials=True
)
```

**Environment Variables:**

```bash
# CORS Configuration
CORS_ORIGINS="http://localhost:3000,https://myapp.com"

# TrustedHost Configuration
ALLOWED_HOSTS="localhost,myapp.com,*.myapp.com"
```

### 3. CLI Command (`ftf make:middleware`)

**Feature:**

Generates middleware class skeleton with dispatch() method.

**Usage:**

```bash
$ ftf make:middleware LogRequests
✓ Middleware created: src/ftf/http/middleware/log_requests.py
💡 Register with: app.add_middleware(LogRequests)
```

**Generated Template:**

```python
from typing import Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class LogRequests(BaseHTTPMiddleware):
    """LogRequests middleware for HTTP request/response processing."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # BEFORE REQUEST
        # Add logging, auth, rate limiting, etc.

        response: Response = await call_next(request)

        # AFTER REQUEST
        # Add headers, log response, etc.

        return response
```

### 4. Integration with FastTrackFramework

**Auto-Registration:**

The `ExceptionHandler` is automatically registered when creating a `FastTrackFramework` instance:

```python
class FastTrackFramework(FastAPI):
    def __init__(self, *args, **kwargs):
        # ... container setup ...

        super().__init__(*args, **kwargs)

        # Auto-register exception handlers (Sprint 3.4)
        from ftf.http.exceptions import ExceptionHandler
        ExceptionHandler.register_all(self)
```

**Zero Configuration Required:**

```python
# Just create the app - exception handling is automatic!
app = FastTrackFramework()

@app.get("/users/{user_id}")
async def get_user(user_id: int, repo: UserRepository = Inject()):
    return await repo.find_or_fail(user_id)  # Raises RecordNotFound
    # Auto-converts to: {"detail": "User not found: 123"} with 404
```

## Implementation Details

### Exception Handler Priority

FastAPI checks handlers in **reverse registration order**. We register:

1. `RecordNotFound` (framework-agnostic, fast_query)
2. `ValidationError` (FormRequest validation)
3. `ValidationException` (422 structured errors)
4. `AppException` (catches all subclasses)

This ensures **most specific handlers** are checked first.

### Middleware Ordering

Middleware runs in **onion pattern**:

```
Request  → CORS → GZip → TrustedHost → Route Handler
Response ← CORS ← GZip ← TrustedHost ← Route Handler
```

**Best Practice:**

1. **CORS first**: Add headers before other middleware
2. **GZip last**: Compress after all processing
3. **TrustedHost early**: Security check before processing

### CORS Security Warning

**⚠️ NEVER in production:**

```python
configure_cors(
    app,
    allow_origins=["*"],
    allow_credentials=True  # ❌ Security vulnerability!
)
```

**✅ Production setup:**

```python
configure_cors(
    app,
    allow_origins=["https://myapp.com", "https://www.myapp.com"],
    allow_credentials=True
)
```

## Test Coverage

**File**: `tests/unit/test_http_kernel.py`
**Total Tests**: 25 (100% passing)
**Coverage**:
- `exceptions.py`: 93.62% (47 statements, 3 missed)
- `middleware/__init__.py`: 85.29% (34 statements, 5 missed)

### Test Categories

**Exception Tests (10 tests):**
- AppException defaults and custom status codes
- AuthenticationError (401 with WWW-Authenticate)
- AuthorizationError (403)
- ValidationException (422 with errors list)

**Exception Handler Tests (6 tests):**
- AuthenticationError → 401 JSON response
- AuthorizationError → 403 JSON response
- ValidationException → 422 with errors
- RecordNotFound → 404
- ValidationError → 422
- Auto-registration on app init

**Middleware Tests (7 tests):**
- CORS default settings
- CORS custom origins
- CORS from environment variable
- GZip compression applied
- TrustedHost validation
- MiddlewareManager configure_all()
- MiddlewareManager enable flags

**Integration Tests (2 tests):**
- Complete error handling flow (401, 403, 404)
- Middleware + exceptions working together

### Sample Test

```python
@pytest.mark.asyncio
async def test_exception_handler_catches_authentication_error() -> None:
    """Test that AuthenticationError is converted to 401 JSON response."""
    app = FastTrackFramework()

    @app.get("/test")
    async def test_route() -> None:
        raise AuthenticationError("Invalid token")

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}
    assert response.headers.get("WWW-Authenticate") == "Bearer"
```

## Comparison with Laravel

### Exception Handling

**Laravel (`app/Exceptions/Handler.php`):**

```php
class Handler extends ExceptionHandler {
    public function register() {
        $this->renderable(function (NotFoundHttpException $e) {
            return response()->json(['message' => 'Not found'], 404);
        });

        $this->renderable(function (AuthenticationException $e) {
            return response()->json(['message' => $e->getMessage()], 401);
        });
    }
}
```

**Fast Track (`src/ftf/http/exceptions.py`):**

```python
class ExceptionHandler:
    @staticmethod
    def register_all(app: FastAPI) -> None:
        app.add_exception_handler(RecordNotFound, handle_record_not_found)
        app.add_exception_handler(AuthenticationError, handle_app_exception)
        # Auto-registers all handlers
```

**Key Differences:**

| Aspect | Laravel | Fast Track |
|--------|---------|------------|
| **Registration** | Manual in Handler::register() | Auto in FastTrackFramework.__init__ |
| **Handler Definition** | Closures in register() | Dedicated async functions |
| **Type Safety** | PHP type hints | Full MyPy strict mode |
| **Async** | No (sync by default) | Yes (async-first) |

### Middleware Configuration

**Laravel (`app/Http/Kernel.php`):**

```php
class Kernel extends HttpKernel {
    protected $middleware = [
        \App\Http\Middleware\TrustProxies::class,
        \Illuminate\Http\Middleware\HandleCors::class,
    ];
}
```

**Fast Track (`app.py`):**

```python
from ftf.http.middleware import MiddlewareManager

app = FastTrackFramework()
MiddlewareManager.configure_all(app)
```

**Key Differences:**

| Aspect | Laravel | Fast Track |
|--------|---------|------------|
| **Configuration** | Class array in Kernel.php | Function calls with env vars |
| **CORS** | config/cors.php | configure_cors() or CORS_ORIGINS |
| **GZip** | Nginx/Apache | Built-in GZipMiddleware |
| **TrustedHost** | Manual (via package) | Built-in configure_trusted_host() |

## Educational Value

### What We Learned

1. **Exception Handler Pattern**
   - Centralized error handling
   - Type-specific handlers
   - Automatic registration

2. **Middleware Onion Pattern**
   - Request flows through layers
   - Response flows back through layers
   - Order matters for security

3. **Environment-Based Configuration**
   - Development: permissive (allow all CORS)
   - Production: strict (specific origins)
   - Never hardcode config

4. **CORS Security**
   - Preflight requests (OPTIONS)
   - Wildcard + credentials = vulnerability
   - Access-Control-Allow-Origin header

5. **Response Compression**
   - GZip transparent to client
   - JSON compresses 70-90%
   - Trade-off: CPU vs bandwidth

### Common Patterns

**Pattern 1: Custom Exception**

```python
from ftf.http import AppException

class RateLimitExceeded(AppException):
    def __init__(self, retry_after: int):
        super().__init__(
            f"Too many requests. Retry after {retry_after} seconds.",
            status_code=429,
            headers={"Retry-After": str(retry_after)}
        )

# Usage
raise RateLimitExceeded(retry_after=60)
# Returns: 429 with Retry-After header
```

**Pattern 2: Custom Middleware**

```python
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Check rate limit
        if exceeded_rate_limit(request.client.host):
            raise RateLimitExceeded(retry_after=60)

        response = await call_next(request)
        return response

# Register
app.add_middleware(RateLimitMiddleware)
```

**Pattern 3: Production Setup**

```python
import os
from ftf.http import FastTrackFramework
from ftf.http.middleware import configure_cors, configure_gzip, configure_trusted_host

app = FastTrackFramework()

# CORS: strict in production
if os.getenv("ENVIRONMENT") == "production":
    configure_cors(
        app,
        allow_origins=["https://myapp.com"],
        allow_credentials=True
    )
else:
    configure_cors(app)  # Allow all for development

# Always enable compression
configure_gzip(app)

# TrustedHost in production only
if os.getenv("ENVIRONMENT") == "production":
    configure_trusted_host(
        app,
        allowed_hosts=["myapp.com", "*.myapp.com"]
    )
```

## Files Created/Modified

### New Files

1. **`src/ftf/http/exceptions.py` (497 lines)**
   - AppException base class
   - Specific exception types (Authentication, Authorization, Validation)
   - Exception handlers (async functions)
   - ExceptionHandler registry

2. **`src/ftf/http/middleware/__init__.py` (374 lines)**
   - configure_cors() with env var support
   - configure_gzip() with compression levels
   - configure_trusted_host() for security
   - MiddlewareManager for one-line setup

3. **`tests/unit/test_http_kernel.py` (341 lines)**
   - 25 tests for exceptions and middleware
   - 100% passing, 93%+ coverage
   - Integration tests for complete flows

### Modified Files

1. **`src/ftf/http/__init__.py`**
   - Exported exception classes
   - Exported middleware functions
   - Updated docstring

2. **`src/ftf/http/app.py`**
   - Removed manual RecordNotFound handler
   - Added ExceptionHandler.register_all() in __init__
   - Cleaner, more maintainable code

3. **`src/ftf/cli/commands/make.py`**
   - Added make:middleware command (58 lines)
   - Creates middleware class skeleton
   - Auto-creates middleware/ directory

4. **`src/ftf/cli/templates.py`**
   - Added get_middleware_template() (135 lines)
   - Comprehensive template with examples
   - Shows dispatch() pattern

## Architecture Decisions

### Decision 1: Auto-Register Exception Handlers

**Why**: Laravel-like experience without manual setup.

**Trade-off**:
- ✅ Zero configuration for users
- ❌ Less control over registration order (but we handle this internally)

**Alternative**: Manual registration like vanilla FastAPI
```python
# Rejected: too verbose
app.add_exception_handler(AuthenticationError, handle_authentication_error)
app.add_exception_handler(AuthorizationError, handle_authorization_error)
# ... 5 more handlers ...
```

### Decision 2: Environment Variable Configuration

**Why**: 12-factor app principles, easy deployment.

**Trade-off**:
- ✅ No hardcoded config
- ✅ Different settings per environment
- ❌ Requires .env file management

**Alternative**: Config files (config/cors.py)
```python
# Rejected: more files, less flexible
from config.cors import ALLOWED_ORIGINS
configure_cors(app, allow_origins=ALLOWED_ORIGINS)
```

### Decision 3: Middleware as Functions, Not Classes

**Why**: Simpler API, less boilerplate.

**Trade-off**:
- ✅ One-line configuration
- ✅ No need to subclass
- ❌ Less customizable (but you can still write custom middleware)

**Alternative**: Middleware classes
```python
# Rejected: too much boilerplate
class CORSConfig:
    def __init__(self, origins):
        self.origins = origins

app.add_middleware(CORSMiddleware, config=CORSConfig(...))
```

### Decision 4: Opt-In TrustedHost

**Why**: Avoid breaking development environment.

**Trade-off**:
- ✅ Development works out of the box
- ❌ Might forget to enable in production

**Mitigation**: Documentation warns about this, provide clear examples.

## Known Limitations

### 1. No HTML Error Pages

**Issue**: All errors return JSON, even for browser requests.

**Workaround**: If you need HTML errors, create custom exception handler:

```python
from starlette.responses import HTMLResponse

@app.exception_handler(404)
async def custom_404(request, exc):
    if "text/html" in request.headers.get("accept", ""):
        return HTMLResponse("<h1>404 Not Found</h1>", status_code=404)
    return JSONResponse({"detail": "Not found"}, status_code=404)
```

**Future**: Sprint 4.x might add content negotiation.

### 2. No Request Middleware

**Issue**: Can't easily transform requests (only responses).

**Workaround**: Use dependencies or write custom BaseHTTPMiddleware.

**Future**: Sprint 4.x might add request transformation helpers.

### 3. Limited Middleware Customization

**Issue**: configure_cors() has many parameters, but not all Starlette options.

**Workaround**: Use Starlette's CORSMiddleware directly for advanced cases:

```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    expose_headers=["X-Custom-Header"],  # Not in configure_cors()
)
```

**Future**: Add more parameters to configure_cors() if needed.

## Production Checklist

Before deploying:

- [ ] Set `CORS_ORIGINS` to specific domains (not `*`)
- [ ] Set `ALLOWED_HOSTS` to specific hosts
- [ ] Enable TrustedHost middleware
- [ ] Verify exception handlers return JSON (not HTML)
- [ ] Test CORS preflight requests
- [ ] Test GZip compression (check Content-Encoding header)
- [ ] Test error responses (401, 403, 404, 422, 500)
- [ ] Set `JWT_SECRET_KEY` environment variable (Sprint 3.3)
- [ ] Configure logging for exceptions (future sprint)

## Next Steps (Future Sprints)

1. **Content Negotiation** (Sprint 4.x)
   - Return JSON for API clients
   - Return HTML for browser requests
   - Accept header parsing

2. **Error Logging** (Sprint 4.x)
   - Log exceptions to Sentry/CloudWatch
   - Include request context (user, IP, etc.)
   - Error aggregation and alerting

3. **Request Transformation** (Sprint 4.x)
   - Middleware for request body transformation
   - Automatic camelCase ↔ snake_case conversion
   - Request sanitization

4. **Rate Limiting** (Sprint 4.x)
   - IP-based rate limiting
   - User-based rate limiting
   - Redis backend for distributed systems

5. **API Versioning** (Sprint 4.x)
   - Version in URL (/api/v1/)
   - Version in header (Accept: application/vnd.api+json; version=1)
   - Automatic deprecation warnings

## Conclusion

Sprint 3.4 successfully implemented the **HTTP Kernel layer**, transforming our framework from a "raw" FastAPI wrapper into a **production-ready** web framework with:

✅ **Global Exception Handling** (automatic, zero-config)
✅ **Standardized Error Responses** (JSON, never HTML)
✅ **CORS Support** (environment-based config)
✅ **Response Compression** (GZip, ~70-90% reduction)
✅ **Security Headers** (TrustedHost middleware)
✅ **CLI Code Generation** (ftf make:middleware)
✅ **25 Comprehensive Tests** (100% passing, 93%+ coverage)

**The framework now provides a Laravel-like developer experience** while maintaining FastAPI's async performance. Developers can focus on business logic, not boilerplate exception handling.

**Key Achievement**: The "Orça Já" frontend can now rely on consistent error responses and CORS support, enabling seamless API integration.

---

**Total Test Count**: 334 tests (309 passing + 25 from Sprint 3.4)
**Overall Coverage**: 65.64%
**Sprint Status**: ✅ **COMPLETE**
