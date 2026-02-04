"""Memory usage reporting and visualization utilities."""

import csv
import logging
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Use non-GUI backend for Windows/headless environments
import matplotlib.pyplot as plt  # noqa: E402
from jinja2 import Template

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Memory Profile Report - {{ timestamp }}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                Roboto, Oxygen, Ubuntu, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 2rem;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #58a6ff; margin-bottom: 0.5rem; }
        .meta { color: #8b949e; margin-bottom: 2rem; font-size: 0.9rem; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 1rem;
        }
        .stat-label { color: #8b949e; font-size: 0.875rem; margin-bottom: 0.25rem; }
        .stat-value { color: #58a6ff; font-size: 1.5rem; font-weight: 600; }
        #memoryPlot { width: 100%; height: 500px; margin-bottom: 2rem; }
        table {
            width: 100%;
            border-collapse: collapse;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            overflow: hidden;
        }
        th, td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #30363d; }
        th { background: #0d1117; color: #58a6ff; font-weight: 600; }
        tr:last-child td { border-bottom: none; }
        tr:hover { background: #1c2128; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Memory Profile Report</h1>
        <div class="meta">Generated at {{ timestamp }}</div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Peak Memory</div>
                <div class="stat-value">{{ peak_memory }} MB</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Average Memory</div>
                <div class="stat-value">{{ avg_memory }} MB</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Min Memory</div>
                <div class="stat-value">{{ min_memory }} MB</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Duration</div>
                <div class="stat-value">{{ duration }} s</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Samples</div>
                <div class="stat-value">{{ sample_count }}</div>
            </div>
        </div>

        <div id="memoryPlot"></div>

        <h2 style="margin-bottom: 1rem; color: #58a6ff;">Memory Timeline</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp (s)</th>
                    <th>Memory (MB)</th>
                    <th>Delta (MB)</th>
                </tr>
            </thead>
            <tbody>
                {% for row in table_data %}
                <tr>
                    <td>{{ "%.2f"|format(row.timestamp) }}</td>
                    <td>{{ "%.2f"|format(row.memory) }}</td>
                    <td style="color: {% if row.delta > 0 %}#f85149{%
                        elif row.delta < 0 %}#3fb950{% else %}#8b949e{% endif %}">
                        {{ "%+.2f"|format(row.delta) }}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <script>
        const data = [{
            x: {{ timestamps | tojson }},
            y: {{ memories | tojson }},
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Memory Usage',
            line: { color: '#58a6ff', width: 2 },
            marker: { size: 6, color: '#58a6ff' }
        }];

        const layout = {
            title: 'Memory Usage Over Time',
            xaxis: { title: 'Time (seconds)', color: '#c9d1d9', gridcolor: '#30363d' },
            yaxis: { title: 'Memory (MB)', color: '#c9d1d9', gridcolor: '#30363d' },
            paper_bgcolor: '#0d1117',
            plot_bgcolor: '#161b22',
            font: { color: '#c9d1d9' }
        };

        Plotly.newPlot('memoryPlot', data, layout, { responsive: true });
    </script>
</body>
</html>
"""


def plot_memory(
    mem_data: list[tuple[float, float]],
    output_path: str | Path = "memplot.png",
    title: str = "Memory Usage Over Time",
) -> None:
    """
    Create and save a memory usage visualization as PNG.

    Args:
        mem_data: List of (timestamp, memory_in_MB) tuples from memory tracking.
        output_path: File path where the PNG will be saved.
        title: Title for the graph.

    Raises:
        ValueError: If mem_data is empty or has invalid format.
        OSError: If saving the file fails.

    Example:
        >>> data = [(0, 23.1), (1.0, 130.5), (2.0, 130.7)]
        >>> plot_memory(data, "output.png")
    """
    if not mem_data:
        raise ValueError("No memory data provided to plot.")

    try:
        timestamps, mem_values = zip(*mem_data, strict=True)
    except (ValueError, TypeError) as e:
        raise ValueError(
            "Memory data format invalid. Expected list of (timestamp, memory_MB) tuples."
        ) from e

    try:
        plt.figure(figsize=(12, 6))
        plt.plot(
            timestamps,
            mem_values,
            marker="o",
            linewidth=2,
            markersize=4,
            color="#58a6ff",
        )
        plt.title(title, fontsize=14, fontweight="bold")
        plt.xlabel("Time (seconds)", fontsize=11)
        plt.ylabel("Memory Usage (MB)", fontsize=11)
        plt.grid(True, alpha=0.3, linestyle="--")
        plt.tight_layout()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Memory plot saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save plot: {e}")
        raise OSError(f"Failed to save memory plot to {output_path}") from e


def export_to_csv(
    mem_data: list[tuple[float, float]], output_path: str | Path = "memory.csv"
) -> None:
    """
    Export memory data to CSV format.

    Args:
        mem_data: List of (timestamp, memory_in_MB) tuples.
        output_path: File path where the CSV will be saved.

    Raises:
        ValueError: If mem_data is empty.
        OSError: If writing the file fails.

    Example:
        >>> data = [(0, 23.1), (1.0, 130.5)]
        >>> export_to_csv(data, "memory.csv")
    """
    if not mem_data:
        raise ValueError("No memory data provided to export.")

    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_seconds", "memory_mb"])
            writer.writerows(mem_data)

        logger.info(f"Memory data exported to CSV: {output_path}")
    except OSError as e:
        logger.error(f"Failed to export CSV: {e}")
        raise OSError(f"Failed to export memory data to {output_path}") from e


def export_to_html(
    mem_data: list[tuple[float, float]], output_path: str | Path = "memory.html"
) -> None:
    """
    Export memory data as an interactive HTML report with visualizations.

    Creates a self-contained HTML file with:
    - Interactive Plotly chart
    - Summary statistics (peak, average, min memory)
    - Detailed data table with deltas

    Args:
        mem_data: List of (timestamp, memory_in_MB) tuples.
        output_path: File path where the HTML will be saved.

    Raises:
        ValueError: If mem_data is empty.
        OSError: If writing the file fails.

    Example:
        >>> data = [(0, 23.1), (1.0, 130.5), (2.0, 135.2)]
        >>> export_to_html(data, "report.html")
    """
    if not mem_data:
        raise ValueError("No memory data provided to export.")

    try:
        timestamps = [t for t, _ in mem_data]
        memories = [m for _, m in mem_data]

        # Calculate statistics
        peak_memory = max(memories)
        avg_memory = sum(memories) / len(memories)
        min_memory = min(memories)
        duration = timestamps[-1] if timestamps else 0
        sample_count = len(mem_data)

        # Prepare table data with deltas
        table_data = []
        for i, (timestamp, memory) in enumerate(mem_data):
            delta = memory - mem_data[i - 1][1] if i > 0 else 0.0
            table_data.append({"timestamp": timestamp, "memory": memory, "delta": delta})

        # Render template
        template = Template(HTML_TEMPLATE)
        html_content = template.render(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            peak_memory=f"{peak_memory:.2f}",
            avg_memory=f"{avg_memory:.2f}",
            min_memory=f"{min_memory:.2f}",
            duration=f"{duration:.2f}",
            sample_count=sample_count,
            timestamps=timestamps,
            memories=memories,
            table_data=table_data,
        )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")

        logger.info(f"Interactive HTML report exported to {output_path}")
    except OSError as e:
        logger.error(f"Failed to export HTML: {e}")
        raise OSError(f"Failed to export HTML report to {output_path}") from e
