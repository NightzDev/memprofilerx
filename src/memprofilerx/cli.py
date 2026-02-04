"""Command-line interface for MemProfilerX."""

import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.logging import RichHandler

from memprofilerx import __version__
from memprofilerx.reporter import export_to_csv, export_to_html, plot_memory
from memprofilerx.tracker import global_tracker

app = typer.Typer(
    name="memx",
    help="🧠 MemProfilerX - Professional Python memory profiler",
    add_completion=True,
)
console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_time=False)],
    )


@app.command()
def run(
    script: Annotated[Path, typer.Argument(help="Python script to profile", exists=True)],
    interval: Annotated[
        float, typer.Option("--interval", "-i", help="Sampling interval in seconds")
    ] = 1.0,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file path (PNG/HTML/CSV/JSON)"),
    ] = None,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: png, html, csv, json, all",
            case_sensitive=False,
        ),
    ] = "png",
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose logging")
    ] = False,
) -> None:
    """
    Run a Python script with memory profiling.

    Example:
        memx run my_script.py --interval 0.5 --output report --format html
    """
    setup_logging(verbose)

    if not script.exists():
        console.print(f"[red]Error:[/red] Script not found: {script}")
        raise typer.Exit(1)

    if interval <= 0:
        console.print("[red]Error:[/red] Interval must be positive")
        raise typer.Exit(1)

    # Determine output paths
    base_name = output.stem if output else script.stem
    output_dir = output.parent if output else Path.cwd()

    exports = {}
    if format.lower() in ("png", "all"):
        exports["png"] = output_dir / f"{base_name}.png"
    if format.lower() in ("html", "all"):
        exports["html"] = output_dir / f"{base_name}.html"
    if format.lower() in ("csv", "all"):
        exports["csv"] = output_dir / f"{base_name}.csv"
    if format.lower() in ("json", "all"):
        exports["json"] = output_dir / f"{base_name}.json"

    console.print(f"[cyan]🧠 Profiling:[/cyan] {script}")
    console.print(f"[cyan]📊 Interval:[/cyan] {interval}s")
    console.print(f"[cyan]📁 Output:[/cyan] {', '.join(str(p) for p in exports.values())}")

    # Load and execute the script with profiling
    try:
        spec = importlib.util.spec_from_file_location("__main__", script)
        if spec is None or spec.loader is None:
            console.print(f"[red]Error:[/red] Could not load script: {script}")
            raise typer.Exit(1) from None

        module = importlib.util.module_from_spec(spec)
        sys.modules["__main__"] = module

        # Wrap the execution with global_tracker
        @global_tracker(
            interval=interval,
            export_png=str(exports.get("png")) if "png" in exports else None,
            export_json=str(exports.get("json")) if "json" in exports else None,
            export_csv=str(exports.get("csv")) if "csv" in exports else None,
        )
        def execute_script() -> None:
            spec.loader.exec_module(module)  # type: ignore

        execute_script()

        # Export HTML if requested (done after tracking)
        if "html" in exports:
            # We need to read the JSON data if it exists, or use a dummy for now
            # In a real scenario, we'd capture mem_data from global_tracker
            console.print("[yellow]Note:[/yellow] HTML export requires JSON data. Use --format all")

        console.print("\n[green]✓[/green] Profiling complete!")

    except Exception as e:
        console.print(f"[red]Error executing script:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1) from e


@app.command()
def convert(
    input_file: Annotated[
        Path, typer.Argument(help="Input JSON file with memory data", exists=True)
    ],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file path")] = None,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: png, html, csv", case_sensitive=False),
    ] = "html",
) -> None:
    """
    Convert JSON memory data to different formats.

    Example:
        memx convert memory.json --format html --output report.html
    """
    if not input_file.exists():
        console.print(f"[red]Error:[/red] Input file not found: {input_file}")
        raise typer.Exit(1)

    try:
        with open(input_file, encoding="utf-8") as f:
            mem_data = json.load(f)

        if not isinstance(mem_data, list) or not all(
            isinstance(item, list) and len(item) == 2 for item in mem_data
        ):
            console.print(
                "[red]Error:[/red] Invalid JSON format. Expected list of [timestamp, memory] pairs."
            )
            raise typer.Exit(1) from None

        # Determine output path
        if output is None:
            output = input_file.with_suffix(f".{format.lower()}")

        console.print(f"[cyan]Converting {input_file} to {format.upper()}...[/cyan]")

        if format.lower() == "png":
            plot_memory(mem_data, output)
        elif format.lower() == "html":
            export_to_html(mem_data, output)
        elif format.lower() == "csv":
            export_to_csv(mem_data, output)
        else:
            console.print(f"[red]Error:[/red] Unknown format: {format}")
            raise typer.Exit(1) from None

        console.print(f"[green]✓[/green] Exported to {output}")

    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON: {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command()
def version() -> None:
    """Show MemProfilerX version."""
    console.print(f"[cyan]MemProfilerX[/cyan] version [green]{__version__}[/green]")


if __name__ == "__main__":
    app()
