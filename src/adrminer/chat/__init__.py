"""Interactive chat CLI module."""

from adrminer.chat.session import SessionManager
from adrminer.chat.parser import CommandParser, CommandParseError
from adrminer.chat.dispatcher import CommandDispatcher

__all__ = [
    "SessionManager",
    "CommandParser",
    "CommandParseError",
    "CommandDispatcher",
    "run_chat",
]


def run_chat(initial_dir=None):
    """
    Run interactive chat CLI.
    
    Args:
        initial_dir: Initial working directory (defaults to cwd)
    """
    from rich.console import Console
    from prompt_toolkit import prompt
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.styles import Style
    
    # Initialize console with theme
    console = Console()
    
    # Print welcome banner
    _print_welcome_banner(console)
    
    # Initialize session
    session = SessionManager(console, initial_dir=initial_dir)
    
    # Initialize dispatcher
    dispatcher = CommandDispatcher(session)
    
    # Setup command history
    history = InMemoryHistory()
    
    # Setup command auto-completion
    # Get all commands and subcommands for completion
    from adrminer.chat.commands import COMMAND_REGISTRY
    command_words = [cmd for cmd in COMMAND_REGISTRY.keys()]
    
    # Add subcommands (e.g., topics_predict, classify_predict)
    for cmd, info in COMMAND_REGISTRY.items():
        if "subcommands" in info:
            for subcmd in info["subcommands"].keys():
                command_words.append(f"{cmd[1:]}_{subcmd}")  # Remove leading / for subcommands
    
    command_completer = WordCompleter(
        command_words,
        ignore_case=True,
        sentence=True
    )
    
    # Setup prompt style (matching Rich's colors)
    prompt_style = Style.from_dict({
        'prompt': 'cyan bold',
    })
    
    def get_prompt():
        """Return the prompt text."""
        return [('class:prompt', 'ADRminer > ')]
    
    # Main loop
    while True:
        try:
            # Get user input with history and completion
            user_input = prompt(
                get_prompt,
                history=history,
                completer=command_completer,
                style=prompt_style,
                complete_while_typing=True,
                enable_history_search=True
            )
            
            # Skip empty input
            if not user_input.strip():
                continue
            
            # Add to session history (for potential future use)
            session.add_to_history(user_input)
            
            # Dispatch command
            result = dispatcher.dispatch(user_input)
            
            # Handle quit
            if result is False:
                console.print("\n[yellow]Goodbye![/yellow]\n")
                break
            
        except KeyboardInterrupt:
            # Handle Ctrl+C
            console.print("\n\n[yellow]Interrupted. Use /quit to exit.[/yellow]")
        except EOFError:
            # Handle Ctrl+D
            console.print("\n\n[yellow]Goodbye![/yellow]\n")
            break
        except Exception as e:
            console.print(f"\n[red]Unexpected error:[/red] {e}")


def _print_welcome_banner(console):
    """Print welcome banner."""
    console.print("\n")
    
    # Main banner (56 chars total, 54 chars between borders)
    console.print("[bold blue]╔══════════════════════════════════════════════════════╗[/bold blue]")
    console.print("[bold blue]║                                                      ║[/bold blue]")
    console.print("[bold blue]║          [yellow]✨ ADRminer Interactive CLI ✨[/yellow]              ║[/bold blue]")
    console.print("[bold blue]║                                                      ║[/bold blue]")
    console.print("[bold blue]║     [cyan]Analyze your Architecture Decision Records[/cyan]       ║[/bold blue]")
    console.print("[bold blue]║                                                      ║[/bold blue]")
    console.print("[bold blue]║  [dim]Topic Mining • Classification • Quality Checks[/dim]      ║[/bold blue]")
    console.print("[bold blue]║                                                      ║[/bold blue]")
    console.print("[bold blue]╚══════════════════════════════════════════════════════╝[/bold blue]")
    
    # Feature highlights
    # console.print("\n[bold green]Features:[/bold green]")
    # console.print("  [dim]•[/dim] [cyan]Interactive command loop[/cyan] - Run commands without repetition")
    # console.print("  [dim]•[/dim] [cyan]Session management[/cyan] - Maintain state across commands")
    # console.print("  [dim]•[/dim] [cyan]Lazy service loading[/cyan] - Fast startup, load on demand")
    # console.print("  [dim]•[/dim] [cyan]Command history[/cyan] - Navigate with ↑/↓ arrows")
    # console.print("  [dim]•[/dim] [cyan]Progress indicators[/cyan] - Visual feedback for long operations")
    
    # Quick start
    console.print("\n[bold yellow]Quick Start:[/bold yellow]")
    console.print("  [dim]•[/dim] Type [bold cyan]/help[/bold cyan] to see all available commands")
    console.print("  [dim]•[/dim] Type [bold cyan]/cd <path>[/bold cyan] to navigate to your ADR directory")
    console.print("  [dim]•[/dim] Type [bold cyan]/topics predict <path>[/bold cyan] to analyze topics")
    console.print("  [dim]•[/dim] Type [bold cyan]/quit[/bold cyan] to exit\n")
    
    # Tips
    # console.print("[dim]💡 Tip: Use Tab for auto-completion and ↑/↓ for command history[/dim]\n")
