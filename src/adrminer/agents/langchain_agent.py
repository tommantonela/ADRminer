"""LangChain-based agent for ADRminer.

This module provides an alternative agent implementation using LangChain's
create_agent() with ADRminer tools and read-only file management capabilities.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from langchain_community.agent_toolkits.file_management.toolkit import FileManagementToolkit

from langgraph.checkpoint.memory import InMemorySaver  

from adrminer.agents.tools import (
    load_adrs,
    mine_topics,
    classify_adrs,
    check_quality,
    generate_insights,
    # export_metadata,
    get_topics_info,
    get_classification_info,
    list_adr_files,
    reset_memory,
    set_session
)
from adrminer.agents.context import AgentContext
from adrminer.config import get_settings
from adrminer.models.llm_factory import create_llm

# System prompt for the ADRminer agent
SYSTEM_PROMPT = """You are ADRminer Assistant, an AI-powered assistant for analyzing Architectural Decision Records (ADRs).

Your capabilities, which rely on specific tools you can access, include:
- Loading and managing ADR files (tool: load_adrs)
- Discovering ADR files in directories (tool: list_adr_files)
- Reading file contents (tool: read_file)
- Listing directory contents (tool: list_directory)
- Mining topics using BERTopic (tool: mine_topics)
- Viewing topic model information (tool: get_topics_info)
- Classifying ADRs using various frameworks (Kruchten, Quality Attributes, Zimmermann) (tool: classify_adrs)
- Viewing classification framework information (tool: get_classification_info)
- Checking ADR quality against templates (e.g., MADR) (tool: check_quality)
- Generating insights from analysis results (tool: generate_insights)
- Resetting agent memory and analysis results (tool: reset_memory)
- Exporting metadata in various formats (tool: export_metadata)

Guidelines:
1. Always ask for clarification if a request is ambiguous
2. For batch operations affecting many ADRs, inform the user about the scope
3. Provide clear, actionable insights and recommendations
4. Use the available tools to perform analyses
5. Maintain context across the session (remember loaded ADRs, previous results)
6. Be concise but thorough in your responses
7. Suggest follow-up analyses when appropriate

Current context:
- Available directories: {available_directories}
- Loaded ADRs: {loaded_adr_count}
- Available analyses: {available_analyses}

You can help users with natural language queries like:
- "Analyze all ADRs in the adrs/ directory"
- "What topics are covered in my ADRs?"
- "Check the quality of these ADRs"
- "Classify ADRs using Kruchten's framework"
- "Generate insights from the analysis results"
- "Read the contents of ADR001.md"
"""


def create_langchain_agent(
    session,
    config: Optional[Any] = None
):
    """
    Factory function to create configured LangChain agent instance.
    
    This function creates a LangChain agent using create_agent() with
    ADRminer-specific configuration, including tools and system prompt.
    It's a drop-in replacement for the Deep Agent implementation.
    
    Args:
        session: SessionManager instance for accessing ADRminer services
        config: Optional AgentConfig (uses default if not provided)
    
    Returns:
        Compiled LangChain agent ready for execution
    
    Raises:
        ImportError: If required packages are not installed
        RuntimeError: If agent creation fails
    """
    # Import LangChain fundamentals (v1 API)
    from langchain.agents import create_agent
    
    # Get settings
    settings = get_settings()
    agent_config = config or settings.agent
    
    # Set session reference for tools
    set_session(session)
    
    # Initialize agent context
    agent_context = AgentContext()
    agent_context.load_from_session(session)
    
    # Print agent context
    if hasattr(session, 'console') and session.console is not None:       
        session.console.print("\n[bold cyan]Agent Context:[/bold cyan]")
        session.console.print(f"  [dim]Available directories:[/dim] {len(agent_context.available_directories)}")
        for i, directory in enumerate(agent_context.available_directories, 1):
            rel_path = directory.relative_to(Path.cwd()) if directory != Path.cwd() else "."
            session.console.print(f"    {i}. [cyan]{rel_path}[/cyan] ([dim]{directory}[/dim])")
        
        session.console.print(f"  [dim]Loaded ADRs:[/dim] {agent_context.get_loaded_adr_count()}")
        if agent_context.analysis_results:
            session.console.print(f"  [dim]Available analyses:[/dim] {', '.join(agent_context.analysis_results.keys())}")
        else:
            session.console.print(f"  [dim]Available analyses:[/dim] None")
        session.console.print()
    
    # Collect ADRminer tools
    adrminer_tools = [
        load_adrs,
        list_adr_files,
        mine_topics,
        get_topics_info,
        classify_adrs,
        get_classification_info,
        check_quality,
        generate_insights,
        reset_memory,
        # export_metadata
    ]
    
    # Create read-only FileManagementToolkit
    # Restrict to current working directory and subdirectories
    root_path = str(Path.cwd())
    
    file_management_toolkit = FileManagementToolkit(
        root_dir=root_path,
        # Only include read-only tools
        selected_tools=["read_file", "list_directory"]
    )
    
    # Get file management tools
    file_tools = file_management_toolkit.get_tools()
    
    # Combine all tools
    all_tools = adrminer_tools + file_tools
    
    # Create LLM
    llm = settings.llm.model # create_llm(settings.llm)
    
    # Customize system prompt with current context
    dirs_str = ", ".join(str(d) for d in agent_context.available_directories)
    context_info = {
        "available_directories": dirs_str,
        "loaded_adr_count": agent_context.get_loaded_adr_count(),
        "available_analyses": list(agent_context.analysis_results.keys())
    }
    customized_prompt = SYSTEM_PROMPT.format(**context_info)
    
    # Create agent using LangChain v1 API
    try:
        agent = create_agent(
            model=llm,
            tools=all_tools,
            system_prompt=customized_prompt,
            checkpointer=InMemorySaver()
        )
        
        return agent
        
    except Exception as e:
        raise RuntimeError(f"Failed to create LangChain agent: {e}")


class LangChainAdrminerAgent:
    """Wrapper around LangChain agent with ADRminer-specific functionality.
    
    This class provides a convenient interface for interacting with the
    LangChain agent, including context management and response handling.
    It's a drop-in replacement for the Deep Agent's AdrminerAgent class.
    """
    
    def __init__(self, session, config: Optional[Any] = None):
        """
        Initialize LangChain ADRminer Agent.
        
        Args:
            session: SessionManager instance
            config: Optional AgentConfig
        """
        self.session = session
        self.config = config
        self.context = AgentContext()
        self.context.load_from_session(session)
        
        # Create the LangChain agent
        self.agent = create_langchain_agent(session, config)
        
        # Thread ID for this session
        self.thread_id = self._generate_thread_id()
    
    def _generate_thread_id(self) -> str:
        """Generate unique thread ID for this session."""
        import uuid
        settings = get_settings()
        prefix = settings.agent.default_session_prefix
        return f"{prefix}{uuid.uuid4().hex[:8]}"
    
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
        try:
            # Update context
            self.context.load_from_session(self.session)
            
            # Invoke agent with standard message format
            result = self.agent.invoke({
                "messages": [
                    {"role": "user", "content": user_input}
                ]
            }, config={"configurable": {"thread_id": self.thread_id}})
            
            # Sync context back to session
            self.context.sync_to_session(self.session)
            
            # Extract response (last message)
            messages = result.get("messages", [])
            response = messages[-1].content if messages else ""
            
            return {
                "success": True,
                "response": response,
                "data": result,
                "thread_id": self.thread_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": f"Error processing query: {str(e)}",
                "data": {},
                "thread_id": self.thread_id
            }
    
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
        # For now, assume approval
        # In a real CLI, this would prompt the user
        # This will be handled by the CLI dispatcher
        return True
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get current agent context.
        
        Returns:
            Dictionary with current context
        """
        self.context.load_from_session(self.session)
        return self.context.to_dict()
    
    def update_context(self, updates: Dict[str, Any]):
        """
        Update agent context.
        
        Args:
            updates: Dictionary of context updates
        """
        # Update context based on provided updates
        if "available_directories" in updates:
            self.context.available_directories = [Path(p) for p in updates["available_directories"]]
        
        if "loaded_adrs" in updates:
            self.context.loaded_adrs = [Path(p) for p in updates["loaded_adrs"]]
        
        if "analysis_results" in updates:
            self.context.analysis_results = updates["analysis_results"]
        
        # Sync to session
        self.context.sync_to_session(self.session)
    
    def get_thread_id(self) -> str:
        """Get the thread ID for this session."""
        return self.thread_id
    
    def get_agent(self):
        """
        Get the underlying LangChain agent.
        
        Returns:
            LangChain agent instance
        """
        return self.agent