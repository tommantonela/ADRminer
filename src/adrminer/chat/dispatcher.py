"""Command dispatcher for interactive chat CLI."""

from typing import Dict, Optional

from adrminer.chat.session import SessionManager
from adrminer.chat.parser import CommandParseError, CommandParser
from adrminer.chat.handlers import (
    HelpHandler,
    ListHandler,
    LLMHandler,
    InspectHandler,
    EnhancedListHandler,
    SummaryHandler,
    QuitHandler,
    TopicsPredictHandler,
    TopicsInfoHandler,
    ClassifyPredictHandler,
    ClassifyInfoHandler,
    CheckPredictHandler,
)


class CommandDispatcher:
    """Dispatch parsed commands to appropriate handlers."""
    
    def __init__(self, session: SessionManager):
        """
        Initialize dispatcher.
        
        Args:
            session: Session manager instance
        """
        self.session = session
        self.parser = CommandParser()
        
        # Map command/subcommand to handler classes
        self._handler_map = {
            "/help": HelpHandler,
            "/list": ListHandler,
            "/summary": SummaryHandler,
            "/quit": QuitHandler,
            "/topics": {
                "predict": TopicsPredictHandler,
                "info": TopicsInfoHandler,
            },
            "/classify": {
                "predict": ClassifyPredictHandler,
                "info": ClassifyInfoHandler,
            },
            "/check": {
                "predict": CheckPredictHandler,
            },
            "/util": {
                "llm": LLMHandler,
                "inspect": InspectHandler,
                "list": EnhancedListHandler,
            },
        }
    
    def dispatch(self, user_input: str) -> Optional[bool]:
        """
        Parse and dispatch user input to handler.
        
        Args:
            user_input: Raw user input string
            
        Returns:
            True if command was handled successfully, False if quit command,
            None if there was an error
        """
        # Add to history
        self.session.add_to_history(user_input)
        
        try:
            # Parse command
            parsed = self.parser.parse(user_input)
        except CommandParseError as e:
            self.session.console.print(f"[red]Parse Error:[/red] {e}")
            return None
        
        command = parsed["command"]
        subcommand = parsed.get("subcommand")
        args = parsed["args"]
        options = parsed["options"]
        
        # Handle quit command specially
        if command == "/quit":
            return False
        
        # Get handler class
        handler_class = self._get_handler_class(command, subcommand)
        
        if handler_class is None:
            self.session.console.print(f"[red]Error:[/red] No handler for {command}")
            if subcommand:
                self.session.console.print(f"  Subcommand: {subcommand}")
            return None
        
        # Instantiate and execute handler
        try:
            handler = handler_class(self.session)
            handler.execute(args, options)
            return True
        except Exception as e:
            self.session.console.print(
                f"[red]Error executing command:[/red] {e}\n"
                f"[dim]Command: {parsed['raw']}[/dim]"
            )
            return None
    
    def _get_handler_class(
        self,
        command: str,
        subcommand: Optional[str]
    ) -> Optional[type]:
        """
        Get handler class for command/subcommand.
        
        Args:
            command: Command name (e.g., "/topics")
            subcommand: Subcommand name (e.g., "predict")
            
        Returns:
            Handler class or None if not found
        """
        handler = self._handler_map.get(command)
        
        if handler is None:
            return None
        
        # If handler is a dict, look up subcommand
        if isinstance(handler, dict):
            if subcommand is None:
                return None
            return handler.get(subcommand)
        
        # Handler is a class (no subcommands)
        return handler