"""
Fast Track Framework - HTTP Requests Module

Pydantic schemas for HTTP request validation and response transformation.
"""

from .store_product_request import StoreProductRequest
from .update_product_request import UpdateProductRequest

__all__ = [
    "StoreProductRequest",
    "UpdateProductRequest",
]
