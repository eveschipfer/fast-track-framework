"""
Sprint 1.2 Bonus: The Active Record Trap (Async Edition)
=========================================================

Educational module demonstrating WHY Active Record pattern doesn't
translate well to async Python, and the engineering challenges involved.

This is INTENTIONALLY "wrong" code - it works but has serious limitations.
The goal is to understand the trade-offs before accepting SQLModel/Repository.

Learning Objectives:
1. Understand ContextVars for request-scoped state
2. See why "magic" patterns lose type safety
3. Experience the pain of hidden dependencies
4. Appreciate explicit dependency injection

WARNING: Do NOT use this pattern in production!
This is educational code showing common mistakes.
"""

import asyncio
from contextvars import ContextVar

from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ============================================================================
# 1. THE "MAGIC" CONTEXT (The Hidden State)
# ============================================================================

# Global ContextVar holding the current request's database session
# Problem: This is GLOBAL state disguised as request-local
_session_context: ContextVar[AsyncSession | None] = ContextVar(
    "session_context", default=None
)


# ============================================================================
# 2. THE ACTIVE RECORD BASE CLASS (The "Magic")
# ============================================================================


class MagicRecord:
    """
    Base class attempting to mimic Laravel's Eloquent Active Record pattern.

    DESIGN PROBLEMS:
    1. Hidden dependency on _session_context (breaks testability)
    2. No type hints for session (IDE can't autocomplete)
    3. Requires middleware setup (fails in CLI/background jobs)
    4. Difficult to reason about transaction boundaries

    WHAT IT TRIES TO DO:
    Make database operations look like:
        user = await User.create(name="John")
        await user.save()

    WHY IT'S PROBLEMATIC:
    - Where's the session? (Hidden!)
    - What if we're outside a request? (Crash!)
    - How do we mock this in tests? (Painful!)
    """

    @classmethod
    @property
    def session(cls) -> AsyncSession:
        """
        Get current request's database session from ContextVar.

        Problem: @property + @classmethod doesn't work as expected.
        This should be a method, not a property, but we're trying
        to make the syntax prettier at the cost of correctness.
        """
        session = _session_context.get()
        if session is None:
            raise RuntimeError(
                "🚨 No database session in context!\n"
                "You're probably:\n"
                "1. Outside an HTTP request (CLI script?)\n"
                "2. In a background job without context\n"
                "3. Forgot to setup middleware\n"
            )
        return session

    @classmethod
    async def create(cls, **kwargs):
        """
        Create and persist a new record.

        LOOKS CLEAN:
            user = await User.create(name="John", email="john@example.com")

        ACTUALLY DOES:
            1. Get session from ContextVar (magic!)
            2. Create instance
            3. Add to session
            4. Commit (potential issue if you wanted a transaction!)
            5. Refresh to get DB-generated values

        PROBLEMS:
        - Auto-commit breaks transaction control
        - No way to batch multiple creates in one transaction
        - If commit fails, hard to rollback
        """
        session = cls.session.fget(cls)  # Ugly workaround for @property issue

        instance = cls(**kwargs)
        session.add(instance)

        # Auto-commit (🚨 This can be dangerous!)
        await session.commit()
        await session.refresh(instance)

        return instance

    @classmethod
    async def find(cls, id: int):
        """
        Find record by primary key.

        LOOKS CLEAN:
            user = await User.find(42)

        PROBLEMS:
        - Hides the query (harder to optimize)
        - No way to eager load relationships
        - Type checker can't verify return type properly
        """
        session = cls.session.fget(cls)

        stmt = select(cls).where(cls.id == id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def save(self):
        """
        Save changes to existing record.

        PROBLEMS:
        - Mutates global session state
        - Auto-commit breaks transaction atomicity
        - No way to save multiple models in one transaction
        """
        session = self.session.fget(self.__class__)

        session.add(self)
        await session.commit()


# ============================================================================
# 3. CONCRETE MODEL (The Pretty Syntax)
# ============================================================================

Base = declarative_base(cls=MagicRecord)


class User(Base):
    """
    User model with Active Record pattern.

    DEVELOPER EXPERIENCE:
    Looks beautiful! Just like Laravel:
        user = await User.create(name="Alice")
        user.name = "Alicia"
        await user.save()

    REALITY:
    - Hidden session dependency
    - Hard to test (need to mock ContextVar)
    - Breaks in non-HTTP contexts
    - Type safety issues
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)


# ============================================================================
# 4. MIDDLEWARE SIMULATION (The Required Plumbing)
# ============================================================================

# Database setup
engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def middleware_simulator(request_name: str, handler):
    """
    Simulates FastAPI middleware that injects session into ContextVar.

    THIS IS REQUIRED for the Active Record pattern to work.
    Forget to add this middleware? Everything breaks.

    In real FastAPI:
        @app.middleware("http")
        async def db_session_middleware(request, call_next):
            async with AsyncSessionLocal() as session:
                token = _session_context.set(session)
                try:
                    response = await call_next(request)
                finally:
                    _session_context.reset(token)
            return response
    """
    async with AsyncSessionLocal() as session:
        # Inject session into ContextVar
        token = _session_context.set(session)

        try:
            print(f"🔄 [Middleware] Starting request: {request_name}")
            await handler()
            print("✅ [Middleware] Request completed")
        finally:
            # CRITICAL: Always reset context
            # Forgetting this = memory leak
            _session_context.reset(token)


# ============================================================================
# 5. USAGE EXAMPLES (The Good and The Bad)
# ============================================================================


async def happy_path_controller():
    """
    Scenario 1: Everything works (inside middleware context).

    This is the "demo" code that makes Active Record look amazing.
    """
    print("\n   Creating user...")
    user = await User.create(name="Anderson Neo", email="neo@matrix.com")
    print(f"   ✅ Created: {user.name} (ID: {user.id})")

    print("\n   Finding user...")
    found = await User.find(user.id)
    print(f"   🔎 Found: {found.email}")

    print("\n   Updating user...")
    found.name = "Neo Anderson"
    await found.save()
    print(f"   ✅ Updated: {found.name}")


async def broken_path_cli_script():
    """
    Scenario 2: CLI script (NO middleware context).

    This is what happens when you try to use Active Record
    outside of an HTTP request. It breaks.

    Real-world cases:
    - Database migration scripts
    - Background jobs
    - CLI commands
    - Unit tests (without fixture setup)
    """
    print("\n   Attempting to create user from CLI script...")
    try:
        user = await User.create(name="Smith")
        print(f"   ✅ Created: {user.name}")
    except RuntimeError as e:
        print(f"   💥 BOOM: {e}")


async def transaction_problem():
    """
    Scenario 3: Transaction control issues.

    Problem: Each save() auto-commits. You can't do:
        user.name = "Alice"
        post.author_id = user.id
        await user.save()  # Commits!
        await post.save()  # Separate commit!

    If second save fails, first is already committed.
    No atomicity!
    """
    print("\n   Creating user and post in 'transaction'...")

    user = await User.create(name="Alice")
    print("   ✅ User created (already committed!)")

    # Imagine post creation fails here
    # User is already in database - can't rollback!
    print("   ⚠️  If next operation fails, user is orphaned in DB")


# ============================================================================
# 6. THE CORRECT WAY (For Comparison)
# ============================================================================


async def explicit_di_controller(session: AsyncSession):
    """
    The "boring but correct" way using explicit dependency injection.

    ADVANTAGES:
    - Session is explicit parameter (testable!)
    - Type checker knows session type
    - Works in ANY context (HTTP, CLI, tests)
    - Full transaction control

    DISADVANTAGES:
    - More verbose (need to pass session around)
    - Less "magical"

    VERDICT: Verbose > Broken
    """
    print("\n   Creating user (explicit DI)...")

    user = User(name="Trinity", email="trinity@matrix.com")
    session.add(user)

    # We control when to commit
    await session.commit()
    await session.refresh(user)

    print(f"   ✅ Created: {user.name} (ID: {user.id})")

    # Full transaction control
    async with session.begin():
        user.name = "Trinity Anderson"
        # Can add multiple operations here
        # All or nothing!

    print(f"   ✅ Updated in transaction: {user.name}")


# ============================================================================
# 7. DEMO RUNNER
# ============================================================================


async def main():
    """Run all scenarios to see the pattern's limitations."""

    # Setup database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("=" * 70)
    print("🎭 Active Record Pattern Demo (Educational Failure)")
    print("=" * 70)

    # Scenario 1: Happy path (looks great!)
    print("\n" + "=" * 70)
    print("SCENARIO 1: Happy Path (Inside Middleware)")
    print("=" * 70)
    await middleware_simulator("POST /users", happy_path_controller)

    # Scenario 2: Broken path (reality check!)
    print("\n" + "=" * 70)
    print("SCENARIO 2: CLI Script (No Middleware)")
    print("=" * 70)
    await broken_path_cli_script()

    # Scenario 3: Transaction issues
    print("\n" + "=" * 70)
    print("SCENARIO 3: Transaction Control Problems")
    print("=" * 70)
    await middleware_simulator("POST /users", transaction_problem)

    # Scenario 4: The correct way
    print("\n" + "=" * 70)
    print("SCENARIO 4: Explicit DI (The Right Way)")
    print("=" * 70)
    async with AsyncSessionLocal() as session:
        await explicit_di_controller(session)

    print("\n" + "=" * 70)
    print("🎓 KEY TAKEAWAYS")
    print("=" * 70)
    print(
        """
1. Active Record pattern was designed for SYNCHRONOUS ORMs
2. Async adds hidden complexity (ContextVars, session management)
3. "Magic" syntax trades testability for convenience
4. Explicit dependency injection is verbose but reliable
5. SQLModel/Repository pattern is the pragmatic middle ground

RECOMMENDATION:
Use SQLModel with explicit session injection:
    async def create_user(session: AsyncSession, data: UserCreate) -> User:
        user = User(**data.dict())
        session.add(user)
        await session.commit()
        return user

It's 2 more lines of code, but:
- Works in ANY context
- Fully testable
- Type-safe
- Transaction-safe
"""
    )


if __name__ == "__main__":
    asyncio.run(main())
