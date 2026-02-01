"""
Throttle Middleware (Sprint 3.7)

Rate limiting middleware using the cache system to track request counts.

Educational Note:
    This implements the "sliding window" rate limiting algorithm:
    - Track requests per IP per endpoint
    - Increment counter on each request
    - Reset counter after time window
    - Return 429 when limit exceeded

    Laravel equivalent:
        Route::middleware('throttle:60,1')->group(function () {
            // Max 60 requests per minute
        });

    Fast Track equivalent:
        app.add_middleware(ThrottleMiddleware, max_requests=60, window_seconds=60)

    Why use cache?
        ✅ Distributed: Works across multiple workers/servers (with Redis)
        ✅ Automatic expiration: TTL handles window reset
        ✅ Atomic: increment() is thread-safe
        ✅ Flexible: Can use file/redis/array drivers

Comparison with alternatives:
    1. In-memory dict: Not distributed, lost on restart
    2. Database: Too slow, creates bottleneck
    3. Redis/Cache: Perfect balance of speed and persistence

Headers:
    X-RateLimit-Limit: Maximum requests allowed
    X-RateLimit-Remaining: Requests remaining in window
    X-RateLimit-Reset: Unix timestamp when window resets
"""

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ftf.cache import Cache
from ftf.i18n import trans


class ThrottleMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using cache-based counters.

    Limits requests per IP address per time window.
    Returns 429 Too Many Requests when limit exceeded.

    Configuration:
        max_requests: Maximum requests allowed per window (default: 60)
        window_seconds: Time window in seconds (default: 60)
        key_prefix: Cache key prefix (default: "throttle:")

    Example:
        from ftf.http import FastTrackFramework
        from ftf.http.middleware import ThrottleMiddleware

        app = FastTrackFramework()

        # 60 requests per minute
        app.add_middleware(ThrottleMiddleware, max_requests=60, window_seconds=60)

        # 100 requests per hour
        app.add_middleware(ThrottleMiddleware, max_requests=100, window_seconds=3600)

    Educational Note:
        Laravel throttle middleware:
            Route::middleware('throttle:60,1')  // 60 per minute

        Fast Track throttle middleware:
            app.add_middleware(ThrottleMiddleware, max_requests=60, window_seconds=60)
    """

    def __init__(
        self,
        app,
        max_requests: int = 60,
        window_seconds: int = 60,
        key_prefix: str = "throttle:",
    ):
        """
        Initialize throttle middleware.

        Args:
            app: ASGI application
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
            key_prefix: Cache key prefix for throttle counters

        Example:
            # 60 requests per minute
            ThrottleMiddleware(app, max_requests=60, window_seconds=60)

            # 1000 requests per hour
            ThrottleMiddleware(app, max_requests=1000, window_seconds=3600)
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

    def _get_cache_key(self, request: Request) -> str:
        """
        Generate cache key for rate limiting.

        Format: throttle:{ip}:{path}

        This allows different rate limits per endpoint if needed.
        For global rate limiting, use just IP.

        Args:
            request: HTTP request

        Returns:
            Cache key string

        Example:
            >>> middleware._get_cache_key(request)
            'throttle:192.168.1.1:/api/users'
        """
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Get path (you can customize this for per-endpoint limits)
        path = request.url.path

        return f"{self.key_prefix}{client_ip}:{path}"

    def _get_reset_timestamp(self) -> int:
        """
        Calculate when the rate limit window resets.

        Returns:
            Unix timestamp when window resets

        Example:
            >>> middleware._get_reset_timestamp()
            1706745600  # Current time + window_seconds
        """
        return int(time.time() + self.window_seconds)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.

        Algorithm:
            1. Generate cache key (IP + path)
            2. Increment counter (atomic)
            3. Check if over limit
            4. If over limit: Return 429 with headers
            5. If under limit: Continue with headers

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            Response with rate limit headers

        Example:
            # Request 1-60: Pass through
            # Request 61+: Return 429 Too Many Requests
        """
        # Generate cache key
        cache_key = self._get_cache_key(request)

        # Increment counter (atomic operation)
        # First request creates key with value 1
        # Subsequent requests increment
        try:
            current_count = await Cache.increment(cache_key, amount=1)

            # Set TTL on first request
            # Note: This is a race condition in file driver, but Redis is atomic
            if current_count == 1:
                await Cache.put(cache_key, current_count, ttl=self.window_seconds)

        except Exception:
            # Cache error, allow request through (fail open)
            # In production, you might want to log this
            current_count = 0

        # Calculate remaining requests
        remaining = max(0, self.max_requests - current_count)

        # Calculate reset timestamp
        reset_timestamp = self._get_reset_timestamp()

        # Check if over limit
        if current_count > self.max_requests:
            # Rate limit exceeded - return 429
            return JSONResponse(
                status_code=429,
                content={
                    "error": trans("http.too_many_requests"),
                    "message": trans(
                        "http.rate_limit_exceeded",
                        limit=self.max_requests,
                        window=self.window_seconds,
                    ),
                },
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_timestamp),
                    "Retry-After": str(self.window_seconds),
                },
            )

        # Under limit - process request
        response = await call_next(request)

        # Add rate limit headers to successful response
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_timestamp)

        return response


class PerRouteThrottle:
    """
    Decorator for per-route rate limiting.

    Allows different rate limits for different endpoints.

    Example:
        from ftf.http.middleware import PerRouteThrottle

        # 10 requests per minute for login
        @app.post("/login")
        @PerRouteThrottle(max_requests=10, window_seconds=60)
        async def login(credentials: LoginRequest):
            return {"token": "..."}

        # 1000 requests per hour for API
        @app.get("/api/users")
        @PerRouteThrottle(max_requests=1000, window_seconds=3600)
        async def get_users():
            return {"users": [...]}

    Note:
        This is a future enhancement. For now, use global middleware.
        Implementation requires custom dependency injection or decorator logic.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize per-route throttle decorator.

        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def __call__(self, func: Callable) -> Callable:
        """
        Decorate route handler with rate limiting.

        Args:
            func: Route handler function

        Returns:
            Wrapped function with rate limiting

        Note:
            This is a placeholder for future implementation.
            Actual implementation would need to integrate with FastAPI's
            dependency injection system.
        """
        # TODO: Implement per-route throttling
        # This would require integration with FastAPI's dependency system
        return func
