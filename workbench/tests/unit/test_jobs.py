"""
Job Queue Tests (Sprint 3.2)

This module tests the Job Queue system including Job, runner, and JobManager.

Test Coverage:
    - Job dispatch and serialization
    - runner function execution
    - IoC Container integration
    - Error handling for invalid job classes
    - Payload attribute setting
    - JobManager initialization

Educational Note:
    These tests demonstrate the "bridge pattern" - wrapping SAQ's function-based
    API with a class-based API that supports Dependency Injection.
"""

import pytest
from redis.asyncio import Redis

from jtc.core import Container
from jtc.jobs import Job, JobManager, get_container, runner, set_container

# ============================================================================
# TEST JOBS
# ============================================================================


class SimpleJob(Job):
    """Simple test job without dependencies."""

    def __init__(self) -> None:
        self.executed = False
        self.user_id: int = 0
        self.email: str = ""

    async def handle(self) -> None:
        """Execute the job."""
        self.executed = True


class JobWithDependency(Job):
    """Test job with dependency injection."""

    def __init__(self, dependency: str):
        self.dependency = dependency
        self.executed = False
        self.data: str = ""

    async def handle(self) -> None:
        """Execute with dependency."""
        self.executed = True


class FailingJob(Job):
    """Test job that always fails."""

    async def handle(self) -> None:
        """Raise an error."""
        raise ValueError("Intentional failure for testing")


# ============================================================================
# PYTEST FIXTURES
# ============================================================================


@pytest.fixture
def container() -> Container:
    """Create a fresh IoC Container for each test."""
    return Container()


@pytest.fixture
async def redis_connection() -> Redis:
    """Create a Redis connection for testing."""
    redis = Redis(host="localhost", port=6379, decode_responses=True, db=1)
    # Clear test database
    await redis.flushdb()
    yield redis
    # Cleanup
    await redis.flushdb()
    await redis.aclose()


@pytest.fixture
def setup_job_manager(redis_connection: Redis) -> None:
    """Initialize JobManager with test Redis."""
    JobManager.initialize("redis://localhost:6379/1")


# ============================================================================
# CONTAINER MANAGEMENT TESTS
# ============================================================================


def test_set_and_get_container(container: Container) -> None:
    """Test that we can set and get the global container."""
    set_container(container)
    retrieved = get_container()
    assert retrieved is container


def test_get_container_without_set_raises_error() -> None:
    """Test that getting container before setting raises error."""
    set_container(None)  # type: ignore
    with pytest.raises(RuntimeError, match="Container not set"):
        get_container()


# ============================================================================
# JOB MANAGER TESTS
# ============================================================================


def test_job_manager_initialize() -> None:
    """Test that JobManager can be initialized."""
    JobManager.initialize("redis://localhost:6379/1")
    queue = JobManager.get_queue()
    assert queue is not None
    assert queue.name == "default"


def test_job_manager_get_queue_before_initialize_raises_error() -> None:
    """Test that getting queue before initialization raises error."""
    # Reset JobManager state
    JobManager._queue = None
    JobManager._redis = None

    with pytest.raises(RuntimeError, match="JobManager not initialized"):
        JobManager.get_queue()


def test_job_manager_get_redis() -> None:
    """Test that we can get the Redis connection."""
    JobManager.initialize("redis://localhost:6379/1")
    redis = JobManager.get_redis()
    assert redis is not None


@pytest.mark.asyncio
async def test_job_manager_close() -> None:
    """Test that JobManager can be closed."""
    JobManager.initialize("redis://localhost:6379/1")
    await JobManager.close()
    # After close, queue and redis should be None
    assert JobManager._queue is None
    assert JobManager._redis is None


# ============================================================================
# JOB DISPATCH TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires Redis server running")
async def test_job_dispatch_enqueues_to_queue(
    container: Container, setup_job_manager: None
) -> None:
    """Test that Job.dispatch() enqueues the job to SAQ."""
    set_container(container)
    container.register(SimpleJob)

    # Dispatch the job
    await SimpleJob.dispatch(user_id=123, email="test@example.com")

    # Verify it was enqueued
    queue = JobManager.get_queue()
    stats = await queue.stats()
    assert stats["queued"] == 1  # One job in queue


# ============================================================================
# RUNNER FUNCTION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_runner_executes_job_successfully(container: Container) -> None:
    """Test that runner can execute a simple job."""
    set_container(container)
    container.register(SimpleJob, scope="singleton")

    # Simulate SAQ calling the runner
    ctx = {"queue": None, "job": None}
    await runner(
        ctx,
        job_class="workbench.tests.unit.test_jobs.SimpleJob",
        payload={"user_id": 456, "email": "user@test.com"},
    )

    # Verify job was executed
    job_instance = container.resolve(SimpleJob)
    assert job_instance.executed is True
    assert job_instance.user_id == 456
    assert job_instance.email == "user@test.com"


@pytest.mark.asyncio
async def test_runner_with_dependency_injection(container: Container) -> None:
    """Test that runner resolves job with dependencies from container."""
    set_container(container)

    # Register dependency in container
    dependency_value = "injected value"
    container.register(str, implementation=lambda: dependency_value, scope="singleton")

    # Register job (will receive string dependency)
    container.register(JobWithDependency, scope="singleton")

    # Execute via runner
    ctx = {"queue": None, "job": None}
    await runner(
        ctx,
        job_class="workbench.tests.unit.test_jobs.JobWithDependency",
        payload={"data": "test data"},
    )

    # Verify job was executed with dependency
    job_instance = container.resolve(JobWithDependency)
    assert job_instance.executed is True
    assert job_instance.dependency == dependency_value
    assert job_instance.data == "test data"


@pytest.mark.asyncio
async def test_runner_raises_import_error_for_invalid_module(
    container: Container,
) -> None:
    """Test that runner raises ImportError for invalid module."""
    set_container(container)

    ctx = {"queue": None, "job": None}
    with pytest.raises(ImportError, match="Cannot import module"):
        await runner(
            ctx,
            job_class="invalid.module.InvalidJob",
            payload={},
        )


@pytest.mark.asyncio
async def test_runner_raises_attribute_error_for_invalid_class(
    container: Container,
) -> None:
    """Test that runner raises AttributeError for invalid class."""
    set_container(container)

    ctx = {"queue": None, "job": None}
    with pytest.raises(AttributeError, match="Class.*not found"):
        await runner(
            ctx,
            job_class="workbench.tests.unit.test_jobs.NonExistentJob",
            payload={},
        )


@pytest.mark.asyncio
async def test_runner_propagates_job_exceptions(container: Container) -> None:
    """Test that exceptions in job.handle() are propagated."""
    set_container(container)
    container.register(FailingJob)

    ctx = {"queue": None, "job": None}
    with pytest.raises(ValueError, match="Intentional failure"):
        await runner(
            ctx,
            job_class="workbench.tests.unit.test_jobs.FailingJob",
            payload={},
        )


# ============================================================================
# PAYLOAD ATTRIBUTE SETTING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_runner_sets_multiple_payload_attributes(container: Container) -> None:
    """Test that runner sets all payload attributes correctly."""
    set_container(container)
    container.register(SimpleJob, scope="singleton")

    ctx = {"queue": None, "job": None}
    await runner(
        ctx,
        job_class="workbench.tests.unit.test_jobs.SimpleJob",
        payload={
            "user_id": 999,
            "email": "multi@test.com",
        },
    )

    job_instance = container.resolve(SimpleJob)
    assert job_instance.user_id == 999
    assert job_instance.email == "multi@test.com"


@pytest.mark.asyncio
async def test_runner_with_empty_payload(container: Container) -> None:
    """Test that runner works with empty payload."""
    set_container(container)
    container.register(SimpleJob, scope="singleton")

    ctx = {"queue": None, "job": None}
    await runner(
        ctx,
        job_class="workbench.tests.unit.test_jobs.SimpleJob",
        payload={},
    )

    job_instance = container.resolve(SimpleJob)
    assert job_instance.executed is True
    # Attributes should have default values
    assert job_instance.user_id == 0
    assert job_instance.email == ""


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires Redis server running")
async def test_complete_job_flow(
    container: Container, setup_job_manager: None
) -> None:
    """Test complete flow: dispatch, enqueue, dequeue, execute."""
    set_container(container)
    container.register(SimpleJob, scope="singleton")

    # Dispatch the job
    await SimpleJob.dispatch(user_id=777, email="flow@test.com")

    # Get the job from queue
    queue = JobManager.get_queue()
    job = await queue.dequeue(timeout=1)

    assert job is not None
    # SAQ job has function name and kwargs
    assert job["function"] == "jtc.jobs.core.runner"
    assert job["kwargs"]["job_class"] == "tests.unit.test_jobs.SimpleJob"
    assert job["kwargs"]["payload"]["user_id"] == 777


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires Redis server running")
async def test_job_with_dependency_full_flow(
    container: Container, setup_job_manager: None
) -> None:
    """Test that jobs with dependencies work through full dispatch-execute flow."""
    set_container(container)

    # Setup dependency
    dependency_value = "test dependency"
    container.register(str, implementation=lambda: dependency_value, scope="singleton")
    container.register(JobWithDependency, scope="singleton")

    # Dispatch
    await JobWithDependency.dispatch(data="test payload")

    # Dequeue and execute manually (simulating worker)
    queue = JobManager.get_queue()
    job = await queue.dequeue(timeout=1)

    assert job is not None

    # Execute the job
    ctx = {"queue": queue, "job": job}
    await runner(
        ctx,
        job_class=job["kwargs"]["job_class"],
        payload=job["kwargs"]["payload"],
    )

    # Verify execution
    job_instance = container.resolve(JobWithDependency)
    assert job_instance.executed is True
    assert job_instance.dependency == dependency_value
    assert job_instance.data == "test payload"
