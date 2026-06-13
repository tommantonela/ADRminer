"""Command-line interface for the ADR Checker.

Provides the `adrchecker` command with a `check` subcommand to assess
ADR quality against the MADR template.

Usage:
    adrchecker check path/to/adr.md
    adrchecker check path/to/adrs/ --mode adherence --json results.json
    adrchecker check path/to/adrs/ --mode sections --parallel
"""

import json
from pathlib import Path
from typing import List, Literal, Optional, Tuple

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)
from rich.table import Table

from adrchecker.checker import ADRChecker

app = typer.Typer(
    name="adrchecker",
    help="Check the quality of Architectural Decision Records (ADRs) against the MADR template.",
    no_args_is_help=True,
)

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_adr_files(path: Path) -> List[Tuple[Path, str]]:
    """Load ADR file(s) from a path.

    Args:
        path: Path to a single ADR file or a directory of `.md` files.

    Returns:
        List of (file_path, content) tuples.
    """
    files: List[Tuple[Path, str]] = []

    if path.is_file():
        try:
            content = path.read_text(encoding="utf-8")
            files.append((path, content))
        except Exception as e:
            console.print(f"[red]Error reading {path}: {e}[/red]")
    elif path.is_dir():
        for md_file in sorted(path.glob("*.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
                files.append((md_file, content))
            except Exception as e:
                console.print(f"[red]Error reading {md_file}: {e}[/red]")

    return files


def _build_metadata(adr_files: List[Tuple[Path, str]]) -> List[dict]:
    """Build metadata dicts for a list of ADR files."""
    metadata_list = []
    for path, _ in adr_files:
        try:
            file_path = str(path.relative_to(Path.cwd()))
        except ValueError:
            file_path = str(path)
        metadata_list.append({"file": file_path, "name": path.name})
    return metadata_list


def _display_results(results: List[dict], adr_files: List[Tuple[Path, str]], mode: str) -> None:
    """Display checking results in a Rich table.

    Args:
        results: List of result dictionaries.
        adr_files: List of (path, content) tuples.
        mode: Checking mode used.
    """
    table = Table(title="ADR Quality Assessment")
    table.add_column("ADR", style="cyan", no_wrap=True)
    table.add_column("Adherence score")
    table.add_column("Section presence")
    table.add_column("Section quality")
    table.add_column("Section consistency")

    def _score_color(value: int, total: int) -> str:
        if total == 0:
            return "[red]0/0[/red]"
        ratio = value / total
        if ratio >= 0.8:
            return f"[green]{value}/{total}[/green]"
        elif ratio >= 0.6:
            return f"[yellow]{value}/{total}[/yellow]"
        else:
            return f"[red]{value}/{total}[/red]"

    for (adr_path, _), result in zip(adr_files, results):
        if "error" in result:
            table.add_row(
                adr_path.name,
                "[red]N/A[/red]",
                "[red]Error[/red]",
                "[red]Error[/red]",
                "[red]Error[/red]",
            )
            continue

        # Adherence score
        template = result.get("template_adherence", {})
        score = template.get("adherence_score", 0.0)
        if score >= 0.8:
            score_display = f"[green]{score:.2f}[/green]"
        elif score >= 0.6:
            score_display = f"[yellow]{score:.2f}[/yellow]"
        elif score >= 0.4:
            score_display = f"[orange1]{score:.2f}[/orange1]"
        else:
            score_display = f"[red]{score:.2f}[/red]"

        # Section statistics
        assessments = result.get("section_assessments", [])
        if assessments:
            present = sum(1 for s in assessments if s.get("presence") == "Yes")
            quality = sum(1 for s in assessments if s.get("content_quality") == "Yes")
            consistent = sum(1 for s in assessments if s.get("purpose_consistency") == "Yes")
            present_str = _score_color(present, len(assessments))
            quality_str = _score_color(quality, len(assessments))
            consistent_str = _score_color(consistent, len(assessments))
        else:
            present_str = "[dim]N/A[/dim]"
            quality_str = "[dim]N/A[/dim]"
            consistent_str = "[dim]N/A[/dim]"

        table.add_row(
            adr_path.name,
            score_display,
            present_str,
            quality_str,
            consistent_str,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command()
def check(
    path: Path = typer.Argument(
        ...,
        help="Path to an ADR file or a directory of ADR `.md` files.",
        exists=True,
    ),
    mode: Literal["adherence", "sections", "full"] = typer.Option(
        "full",
        "--mode",
        "-m",
        help="Checking mode: 'adherence', 'sections', or 'full'.",
    ),
    parallel: bool = typer.Option(
        False,
        "--parallel",
        "-p",
        help="Enable parallel processing for batch checks.",
    ),
    json_output: Optional[Path] = typer.Option(
        None,
        "--json",
        help="Save results to a JSON file.",
    ),
) -> None:
    """Check ADR quality against the MADR template.

    Evaluates ADRs for template adherence (overall score 0.0-1.0),
    section consistency (presence, quality, purpose), or both (full mode).
    """
    # Load ADR files
    console.print("[blue]Loading ADR files...[/blue]")
    adr_files = _load_adr_files(path)

    if not adr_files:
        console.print("[red]No ADR files found.[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Found {len(adr_files)} ADR file(s)[/cyan]")

    # Initialize checker
    console.print("[blue]Initializing ADR checker...[/blue]")
    checker = ADRChecker()

    texts = {path.name: content for path, content in adr_files}
    metadata_list = _build_metadata(adr_files)

    # Run checks
    console.print(f"[blue]Checking ADRs (mode: {mode}, parallel: {parallel})...[/blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Processing {len(texts)} ADR(s)...", total=len(texts))

        if mode == "adherence":
            results = checker.check_madr_adherence_batch(texts, as_dict=True, parallel=parallel)
        elif mode == "sections":
            results = checker.check_sections_batch(texts, as_dict=True, parallel=parallel)
        else:  # full
            results = checker.check_batch(texts, as_dict=True, parallel=parallel)

        progress.update(task, completed=len(results))

    # Attach metadata to results for display/export
    for result, metadata in zip(results, metadata_list):
        if isinstance(result, dict) and "error" not in result:
            result.setdefault("metadata", metadata)

    # Display results
    console.print("\n[bold]Results:[/bold]")
    _display_results(results, adr_files, mode)

    # Save to JSON if requested
    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        with open(json_output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
        console.print(f"[green]✓ Results saved to {json_output}[/green]")

    console.print("[green]✓ Checking completed successfully![/green]")


@app.command()
def version() -> None:
    """Show the version of adrchecker."""
    from adrchecker import __version__

    console.print(f"adrchecker v{__version__}")


# Entry point for console_scripts
def cli() -> None:
    """Main entry point for the `adrchecker` CLI command."""
    app()


if __name__ == "__main__":
    cli()