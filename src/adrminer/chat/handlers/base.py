"""Base handler class for command handlers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from adrminer.chat.session import SessionManager


class BaseHandler(ABC):
    """Base class for command handlers."""
    
    def __init__(self, session: SessionManager):
        """
        Initialize handler.
        
        Args:
            session: Session manager instance
        """
        self.session = session
    
    @abstractmethod
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any]
    ) -> None:
        """
        Execute the command.
        
        Args:
            args: Positional arguments
            options: Key-value options
        """
        pass
    
    def print_success(self, message: str):
        """Print success message."""
        self.session.console.print(f"[green]✓ {message}[/green]")
    
    def print_error(self, message: str):
        """Print error message."""
        self.session.console.print(f"[red]✗ {message}[/red]")
    
    def print_warning(self, message: str):
        """Print warning message."""
        self.session.console.print(f"[yellow]⚠ {message}[/yellow]")
    
    def print_info(self, message: str):
        """Print info message."""
        self.session.console.print(f"[blue]ℹ {message}[/blue]")
    
    def confirm_batch_operation(
        self,
        operation: str,
        file_count: int,
        threshold: int = 1
    ) -> bool:
        """
        Ask user for confirmation before batch operation.
        
        Args:
            operation: Description of operation
            file_count: Number of files to process
            threshold: Threshold for requiring confirmation (default: 1 = always confirm)
            
        Returns:
            True if user confirms, False otherwise
        """
        # Skip confirmation if below threshold
        if file_count < threshold:
            return True
        
        # Show simple, clear message
        self.session.console.print(
            f"\n[blue]ℹ About to process {file_count} ADR file(s)[/blue]"
        )
        self.session.console.print(
            f"[dim]Operation: {operation}[/dim]"
        )
        
        from rich.prompt import Prompt
        response = Prompt.ask(
            "\n[cyan]Continue? (yes/no or y/n)[/cyan]",
            default="yes"
        )
        
        return response.lower() in ["yes", "y"]
