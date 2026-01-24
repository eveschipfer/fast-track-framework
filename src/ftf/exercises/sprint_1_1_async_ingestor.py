"""
Sprint 1.1: Async Python Fundamentals
=====================================

Educational module demonstrating:
- Async file I/O with aiofiles
- Concurrent task execution with asyncio.gather
- Exception handling in async contexts
- Type hints and dataclasses
- Context managers (sync and async)

Learning Objectives:
1. Understand event loop mechanics
2. Master asyncio.gather with return_exceptions
3. Handle mixed results (Success/Exception)
4. Use Semaphore for concurrency control
"""

import asyncio
import json
import random
from dataclasses import asdict, dataclass, field

import aiofiles

# ============================================================================
# 1. DATA MODELS (Type-Safe Structures)
# ============================================================================


@dataclass
class Transaction:
    """
    Represents a financial transaction.

    Attributes:
        id: Unique transaction identifier
        amount: Transaction amount (negative values trigger validation error)
        status: Processing status (pending/processed/failed)
    """

    id: str
    amount: float
    status: str = "pending"


@dataclass
class Report:
    """
    Aggregated report of batch processing results.

    Attributes:
        total_processed: Count of successfully processed transactions
        total_amount: Sum of all successful transaction amounts
        failed_ids: List of transaction IDs that failed processing
    """

    total_processed: int
    total_amount: float
    failed_ids: list[str] = field(default_factory=list)


# ============================================================================
# 2. ASYNC SERVICE LAYER (Simulated External API)
# ============================================================================


async def process_transaction(tx: Transaction) -> Transaction:
    """
    Simulates an async API call with variable latency.

    This demonstrates non-blocking I/O: while one transaction "waits" for
    the API response (simulated via asyncio.sleep), other transactions
    can be processed concurrently.

    Args:
        tx: Transaction to process

    Returns:
        The same transaction with updated status

    Raises:
        ValueError: If transaction amount is negative

    Note:
        Uses asyncio.sleep (non-blocking) instead of time.sleep (blocking).
        If we used time.sleep, the entire event loop would freeze.
    """
    # Simulate network latency (100-500ms)
    delay = random.uniform(0.1, 0.5)
    await asyncio.sleep(delay)

    # Business rule validation
    if tx.amount < 0:
        raise ValueError(f"Negative amount for TX {tx.id}")

    # Mutation (not ideal, but educational)
    # Better: return Transaction(id=tx.id, amount=tx.amount, status="processed")
    tx.status = "processed"
    print(f"✅ Processed {tx.id} (${tx.amount:.2f}) in {delay:.2f}s")

    return tx


# ============================================================================
# 3. CORE BUSINESS LOGIC (Async Pipeline)
# ============================================================================


async def ingest_data(file_path: str) -> Report:
    """
    Complete ETL pipeline: Extract → Transform → Load → Aggregate.

    Pipeline stages:
    1. Read JSON file asynchronously
    2. Deserialize to dataclass instances
    3. Process all transactions concurrently
    4. Aggregate results into report

    Args:
        file_path: Path to JSON file with transaction data

    Returns:
        Report with processing statistics

    Example:
        >>> report = await ingest_data("transactions.json")
        >>> print(f"Processed: {report.total_processed}")
    """
    print(f"📂 Reading {file_path}...")

    # ------------------------------------------------------------------
    # STAGE 1: Async File I/O
    # ------------------------------------------------------------------
    try:
        async with aiofiles.open(file_path) as f:
            content = await f.read()
            raw_data = json.loads(content)
    except FileNotFoundError:
        print("⚠️  File not found, using mock data...")
        # Generate 20 mock transactions
        raw_data = [
            {"id": f"tx_{i}", "amount": random.uniform(-10, 100)} for i in range(20)
        ]

    # ------------------------------------------------------------------
    # STAGE 2: Deserialization (Dict → Dataclass)
    # ------------------------------------------------------------------
    transactions: list[Transaction] = [Transaction(**item) for item in raw_data]

    print(f"🚀 Starting batch processing for {len(transactions)} items...")

    # ------------------------------------------------------------------
    # STAGE 3: Concurrent Processing (THE MAGIC)
    # ------------------------------------------------------------------
    # Key Insight: return_exceptions=True
    #
    # Without it: First exception stops everything, other tasks are cancelled
    # With it: All tasks complete, exceptions are returned as values
    #
    # Result type: List[Union[Transaction, Exception]]
    results: list[Transaction | Exception] = await asyncio.gather(
        *[process_transaction(tx) for tx in transactions], return_exceptions=True
    )

    # ------------------------------------------------------------------
    # STAGE 4: Result Aggregation (Type Narrowing)
    # ------------------------------------------------------------------
    successful: list[Transaction] = []
    failed_ids: list[str] = []

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # It's an exception - capture original transaction ID
            failed_ids.append(transactions[i].id)
            print(f"💥 Failed: {transactions[i].id} - {result}")
        else:
            # It's a successful Transaction
            successful.append(result)

    # Calculate aggregates
    total_amount = sum(tx.amount for tx in successful)

    return Report(
        total_processed=len(successful),
        total_amount=total_amount,
        failed_ids=failed_ids,
    )


# ============================================================================
# 4. ADVANCED: CONCURRENCY CONTROL WITH SEMAPHORE
# ============================================================================


async def process_transaction_with_limit(
    tx: Transaction, semaphore: asyncio.Semaphore
) -> Transaction:
    """
    Process transaction with concurrency limiting.

    Use case: External API has rate limit (e.g., max 5 requests/second).
    Semaphore ensures we never exceed the limit.

    Args:
        tx: Transaction to process
        semaphore: Semaphore with max concurrent operations

    Returns:
        Processed transaction
    """
    async with semaphore:  # Acquire token (blocks if limit reached)
        return await process_transaction(tx)
    # Token automatically released on exit


async def ingest_data_with_rate_limit(
    file_path: str, max_concurrent: int = 5
) -> Report:
    """
    Same as ingest_data but with rate limiting.

    Args:
        file_path: Path to JSON file
        max_concurrent: Maximum concurrent API calls

    Returns:
        Report with processing statistics
    """
    print(f"📂 Reading {file_path} (max {max_concurrent} concurrent)...")

    try:
        async with aiofiles.open(file_path) as f:
            content = await f.read()
            raw_data = json.loads(content)
    except FileNotFoundError:
        raw_data = [
            {"id": f"tx_{i}", "amount": random.uniform(-10, 100)} for i in range(20)
        ]

    transactions: list[Transaction] = [Transaction(**item) for item in raw_data]

    # Create semaphore (max N concurrent operations)
    semaphore = asyncio.Semaphore(max_concurrent)

    print(f"🚀 Processing {len(transactions)} items (rate limited)...")

    results: list[Transaction | Exception] = await asyncio.gather(
        *[process_transaction_with_limit(tx, semaphore) for tx in transactions],
        return_exceptions=True,
    )

    # Aggregation logic (same as before)
    successful: list[Transaction] = []
    failed_ids: list[str] = []

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            failed_ids.append(transactions[i].id)
        else:
            successful.append(result)

    total_amount = sum(tx.amount for tx in successful)

    return Report(
        total_processed=len(successful),
        total_amount=total_amount,
        failed_ids=failed_ids,
    )


# ============================================================================
# 5. ENTRY POINT & DEMO
# ============================================================================


async def main():
    """Main execution function."""

    print("=" * 70)
    print("DEMO 1: Basic Async Processing")
    print("=" * 70)

    report = await ingest_data("dummy.json")

    print("\n" + "=" * 70)
    print("📊 FINAL REPORT")
    print("=" * 70)
    print(json.dumps(asdict(report), indent=2))

    # Calculate metrics
    total_attempted = report.total_processed + len(report.failed_ids)
    success_rate = (
        (report.total_processed / total_attempted * 100) if total_attempted > 0 else 0
    )
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    print(f"💰 Total Amount: ${report.total_amount:.2f}")

    # Demo 2: Rate limited version
    print("\n" + "=" * 70)
    print("DEMO 2: Rate-Limited Processing (max 3 concurrent)")
    print("=" * 70)

    report2 = await ingest_data_with_rate_limit("dummy.json", max_concurrent=3)
    print(f"\n✅ Processed: {report2.total_processed}")
    print(f"❌ Failed: {len(report2.failed_ids)}")


if __name__ == "__main__":
    # asyncio.run() creates event loop, runs main(), closes loop
    asyncio.run(main())
