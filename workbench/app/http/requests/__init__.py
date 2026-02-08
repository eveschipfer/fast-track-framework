"""
Fast Track Framework - HTTP Requests Module

Pydantic schemas for HTTP request validation and response transformation.
"""

from .product_request import ProductCreate, ProductUpdate, ProductResponse

__all__ = [
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
]
