"""Deep Agent implementation for ADRminer (legacy).

This module contains the original Deep Agent implementation using the
Deep Agents framework. This has been replaced by the LangChain
implementation in langchain_agent.py but is kept for reference
and potential future use.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from adrminer.agents.tools import (
    load_adrs,
    mine_topics,
    classify_adrs,
    check_quality,
    generate_insights,
    # export_metadata,
    get_topic_info,
    get_classification_info,
    list_adr_files,
    set_session
)
from adrminer.agents.context import AgentContext
from adrminer.config import get_settings

# Import Deep Agents framework
from deepagents import create_deep_agent, FilesystemPermission
from deepagents.backends import FilesystemBackend, StoreBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

# System prompt for the ADRminer agent
SYSTEM_PROMPT = """You are ADRminer Assistant, an AI-powered assistant for analyzing Architectural Decision Records (ADRs).

Your capabilities, which rely on specific tools you can access, include:
- Loading and managing ADR files (tool: load_adrs)
- Discovering ADR files in directories (tool: list_adr_files)
- Mining topics using BERTopic (tool: mine_topics)
- Viewing topic model information (tool: get_topic_info)
- Classifying ADRs using various frameworks (Kruchten, Quality Attributes, Zimmermann) (tool: classify_adrs)
- Viewing classification framework information (tool: get_classification_info)
- Checking ADR quality against templates (e.g., MADR) (tool: check_quality)
- Generating insights from analysis results (tool: generate_insights)
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
"""


def create_deep_adrminer_agent(
    session,
    config: Optional[Any] = None
):
    """
    Factory function to create configured Deep Agent instance.
    
    This function creates a Deep Agent with ADRminer-specific configuration,
    including middleware (TodoList, Filesystem, HITL, Memory), tools,
    and system prompt.
    
    Args:
        session: SessionManager instance for accessing ADRminer services
        config: Optional AgentConfig (uses default if not provided)
    
    Returns:
        Compiled Deep Agent graph ready for execution
    
    Raises:
        ImportError: If deepagents or langgraph are not installed
        RuntimeError: If agent creation fails
    """

    
    # Get settings
    settings = get_settings()
    agent_config = config or settings.agent
    
    # Set session reference for tools
    set_session(session)
    
    # Initialize agent context
    agent_context = AgentContext()
    agent_context.load_from_session(session)
    
    # Print backend/middleware availability info
    if hasattr(session, 'console'):       
        # Print agent context
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
    
    # Collect all tools
    tools = [
        load_adrs,
        list_adr_files,
        mine_topics,
        get_topic_info,
        classify_adrs,
        get_classification_info,
        check_quality,
        generate_insights,
        # export_metadata
    ]
    
    # Create checkpointer and store separately
    checkpointer = MemorySaver() if agent_config.memory_enabled else None
    store = None
    
    # Initialize filesystem backend
    fs_backend = FilesystemBackend(
        root_dir=str(Path.cwd()),
        virtual_mode=True # agent_config.middleware.virtual_filesystem
    )
    
    # Configure middleware based on settings
    middleware = []
    # TodoList middleware for task planning (if available)
    # todo_middleware = TodoListMiddleware()
    # middleware.append(todo_middleware)
    # memory_middleware = MemoryMiddleware(backend=memory_backend, sources=[])
    # middleware.append(memory_middleware)
    
    # Customize system prompt with current context
    dirs_str = ", ".join(str(d) for d in agent_context.available_directories)
    context_info = {
        "available_directories": dirs_str,
        "loaded_adr_count": agent_context.get_loaded_adr_count(),
        "available_analyses": list(agent_context.analysis_results.keys())
    }
    customized_prompt = SYSTEM_PROMPT.format(**context_info)
    
    # Configure interrupt rules for HITL
    interrupt_on = {}
    if agent_config.hitl_enabled:
        interrupt_on = {
            "classify_adrs": True,
            "check_quality": True,
            "mine_topics": True
        }
    
    # Create the agent
    try:
        agent = create_deep_agent(
            model=settings.llm.model,
            backend=fs_backend,
            # permissions=[
            #         FilesystemPermission(
            #             operations=["write"],
            #             paths=["/**"],
            #             mode="deny",
            #         ),
            #     ],
            tools=tools,
            system_prompt=customized_prompt,
            # middleware=[], #middleware,
            # interrupt_on=interrupt_on,
            # checkpointer=checkpointer,
            # store=store
        )
        
        return agent
        
    except Exception as e:
        raise RuntimeError(f"Failed to create Deep Agent: {e}")


class DeepAdrminerAgent:
    """Wrapper around Deep Agent with ADRminer-specific functionality.
    
    This class provides a convenient interface for interacting with the
    Deep Agent, including context management and response handling.
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
        self.context = AgentContext()
        self.context.load_from_session(session)
        
        # Create the Deep Agent
        self.agent = create_deep_adrminer_agent(session, config)
        
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
            result = self.agent.invoke(
                {
                    "messages": [
                        {"role": "user", "content": user_input}
                    ]
                },
                config={
                    "configurable": {
                        "thread_id": self.thread_id
                    }
                }
            )
            
            # Sync context back to session
            self.context.sync_to_session(self.session)
            
            return {
                "success": True,
                "response": result.get("messages", [])[-1].content if result.get("messages") else "",
                "data": result.get("data", {}),
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
        
        Args:
            interrupt_data: Interrupt data from agent
        
        Returns:
            True if user approved, False if cancelled
        """
        # Extract interrupt information
        tool_name = interrupt_data.get("tool_name")
        message = interrupt_data.get("message", "")
        num_affected = interrupt_data.get("num_affected", 0)
        
        # Format message
        if num_affected > 0:
            formatted_message = message.format(num=num_affected)
        else:
            formatted_message = message
        
        # For now, we'll assume approval
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