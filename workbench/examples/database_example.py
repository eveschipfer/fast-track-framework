"""
Complete Database Integration Example

This example demonstrates the full stack:
1. FastAPI app with IoC Container
2. SQLAlchemy AsyncEngine (singleton)
3. AsyncSession (scoped per request)
4. Repository Pattern for CRUD operations
5. Automatic session cleanup

Run:
    python examples/database_example.py

Then test:
    curl -X POST http://localhost:8000/users -H "Content-Type: application/json" -d '{"name":"Alice","email":"alice@example.com"}'
    curl http://localhost:8000/users
    curl http://localhost:8000/users/1
    curl -X PUT http://localhost:8000/users/1 -H "Content-Type: application/json" -d '{"name":"Alice Updated"}'
    curl -X DELETE http://localhost:8000/users/1
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from typing import Optional

import uvicorn
from pydantic import BaseModel
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from jtc.database import AsyncSessionFactory, Base, BaseRepository, create_engine
from jtc.http import FastTrackFramework, Inject

# ============================================================================
# 1. DEFINE MODEL
# ============================================================================


class User(Base):
    """User model with SQLAlchemy 2.0 style."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)

    def __repr__(self) -> str:
        return f"User(id={self.id}, name='{self.name}', email='{self.email}')"


# ============================================================================
# 2. DEFINE REPOSITORY
# ============================================================================


class UserRepository(BaseRepository[User]):
    """User repository with custom methods."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address."""
        from sqlalchemy import select

        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


# ============================================================================
# 3. DEFINE PYDANTIC SCHEMAS
# ============================================================================


class UserCreate(BaseModel):
    """Schema for creating a user."""

    name: str
    email: str


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    name: str


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


# ============================================================================
# 4. CREATE APPLICATION
# ============================================================================


def create_app() -> FastTrackFramework:
    """Create and configure FastAPI application."""
    app = FastTrackFramework(
        title="Fast Track Framework - Database Example",
        description="Complete example with Repository Pattern",
        version="1.0.0",
    )

    # Setup database engine (singleton)
    print("🔧 Creating database engine...")
    engine = create_engine(
        "sqlite+aiosqlite:///./example.db",
        echo=True,  # Enable SQL logging
    )
    app.container.register(AsyncEngine, instance=engine)

    # Register session factory (scoped)
    print("🔧 Registering session factory...")

    def session_factory() -> AsyncSession:
        factory = AsyncSessionFactory()
        return factory()

    app.register(AsyncSession, implementation=session_factory, scope="scoped")

    # Register repository (transient)
    print("🔧 Registering repository...")
    app.register(UserRepository, scope="transient")

    # Create tables on startup
    @app.on_event("startup")
    async def create_tables() -> None:
        """Create database tables."""
        print("📊 Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created")

    # Cleanup on shutdown
    @app.on_event("shutdown")
    async def dispose_engine() -> None:
        """Dispose database engine."""
        print("🧹 Disposing database engine...")
        await engine.dispose()
        print("✅ Database engine disposed")

    return app


# ============================================================================
# 5. DEFINE ROUTES
# ============================================================================

app = create_app()


@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    repo: UserRepository = Inject(UserRepository),
) -> User:
    """
    Create a new user.

    Example:
        curl -X POST http://localhost:8000/users \\
             -H "Content-Type: application/json" \\
             -d '{"name":"Alice","email":"alice@example.com"}'
    """
    # Check if email already exists
    existing = await repo.find_by_email(data.email)
    if existing:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Email already exists")

    # Create user
    user = User(name=data.name, email=data.email)
    created = await repo.create(user)
    print(f"✅ Created user: {created}")
    return created


@app.get("/users", response_model=list[UserResponse])
async def list_users(
    limit: int = 10,
    offset: int = 0,
    repo: UserRepository = Inject(UserRepository),
) -> list[User]:
    """
    List all users with pagination.

    Example:
        curl http://localhost:8000/users
        curl http://localhost:8000/users?limit=5&offset=0
    """
    users = await repo.all(limit=limit, offset=offset)
    print(f"📋 Retrieved {len(users)} users")
    return users


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    repo: UserRepository = Inject(UserRepository),
) -> User:
    """
    Get a specific user by ID.

    Example:
        curl http://localhost:8000/users/1
    """
    user = await repo.find_or_fail(user_id)
    print(f"👤 Retrieved user: {user}")
    return user


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    repo: UserRepository = Inject(UserRepository),
) -> User:
    """
    Update a user's information.

    Example:
        curl -X PUT http://localhost:8000/users/1 \\
             -H "Content-Type: application/json" \\
             -d '{"name":"Alice Updated"}'
    """
    user = await repo.find_or_fail(user_id)
    user.name = data.name
    updated = await repo.update(user)
    print(f"✏️ Updated user: {updated}")
    return updated


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    repo: UserRepository = Inject(UserRepository),
) -> dict[str, bool]:
    """
    Delete a user.

    Example:
        curl -X DELETE http://localhost:8000/users/1
    """
    user = await repo.find_or_fail(user_id)
    await repo.delete(user)
    print(f"🗑️ Deleted user: {user}")
    return {"deleted": True}


@app.get("/users/email/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: str,
    repo: UserRepository = Inject(UserRepository),
) -> User:
    """
    Find user by email (demonstrates custom repository method).

    Example:
        curl http://localhost:8000/users/email/alice@example.com
    """
    user = await repo.find_by_email(email)
    if user is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User not found")
    print(f"📧 Found user by email: {user}")
    return user


@app.get("/stats")
async def get_stats(repo: UserRepository = Inject(UserRepository)) -> dict:
    """
    Get database statistics.

    Example:
        curl http://localhost:8000/stats
    """
    total = await repo.count()
    return {
        "total_users": total,
        "database": "SQLite (in-memory)",
        "pattern": "Repository Pattern (NOT Active Record)",
    }


# ============================================================================
# 6. RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Fast Track Framework - Database Example")
    print("=" * 60)
    print()
    print("📖 Documentation: http://localhost:8000/docs")
    print("🔍 ReDoc: http://localhost:8000/redoc")
    print()
    print("Try these commands:")
    print("  # Create user")
    print('  curl -X POST http://localhost:8000/users -H "Content-Type: application/json" -d \'{"name":"Alice","email":"alice@example.com"}\'')
    print()
    print("  # List users")
    print("  curl http://localhost:8000/users")
    print()
    print("  # Get user by ID")
    print("  curl http://localhost:8000/users/1")
    print()
    print("  # Update user")
    print('  curl -X PUT http://localhost:8000/users/1 -H "Content-Type: application/json" -d \'{"name":"Alice Updated"}\'')
    print()
    print("  # Delete user")
    print("  curl -X DELETE http://localhost:8000/users/1")
    print()
    print("  # Find by email")
    print("  curl http://localhost:8000/users/email/alice@example.com")
    print()
    print("  # Get stats")
    print("  curl http://localhost:8000/stats")
    print()
    print("=" * 60)
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
