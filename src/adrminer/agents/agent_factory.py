"""Factory for creating Agents for ADRminer.

This module provides the factory function to create configured agent
instances with appropriate tools and system prompts for ADRminer's
natural language interface. Uses LangChain implementation.
"""

from typing import Any, Dict, Optional

from adrminer.agents.langchain_agent import (
    LangChainAdrminerAgent,
    create_langchain_agent
)


def create_adrminer_agent(
    session,
    config: Optional[Any] = None
):
    """
    Factory function to create configured agent instance.
    
    This function creates a LangChain agent with ADRminer-specific
    configuration, including tools and system prompt. Uses LangChain's
    create_agent() from the fundamentals skill.
    
    Args:
        session: SessionManager instance for accessing ADRminer services
        config: Optional AgentConfig (uses default if not provided)
    
    Returns:
        Compiled LangChain agent ready for execution
    
    Raises:
        ImportError: If required packages are not installed
        RuntimeError: If agent creation fails
    """
    # Use the LangChain agent factory
    return create_langchain_agent(session, config)


class AdrminerAgent:
    """Wrapper around LangChain Agent with ADRminer-specific functionality.
    
    This class provides a convenient interface for interacting with the
    LangChain agent, including context management and response handling.
    It's a drop-in replacement for the original Deep Agent implementation.
    """
    
    def __init__(self, session, config: Optional[Any] = None):
        """
        Initialize ADRminer Agent.
        
        Args:
            session: SessionManager instance
            config: Optional AgentConfig
        """
        self.session = session
        self.config = config
        
        # Create the LangChain Agent wrapper
        self.langchain_agent = LangChainAdrminerAgent(session, config)
    
    def process_natural_language(self, user_input: str) -> Dict[str, Any]:
        """
        Process natural language query through the agent.
        
        Args:
            user_input: Natural language query from user
        
        Returns:
            Dictionary with agent response and metadata
        
        Raises:
            RuntimeError: If agent execution fails
        """
        # Delegate to LangChain agent
        return self.langchain_agent.process_natural_language(user_input)
    
    def handle_interrupt(self, interrupt_data: Dict[str, Any]) -> bool:
        """
        Handle human-in-the-loop interrupt.
        
        Note: This is a placeholder for future middleware integration.
        The current implementation does not support interrupts.
        
        Args:
            interrupt_data: Interrupt data from agent
        
        Returns:
            True if user approved, False if cancelled
        """
        # Delegate to LangChain agent
        return self.langchain_agent.handle_interrupt(interrupt_data)
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get current agent context.
        
        Returns:
            Dictionary with current context
        """
        return self.langchain_agent.get_context()
    
    def update_context(self, updates: Dict[str, Any]):
        """
        Update agent context.
        
        Args:
            updates: Dictionary of context updates
        """
        # Delegate to LangChain agent
        self.langchain_agent.update_context(updates)
    
    def get_thread_id(self) -> str:
        """Get the thread ID for this session."""
        return self.langchain_agent.get_thread_id()
    
    def get_agent(self):
        """
        Get the underlying LangChain agent.
        
        Returns:
            LangChain agent instance
        """
        return self.langchain_agent.get_agent()