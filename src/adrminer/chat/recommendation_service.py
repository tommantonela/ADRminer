"""CLI Command Recommendation Service.

This service provides CLI command recommendations to users after they
interact with the agent, helping them discover equivalent
CLI commands for direct execution.
"""

from typing import Dict, List, Optional, Set
from rich.console import Console

from adrminer.agents import tools


class RecommendationService:
    """Service for providing CLI command recommendations.
    
    This service reads metadata from agent tools (decorated with
    @tool_metadata) and generates CLI command recommendations
    to help users discover equivalent CLI commands.
    """
    
    def __init__(self, console: Console):
        """Initialize the recommendation service.
        
        Args:
            console: Rich console for formatted output
        """
        self.console = console
        self._tool_metadata_cache = self._build_metadata_cache()
    
    def _build_metadata_cache(self) -> Dict[str, Dict]:
        """Build a cache of tool metadata.
        
        Returns:
            Dictionary mapping tool names to their metadata
        """
        cache = {}
        
        # List of tools to check for metadata
        tool_functions = [
            tools.load_adrs,
            tools.list_adr_files,
            tools.mine_topics,
            tools.classify_adrs,
            tools.check_quality,
            tools.generate_insights,
            tools.get_topics_info,
            tools.get_classification_info,
            tools.reset_memory
        ]
        
        # Extract metadata from each tool
        for tool in tool_functions:
            # Handle both raw functions and LangChain StructuredTool objects
            if hasattr(tool, 'name'):
                # This is a StructuredTool
                tool_name = tool.name
                
                # Check for metadata on the tool object itself
                if hasattr(tool, '_tool_metadata'):
                    cache[tool_name] = tool._tool_metadata
            elif hasattr(tool, '__name__'):
                # This is a raw function
                tool_name = tool.__name__
                
                if hasattr(tool, '_tool_metadata'):
                    cache[tool_name] = tool._tool_metadata
        
        return cache
    
    def get_recommendations(self, tool_names: List[str]) -> Dict[str, List[str]]:
        """Get CLI command recommendations for used tools.
        
        Args:
            tool_names: List of tool names that were used
        
        Returns:
            Dictionary mapping descriptions to lists of commands
        """
        recommendations = {}
        seen_commands: Set[str] = set()
        
        for tool_name in tool_names:
            metadata = self._tool_metadata_cache.get(tool_name)
            if not metadata:
                continue
            
            related_commands = metadata.get('related_commands', [])
            description = metadata.get('description', 'CLI commands')
            
            # Initialize list for this description if not exists
            if description not in recommendations:
                recommendations[description] = []
            
            # Add commands we haven't seen yet
            for cmd in related_commands:
                if cmd not in seen_commands:
                    recommendations[description].append(cmd)
                    seen_commands.add(cmd)
        
        return recommendations
    
    def show_recommendations(self, tool_names: List[str]):
        """Display CLI command recommendations to the user.
        
        Args:
            tool_names: List of tool names that were used
        """
        recommendations = self.get_recommendations(tool_names)
        
        if not recommendations:
            return
        
        # Display compact recommendations
        self.console.print()
        self.console.print("[cyan bold]💡 Tip:[/cyan bold] You can also execute these commands directly:", highlight=False)
        self.console.print()
        
        # Group commands by description
        for description, commands in recommendations.items():
            # Display description (without heading markers)
            self.console.print(f"[dim]{description}:[/dim]")
            
            # Display commands inline
            cmd_list = ", ".join(f"[cyan]{cmd}[/cyan]" for cmd in commands)
            self.console.print(f"  {cmd_list}")
            self.console.print()
        
        self.console.print("[dim]Type any command to execute it, or use /help for more information.[/dim]", highlight=False)
        self.console.print()
    
    def get_all_tools_metadata(self) -> Dict[str, Dict]:
        """Get metadata for all available tools.
        
        Returns:
            Dictionary mapping tool names to their metadata
        
        Useful for debugging or displaying all available recommendations.
        """
        return self._tool_metadata_cache.copy()