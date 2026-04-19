"""Utility CLI commands for ADRminer."""

import json
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console()

# Create utility app
util_app = typer.Typer(help="Utility commands")


@util_app.command("delete-metadata")
def delete_sidecars(
    path: Path = typer.Argument(
        ...,
        help="Path to ADR file or directory",
        exists=True,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Show what would be deleted without actually deleting",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output including each file",
    ),
) -> None:
    """
    Delete sidecar metadata JSON files for ADRs.
    
    Remove all .metadata.json sidecar files for ADRs in the specified path.
    This is useful for forcing re-analysis of ADRs.
    """
    # Collect sidecar files
    # Support multiple sidecar file types
    sidecar_patterns = [
        "*.adrminer.checking.json",
        "*.metadata.json",
        "*.adrminer.classification.json",
    ]
    
    if path.is_file():
        # Single file - check if it's a metadata file
        is_metadata = any(
            path.suffix == ".json" and 
            path.name.endswith(pattern.replace("*", ""))
            for pattern in sidecar_patterns
        )
        if is_metadata:
            sidecar_files = [path]
        else:
            # Get sidecar for this ADR (try all patterns)
            sidecar_files = []
            for pattern in sidecar_patterns:
                suffix = pattern.replace("*", "")
                sidecar_path = path.with_suffix(suffix)
                if sidecar_path.exists():
                    sidecar_files.append(sidecar_path)
    else:
        # Directory - find all metadata files
        sidecar_files = []
        for pattern in sidecar_patterns:
            sidecar_files.extend(list(path.rglob(pattern)))
    
    if not sidecar_files:
        console.print("[yellow]No sidecar metadata files found[/yellow]")
        raise typer.Exit(code=0)
    
    console.print(f"\n[bold]Found {len(sidecar_files)} sidecar file(s)[/bold]\n")
    
    # Show files if verbose or dry run
    if verbose or dry_run:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Sidecar File", style="green")
        table.add_column("Size", justify="right")
        
        for i, sidecar_file in enumerate(sidecar_files, 1):
            size = _format_size(sidecar_file.stat().st_size)
            rel_path = sidecar_file.relative_to(path) if path.is_dir() else sidecar_file.name
            table.add_row(str(i), str(rel_path), size)
        
        console.print(table)
        console.print()
    
    if dry_run:
        console.print("[yellow]Dry run mode - no files were deleted[/yellow]")
        raise typer.Exit(code=0)
    
    # Confirm deletion
    console.print("[red]This will delete all sidecar metadata files![/red]")
    confirm = typer.confirm("Are you sure you want to continue?", default=False)
    
    if not confirm:
        console.print("[yellow]Operation cancelled[/yellow]")
        raise typer.Exit(code=0)
    
    # Delete files with progress
    deleted: List[Path] = []
    failed: List[tuple[Path, str]] = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Deleting sidecar files...", total=len(sidecar_files))
        
        for sidecar_file in sidecar_files:
            try:
                sidecar_file.unlink()
                deleted.append(sidecar_file)
            except Exception as e:
                failed.append((sidecar_file, str(e)))
            
            progress.update(task, advance=1)
    
    # Show results
    console.print()
    if deleted:
        console.print(f"[green]✓ Successfully deleted {len(deleted)} sidecar file(s)[/green]")
    
    if failed:
        console.print(f"[red]✗ Failed to delete {len(failed)} file(s):[/red]")
        for failed_file, error in failed:
            console.print(f"  [red]• {failed_file.name}: {error}[/red]")
        raise typer.Exit(code=1)
    
    # Show deleted files in verbose mode
    if verbose and deleted:
        console.print("\n[bold]Deleted files:[/bold]")
        for sidecar_file in deleted:
            rel_path = sidecar_file.relative_to(path) if path.is_dir() else sidecar_file.name
            console.print(f"  • {rel_path}")


@util_app.command("list")
def list_sidecars(
    path: Path = typer.Argument(
        ...,
        help="Path to ADR file or directory",
        exists=True,
    ),
    show_size: bool = typer.Option(
        True,
        "--size/--no-size",
        help="Show file sizes",
    ),
    show_modified: bool = typer.Option(
        False,
        "--modified",
        "-m",
        help="Show modification dates",
    ),
) -> None:
    """
    List sidecar metadata JSON files for ADRs.
    
    Display all sidecar files (.adrminer.checking.json, .metadata.json, .adrminer.classification.json)
    found in the specified path.
    """
    # Collect sidecar files
    # Support multiple sidecar file types
    sidecar_patterns = [
        "*.adrminer.checking.json",
        "*.metadata.json",
        "*.adrminer.classification.json",
    ]
    
    if path.is_file():
        # Single file - check if it's a metadata file
        is_metadata = any(
            path.suffix == ".json" and 
            path.name.endswith(pattern.replace("*", ""))
            for pattern in sidecar_patterns
        )
        if is_metadata:
            sidecar_files = [path]
        else:
            # Get sidecar for this ADR (try all patterns)
            sidecar_files = []
            for pattern in sidecar_patterns:
                suffix = pattern.replace("*", "")
                sidecar_path = path.with_suffix(suffix)
                if sidecar_path.exists():
                    sidecar_files.append(sidecar_path)
    else:
        # Directory - find all metadata files
        sidecar_files = []
        for pattern in sidecar_patterns:
            sidecar_files.extend(list(path.rglob(pattern)))
    
    if not sidecar_files:
        console.print("[yellow]No sidecar metadata files found[/yellow]")
        raise typer.Exit(code=0)
    
    console.print(f"\n[bold]Found {len(sidecar_files)} sidecar file(s)[/bold]\n")
    
    # Build table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Sidecar File", style="green")
    
    if show_size:
        table.add_column("Size", justify="right")
    
    if show_modified:
        table.add_column("Modified")
    
    # Sort files by path
    sidecar_files.sort()
    
    from datetime import datetime
    for i, sidecar_file in enumerate(sidecar_files, 1):
        rel_path = sidecar_file.relative_to(path) if path.is_dir() else sidecar_file.name
        row = [str(i), str(rel_path)]
        
        if show_size:
            size = _format_size(sidecar_file.stat().st_size)
            row.append(size)
        
        if show_modified:
            mtime = datetime.fromtimestamp(sidecar_file.stat().st_mtime)
            row.append(mtime.strftime("%Y-%m-%d %H:%M:%S"))
        
        table.add_row(*row)
    
    console.print(table)


def _format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


@util_app.command("inspect")
def inspect_adr(
    path: Path = typer.Argument(
        ...,
        help="Path to ADR file",
        exists=True,
    ),
    show_metadata: bool = typer.Option(
        True,
        "--metadata/--no-metadata",
        help="Show metadata if available",
    ),
    show_content: bool = typer.Option(
        True,
        "--content/--no-content",
        help="Show ADR content",
    ),
) -> None:
    """
    Inspect an ADR file and its metadata.
    
    Display the ADR content in order: Title, metadata (if available), and remaining content.
    This provides a comprehensive view of the ADR and any analysis results.
    """
    # Validate it's a markdown file
    if path.suffix.lower() not in [".md", ".markdown"]:
        console.print(f"[red]Error: File must be a markdown file (.md or .markdown)[/red]")
        raise typer.Exit(code=1)
    
    # Read ADR content
    try:
        with open(path, "r", encoding="utf-8") as f:
            adr_content = f.read()
    except Exception as e:
        console.print(f"[red]Error reading ADR file: {e}[/red]")
        raise typer.Exit(code=1)
    
    # Parse title (first heading)
    title = _extract_title(adr_content)
    
    # Display title
    console.print()
    console.print(Panel(
        Text(title, style="bold white", justify="center"),
        title="[bold cyan]ADR Title[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))
    console.print()
    
    # Check for and display metadata
    # Try multiple possible metadata file names
    metadata_paths = [
        path.with_suffix(".adrminer.checking.json"),  # Checking service metadata
        path.with_suffix(".metadata.json"),  # Legacy metadata
        path.with_suffix(".adrminer.classification.json"),  # Classification metadata
    ]
    
    metadata_path = None
    for mp in metadata_paths:
        if mp.exists():
            metadata_path = mp
            break
    
    if show_metadata and metadata_path:
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            # Display metadata
            console.print(Panel(
                _format_metadata(metadata),
                title="[bold magenta]ADR Metadata[/bold magenta]",
                border_style="magenta",
                padding=(0, 1),
            ))
            console.print()
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read metadata file: {e}[/yellow]")
            console.print()
    elif show_metadata:
        console.print("[yellow]No metadata file found[/yellow]")
        console.print()
    
    # Display remaining content
    if show_content:
        remaining_content = _extract_remaining_content(adr_content)
        if remaining_content:
            console.print(Panel(
                Syntax(remaining_content, "markdown", theme="monokai", line_numbers=False),
                title="[bold green]ADR Content[/bold green]",
                border_style="green",
                padding=(0, 1),
            ))
            console.print()
        else:
            console.print("[yellow]No additional content to display[/yellow]")


def _extract_title(content: str) -> str:
    """
    Extract the title (first heading) from ADR content.
    
    Args:
        content: ADR markdown content
        
    Returns:
        Title text without markdown heading syntax
    """
    lines = content.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("#"):
            # Remove leading # characters and whitespace
            title = line.lstrip("#").strip()
            return title if title else "Untitled ADR"
    return "Untitled ADR"


def _format_metadata(metadata: dict) -> str:
    """
    Format metadata for display.
    
    Args:
        metadata: Metadata dictionary
        
    Returns:
        Formatted metadata string
    """
    lines = []
    
    # Helper to format values
    def format_value(key: str, value, indent: int = 0) -> str:
        prefix = "  " * indent
        if isinstance(value, dict):
            result = [f"{prefix}[cyan]{key}[/cyan]:"]
            for k, v in value.items():
                result.append(format_value(k, v, indent + 1))
            return "\n".join(result)
        elif isinstance(value, list):
            result = [f"{prefix}[cyan]{key}[/cyan]:"]
            for item in value:
                result.append(f"{prefix}  • [white]{item}[/white]")
            return "\n".join(result)
        else:
            return f"{prefix}[cyan]{key}[/cyan]: [white]{value}[/white]"
    
    # Format top-level keys
    for key, value in metadata.items():
        lines.append(format_value(key, value))
    
    return "\n".join(lines)


def _extract_remaining_content(content: str) -> str:
    """
    Extract content after the title for display.
    
    Args:
        content: ADR markdown content
        
    Returns:
        Remaining content after the title
    """
    lines = content.split("\n")
    
    # Skip the title (first heading)
    for i, line in enumerate(lines):
        if line.strip().startswith("#"):
            # Return everything after this line
            remaining = "\n".join(lines[i + 1:]).lstrip("\n")
            return remaining
    
    # If no heading found, return entire content
    return content
