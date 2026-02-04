"""Pytest configuration and shared fixtures."""

import logging

import pytest


@pytest.fixture(autouse=True)
def setup_logging() -> None:
    """Configure logging for tests."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@pytest.fixture
def suppress_console_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """Suppress rich console output during tests."""
    from rich.console import Console

    # Create a null console that doesn't output anything
    null_console = Console(file=open("/dev/null", "w") if hasattr(open, "__file__") else None, force_terminal=False)
    monkeypatch.setattr("memprofilerx.tracker.console", null_console)
