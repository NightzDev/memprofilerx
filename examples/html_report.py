"""Example: Generate interactive HTML memory report."""

import time

from memprofilerx import global_tracker


@global_tracker(interval=0.3, export_json="output/data.json")
def data_processing_pipeline() -> dict[str, int]:
    """Simulate a data processing pipeline."""
    print("🔄 Starting data processing pipeline...")

    # Stage 1: Data ingestion
    print("📥 Stage 1: Ingesting data...")
    raw_data = {i: f"value_{i}" for i in range(100_000)}
    time.sleep(1)

    # Stage 2: Data transformation
    print("🔧 Stage 2: Transforming data...")
    processed_data = {k: v.upper() for k, v in raw_data.items()}
    time.sleep(1)

    # Stage 3: Data aggregation
    print("📊 Stage 3: Aggregating results...")
    result = {"total_items": len(processed_data), "sample": processed_data[0]}
    time.sleep(0.5)

    print("✅ Pipeline complete!")
    return result


if __name__ == "__main__":
    result = data_processing_pipeline()
    print(f"\n📊 Pipeline result: {result}")

    # Convert JSON to HTML report
    print("\n🌐 Generating interactive HTML report...")
    import json

    from memprofilerx.reporter import export_to_html

    with open("output/data.json") as f:
        mem_data = json.load(f)

    export_to_html(mem_data, "output/interactive_report.html")
    print("✅ HTML report generated: output/interactive_report.html")
    print("   Open it in your browser to explore the interactive visualization!")
