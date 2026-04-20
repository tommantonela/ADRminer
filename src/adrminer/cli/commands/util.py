"""Utility commands for diagnostics and testing."""

import typer
from rich.console import Console
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
    console.print(f"[dim]Prompt: \"{prompt}\"[/dim]\n")
    
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