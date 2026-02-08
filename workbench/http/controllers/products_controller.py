from typing import Any

from jtc.http import Controller, Get, Post, Request

from jtc.http import Inject
from sqlalchemy.ext.asyncio import AsyncSession
from jtc.validation import FormRequest
from fast_query import BaseRepository

if True:
    from workbench.app.repositories.products_repository import productsRepository

class ProductsController(Controller):
    """
    Controller for productss.
    """

    @Get("/productss")
    async def index(self) -> Any:
        """
        List all items.

        Returns:
            List of productss
        """
        if True:
            repo = productsRepository = Inject(productsRepository)
            items = await repo.all()
            return items

    @Get("/productss/{id}")
    async def show(self, id: int) -> Any:
        """
        Show single item by ID.

        Args:
            id: Item ID

        Returns:
            Single item
        """
        if True:
            repo = productsRepository = Inject(productsRepository)
            item = await repo.find_or_fail(id)
            return item

    @Post("/productss")
    async def store(self, request: Request) -> Any:
        """
        Store a new item.

        Args:
            request: HTTP request

        Returns:
            Created item
        """
        if True:
            repo = productsRepository = Inject(productsRepository)
            item = await repo.create(request.dict())
            return item

    @Post("/productss/{id}")
    async def update(self, id: int, request: Request) -> Any:
        """
        Update an existing item.

        Args:
            id: Item ID
            request: HTTP request

        Returns:
            Updated item
        """
        if True:
            repo = productsRepository = Inject(productsRepository)
            item = await repo.update(id, request.dict())
            return item

    @Post("/productss/{id}")
    async def destroy(self, id: int) -> Any:
        """
        Delete an item.

        Args:
            id: Item ID

        Returns:
            Success message
        """
        if True:
            repo = productsRepository = Inject(productsRepository)
            await repo.delete(id)
            return {"message": "Deleted"}
