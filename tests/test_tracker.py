"""Comprehensive tests for memory tracking functionality."""

import time
from pathlib import Path

import pytest

from memprofilerx.tracker import analyze_live_objects, global_tracker, track_memory


class TestTrackMemory:
    """Tests for track_memory decorator."""

    def test_basic_tracking(self) -> None:
        """Test basic memory tracking returns correct structure."""

        @track_memory(interval=0.1)
        def dummy() -> int:
            return 123

        result = dummy()
        assert result["result"] == 123
        assert isinstance(result["memory_usage"], list)
        assert len(result["memory_usage"]) > 0
        assert all(isinstance(item, tuple) and len(item) == 2 for item in result["memory_usage"])

    def test_with_gc_analysis(self) -> None:
        """Test tracking with GC analysis enabled."""

        @track_memory(interval=0.1, analyze_gc=True)
        def create_objects() -> list[int]:
            return list(range(10000))

        result = create_objects()
        assert "live_objects" in result
        assert isinstance(result["live_objects"], dict)
        assert result["result"] == list(range(10000))

    def test_with_callback(self) -> None:
        """Test tracking with custom callback."""
        callback_data: list[tuple[float, float]] = []

        def callback(timestamp: float, memory: float) -> None:
            callback_data.append((timestamp, memory))

        @track_memory(interval=0.1, callback=callback)
        def dummy() -> str:
            time.sleep(0.3)
            return "done"

        result = dummy()
        assert result["result"] == "done"
        assert len(callback_data) > 0
        assert all(isinstance(t, float) and isinstance(m, float) for t, m in callback_data)

    def test_with_duration_limit(self) -> None:
        """Test tracking stops after duration limit."""

        @track_memory(interval=0.1, duration=0.3)
        def long_function() -> str:
            time.sleep(1.0)
            return "done"

        result = long_function()
        # Should have stopped monitoring after 0.3s even though function ran for 1s
        last_timestamp = result["memory_usage"][-1][0] if result["memory_usage"] else 0
        assert last_timestamp < 0.5  # Some buffer for timing

    def test_invalid_interval(self) -> None:
        """Test that invalid interval raises ValueError."""
        with pytest.raises(ValueError, match="Interval must be positive"):

            @track_memory(interval=-1.0)
            def dummy() -> None:
                pass

    def test_invalid_duration(self) -> None:
        """Test that invalid duration raises ValueError."""
        with pytest.raises(ValueError, match="Duration must be positive"):

            @track_memory(duration=-5.0)
            def dummy() -> None:
                pass

    def test_function_exception_propagates(self) -> None:
        """Test that exceptions in tracked function propagate correctly."""

        @track_memory(interval=0.1)
        def failing_function() -> None:
            raise RuntimeError("Test error")

        with pytest.raises(RuntimeError, match="Test error"):
            failing_function()

    def test_callback_exception_handled(self) -> None:
        """Test that callback exceptions don't crash monitoring."""

        def bad_callback(_timestamp: float, _memory: float) -> None:
            raise ValueError("Callback error")

        @track_memory(interval=0.1, callback=bad_callback)
        def dummy() -> str:
            time.sleep(0.2)
            return "done"

        # Should complete despite callback errors
        result = dummy()
        assert result["result"] == "done"


class TestGlobalTracker:
    """Tests for global_tracker decorator."""

    def test_basic_global_tracking(self, tmp_path: Path) -> None:
        """Test basic global tracking."""
        json_path = tmp_path / "memory.json"

        @global_tracker(interval=0.1, export_json=json_path)
        def dummy() -> str:
            time.sleep(0.2)
            return "complete"

        result = dummy()
        assert result == "complete"
        assert json_path.exists()

    def test_png_export(self, tmp_path: Path) -> None:
        """Test PNG export from global tracker."""
        png_path = tmp_path / "memory.png"

        @global_tracker(interval=0.1, export_png=png_path)
        def dummy() -> int:
            time.sleep(0.2)
            return 42

        result = dummy()
        assert result == 42
        assert png_path.exists()
        assert png_path.stat().st_size > 0

    def test_csv_export(self, tmp_path: Path) -> None:
        """Test CSV export from global tracker."""
        csv_path = tmp_path / "memory.csv"

        @global_tracker(interval=0.1, export_csv=csv_path)
        def dummy() -> str:
            time.sleep(0.2)
            return "done"

        result = dummy()
        assert result == "done"
        assert csv_path.exists()
        content = csv_path.read_text()
        assert "timestamp" in content
        assert "memory_mb" in content

    def test_multiple_exports(self, tmp_path: Path) -> None:
        """Test exporting to multiple formats simultaneously."""
        json_path = tmp_path / "memory.json"
        png_path = tmp_path / "memory.png"
        csv_path = tmp_path / "memory.csv"

        @global_tracker(
            interval=0.1,
            export_json=json_path,
            export_png=png_path,
            export_csv=csv_path,
        )
        def dummy() -> bool:
            time.sleep(0.2)
            return True

        result = dummy()
        assert result is True
        assert json_path.exists()
        assert png_path.exists()
        assert csv_path.exists()

    def test_invalid_interval(self) -> None:
        """Test that invalid interval raises ValueError."""
        with pytest.raises(ValueError, match="Interval must be positive"):

            @global_tracker(interval=0)
            def dummy() -> None:
                pass


class TestAnalyzeLiveObjects:
    """Tests for analyze_live_objects function."""

    def test_basic_analysis(self) -> None:
        """Test basic object analysis."""
        # Create some objects
        _data = list(range(10000))
        _mapping = {i: str(i) for i in range(1000)}

        result = analyze_live_objects(min_size_kb=1)
        assert isinstance(result, dict)
        assert "list" in result or "dict" in result  # Should find some common types

    def test_min_size_filter(self) -> None:
        """Test that min_size_kb filter works."""
        result_high = analyze_live_objects(min_size_kb=1000)
        result_low = analyze_live_objects(min_size_kb=1)

        # Lower threshold should return more types
        assert len(result_low) >= len(result_high)

    def test_invalid_min_size(self) -> None:
        """Test that negative min_size raises ValueError."""
        with pytest.raises(ValueError, match="min_size_kb must be non-negative"):
            analyze_live_objects(min_size_kb=-10)

    def test_return_format(self) -> None:
        """Test that return format is correct."""
        result = analyze_live_objects(min_size_kb=1)
        for type_name, stats in result.items():
            assert isinstance(type_name, str)
            assert "count" in stats
            assert "total_size_kb" in stats
            assert isinstance(stats["count"], int)
            assert isinstance(stats["total_size_kb"], (int, float))
            assert stats["count"] > 0
            assert stats["total_size_kb"] > 0
