"""
Blog Example - Complete CRUD API with Relationships

This example demonstrates:
    - QueryBuilder fluent interface
    - One-to-many relationships (User -> Posts, Post -> Comments)
    - Many-to-many relationships (User <-> Roles)
    - Eager loading with with_() to prevent N+1 queries
    - Repository Pattern with FastTrackFramework
    - Dependency injection with Inject()

Features:
    - List posts with pagination and search
    - Get post with author and comments (eager loaded)
    - Create post for authenticated user
    - List users with their roles
    - Query builder filtering and ordering

Run:
    poetry run python examples/blog_example.py

Then visit:
    http://localhost:8000/posts - List posts with pagination
    http://localhost:8000/posts/1 - Get post with relationships
    http://localhost:8000/users - List users with roles
    http://localhost:8000/users/1/posts - Get user's posts

Educational Notes:
    - All relationship access requires eager loading (lazy="raise")
    - with_() uses selectinload (2 queries: main + relationship)
    - with_joined() uses joinedload (1 query with JOIN)
    - QueryBuilder is type-safe (Generic[T] preserves model type)
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from ftf.database import (
    AsyncSessionFactory,
    Base,
    BaseRepository,
    create_engine,
    get_engine,
)
from ftf.http import FastTrackFramework, Inject
from app.models import Comment, Post, Role, User

# ===========================
# REPOSITORIES
# ===========================


class UserRepository(BaseRepository[User]):
    """User repository with custom methods."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_with_roles(self, user_id: int) -> User:
        """Get user with roles eager loaded."""
        return await (
            self.query()
            .where(User.id == user_id)
            .with_(User.roles)  # Eager load roles
            .first_or_fail()
        )

    async def find_by_email(self, email: str) -> User | None:
        """Find user by email."""
        return await self.query().where(User.email == email).first()


class PostRepository(BaseRepository[Post]):
    """Post repository with custom methods."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Post)

    async def list_with_author(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
    ) -> list[Post]:
        """
        List posts with authors, with optional search.

        Demonstrates:
            - Pagination with paginate()
            - Filtering with where_like()
            - Ordering with latest()
            - Eager loading with with_()
        """
        query = (
            self.query()
            .with_(Post.author)  # Prevent N+1: load authors in separate query
            .latest()  # Order by created_at desc
        )

        if search:
            query = query.where_like(Post.title, f"%{search}%")

        return await query.paginate(page=page, per_page=per_page).get()

    async def get_with_relationships(self, post_id: int) -> Post:
        """
        Get post with author and comments.

        Demonstrates:
            - Multiple eager loads
            - Nested relationships (comments -> author)
        """
        return await (
            self.query()
            .where(Post.id == post_id)
            .with_(
                Post.author,  # Load post author
                Post.comments,  # Load comments
            )
            .first_or_fail()
        )

    async def get_user_posts(self, user_id: int) -> list[Post]:
        """Get all posts by a specific user."""
        return await (
            self.query()
            .where(Post.user_id == user_id)
            .with_(Post.author)
            .latest()
            .get()
        )


class CommentRepository(BaseRepository[Comment]):
    """Comment repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Comment)


class RoleRepository(BaseRepository[Role]):
    """Role repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Role)


# ===========================
# APPLICATION SETUP
# ===========================


@asynccontextmanager
async def lifespan(app: FastTrackFramework) -> AsyncGenerator[None]:
    """
    Application lifespan manager.

    Sets up database engine and session factory on startup,
    cleans up on shutdown.
    """
    # Startup: Create database engine
    engine = create_engine("sqlite+aiosqlite:///./blog_example.db", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed database with sample data
    await seed_database(engine)

    yield

    # Shutdown: Cleanup
    await engine.dispose()


async def seed_database(engine: AsyncEngine) -> None:
    """Seed database with sample data."""
    factory = AsyncSessionFactory()
    async with factory() as session:
        # Check if data already exists
        existing_users = (await session.execute("SELECT COUNT(*) FROM users")).scalar()

        if existing_users and existing_users > 0:
            return  # Already seeded

        # Create roles
        admin_role = Role(name="admin", description="Administrator")
        user_role = Role(name="user", description="Regular user")
        session.add_all([admin_role, user_role])
        await session.commit()

        # Create users
        alice = User(name="Alice Admin", email="alice@example.com")
        bob = User(name="Bob User", email="bob@example.com")
        session.add_all([alice, bob])
        await session.commit()

        # Assign roles (many-to-many)
        # Refresh to get relationships loaded
        await session.refresh(alice, ["roles"])
        await session.refresh(bob, ["roles"])
        await session.refresh(admin_role, ["users"])
        await session.refresh(user_role, ["users"])

        admin_role.users.append(alice)
        user_role.users.append(alice)
        user_role.users.append(bob)
        await session.commit()

        # Create posts
        post1 = Post(
            title="Introduction to Fast Track Framework",
            content="Fast Track Framework brings Laravel-like DX to async Python...",
            user_id=alice.id,
        )
        post2 = Post(
            title="Understanding Async Patterns",
            content="Async Python can be tricky, but with the right patterns...",
            user_id=alice.id,
        )
        post3 = Post(
            title="My First Post",
            content="Hello, world! This is Bob's first post.",
            user_id=bob.id,
        )
        session.add_all([post1, post2, post3])
        await session.commit()

        # Create comments
        comment1 = Comment(
            content="Great article! Very helpful.",
            post_id=post1.id,
            user_id=bob.id,
        )
        comment2 = Comment(
            content="Looking forward to more posts like this.",
            post_id=post1.id,
            user_id=bob.id,
        )
        comment3 = Comment(
            content="Welcome to the platform!",
            post_id=post3.id,
            user_id=alice.id,
        )
        session.add_all([comment1, comment2, comment3])
        await session.commit()



# Create app
app = FastTrackFramework(lifespan=lifespan)


# ===========================
# DEPENDENCY INJECTION SETUP
# ===========================


# Register AsyncEngine (singleton)
@app.on_event("startup")
async def setup_database() -> None:
    """Register database dependencies."""
    engine = get_engine()
    app.container.register(AsyncEngine, scope="singleton")
    app.container._singletons[AsyncEngine] = engine


# Register AsyncSession factory (scoped per request)
def session_factory() -> AsyncSession:
    """Create async session."""
    factory = AsyncSessionFactory()
    return factory()


app.register(AsyncSession, implementation=session_factory, scope="scoped")

# Register repositories (transient - new instance per resolve)
app.register(UserRepository, scope="transient")
app.register(PostRepository, scope="transient")
app.register(CommentRepository, scope="transient")
app.register(RoleRepository, scope="transient")


# ===========================
# ROUTES
# ===========================


@app.get("/")
async def index() -> dict[str, str]:
    """API index."""
    return {
        "message": "Blog API Example",
        "endpoints": {
            "posts": "/posts?page=1&per_page=20&search=async",
            "post_detail": "/posts/{id}",
            "users": "/users",
            "user_detail": "/users/{id}",
            "user_posts": "/users/{id}/posts",
        },
    }


@app.get("/posts")
async def list_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = None,
    repo: PostRepository = Inject(PostRepository),
) -> dict[str, object]:
    """
    List posts with pagination and optional search.

    Demonstrates:
        - Query parameters with validation
        - Pagination
        - Search filtering
        - Eager loading (prevents N+1)
    """
    posts = await repo.list_with_author(page=page, per_page=per_page, search=search)

    return {
        "posts": [
            {
                "id": post.id,
                "title": post.title,
                "content": post.content[:100] + "...",  # Truncate
                "author": {
                    "id": post.author.id,
                    "name": post.author.name,
                    "email": post.author.email,
                },
                "created_at": post.created_at.isoformat(),
            }
            for post in posts
        ],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": await repo.query().count(),
        },
    }


@app.get("/posts/{post_id}")
async def get_post(
    post_id: int,
    repo: PostRepository = Inject(PostRepository),
) -> dict[str, object]:
    """
    Get post with author and comments.

    Demonstrates:
        - Eager loading multiple relationships
        - Automatic 404 with first_or_fail()
        - Nested data serialization
    """
    post = await repo.get_with_relationships(post_id)

    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author": {
            "id": post.author.id,
            "name": post.author.name,
            "email": post.author.email,
        },
        "comments": [
            {
                "id": comment.id,
                "content": comment.content,
                "created_at": comment.created_at.isoformat(),
            }
            for comment in post.comments
        ],
        "created_at": post.created_at.isoformat(),
    }


@app.get("/users")
async def list_users(
    repo: UserRepository = Inject(UserRepository),
) -> dict[str, list[dict[str, object]]]:
    """
    List all users with their roles.

    Demonstrates:
        - Many-to-many relationship eager loading
    """
    users = await repo.query().with_(User.roles).get()

    return {
        "users": [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "roles": [role.name for role in user.roles],
            }
            for user in users
        ]
    }


@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    repo: UserRepository = Inject(UserRepository),
) -> dict[str, object]:
    """Get user with roles."""
    user = await repo.get_with_roles(user_id)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "roles": [
            {"id": role.id, "name": role.name, "description": role.description}
            for role in user.roles
        ],
    }


@app.get("/users/{user_id}/posts")
async def get_user_posts(
    user_id: int,
    user_repo: UserRepository = Inject(UserRepository),
    post_repo: PostRepository = Inject(PostRepository),
) -> dict[str, object]:
    """
    Get user's posts.

    Demonstrates:
        - Multiple repository injection
        - Filtering by foreign key
    """
    # Verify user exists
    user = await user_repo.find_or_fail(user_id)

    # Get user's posts
    posts = await post_repo.get_user_posts(user_id)

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
        "posts": [
            {
                "id": post.id,
                "title": post.title,
                "content": post.content[:100] + "...",
                "created_at": post.created_at.isoformat(),
            }
            for post in posts
        ],
        "total": len(posts),
    }


# ===========================
# MAIN
# ===========================

if __name__ == "__main__":
    import uvicorn


    uvicorn.run(app, host="0.0.0.0", port=8000)
