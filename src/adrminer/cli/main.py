"""Main CLI entry point for ADRminer."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from adrminer import __version__

# Create typer app
cli = typer.Typer(
    name="adrminer",
    help="Analyze your Architectural Decision Records (ADRs)",
    add_completion=True,
    no_args_is_help=True,
)

# Rich console
console = Console()


@cli.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (YAML)",
        exists=True,
    ),
) -> None:
    """
    ADRminer - Analyze your Architectural Decision Records.
    
    Extract topics, classify decisions, and check quality using AI.
    """
    if version:
        typer.echo(f"ADRminer {__version__}")
        raise typer.Exit()
    
    # Load custom config if provided
    if config:
        from adrminer.config import get_settings
        get_settings(config_path=config)


# Import subcommands
from adrminer.cli.commands.init import init_app
from adrminer.cli.commands.topics import topics_app
from adrminer.cli.commands.classify import classify_app
from adrminer.cli.commands.check import check
from adrminer.cli.commands.util import util_app

# Register subcommands
cli.add_typer(init_app, name="init", help="Initialize ADRminer configuration")
cli.add_typer(topics_app, name="topics", help="Topic mining commands")
cli.add_typer(classify_app, name="classify", help="Classification commands")
cli.command(name="check")(check)
cli.add_typer(util_app, name="util", help="Utility commands")


if __name__ == "__main__":
    cli()