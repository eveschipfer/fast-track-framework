"""
HTTP Controllers Package

This package contains HTTP controllers for the workbench application.
Similar to Laravel's app/Http/Controllers directory, this is where
you define your route handlers.

Controllers Registered:
    - product_controller: Product CRUD endpoints (router-based, JTC design)

Usage:
    from app.http.controllers.product_controller import router as product_router
    from app.http.controllers.product_controller import ProductService

    # Register with FastAPI app via RouteServiceProvider
    app.include_router(product_router, prefix="/api")
"""

__all__ = []
