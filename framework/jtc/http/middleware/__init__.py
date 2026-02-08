"""
Middleware Manager (Sprint 3.4)

This module provides a clean interface for configuring standard middleware
components like CORS, TrustedHost, and GZip compression.

Key Features:
    - CORS configuration from environment variables
    - Security headers via TrustedHost middleware
    - Response compression with GZip
    - Clean wrapper around Starlette middleware

Educational Note:
    Laravel uses app/Http/Kernel.php to define middleware stacks.
    We do the same here but adapted for FastAPI/Starlette's middleware system.

    Key Difference:
        - Laravel: Middleware classes with handle() method
        - FastAPI/Starlette: Middleware via add_middleware() or BaseHTTPMiddleware

Architecture Decision:
    We provide helper functions (configure_cors, configure_gzip) instead of
    requiring users to manually add_middleware() with complex configs.
    This makes the API more Laravel-like and beginner-friendly.

Usage:
    from jtc.http.middleware import configure_cors, configure_gzip

    app = FastTrackFramework()
    configure_cors(app)  # Auto-reads from .env
    configure_gzip(app)

Comparison with Laravel:
    Laravel (app/Http/Kernel.php):
        protected $middleware = [
            \\App\\Http\\Middleware\\TrustProxies::class,
            \\Illuminate\\Http\\Middleware\\HandleCors::class,
        ];

    Fast Track:
        configure_cors(app)
        configure_trusted_host(app)
"""

import os

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .database import DatabaseSessionMiddleware


# ============================================================================
# CORS MIDDLEWARE
# ============================================================================


def configure_cors(
    app: FastAPI,
    allow_origins: list[str] | None = None,
    allow_credentials: bool = True,
    allow_methods: list[str] | None = None,
    allow_headers: list[str] | None = None,
) -> None:
    """
    Configure CORS (Cross-Origin Resource Sharing) middleware.

    This is essential for frontend applications (React, Vue, Angular) that
    need to make API calls from a different domain.

    Args:
        app: The FastAPI application
        allow_origins: List of allowed origins (default: from CORS_ORIGINS env var)
        allow_credentials: Allow credentials (cookies, auth headers)
        allow_methods: Allowed HTTP methods (default: all)
        allow_headers: Allowed HTTP headers (default: all)

    Environment Variables:
        CORS_ORIGINS: Comma-separated list of allowed origins
            Example: "http://localhost:3000,https://myapp.com"
            Default: ["*"] (allow all)

    Example:
        >>> # Allow all origins (development only!)
        >>> configure_cors(app)
        >>>
        >>> # Production: restrict to specific origins
        >>> configure_cors(
        ...     app,
        ...     allow_origins=["https://myapp.com", "https://www.myapp.com"]
        ... )

    Security Warning:
        DO NOT use allow_origins=["*"] with allow_credentials=True in production!
        This is a security vulnerability. Instead, specify exact allowed origins.

    Educational Note:
        CORS is a security feature that prevents malicious websites from
        making unauthorized requests to your API. When a browser makes a
        cross-origin request, it sends a preflight OPTIONS request to check
        if the server allows it.

        How it works:
        1. Browser sends OPTIONS request with Origin header
        2. Server responds with Access-Control-Allow-Origin header
        3. If allowed, browser sends the actual request
        4. Server includes CORS headers in response

    Comparison with Laravel:
        Laravel (config/cors.php):
            'allowed_origins' => explode(',', env('CORS_ORIGINS', '*')),
            'allowed_methods' => ['*'],
            'allowed_headers' => ['*'],
            'allow_credentials' => true,

        Fast Track:
            configure_cors(app)  # Reads from CORS_ORIGINS env var
    """
    # Read from environment variable if not provided
    if allow_origins is None:
        origins_str = os.getenv("CORS_ORIGINS", "*")
        if origins_str == "*":
            allow_origins = ["*"]
        else:
            # Split comma-separated list and strip whitespace
            allow_origins = [origin.strip() for origin in origins_str.split(",")]

    # Default: allow all methods
    if allow_methods is None:
        allow_methods = ["*"]

    # Default: allow all headers
    if allow_headers is None:
        allow_headers = ["*"]

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )


# ============================================================================
# TRUSTED HOST MIDDLEWARE
# ============================================================================


def configure_trusted_host(
    app: FastAPI,
    allowed_hosts: list[str] | None = None,
) -> None:
    """
    Configure TrustedHost middleware for security.

    This prevents Host header attacks by validating the Host header
    against a whitelist of allowed hosts.

    Args:
        app: The FastAPI application
        allowed_hosts: List of allowed host patterns (default: from ALLOWED_HOSTS env)

    Environment Variables:
        ALLOWED_HOSTS: Comma-separated list of allowed hosts
            Example: "localhost,myapp.com,*.myapp.com"
            Default: ["*"] (allow all, not recommended for production)

    Example:
        >>> # Development: allow all
        >>> configure_trusted_host(app)
        >>>
        >>> # Production: restrict to specific hosts
        >>> configure_trusted_host(
        ...     app,
        ...     allowed_hosts=["myapp.com", "*.myapp.com"]
        ... )

    Security Warning:
        Always specify allowed_hosts in production! Host header attacks
        can lead to cache poisoning, password reset poisoning, and more.

    Educational Note:
        Host header attacks exploit applications that trust the Host header.
        An attacker can send a request with a malicious Host header, which
        might be used to generate URLs (password reset links, etc.) pointing
        to the attacker's domain.

        How TrustedHost protects you:
        1. Validates Host header against whitelist
        2. Returns 400 Bad Request if Host is not allowed
        3. Supports wildcards (*.example.com)

    Comparison with Laravel:
        Laravel doesn't have built-in TrustedHost middleware, but uses
        TrustProxies middleware for similar security concerns.

        Fast Track provides TrustedHost as a first-class citizen because
        it's a common attack vector for FastAPI applications.
    """
    # Read from environment variable if not provided
    if allowed_hosts is None:
        hosts_str = os.getenv("ALLOWED_HOSTS", "*")
        if hosts_str == "*":
            allowed_hosts = ["*"]
        else:
            # Split comma-separated list and strip whitespace
            allowed_hosts = [host.strip() for host in hosts_str.split(",")]

    # Add TrustedHost middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts,
    )


# ============================================================================
# GZIP COMPRESSION MIDDLEWARE
# ============================================================================


def configure_gzip(
    app: FastAPI,
    minimum_size: int = 1000,
    compresslevel: int = 5,
) -> None:
    """
    Configure GZip compression middleware.

    Compresses HTTP responses to reduce bandwidth and improve load times.
    This is especially important for JSON APIs with large responses.

    Args:
        app: The FastAPI application
        minimum_size: Minimum response size (bytes) to compress (default: 1000)
        compresslevel: Compression level 1-9 (default: 5)
            1 = fastest, lowest compression
            9 = slowest, highest compression
            5 = balanced (recommended)

    Example:
        >>> # Default settings (recommended)
        >>> configure_gzip(app)
        >>>
        >>> # Aggressive compression (slower but smaller)
        >>> configure_gzip(app, minimum_size=500, compresslevel=9)
        >>>
        >>> # Fast compression (faster but larger)
        >>> configure_gzip(app, minimum_size=2000, compresslevel=1)

    Performance Note:
        - compresslevel=1: ~70% size reduction, very fast
        - compresslevel=5: ~75% size reduction, balanced (default)
        - compresslevel=9: ~80% size reduction, slower

        For most APIs, level 5 is the sweet spot. Only use level 9 if
        bandwidth is extremely expensive and CPU is cheap.

    Educational Note:
        GZip compression is transparent to the client. The browser
        automatically decompresses responses. The flow:

        1. Browser sends: Accept-Encoding: gzip
        2. Server compresses response
        3. Server adds: Content-Encoding: gzip
        4. Browser automatically decompresses

        JSON responses compress extremely well (often 70-90% reduction)
        because JSON has lots of repeated keys and whitespace.

    Comparison with Laravel:
        Laravel doesn't have built-in GZip middleware. Instead, it's
        typically handled by the web server (nginx, Apache).

        Fast Track includes it as a first-class citizen because:
        - Easy to configure programmatically
        - Works in development without nginx
        - Can be toggled per-environment
    """
    app.add_middleware(
        GZipMiddleware,
        minimum_size=minimum_size,
        compresslevel=compresslevel,
    )


# ============================================================================
# MIDDLEWARE MANAGER
# ============================================================================


class MiddlewareManager:
    """
    Centralized middleware configuration manager.

    This class provides a Laravel-like API for configuring all middleware
    in one place. It's a convenience wrapper around the configure_* functions.

    Example:
        >>> app = FastTrackFramework()
        >>> MiddlewareManager.configure_all(app)
        >>> # CORS, GZip, and TrustedHost are now configured

    Educational Note:
        This is similar to Laravel's app/Http/Kernel.php which defines
        global middleware, route middleware, and middleware groups.

        We keep it simpler: just global middleware for now. Route-specific
        middleware can be added via FastAPI's dependency injection.

    Comparison with Laravel:
        Laravel (app/Http/Kernel.php):
            protected $middleware = [
                \\App\\Http\\Middleware\\TrustProxies::class,
                \\Illuminate\\Http\\Middleware\\HandleCors::class,
            ];

        Fast Track:
            MiddlewareManager.configure_all(app)
    """

    @staticmethod
    def configure_all(
        app: FastAPI,
        enable_cors: bool = True,
        enable_gzip: bool = True,
        enable_trusted_host: bool = False,
    ) -> None:
        """
        Configure all standard middleware.

        Args:
            app: The FastAPI application
            enable_cors: Enable CORS middleware (default: True)
            enable_gzip: Enable GZip compression (default: True)
            enable_trusted_host: Enable TrustedHost middleware (default: False)

        Example:
            >>> # Development: CORS + GZip only
            >>> MiddlewareManager.configure_all(app)
            >>>
            >>> # Production: All security features
            >>> MiddlewareManager.configure_all(
            ...     app,
            ...     enable_trusted_host=True
            ... )

        Educational Note:
            We enable CORS and GZip by default because they're almost
            always needed. TrustedHost is opt-in because it requires
            configuration (allowed_hosts) and can break development if
            misconfigured.

        Recommended Setup:
            Development:
                - CORS: enabled (allow all)
                - GZip: enabled
                - TrustedHost: disabled

            Production:
                - CORS: enabled (specific origins)
                - GZip: enabled
                - TrustedHost: enabled (specific hosts)
        """
        if enable_cors:
            configure_cors(app)

        if enable_gzip:
            configure_gzip(app)

        if enable_trusted_host:
            configure_trusted_host(app)
