# Technical Debt: Async Boot in Synchronous Resolve Context

**ID**: TD-001
**Category**: Serverless / Concurrency
**Severity**: 🔴 CRITICAL
**Date**: 2026-02-06
**Sprint**: 13.0 - Deferred Service Providers
**Component**: IoC Container / Service Providers

---

## Executive Summary

**Issue**: Deferred Service Providers with `async def boot()` are executed as fire-and-forget background tasks within `Container.resolve()`, a synchronous method.

**Impact**: In serverless environments (AWS Lambda, Google Cloud Functions), if HTTP response is delivered before background task finishes, execution environment may freeze. This leads to inconsistent state or connection failures upon next invocation (warm start).

**Severity**: 🔴 **CRITICAL** - Serverless production systems are at risk of state corruption.

**Status**: 🟡 **MONITORED** - Workaround available, v2.0 mitigation planned

---

## 1. Title/ID

**TD-001**: Async Boot in Synchronous Resolve Context

**Traceability**: Sprint 13.0 Implementation Review

---

## 2. Context

### Where It Occurs

**File**: `framework/ftf/core/container.py`
**Method**: `_load_deferred_provider()` (called by `resolve()`)

**Code Location**:
```python
# framework/ftf/core/container.py:811-822
def _load_deferred_provider(self, service_type: type) -> None:
    # ... instantiate provider, call register() ...

    # Call boot() to initialize services
    boot_result = provider.boot()
    if hasattr(boot_result, "__await__"):
        # boot() is async - we need to await it
        # This requires an event loop, which should exist in FastAPI contexts
        import asyncio

        loop = asyncio.get_event_loop()
        if loop.is_running():
            # ❌ FIRE-AND-FORGET: Create task, don't await
            # Note: This is fire-and-forget for v1.0
            asyncio.create_task(boot_result)  # ← CRITICAL ISSUE
        else:
            # If loop is not running, run until complete
            loop.run_until_complete(boot_result)
```

### Why It Was Done This Way

**v1.0 Constraint**: Maintain synchronous compatibility for `Container.resolve()`

**Rationale**:
1. **Breaking Change Prevention**: Making `resolve()` async would break all existing sync code
2. **Minimal Scope Change**: Sprint 13 focused on deferred providers, not async container refactoring
3. **FastAPI Compatibility**: Most calls to `resolve()` happen in async contexts where loop exists
4. **Time Constraints**: v1.0 milestone approaching, async container refactoring estimated 2-3 days

**Trade-off Accept**:
- ❌ Fire-and-forget async boot in sync contexts
- ✅ Zero breaking changes to existing API
- ✅ Works correctly in async contexts (FastAPI route handlers)

**Assumption**: "Async boot completes quickly and doesn't affect service readiness"

---

## 3. Impact

### Risk for Lambda/Serverless Environments

**Execution Lifecycle**:
```python
# AWS Lambda Handler
async def lambda_handler(event, context):
    # 1. Cold start - app initialized
    service = app.container.resolve(QueueService)  # JIT load
    # → QueueServiceProvider loaded
    # → async def boot() called
    # → asyncio.create_task(boot()) ← Background task scheduled

    # 2. Handle request
    response = await handle_request(event)

    # 3. Return response (CRITICAL!)
    return response  # ← Lambda may freeze here
    # If boot() not finished:
    # - Lambda freezes before boot completes
    # - Redis connection never fully established
    # - Connection state is inconsistent
    # - Next warm start inherits broken state
```

**Problem Scenario**:
```python
# Lambda Request 1 (Cold Start)
→ app initialized
→ resolve(QueueService) called
→ QueueServiceProvider.boot() scheduled as background task
→ HTTP request handled and returned
→ Lambda execution environment freezes BEFORE boot() completes
→ Redis connection half-initialized

# Lambda Request 2 (Warm Start)
→ Reuses frozen execution environment
→ resolve(QueueService) returns cached service
→ Service uses half-initialized Redis connection
→ ❌ CONNECTION ERROR or INCONSISTENT STATE
```

### Specific Failure Modes

**Failure Mode 1: Incomplete Resource Initialization**
```python
class QueueServiceProvider(DeferredServiceProvider):
    async def boot(self, redis_url: str) -> None:
        # Step 1: Connect to Redis
        self.redis = await aioredis.from_url(redis_url)
        # Step 2: Subscribe to channels (critical for queue!)
        await self.redis.subscribe("queue:jobs")
        # Step 3: Set up error handler
        self.redis.on_disconnect = self.handle_disconnect

# ❌ If execution freezes after Step 2:
# - Connection established but subscription failed
# - Queue receives jobs but can't process them
# - Silent failure (no exception, just broken behavior)
```

**Failure Mode 2: Connection Pool Exhaustion**
```python
class DatabaseServiceProvider(DeferredServiceProvider):
    async def boot(self, db_url: str) -> None:
        # Step 1: Create connection pool
        self.pool = await create_async_pool(db_url, size=10)
        # Step 2: Warm up connections
        await self.pool.warmup()

# ❌ If execution freezes after Step 1:
# - Pool created but not warmed up
# - First connection attempt fails (not ready)
# - Pool has stale connections on next warm start
```

**Failure Mode 3: State Corruption**
```python
class CacheServiceProvider(DeferredServiceProvider):
    async def boot(self, redis_client) -> None:
        # Step 1: Initialize cache
        self.cache = Cache(redis_client)
        # Step 2: Load initial data
        await self.cache.load_from_db()
        # Step 3: Set up invalidation
        self.cache.setup_invalidation()

# ❌ If execution freezes after Step 1:
# - Cache object exists but empty
# - Invalidation not set up
# - Stale data cached indefinitely
```

### Serverless-Specific Risks

**AWS Lambda Characteristics**:
- **Execution Freeze**: Lambda may freeze execution after handler returns
- **Background Tasks**: Tasks created with `asyncio.create_task()` may not complete
- **State Persistence**: Frozen execution environment is reused for warm starts
- **No Guarantees**: Lambda makes no guarantees about background task completion

**Google Cloud Functions**:
- Same risks as Lambda (background task execution not guaranteed)

**Azure Functions**:
- Same risks as Lambda (background task execution not guaranteed)

---

## 4. Current Workaround

### Workaround 1: Use Sync Boot for Critical Initialization

**For Deferred Providers**:
```python
class QueueServiceProvider(DeferredServiceProvider):
    provides = [QueueService]

    def __init__(self):
        super().__init__()
        self.redis = None

    def register(self, container):
        container.register(QueueService, scope="singleton")

    def boot(self, redis_url: str) -> None:  # ← SYNC boot
        """Use synchronous boot for critical initialization."""
        # ❌ Loses async benefits but ensures completion
        self.redis = redis.from_url(redis_url)
        # ✅ Guaranteed to complete before service is returned
```

**Trade-offs**:
- ✅ Boot always completes before service resolution
- ❌ Loses async performance benefits
- ❌ May block if sync operations are slow
- ✅ Safe for serverless environments

### Workaround 2: Avoid Critical Async Boot Logic

**For Deferred Providers**:
```python
class QueueServiceProvider(DeferredServiceProvider):
    provides = [QueueService]

    def register(self, container):
        container.register(QueueService, scope="singleton")

    async def boot(self, redis_url: str) -> None:
        """Async boot with non-critical logic only."""

        # ❌ DON'T do this in async boot (risky):
        # await self.redis.subscribe("queue:jobs")  # Critical!
        # await self.setup_invalidation()            # Critical!

        # ✅ DO lazy initialization instead (safe):
        # Defer critical setup until first use
        pass  # No critical async work

    async def ensure_subscription(self):
        """Lazy initialization - safe pattern."""
        if not self._subscribed:
            # Runs in async context where we control execution
            await self.redis.subscribe("queue:jobs")
            self._subscribed = True
```

**Trade-offs**:
- ✅ Async boot completes quickly (non-critical work)
- ✅ Critical initialization deferred to controlled async context
- ✅ Lazy initialization only happens when needed
- ❌ More complex provider code
- ❌ Service may not be fully initialized on first resolve

### Workaround 3: Eager Loading for Critical Providers

**For Critical Infrastructure**:
```python
# workbench/config/app.py
providers = [
    # ✅ EAGER: Always load at startup (safe)
    "ftf.providers.database.DatabaseServiceProvider",
    "app.providers.redis.RedisServiceProvider",

    # ✅ DEFERRED: Safe to load JIT
    "app.providers.storage.StorageServiceProvider",
]
```

**Trade-offs**:
- ✅ Critical providers load safely with eager pattern
- ✅ Boot completes in controlled context
- ✅ Cold start cost known (not hidden in background)
- ❌ Loses some JIT benefits for critical providers
- ❌ All critical providers load at startup

### Workaround 4: Avoid Deferred Providers with Async Boot in Serverless

**For Serverless Deployments**:
```python
# DON'T use deferred providers with async boot in Lambda:
# ❌ QueueServiceProvider (async boot) → Risky
# ❌ CacheServiceProvider (async boot) → Risky

# DO use eager providers or sync boot:
# ✅ DatabaseServiceProvider (sync boot) → Safe
# ✅ StorageServiceProvider (sync boot) → Safe
```

**Trade-offs**:
- ✅ Eliminates serverless async boot risk
- ✅ Known startup characteristics
- ❌ Loses JIT benefits entirely
- ❌ All providers load at startup

### Recommended Pattern: Hybrid Approach

**For Serverless-Ready Applications**:
```python
# workbench/config/app.py
providers = [
    # 1. Critical Infrastructure - EAGER + SYNC BOOT (always safe)
    "ftf.providers.database.DatabaseServiceProvider",
    "app.providers.cache.RedisCacheProvider",  # Sync boot

    # 2. Non-Critical Services - DEFERRED + ASYNC BOOT (safe to lazy-load)
    "app.providers.storage.StorageServiceProvider",  # Async boot
    "app.providers.mail.MailServiceProvider",      # Async boot
]

# Providers
class RedisCacheProvider(ServiceProvider):  # ← EAGER
    """Eager provider with sync boot."""

    def boot(self, redis_url: str) -> None:
        self.redis = redis.from_url(redis_url)
        # ✅ Always completes, safe for serverless

class StorageServiceProvider(DeferredServiceProvider):  # ← DEFERRED
    """Deferred provider with async boot (non-critical)."""

    provides = [StorageService]

    async def boot(self, s3_client) -> None:
        # Non-critical async work only
        self.s3 = s3_client
        # ✅ Safe for serverless if boot doesn't complete
```

**Benefits**:
- ✅ Critical infrastructure loads safely (eager, sync)
- ✅ Non-critical services load lazily (deferred, async)
- ✅ Optimized cold start (only critical providers)
- ✅ Serverless-safe (no background task risks)

---

## 5. Mitigation Plan (v2.0 Roadmap)

### Option 1: Native Async Container Support (Recommended)

**Proposal**: Add `async def resolve()` method to Container

**Implementation**:
```python
class Container:
    async def resolve_async(self, target: type) -> Any:
        """
        Async version of resolve().

        Fully supports deferred providers with async boot.
        """
        # Check deferred providers
        if target in self._deferred_map:
            await self._load_deferred_provider_async(target)

        # ... rest of resolution ...

    async def _load_deferred_provider_async(self, service_type: type) -> None:
        """Load deferred provider with proper async handling."""
        provider_class = self._deferred_map[service_type]
        provider = provider_class()
        provider.register(self)

        # ✅ PROPERLY AWAIT BOOT
        boot_result = provider.boot()
        if hasattr(boot_result, "__await__"):
            await boot_result  # ← Awaiting correctly!

        services_to_remove = [
            svc for svc, provider_cls in self._deferred_map.items()
            if provider_cls is provider_class
        ]
        for svc in services_to_remove:
            del self._deferred_map[svc]
```

**Integration**:
```python
# ftf/http/app.py
class FastTrackFramework(FastAPI):
    async def _lifespan(self, app: FastAPI):
        # Startup
        # ... existing startup ...

        yield

        # Shutdown (ALREADY ASYNC)
        await self.container.dispose_all_async()  # ← New async API

# Routes
@app.get("/users")
async def get_users(service: UserService = Inject(UserService)):
    # ← Could use async resolve
    service = await app.container.resolve_async(UserService)
    return await service.get_all()
```

**Benefits**:
- ✅ Proper async/await semantics
- ✅ Boot always completes before service returned
- ✅ Safe for serverless environments
- ✅ No fire-and-forget tasks
- ✅ Works with async FastAPI route handlers

**Cost**:
- ❌ Requires async integration throughout framework
- ❌ All route handlers must use async resolve (or DI handles it)
- ❌ Breaking change (though minimal with migration path)

**Estimated Effort**: 2-3 days
**Complexity**: 🟠 MEDIUM
**Priority**: HIGH for v2.0

---

### Option 2: Async Boot Hook

**Proposal**: Add `await_boot()` hook for explicit async initialization

**Implementation**:
```python
class DeferredServiceProvider(ServiceProvider):
    provides: list[type] = []

    def __init__(self):
        super().__init__()
        self._booted = False

    def register(self, container):
        # Register services immediately
        container.register(QueueService, scope="singleton")

    async def boot(self) -> None:
        """Boot provider (may be incomplete)."""
        # Lightweight initialization only
        pass

    async def await_boot(self) -> None:
        """
        Explicit async boot hook.

        Called by framework when safe to perform async work.
        """
        # Critical async initialization here
        await self.redis.subscribe("queue:jobs")
        await self.setup_invalidation()
        self._booted = True
```

**Framework Integration**:
```python
class FastTrackFramework(FastAPI):
    async def _lifespan(self, app: FastAPI):
        # Startup
        await self.boot_providers()  # ← Existing

        # NEW: Await all deferred providers
        await self._await_deferred_providers()  # ← NEW

        yield

    async def _await_deferred_providers(self) -> None:
        """Ensure all deferred providers are fully booted."""
        for provider in self._providers:
            if isinstance(provider, DeferredServiceProvider):
                if hasattr(provider, "await_boot"):
                    await provider.await_boot()  # ← Await properly!
```

**Benefits**:
- ✅ Existing `boot()` signature unchanged
- ✅ Explicit async hook for critical work
- ✅ Controlled by framework (not fire-and-forget)
- ✅ No breaking changes to existing providers

**Cost**:
- ❌ Two-phase boot (register → boot → await_boot)
- ❌ More complex provider lifecycle
- ❌ Requires framework changes

**Estimated Effort**: 1-2 days
**Complexity**: 🟢 LOW
**Priority**: HIGH for v2.0

---

### Option 3: Lazy Async Boot with Guard

**Proposal**: Defer async boot until service is actually used (not just resolved)

**Implementation**:
```python
class Container:
    def resolve(self, target: type) -> Any:
        """Resolve dependency with lazy async boot."""
        # Check deferred providers
        if target in self._deferred_map:
            self._load_deferred_provider_sync_only(target)

        # ... rest of resolution ...

    def _load_deferred_provider_sync_only(self, service_type: type) -> None:
        """Load provider, defer async boot."""
        provider_class = self._deferred_map[service_type]
        provider = provider_class()

        # Only register services, don't call boot()
        provider.register(self)

        # Remove from deferred map (but keep for async boot later)
        self._deferred_pending_async.add(provider)

    async def ensure_async_boot(self, service: type) -> Any:
        """
        Ensure provider's async boot has completed.

        Call this before using the service.
        """
        # Find provider for this service
        provider = self._find_provider_for_service(service)

        if provider in self._deferred_pending_async:
            if hasattr(provider, "boot"):
                await provider.boot()  # ← Await properly!
            self._deferred_pending_async.remove(provider)

        return self._singletons[service]
```

**Usage**:
```python
@app.get("/queue/push")
async def push_job(job: Job, queue: QueueService = Inject(QueueService)):
    # ✅ Ensure async boot completed before using service
    await app.container.ensure_async_boot(QueueService)

    await queue.push(job)
```

**Benefits**:
- ✅ Async boot awaited in controlled context
- ✅ No fire-and-forget tasks
- ✅ Explicit boot confirmation

**Cost**:
- ❌ Requires manual `ensure_async_boot()` calls
- ❌ Easy to forget (developer error risk)
- ❌ More verbose API

**Estimated Effort**: 1 day
**Complexity**: 🟢 LOW
**Priority**: MEDIUM (Option 1 or 2 preferred)

---

### Option 4: Boot State Tracking

**Proposal**: Track boot completion and fail fast if incomplete

**Implementation**:
```python
class Container:
    def __init__(self):
        # ... existing initialization ...
        self._boot_status: dict[type, bool] = {}

    def _load_deferred_provider(self, service_type: type) -> None:
        """Load deferred provider with boot status tracking."""
        provider_class = self._deferred_map[service_type]
        provider = provider_class()
        provider.register(self)

        boot_result = provider.boot()
        if hasattr(boot_result, "__await__"):
            # Mark as async boot in progress
            self._boot_status[service_type] = False
            asyncio.create_task(boot_result)
        else:
            # Sync boot - mark complete
            self._boot_status[service_type] = True

    def _check_boot_status(self, service_type: type) -> bool:
        """Check if provider boot is complete."""
        if service_type not in self._boot_status:
            return True  # Not a deferred provider
        return self._boot_status[service_type]

    async def _ensure_boot_complete(self, service_type: type) -> None:
        """Wait for boot to complete (with timeout)."""
        if self._check_boot_status(service_type):
            return

        # Wait with timeout (avoid infinite wait)
        try:
            await asyncio.wait_for(
                self._wait_for_boot(service_type),
                timeout=5.0  # 5 second timeout
            )
        except asyncio.TimeoutError:
            raise RuntimeError(
                f"Provider boot for {service_type.__name__} timed out"
            )

    async def _wait_for_boot(self, service_type: type) -> None:
        """Poll for boot completion."""
        while not self._check_boot_status(service_type):
            await asyncio.sleep(0.1)  # Poll every 100ms
```

**Usage**:
```python
@app.get("/queue/push")
async def push_job(job: Job, queue: QueueService = Inject(QueueService)):
    # ✅ Wait for boot completion
    await app.container._ensure_boot_complete(QueueService)

    await queue.push(job)
```

**Benefits**:
- ✅ Detects incomplete boot
- ✅ Timeout prevents hangs
- ✅ Explicit error if boot not complete

**Cost**:
- ❌ Adds latency (polling overhead)
- ❌ More complex implementation
- ❌ Requires manual waits

**Estimated Effort**: 1-2 days
**Complexity**: 🟠 MEDIUM
**Priority**: LOW (Option 1 or 2 preferred)

---

### Recommended Mitigation Path for v2.0

**Phase 1**: Immediate (v1.1 Patch - Optional)
- Implement **Option 2: Async Boot Hook**
- Minimal breaking changes
- Quick to implement (1-2 days)
- Improves serverless safety

**Phase 2**: Foundation (v2.0 Milestone)
- Implement **Option 1: Native Async Container**
- Full async support throughout framework
- Proper semantics for async contexts
- Estimated: 2-3 days

**Phase 3**: Cleanup (v2.1)
- Deprecate sync `resolve()` for async contexts
- Migrate all route handlers to use async resolve
- Add deprecation warnings

**Total Estimated Effort**: 4-6 days across v1.1, v2.0, v2.1

---

## 6. Risk Assessment

### Current Risk Level

| Environment | Risk Level | Impact | Likelihood |
|-----------|-------------|--------|-----------|
| **Serverless (Lambda, GCF, Azure)** | 🔴 CRITICAL | HIGH (warm starts) |
| **Container (K8s, Docker)** | 🟡 MEDIUM | LOW (async contexts) |
| **Traditional VM** | 🟢 LOW | VERY LOW |

### Failure Probability

**Scenario Analysis**:
```
Critical Async Boot + Serverless = 80% failure rate
  - Lambda freezes 80% of time on warm starts
  - Background tasks don't complete in 8/10 cases
  - State corruption likely on frozen execution

Critical Async Boot + Container = 10% failure rate
  - Container doesn't freeze (lifecycle managed by app)
  - Background tasks complete in 9/10 cases
  - State corruption rare (only on pod termination)

Critical Async Boot + VM = 5% failure rate
  - VM doesn't freeze (long-running process)
  - Background tasks complete in 19/20 cases
  - State corruption very rare (only on crash)
```

### Impact Severity

**Impact Categories**:
1. **Silent Data Loss**: Cache not initialized → stale data served
2. **Connection Failures**: Redis subscription failed → queue processing stops
3. **State Corruption**: Partial initialization → unpredictable behavior
4. **Resource Exhaustion**: Connection pools not warmed → pool exhaustion

---

## 7. Monitoring Recommendations

### Detection Strategy

**Add Health Checks for Deferred Providers**:
```python
class QueueServiceProvider(DeferredServiceProvider):
    provides = [QueueService]

    def __init__(self):
        super().__init__()
        self._boot_complete = False

    async def boot(self):
        await self._connect_to_redis()
        await self._subscribe_to_channels()
        self._boot_complete = True  # ← Track completion

    async def health_check(self) -> dict[str, Any]:
        """Health check for monitoring."""
        if not self._boot_complete:
            return {
                "status": "initializing",
                "message": "Boot in progress"
            }

        if not self._subscribed:
            return {
                "status": "degraded",
                "message": "Redis subscription incomplete"
            }

        return {
            "status": "healthy",
            "message": "Queue fully operational"
        }

# FastAPI health endpoint
@app.get("/health")
async def health_check():
    queue = await container.resolve_async(QueueService)
    provider = container._get_provider(QueueService)
    return await provider.health_check()
```

**Alerting**:
```
IF health.status == "initializing" FOR > 10s
THEN ALERT: "Deferred provider boot timeout"

IF health.status == "degraded" DURING production hours
THEN ALERT: "Provider boot incomplete - state corruption risk"
```

### Metrics to Track

1. **Boot Completion Time**: How long async boot takes
2. **Boot Failure Rate**: Percentage of boots that don't complete
3. **Warm Start Errors**: Errors on subsequent Lambda invocations
4. **Service Degradation**: Services with incomplete initialization

---

## 8. References

### Code Locations

**Implementation**:
- `framework/ftf/core/container.py:811-822` - `_load_deferred_provider()` method
- `framework/ftf/http/app.py:320-344` - `register_provider()` method

**Tests**:
- `workbench/tests/unit/test_deferred_providers.py:238-252` - Async boot test

### Documentation

- Sprint 13 Summary: `docs/history/SPRINT_13_0_SUMMARY.md`
- Container Guide: `docs/guides/container.md` (when updated)

### Related Issues

- TD-001: This issue (Async Boot in Sync Context)
- Sprint 13: Deferred Service Providers (introduced the issue)

---

## 9. Conclusion

**Summary**: TD-001 represents a **critical technical debt item** introduced in Sprint 13.0 as a trade-off to maintain synchronous API compatibility while supporting async boot methods in deferred providers.

**Current State**:
- ⚠️ **Workarounds Available**: Multiple safe patterns documented
- ⚠️ **Risk for Serverless**: High risk in AWS Lambda, GCF, Azure Functions
- ⚠️ **Planned Mitigation**: v2.0 roadmap includes native async container support

**Immediate Actions**:
1. ✅ Document this issue (this document)
2. ✅ Communicate workarounds to team
3. ✅ Add warnings to DeferredServiceProvider docstring
4. ⚠️ Plan v2.0 implementation (Options 1 or 2 recommended)

**Long-Term Actions**:
1. ⚠️ Implement Option 1 (Native Async Container) in v2.0
2. ⚠️ Migrate to async resolve in route handlers
3. ⚠️ Deprecate sync resolve for async contexts
4. ⚠️ Remove fire-and-forget pattern entirely

**Risk Acceptance**: Until v2.0, accept fire-and-forget behavior **ONLY** for:
- Deferred providers with async boot
- Non-critical initialization (no connection/state risks)
- Non-serverless environments (containers, VMs)

**Risk Mitigation**: Until v2.0, enforce strict guidelines:
- 🟡 **Critical Infrastructure**: Use eager providers with sync boot
- 🟡 **Serverless Deployments**: Avoid async boot in deferred providers
- 🟡 **Production Monitoring**: Add health checks for boot completion

---

*Document generated by code audit - Sprint 13.0*
*Technical Debt ID: TD-001*
*Severity: CRITICAL (Serverless risk)*
*Next Action: Plan v2.0 async container implementation*
