"""
Pagination Tests (Fixed Sprint 16.1)
"""
import pytest
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from fast_query import Base, BaseRepository, create_engine
from fast_query.pagination import LengthAwarePaginator
from ftf.resources.core import JsonResource

# --- Mocks ---
class PaginationItem(Base):
    __tablename__ = "pagination_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

class PaginationRepo(BaseRepository[PaginationItem]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, PaginationItem)

class ItemResource(JsonResource):
    def to_array(self, request) -> dict:
        return {"id": self.resource.id, "name": self.resource.name}

# --- Fixtures ---
@pytest.fixture
async def engine() -> AsyncEngine:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncSession:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session

@pytest.fixture
async def repo(session: AsyncSession) -> PaginationRepo:
    repo = PaginationRepo(session)
    items = [PaginationItem(name=f"Item {i}") for i in range(1, 56)]
    session.add_all(items)
    await session.commit()
    return repo

# --- Tests ---
@pytest.mark.asyncio
class TestRepositoryPagination:
    async def test_paginate_returns_paginator_instance(self, repo: PaginationRepo):
        paginator = await repo.paginate()
        assert isinstance(paginator, LengthAwarePaginator)

    async def test_paginate_first_page(self, repo: PaginationRepo):
        paginator = await repo.paginate(page=1, per_page=10)
        assert paginator.total == 55
        assert paginator.last_page == 6
        assert len(paginator.items) == 10
        assert paginator.items[0].name == "Item 1"

    async def test_paginate_last_page_partial(self, repo: PaginationRepo):
        paginator = await repo.paginate(page=6, per_page=10)
        assert len(paginator.items) == 5
        assert paginator.items[0].name == "Item 51"

    async def test_paginate_empty_results(self, session: AsyncSession):
        empty_repo = PaginationRepo(session)
        paginator = await empty_repo.paginate()
        assert paginator.total == 0
        assert len(paginator.items) == 0

@pytest.mark.asyncio
class TestResourceCollectionPagination:
    async def test_collection_meta(self, repo: PaginationRepo):
        paginator = await repo.paginate(page=1, per_page=10)
        collection = ItemResource.collection(paginator)
        response = collection.resolve()
        assert response["meta"]["total"] == 55
        assert response["meta"]["per_page"] == 10
