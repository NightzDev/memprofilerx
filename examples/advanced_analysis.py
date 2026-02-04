"""Example: Advanced memory analysis with GC inspection."""

import time
from typing import Any

from memprofilerx import track_memory


class DataProcessor:
    """Example class that processes and caches data."""

    def __init__(self) -> None:
        self.cache: dict[int, list[int]] = {}

    def process_batch(self, batch_size: int) -> list[int]:
        """Process a batch of numbers."""
        if batch_size in self.cache:
            return self.cache[batch_size]

        result = [i * 2 for i in range(batch_size)]
        self.cache[batch_size] = result
        return result


@track_memory(interval=0.5, analyze_gc=True)
def memory_intensive_operation() -> dict[str, Any]:
    """Perform memory-intensive operations with caching."""
    print("🧠 Starting memory-intensive operation with GC analysis...\n")

    processor = DataProcessor()

    # Phase 1: Build up cache
    print("📈 Phase 1: Building cache...")
    for size in [10_000, 50_000, 100_000, 200_000]:
        processor.process_batch(size)
        print(f"  Processed batch of {size:,} items")
        time.sleep(0.5)

    # Phase 2: Reuse cache (should not increase memory significantly)
    print("\n♻️  Phase 2: Reusing cached data...")
    for size in [10_000, 50_000]:
        processor.process_batch(size)
        print(f"  Retrieved cached batch of {size:,} items")
        time.sleep(0.3)

    # Phase 3: Create temporary objects
    print("\n📦 Phase 3: Creating temporary objects...")
    temp_data = [{"id": i, "data": list(range(100))} for i in range(1000)]
    time.sleep(0.5)

    print("\n✅ Operation complete!")
    return {
        "cache_size": len(processor.cache),
        "temp_objects": len(temp_data),
    }


if __name__ == "__main__":
    result_data = memory_intensive_operation()

    print("\n" + "=" * 60)
    print("📊 EXECUTION RESULTS")
    print("=" * 60)

    function_result = result_data["result"]
    print(f"\n✓ Function returned: {function_result}")

    memory_usage = result_data["memory_usage"]
    print(f"\n📈 Memory samples collected: {len(memory_usage)}")
    if memory_usage:
        peak_mem = max(m for _, m in memory_usage)
        avg_mem = sum(m for _, m in memory_usage) / len(memory_usage)
        print(f"   Peak memory: {peak_mem:.2f} MB")
        print(f"   Average memory: {avg_mem:.2f} MB")

    if "live_objects" in result_data:
        print("\n🧬 LIVE OBJECTS ANALYSIS (types using >100 KB)")
        print("=" * 60)
        live_objects = result_data["live_objects"]

        # Sort by size
        sorted_objects = sorted(
            live_objects.items(),
            key=lambda x: x[1]["total_size_kb"],
            reverse=True,
        )

        for type_name, stats in sorted_objects[:10]:  # Top 10
            count = stats["count"]
            size_kb = stats["total_size_kb"]
            size_mb = size_kb / 1024
            avg_size_bytes = (size_kb * 1024) / count if count > 0 else 0

            print(f"\n{type_name}:")
            print(f"  • Count: {count:,}")
            print(f"  • Total size: {size_mb:.2f} MB ({size_kb:.2f} KB)")
            print(f"  • Avg size per object: {avg_size_bytes:.1f} bytes")

    print("\n" + "=" * 60)
