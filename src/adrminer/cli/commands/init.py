"""Initialize ADRminer configuration."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

console = Console()

# Create init app
init_app = typer.Typer(help="Initialize ADRminer configuration")


@init_app.command()
def config(
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for config file (default: ./.adrminer.yaml in current directory)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing config file",
    ),
) -> None:
    """
    Create a default configuration file.
    
    This creates a YAML configuration file with default settings for ADRminer.
    """
    # Determine output path
    if output_path is None:
        # Default to current directory (project-local config)
        output_path = Path.cwd() / ".adrminer.yaml"
    else:
        output_path = output_path.expanduser()
    
    # Check if file exists
    if output_path.exists() and not force:
        console.print(
            f"[yellow]Config file already exists at {output_path}[/yellow]"
        )
        console.print("Use --force to overwrite.")
        raise typer.Exit(code=1)
    
    # Copy default config
    # Default config is packaged with the package
    import adrminer.config
    default_config_file = Path(adrminer.config.__file__).parent / "default_config.yaml"
    
    if not default_config_file.exists():
        console.print(f"[red]Default config not found at {default_config_file}[/red]")
        raise typer.Exit(code=1)
    
    import shutil
    
    try:
        shutil.copy(default_config_file, output_path)
        console.print(
            Panel(
                f"✅ Configuration file created at:\n\n[bold green]{output_path}[/bold green]\n\n"
                f"Edit this file to customize your ADRminer settings.",
                title="Configuration Initialized",
                border_style="green",
            )
        )
        
        # Show next steps
        console.print("\n[next steps]Next steps:[/next steps]")
        console.print("1. Edit the configuration file to set your preferences")
        console.print("2. Set up your API keys:")
        console.print("   - OpenAI: export OPENAI_API_KEY=your_key")
        console.print("   - Anthropic: export ANTHROPIC_API_KEY=your_key")
        console.print("3. Run: adrminer topics predict <path-to-adrs>")
        
    except Exception as e:
        console.print(f"[red]Failed to create config file: {e}[/red]")
        raise typer.Exit(code=1)


@init_app.command()
def models(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Download models even if they exist",
    ),
) -> None:
    """
    Download pre-trained models.
    
    This downloads the pre-trained BERTopic model and example files.
    """
    # Create models directory
    models_dir = Path.home() / ".adrminer" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if model already exists
    topic_model_path = models_dir / "topic_model"
    
    if topic_model_path.exists() and not force:
        console.print("[yellow]Topic model already downloaded.[/yellow]")
        console.print("Use --force to re-download.")
        return
    
    console.print("[blue]Downloading pre-trained topic model...[/blue]")
    
    # TODO: Implement model download
    # For now, just show what would happen
    console.print("\n[yellow]Model download not yet implemented.[/yellow]")
    console.print("\nFor now, please manually place your trained BERTopic model at:")
    console.print(f"  [bold]{topic_model_path}[/bold]")
    console.print("\nYou can train a model using:")
    console.print("  adrminer train topics <path-to-adrs>")


@init_app.command()
def examples(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Download examples even if they exist",
    ),
) -> None:
    """
    Download classification examples.
    
    This downloads few-shot examples for classification frameworks.
    """
    # Create examples directory
    examples_dir = Path.home() / ".adrminer" / "examples"
    examples_dir.mkdir(parents=True, exist_ok=True)
    
    console.print("[blue]Downloading classification examples...[/blue]")
    
    # TODO: Implement examples download
    # For now, just show what would happen
    console.print("\n[yellow]Examples download not yet implemented.[/yellow]")
    console.print("\nFor now, please manually place your example files at:")
    console.print(f"  [bold]{examples_dir}[/bold]")
    console.print("\nRequired files:")
    console.print("  - kruchten_examples.json")
    console.print("  - qas_examples.json")
    console.print("  - zimmermann_examples.json")