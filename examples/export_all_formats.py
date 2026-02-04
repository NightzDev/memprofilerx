"""Example: Export memory profile to all supported formats."""

import time

from memprofilerx import global_tracker


@global_tracker(
    interval=0.5,
    export_png="output/memory_profile.png",
    export_json="output/memory_profile.json",
    export_csv="output/memory_profile.csv",
)
def simulate_workload() -> None:
    """Simulate a workload with varying memory usage."""
    print("🚀 Starting workload simulation...")

    # Phase 1: Gradual memory increase
    print("📈 Phase 1: Allocating memory...")
    data_chunks = []
    for i in range(5):
        chunk = [x for x in range(1_000_000)]
        data_chunks.append(chunk)
        time.sleep(0.5)

    # Phase 2: Stable memory usage
    print("⏸️  Phase 2: Stable memory usage...")
    time.sleep(2)

    # Phase 3: Memory cleanup
    print("📉 Phase 3: Releasing memory...")
    data_chunks.clear()
    time.sleep(1)

    print("✅ Workload complete!")


if __name__ == "__main__":
    simulate_workload()
    print("\n📊 Memory profiles exported to:")
    print("  - output/memory_profile.png (visualization)")
    print("  - output/memory_profile.json (raw data)")
    print("  - output/memory_profile.csv (spreadsheet format)")
