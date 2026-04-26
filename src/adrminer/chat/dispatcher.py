"""Command dispatcher for interactive chat CLI."""

from typing import Dict, Optional

from rich.markdown import Markdown

from adrminer.chat.session import SessionManager
from adrminer.chat.parser import CommandParseError, CommandParser
from adrminer.chat.recommendation_service import RecommendationService
from adrminer.chat.handlers import (
    HelpHandler,
    ListHandler,
    LLMHandler,
    InspectHandler,
    EnhancedListHandler,
    SummaryHandler,
    QuitHandler,
    ResetMemoryHandler,
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
        self.recommendation_service = RecommendationService(session.console)
        
        # Map command/subcommand to handler classes
        self._handler_map = {
            "/help": HelpHandler,
            "/list": ListHandler,
            "/summary": SummaryHandler,
            "/quit": QuitHandler,
            "/reset_memory": ResetMemoryHandler,
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
        
        # Check if natural language input
        if self._is_natural_language(user_input):
            return self._route_to_agent(user_input)
        
        # Handle as command
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
    
    def _is_natural_language(self, user_input: str) -> bool:
        """
        Determine if input is natural language or a command.
        
        Args:
            user_input: Raw user input string
            
        Returns:
            True if input appears to be natural language, False if command
        """
        # Commands start with '/'
        if user_input.strip().startswith('/'):
            return False
        
        # Empty input is not natural language
        if not user_input.strip():
            return False
        
        # Short single words might be typos, treat as natural language
        # Agent can clarify if needed
        return True
    
    def _route_to_agent(self, user_input: str) -> Optional[bool]:
        """
        Route natural language input to Deep Agent.
        
        Args:
            user_input: Natural language query string
            
        Returns:
            True if processed successfully, False if quit, None if error
        """
        # Get agent (lazy-loaded)
        agent = self.session.agent
        
        if agent is None:
            self.session.console.print(
                "[yellow]AI assistant not available.[/yellow]\n"
                "[dim]Use commands (starting with /) for analysis.[/dim]"
            )
            return None
        
        # Sync context before processing
        self.session.sync_agent_context()
        
        # Process natural language query
        try:
            result = agent.process_natural_language(user_input)
            
            if result["success"]:
                # Display agent response with Markdown formatting
                response = result["response"]
                if response:
                    self.session.console.print()
                    self.session.console.print("[cyan bold]AI:[/cyan bold]")
                    self.session.console.print(Markdown(response))
                    self.session.console.print()
                
                # Display data if available
                if result.get("data"):
                    data = result["data"]
                    if isinstance(data, dict):
                        # Display structured data nicely
                        for key, value in data.items():
                            if isinstance(value, (list, dict)):
                                self.session.console.print(f"  [dim]{key}:[/dim] {len(value)} items" if isinstance(value, list) else f"  [dim]{key}:[/dim] {value}")
                            else:
                                self.session.console.print(f"  [dim]{key}:[/dim] {value}")
                
                # Show CLI command recommendations based on tools used
                tool_calls = agent.extract_tool_calls(result)
                if tool_calls:
                    self.recommendation_service.show_recommendations(tool_calls)
                
                return True
            else:
                # Error occurred
                self.session.console.print(f"[red]AI Error:[/red] {result['response']}")
                return None
                
        except Exception as e:
            self.session.console.print(f"[red]Error processing query:[/red] {e}")
            return None
