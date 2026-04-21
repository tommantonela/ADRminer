"""Utility commands for diagnostics and testing."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from adrminer.config import get_settings
from adrminer.models.llm_factory import create_llm, reset_llm_cache
from adrminer.config import reset_settings

util_app = typer.Typer(help="Utility commands")
console = Console()


@util_app.command()
def llm(
    prompt: str = typer.Option(
        "How are you doing?",
        "--prompt",
        "-p",
        help="Test prompt to send to LLM"
    ),
) -> None:
    """
    Check and test currently configured LLM.
    
    Displays current LLM configuration and sends a test prompt
    to verify LLM is working correctly.
    
    \b
    Examples:
        # Check LLM with default test prompt
        adrminer util llm
        
        # Use custom test prompt
        adrminer util llm --prompt "What is 2+2?"
    """
    # Reset caches to ensure fresh configuration
    reset_settings()
    reset_llm_cache()
    
    # Load settings
    settings = get_settings()
    
    # Display configuration
    console.print("\n[bold cyan]🔧 Current LLM Configuration[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="green")
    table.add_column("Value", style="yellow")
    
    table.add_row("Provider", settings.llm.provider)
    table.add_row("Model", settings.llm.model)
    table.add_row("Temperature", str(settings.llm.temperature))
    table.add_row("Max Tokens", str(settings.llm.max_tokens))
    if settings.llm.provider == "ollama":
        table.add_row("Ollama Base URL", settings.llm.ollama_base_url or "default")
    
    console.print(table)
    
    # Create LLM instance
    console.print("\n[blue]Creating LLM instance...[/blue]")
    try:
        llm = create_llm()
        console.print(f"[green]✓ LLM created successfully[/green]")
        console.print(f"[dim]Type: {type(llm).__module__}.{type(llm).__name__}[/dim]\n")
    except Exception as e:
        console.print(f"[red]✗ Failed to create LLM: {e}[/red]")
        raise typer.Exit(code=1)
    
    # Send test prompt
    console.print(f"[blue]Sending test prompt...[/blue]")
    console.print(f'[dim]Prompt: "{prompt}"[/dim]\n')
    
    try:
        response = llm.invoke(prompt)
        console.print(Panel(
            f"[bold]Response:[/bold]\n{response.content}",
            title="[green]✓ LLM Response[/green]",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"[red]✗ Failed to get response: {e}[/red]")
        raise typer.Exit(code=1)


@util_app.command()
def inspect(
    path: Path = typer.Argument(
        ...,
        help="Path to ADR file",
        exists=True,
    ),
    metadata: bool = typer.Option(
        False,
        "--metadata",
        "-m",
        help="Show metadata alongside ADR (if available in sidecar files)",
    ),
    raw: bool = typer.Option(
        False,
        "--raw",
        help="Show raw content without Markdown formatting",
    ),
    width: Optional[int] = typer.Option(
        None,
        "--width",
        "-w",
        help="Set display width (default: auto-detect terminal width)",
    ),
) -> None:
    """
    Inspect and display an ADR with Rich Markdown rendering.
    
    Displays ADR content with beautiful Markdown formatting in console.
    Can optionally display metadata from sidecar files.
    
    \b
    Examples:
        # View ADR with Markdown rendering
        adrminer util inspect examples/pharmacy-food/adrs/ADR001-microservice-style.md
        
        # View ADR with metadata
        adrminer util inspect examples/pharmacy-food/adrs/ADR001-microservice-style.md --metadata
        
        # View raw content (no Markdown formatting)
        adrminer util inspect examples/pharmacy-food/adrs/ADR001-microservice-style.md --raw
    """
    # Validate file is a markdown file
    if path.suffix not in [".md", ".MD", ".markdown"]:
        console.print(f"[red]✗ Error: {path.name} is not a markdown file[/red]")
        raise typer.Exit(code=1)
    
    # Read ADR content
    try:
        with open(path, "r", encoding="utf-8") as f:
            adr_content = f.read()
    except Exception as e:
        console.print(f"[red]✗ Failed to read {path.name}: {e}[/red]")
        raise typer.Exit(code=1)
    
    # Display ADR header
    console.print(f"\n[bold cyan]📄 {path.name}[/bold cyan]\n")
    
    # Create console with custom width if specified
    if width:
        display_console = Console(width=width)
    else:
        display_console = console
    
    # Render content
    if raw:
        # Display raw content
        display_console.print(adr_content)
    else:
        # Display with Rich Markdown
        display_console.print(Panel(
            Markdown(adr_content),
            title="[bold]ADR Content[/bold]",
            border_style="cyan",
            padding=(1, 2),
        ))
    
    # Display metadata if requested
    if metadata:
        _display_metadata(path, display_console)


def _load_adr_files(path: Path) -> list[Path]:
    """
    Load ADR files from a path.
    
    Args:
        path: Path to ADR file or directory
    
    Returns:
        List of ADR file paths
    """
    if path.is_file():
        # Single ADR file
        if path.suffix in [".md", ".MD", ".markdown"]:
            return [path]
        else:
            return []
    elif path.is_dir():
        # Directory: load all .md files
        return sorted(path.glob("*.md"))
    else:
        return []


def _has_metadata(adr_path: Path) -> bool:
    """
    Check if an ADR has metadata file.
    
    Args:
        adr_path: Path to ADR file
    
    Returns:
        True if metadata file exists
    """
    metadata_paths = [
        adr_path.with_suffix('.adrminer.checking.json'),
        adr_path.with_suffix('.metadata.json'),
        adr_path.with_suffix('.adrminer.classification.json'),
    ]
    return any(mp.exists() for mp in metadata_paths)


def _load_metadata(adr_path: Path) -> dict | None:
    """
    Load metadata for an ADR.
    
    Args:
        adr_path: Path to ADR file
    
    Returns:
        Metadata dict or None
    """
    metadata_paths = [
        adr_path.with_suffix('.adrminer.checking.json'),
        adr_path.with_suffix('.metadata.json'),
        adr_path.with_suffix('.adrminer.classification.json'),
    ]
    
    for metadata_path in metadata_paths:
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                continue
    
    return None


def _extract_title(content: str) -> str:
    """
    Extract title from ADR content.
    
    Args:
        content: ADR markdown content
    
    Returns:
        Title string
    """
    # Try to find first heading
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('#'):
            # Remove # and trim
            title = line.lstrip('#').strip()
            return title[:60] + '...' if len(title) > 60 else title
    return "No title"


@util_app.command()
def list(
    path: Path = typer.Argument(
        ...,
        help="Path to ADR file or directory",
        exists=True,
    ),
    has_metadata: bool = typer.Option(
        False,
        "--has-metadata",
        "-m",
        help="Show only ADRs that have metadata",
    ),
    details: bool = typer.Option(
        False,
        "--details",
        "-d",
        help="Show detailed information (title, status, topic, classifications)",
    ),
    compact: bool = typer.Option(
        False,
        "--compact",
        "-c",
        help="Show compact list (filenames only)",
    ),
) -> None:
    """
    List ADRs in a given location.
    
    Displays ADR files with optional filtering and detail levels.
    Shows metadata information when available.
    
    \b
    Examples:
        # List all ADRs
        adrminer util list examples/pharmacy-food/adrs
        
        # List only ADRs with metadata
        adrminer util list examples/pharmacy-food/adrs --has-metadata
        
        # List with details
        adrminer util list examples/pharmacy-food/adrs --details
        
        # Compact list (filenames only)
        adrminer util list examples/pharmacy-food/adrs --compact
    """
    # Load ADR files
    adr_files = _load_adr_files(path)
    
    if not adr_files:
        console.print(f"[red]✗ No ADR files found in {path}[/red]")
        raise typer.Exit(code=1)
    
    # Filter by metadata if requested
    if has_metadata:
        adr_files = [f for f in adr_files if _has_metadata(f)]
        if not adr_files:
            console.print(f"[yellow]⚠ No ADRs with metadata found in {path}[/yellow]")
            raise typer.Exit(code=0)
    
    # Compact mode: just list filenames
    if compact:
        console.print(f"[cyan]Found {len(adr_files)} ADR(s):[/cyan]\n")
        for adr_file in adr_files:
            console.print(f"  • {adr_file.name}")
        return
    
    # Display in table
    if details:
        # Detailed table
        table = Table(title=f"ADRs ({len(adr_files)} found)")
        table.add_column("#", style="cyan", width=4)
        table.add_column("File", style="green", no_wrap=True)
        table.add_column("Title", style="yellow")
        table.add_column("Has Metadata", justify="center", width=14)
        table.add_column("Topic", style="magenta")
        
        for idx, adr_file in enumerate(adr_files, 1):
            # Read ADR content
            try:
                with open(adr_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                title = _extract_title(content)
            except Exception:
                title = "Error reading"
            
            # Check for metadata
            has_meta = _has_metadata(adr_file)
            meta_status = "[green]✓[/green]" if has_meta else "[dim]–[/dim]"
            
            # Load topic if available
            topic = "N/A"
            if has_meta:
                metadata = _load_metadata(adr_file)
                if metadata and "topics" in metadata:
                    topic_data = metadata["topics"]
                    topic = topic_data.get("topic_label", "N/A")
                    # Truncate if too long
                    topic = topic[:25] + '...' if len(topic) > 25 else topic
            
            table.add_row(str(idx), adr_file.name, title, meta_status, topic)
        
        console.print(table)
    else:
        # Simple table
        table = Table(title=f"ADRs ({len(adr_files)} found)")
        table.add_column("#", style="cyan", width=4)
        table.add_column("File", style="green", no_wrap=True)
        table.add_column("Has Metadata", justify="center", width=14)
        
        for idx, adr_file in enumerate(adr_files, 1):
            has_meta = _has_metadata(adr_file)
            meta_status = "[green]✓[/green]" if has_meta else "[dim]–[/dim]"
            table.add_row(str(idx), adr_file.name, meta_status)
        
        console.print(table)


def _display_metadata(adr_path: Path, console: Console) -> None:
    """
    Display metadata for an ADR if available in sidecar files.
    
    Args:
        adr_path: Path to ADR file
        console: Console instance to use for output
    """
    # Try to find metadata file
    metadata = None
    metadata_paths = [
        adr_path.with_suffix('.adrminer.checking.json'),
        adr_path.with_suffix('.metadata.json'),
        adr_path.with_suffix('.adrminer.classification.json'),
    ]
    
    for metadata_path in metadata_paths:
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                break
            except Exception as e:
                console.print(f"[yellow]⚠ Warning: Could not read {metadata_path.name}: {e}[/yellow]")
                continue
    
    if not metadata:
        console.print("\n[yellow]⚠ No metadata found for this ADR[/yellow]")
        return
    
    # Display metadata in table
    console.print("\n[bold cyan]📊 Metadata[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Category", style="green", width=20)
    table.add_column("Value", style="yellow")
    
    # Topic
    if "topics" in metadata:
        topic = metadata["topics"]
        table.add_row("Topic", topic.get("topic_label", "N/A"))
        table.add_row("Probability", f"{topic.get('probability', 0):.2%}")
    
    # Classifications
    if "classifications" in metadata:
        for framework, cls in metadata["classifications"].items():
            primary = cls.get("primary_category", "N/A")
            confidence = cls.get("confidence", 0)
            table.add_row(framework.capitalize(), f"{primary} ({confidence:.0%})")
    
    # Quality check
    if "check" in metadata:
        quality = metadata["check"]
        adherence = quality.get("template_adherence", {})
        score = adherence.get("adherence_score", "N/A")
        table.add_row("Quality Score", str(score))
        
        # Section summary
        assessments = quality.get("section_assessments", [])
        if assessments:
            present = sum(1 for a in assessments if a.get("presence") == "Yes")
            table.add_row("Sections Present", f"{present}/{len(assessments)}")
    
    console.print(table)
