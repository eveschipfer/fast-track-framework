"""
JwtMiddleware

Starlette BaseHTTPMiddleware that intercepts every inbound request and, when
an ``Authorization: Bearer <token>`` header is present, validates the JWT
and injects the decoded payload into ``request.state.user``.

Behaviour matrix:
    No Authorization header  → request.state.user = None  (public routes continue)
    Valid token              → request.state.user = payload dict
    Expired token            → 401 JSON response (token has expired, client must refresh)
    Tampered signature       → 403 JSON response (security violation)
    Malformed / unknown err  → 401 JSON response

This middleware does NOT enforce authentication on every route.  Protected
endpoints should additionally declare a dependency (e.g. ``CurrentUser``) that
rejects requests where ``request.state.user`` is None.

Example usage in a protected route:
    @router.get("/me")
    async def me(request: Request):
        if not getattr(request.state, "user", None):
            raise HTTPException(status_code=401, detail="Not authenticated")
        return request.state.user

Or use the ``CurrentUser`` dependency which handles this automatically.
"""

from typing import Any

from fastapi.responses import JSONResponse
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidSignatureError, InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from jtc.auth.jwt import decode_token


class JwtMiddleware(BaseHTTPMiddleware):
    """
    JWT validation middleware.

    Reads the ``Authorization`` header, validates the Bearer token, and
    attaches the decoded payload to ``request.state.user``.

    HTTP error responses follow RFC 6750:
        401 Unauthorized  — Missing or invalid/expired token.
        403 Forbidden     — Valid token structure but signature tampered.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Initialise to None so route handlers can check for unauthenticated state
        request.state.user = None

        authorization: str | None = request.headers.get("Authorization")

        if not authorization:
            # No header → allow through; protected routes enforce auth themselves
            return await call_next(request)

        parts = authorization.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid Authorization header format. Expected 'Bearer <token>'."
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = parts[1]

        try:
            payload: dict[str, Any] = decode_token(token)
            request.state.user = payload

        except ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token has expired. Please refresh your token."},
                headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
            )

        except InvalidSignatureError:
            # Signature mismatch → 403 (token was tampered with)
            return JSONResponse(
                status_code=403,
                content={"detail": "Token signature verification failed."},
            )

        except (DecodeError, InvalidTokenError):
            return JSONResponse(
                status_code=401,
                content={"detail": "Could not validate token."},
                headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
            )

        return await call_next(request)
