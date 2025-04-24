import matplotlib.pyplot as plt
from typing import List, Tuple


def plot_memory(
    mem_data: List[Tuple[float, float]],
    output_path: str = "memplot.png",
    title: str = "Memory Usage Over Time"
) -> None:
    """
    Plots memory usage over time and saves the result as a PNG file.

    Args:
        mem_data: List of (timestamp, memory_in_MB) tuples.
        output_path: Path where the PNG image will be saved.
        title: Title of the graph.
    """
    if not mem_data:
        raise ValueError("No memory data provided to plot.")

    try:
        timestamps, mem_values = zip(*mem_data)
    except ValueError:
        raise ValueError("Memory data format invalid. Expected list of (timestamp, memory_MB).")

    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, mem_values, marker='o', linewidth=2)
    plt.title(title)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Memory Usage (MB)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
