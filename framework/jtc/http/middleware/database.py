"""
Database Session Middleware

This middleware ensures proper session lifecycle management:
1. Initializes a fresh scoped cache (ContextVar) per request
2. Pre-resolves AsyncSession so route handlers share the SAME session
3. Commits transactions on successful responses (2xx status codes)
4. Rolls back transactions on errors (4xx/5xx status codes or exceptions)
5. Always closes sessions and clears scoped cache after request completion

Without this middleware, failed requests leave sessions in a "dirty" state
that causes PendingRollbackError on subsequent requests.

Usage:
    from jtc.http.middleware import DatabaseSessionMiddleware

    app = FastTrackFramework()
    app.add_middleware(DatabaseSessionMiddleware)

Educational Note:
    SQLAlchemy sessions need explicit transaction management:
    - session.commit() on success
    - session.rollback() on error
    - session.close() to release connection back to pool

    This middleware automates this pattern for FastAPI/Starlette applications.

    CRITICAL: The middleware MUST use request.app.container (the app's real
    container) instead of Container() (which creates an empty container with
    no registrations). It also pre-resolves the session BEFORE call_next()
    so that route handlers (via Inject(AsyncSession)) find the same session
    in the scoped cache.
"""

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from jtc.core import clear_scoped_cache_async, set_scoped_cache


class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that manages database session lifecycle per request.

    For each request:
    1. Initializes scoped cache (ContextVar) for request isolation
    2. Pre-resolves AsyncSession from the app's container
    3. On success (2xx): Commits the transaction
    4. On error (exception or 4xx/5xx): Rolls back the transaction
    5. Always: Closes session and clears scoped cache

    This prevents PendingRollbackError when a request fails and leaves
    the session in a dirty state.

    IMPORTANT: Uses request.app.container to access the SAME container
    that Inject() uses, ensuring middleware and route handlers share
    the same session instance via the scoped cache.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request and manage session lifecycle.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response: HTTP response
        """
        # Initialize a fresh scoped cache for this request
        # This ensures each request gets isolated scoped instances
        set_scoped_cache({})

        # Use the APP's container (has all registrations)
        container = request.app.container
        session = None

        try:
            # Pre-resolve the session BEFORE call_next() so that
            # route handlers (via Inject(AsyncSession)) find the SAME
            # session in the scoped cache
            try:
                session = container.resolve(AsyncSession)
            except Exception:
                # AsyncSession not registered (no DatabaseServiceProvider), skip
                pass

            # Call next middleware/handler
            response = await call_next(request)

            # Commit or rollback based on response status
            if session is not None:
                if 200 <= response.status_code < 300:
                    try:
                        await session.commit()
                    except Exception:
                        await session.rollback()
                        raise
                else:
                    # Rollback on client/server errors (4xx/5xx)
                    await session.rollback()

            return response

        except Exception as e:
            # Rollback on exception
            if session is not None:
                try:
                    await session.rollback()
                except Exception:
                    pass

            raise e

        finally:
            # Always close session to return connection to pool
            if session is not None:
                try:
                    await session.close()
                except Exception:
                    pass

            # Clear scoped cache (disposes all scoped instances)
            await clear_scoped_cache_async()
