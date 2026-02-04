"""Comprehensive tests for memory reporting and visualization."""

from pathlib import Path

import pytest

from memprofilerx.reporter import export_to_csv, export_to_html, plot_memory


@pytest.fixture
def sample_memory_data() -> list[tuple[float, float]]:
    """Sample memory data for testing."""
    return [
        (0.0, 23.5),
        (1.0, 45.2),
        (2.0, 67.8),
        (3.0, 89.1),
        (4.0, 72.3),
        (5.0, 55.6),
    ]


@pytest.fixture
def empty_memory_data() -> list[tuple[float, float]]:
    """Empty memory data for testing error cases."""
    return []


class TestPlotMemory:
    """Tests for plot_memory function."""

    def test_basic_plot(self, sample_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test basic PNG plot generation."""
        output_path = tmp_path / "test_plot.png"
        plot_memory(sample_memory_data, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 1000  # PNG should be reasonably sized

    def test_custom_title(self, sample_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test plot with custom title."""
        output_path = tmp_path / "custom_title.png"
        plot_memory(sample_memory_data, output_path, title="Custom Memory Profile")

        assert output_path.exists()

    def test_creates_parent_directories(self, sample_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test that parent directories are created if they don't exist."""
        output_path = tmp_path / "subdir" / "nested" / "plot.png"
        plot_memory(sample_memory_data, output_path)

        assert output_path.exists()
        assert output_path.parent.exists()

    def test_empty_data_raises_error(self, empty_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test that empty data raises ValueError."""
        output_path = tmp_path / "plot.png"
        with pytest.raises(ValueError, match="No memory data provided"):
            plot_memory(empty_memory_data, output_path)

    def test_invalid_data_format_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid data format raises ValueError."""
        invalid_data = [(1.0,), (2.0, 3.0, 4.0)]  # Wrong tuple sizes
        output_path = tmp_path / "plot.png"

        with pytest.raises(ValueError, match="Memory data format invalid"):
            plot_memory(invalid_data, output_path)  # type: ignore


class TestExportToCSV:
    """Tests for export_to_csv function."""

    def test_basic_csv_export(self, sample_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test basic CSV export."""
        output_path = tmp_path / "memory.csv"
        export_to_csv(sample_memory_data, output_path)

        assert output_path.exists()
        content = output_path.read_text()

        # Check header
        assert "timestamp_seconds" in content
        assert "memory_mb" in content

        # Check data
        lines = content.strip().split("\n")
        assert len(lines) == len(sample_memory_data) + 1  # +1 for header

    def test_csv_content_accuracy(self, sample_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test that CSV content matches input data."""
        output_path = tmp_path / "memory.csv"
        export_to_csv(sample_memory_data, output_path)

        content = output_path.read_text()
        lines = content.strip().split("\n")[1:]  # Skip header

        for line, (timestamp, memory) in zip(lines, sample_memory_data):
            parts = line.split(",")
            assert float(parts[0]) == timestamp
            assert float(parts[1]) == memory

    def test_creates_parent_directories(self, sample_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test that parent directories are created."""
        output_path = tmp_path / "reports" / "output" / "memory.csv"
        export_to_csv(sample_memory_data, output_path)

        assert output_path.exists()

    def test_empty_data_raises_error(self, empty_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test that empty data raises ValueError."""
        output_path = tmp_path / "memory.csv"
        with pytest.raises(ValueError, match="No memory data provided"):
            export_to_csv(empty_memory_data, output_path)


class TestExportToHTML:
    """Tests for export_to_html function."""

    def test_basic_html_export(self, sample_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test basic HTML report generation."""
        output_path = tmp_path / "report.html"
        export_to_html(sample_memory_data, output_path)

        assert output_path.exists()
        content = output_path.read_text()

        # Check for essential HTML elements
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "</html>" in content

    def test_html_contains_data(self, sample_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test that HTML report contains the actual data."""
        output_path = tmp_path / "report.html"
        export_to_html(sample_memory_data, output_path)

        content = output_path.read_text()

        # Check for statistics
        assert "Peak Memory" in content
        assert "Average Memory" in content
        assert "Duration" in content

        # Check for plotly
        assert "plotly" in content.lower()

    def test_html_table_data(self, sample_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test that HTML table contains timestamp and memory data."""
        output_path = tmp_path / "report.html"
        export_to_html(sample_memory_data, output_path)

        content = output_path.read_text()

        # Check for table elements
        assert "<table>" in content or "<table" in content
        assert "Timestamp" in content
        assert "Memory" in content

    def test_creates_parent_directories(self, sample_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test that parent directories are created."""
        output_path = tmp_path / "reports" / "analysis" / "report.html"
        export_to_html(sample_memory_data, output_path)

        assert output_path.exists()

    def test_empty_data_raises_error(self, empty_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test that empty data raises ValueError."""
        output_path = tmp_path / "report.html"
        with pytest.raises(ValueError, match="No memory data provided"):
            export_to_html(empty_memory_data, output_path)

    def test_statistics_calculation(self, sample_memory_data: list[tuple[float, float]], tmp_path: Path) -> None:
        """Test that statistics are calculated correctly in HTML."""
        output_path = tmp_path / "report.html"
        export_to_html(sample_memory_data, output_path)

        content = output_path.read_text()

        # Calculate expected values
        memories = [m for _, m in sample_memory_data]
        expected_peak = max(memories)

        # Peak should be in the HTML (with some tolerance for formatting)
        assert str(int(expected_peak)) in content or f"{expected_peak:.1f}" in content or f"{expected_peak:.2f}" in content
