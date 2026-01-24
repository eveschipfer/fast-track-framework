"""
Sprint 1.2: IoC Container Demo
==============================

Educational demonstrations of the Dependency Injection container.

This file contains:
- Demo service classes (Database, UserService, etc.)
- Demo functions showing various DI scenarios
- Examples of singleton, transient, and scoped lifetimes

Run this file to see the IoC container in action:
    python src/ftf/exercises/sprint_1_2_demo.py
"""


from ftf.core import CircularDependencyError, Container, DependencyResolutionError

# ============================================================================
# DEMO SERVICES (Example Domain Model)
# ============================================================================


class Database:
    """
    Simulates database connection.
    Should be singleton to prevent connection pool exhaustion.
    """

    def __init__(self):
        self.connection_id = id(self)
        print(f"   🔌 Database connected (id: {self.connection_id})")

    def connect(self) -> str:
        return f"Connected to PGSQL (conn_id: {self.connection_id})"


class CacheService:
    """
    Simulates cache service (Redis, Memcached, etc).
    Also should be singleton.
    """

    def __init__(self):
        self.cache_id = id(self)
        print(f"   💾 Cache initialized (id: {self.cache_id})")

    def get(self, key: str) -> str | None:
        return None


class UserRepository:
    """
    Repository with single dependency (Database).
    """

    def __init__(self, db: Database):
        self.db = db
        print(f"   📦 UserRepository created with db {db.connection_id}")

    def get_users(self) -> str:
        return f"{self.db.connect()} → SELECT * FROM users"


class UserService:
    """
    Service with nested dependency (Service → Repo → DB).
    """

    def __init__(self, repo: UserRepository):
        self.repo = repo
        print("   ⚙️  UserService created")

    def list_active(self) -> str:
        return f"Filtering active: {self.repo.get_users()}"


class EmailService:
    """Service without dependencies."""

    def __init__(self):
        print("   📧 EmailService created")

    def send(self, to: str, body: str) -> str:
        return f"Email sent to {to}: {body}"


class NotificationService:
    """
    Complex service with multiple dependencies.
    Demonstrates parallel resolution.
    """

    def __init__(
        self, email: EmailService, user_service: UserService, cache: CacheService
    ):
        self.email = email
        self.user_service = user_service
        self.cache = cache
        print("   🔔 NotificationService created")

    def notify_all(self) -> str:
        users = self.user_service.list_active()
        email_result = self.email.send("admin@example.com", "Alert!")
        return f"{users} | {email_result}"


# ============================================================================
# DEMO FUNCTIONS
# ============================================================================


def demo_basic_resolution():
    """Demo 1: Basic dependency resolution."""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Resolution (No Dependencies)")
    print("=" * 70)

    container = Container()
    container.register(EmailService)

    service = container.resolve(EmailService)
    print(f"✅ Result: {service.send('test@example.com', 'Hello!')}")


def demo_nested_dependencies():
    """Demo 2: Nested dependency chain."""
    print("\n" + "=" * 70)
    print("DEMO 2: Nested Dependencies (Service → Repo → DB)")
    print("=" * 70)

    container = Container()
    container.register(Database, scope="singleton")
    container.register(UserRepository)
    container.register(UserService)

    print("\n⏳ Resolving UserService...")
    service = container.resolve(UserService)

    print(f"\n✅ Result: {service.list_active()}")


def demo_singleton_behavior():
    """Demo 3: Singleton returns same instance."""
    print("\n" + "=" * 70)
    print("DEMO 3: Singleton Behavior")
    print("=" * 70)

    container = Container()
    container.register(Database, scope="singleton")

    print("\n⏳ First resolve...")
    db1 = container.resolve(Database)

    print("\n⏳ Second resolve...")
    db2 = container.resolve(Database)

    print(f"\n✅ Same instance: {db1 is db2}")
    print(f"   Connection IDs: {db1.connection_id} == {db2.connection_id}")


def demo_transient_behavior():
    """Demo 4: Transient creates new instances."""
    print("\n" + "=" * 70)
    print("DEMO 4: Transient Behavior")
    print("=" * 70)

    container = Container()
    container.register(EmailService, scope="transient")

    print("\n⏳ First resolve...")
    svc1 = container.resolve(EmailService)

    print("\n⏳ Second resolve...")
    svc2 = container.resolve(EmailService)

    print(f"\n✅ Different instances: {svc1 is not svc2}")


def demo_multiple_dependencies():
    """Demo 5: Service with multiple dependencies."""
    print("\n" + "=" * 70)
    print("DEMO 5: Multiple Dependencies")
    print("=" * 70)

    container = Container()
    container.register(Database, scope="singleton")
    container.register(CacheService, scope="singleton")
    container.register(UserRepository)
    container.register(UserService)
    container.register(EmailService)
    container.register(NotificationService)

    print("\n⏳ Resolving NotificationService (complex dependency tree)...")
    notifier = container.resolve(NotificationService)

    print(f"\n✅ Result: {notifier.notify_all()}")


def demo_circular_dependency():
    """Demo 6: Circular dependency detection."""
    print("\n" + "=" * 70)
    print("DEMO 6: Circular Dependency Detection")
    print("=" * 70)

    # Create circular dependency
    # Note: In Python 3.14, forward references in function scope
    # raise DependencyResolutionError instead of CircularDependencyError
    class ServiceA:
        def __init__(self, b: "ServiceB"):
            self.b = b

    class ServiceB:
        def __init__(self, a: ServiceA):
            self.a = a

    container = Container()
    container.register(ServiceA)
    container.register(ServiceB)

    print("\n⏳ Attempting to resolve ServiceA...")
    try:
        container.resolve(ServiceA)
        print("❌ Should have raised an error!")
    except (CircularDependencyError, DependencyResolutionError) as e:
        print(f"✅ Circular/forward reference error detected:\n   {e}")


def main():
    """Run all demos."""
    print("=" * 70)
    print("🚀 IoC Container - Demo Suite")
    print("=" * 70)

    demo_basic_resolution()
    demo_nested_dependencies()
    demo_singleton_behavior()
    demo_transient_behavior()
    demo_multiple_dependencies()
    demo_circular_dependency()

    print("\n" + "=" * 70)
    print("✅ All demos completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
