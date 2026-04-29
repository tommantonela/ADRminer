"""LangChain-based agent for ADRminer.

This module provides an alternative agent implementation using LangChain's
create_agent() with ADRminer tools and read-only file management capabilities.
"""

from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_community.agent_toolkits.file_management.toolkit import FileManagementToolkit

from langgraph.checkpoint.memory import InMemorySaver  

from langchain.agents.middleware import SummarizationMiddleware

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


def load_system_prompt() -> str:
    """Load the system prompt from the prompts directory."""
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_file = prompts_dir / "agent_system_prompt.md"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Agent system prompt not found at {prompt_file}")
    
    return prompt_file.read_text(encoding="utf-8")


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
    
    # Create LLM via factory (passes max_input_tokens to the model)
    llm = create_llm(settings=settings)
    
    # Customize system prompt with current context
    dirs_str = ", ".join(str(d) for d in agent_context.available_directories)
    context_info = {
        "available_directories": dirs_str,
        "loaded_adr_count": agent_context.get_loaded_adr_count(),
        "available_analyses": list(agent_context.analysis_results.keys())
    }
    
    # Load and customize system prompt
    system_prompt = load_system_prompt()
    customized_prompt = system_prompt.format(**context_info)
    
    # Read summarization middleware parameters from settings
    mw = settings.agent.middleware
    
    # Create agent using LangChain v1 API
    try:
        agent = create_agent(
            model=llm,
            tools=all_tools,
            system_prompt=customized_prompt,
            checkpointer=InMemorySaver(),
            middleware=[
                # Trigger automatic summarization when the context window reaches
                # a given fraction of capacity or a max number of messages accumulated,
                # then reduce the context keeping only a fraction of it
                SummarizationMiddleware(
                    model=llm,
                    trigger=[
                        ("fraction", mw.summarization_trigger_fraction),
                        ("messages", mw.summarization_trigger_messages),
                    ],
                    keep=("fraction", mw.summarization_keep_fraction)
                )
            ]
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
        
        # Use session's shared agent context instead of creating a new one
        self.context = session.agent_context
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
    
    def _build_context_summary(self) -> str:
        """
        Build a human-readable context summary from current session state.
        
        This summary is injected into each user message so the LLM always
        sees the latest analysis results, even if they were produced by
        direct commands (not by the agent's own tools).
        
        Returns:
            Formatted context string for LLM consumption
        """
        lines = ["[Current Session Context]"]
        
        # Loaded ADRs
        adr_count = self.context.get_loaded_adr_count()
        if adr_count > 0:
            lines.append(f"- Loaded ADRs: {adr_count} file(s)")
        else:
            lines.append("- Loaded ADRs: none")
        
        # Analysis results
        results = self.context.analysis_results
        if results:
            lines.append("- Available analyses:")
            
            # Classification results
            if "classification" in results:
                cls_data = results["classification"]
                if isinstance(cls_data, list):
                    count = len(cls_data)
                    categories = [r.get("primary_category", "Unknown") for r in cls_data if isinstance(r, dict)]
                    confidences = [r.get("confidence", 0.0) for r in cls_data if isinstance(r, dict)]
                    avg_conf = sum(confidences) / len(confidences) if confidences else 0
                    top_cats = Counter(categories).most_common(3)
                    cat_summary = ", ".join(f"{cat} ({cnt})" for cat, cnt in top_cats)
                    lines.append(f"  * Classification: {count} ADR(s) classified "
                                 f"(avg confidence: {avg_conf:.2f}, top: {cat_summary})")
                elif isinstance(cls_data, dict):
                    inner = cls_data.get("results", [])
                    framework = cls_data.get("framework", "unknown")
                    count = len(inner) if isinstance(inner, list) else 0
                    lines.append(f"  * Classification: {count} ADR(s) classified "
                                 f"(framework: {framework})")
            
            # Topics results
            if "topics" in results:
                topic_data = results["topics"]
                if isinstance(topic_data, list):
                    count = len(topic_data)
                    topic_labels = [r.get("topic_label", "Unknown") for r in topic_data if isinstance(r, dict)]
                    top_topics = Counter(topic_labels).most_common(3)
                    topic_summary = ", ".join(f"{t} ({c})" for t, c in top_topics)
                    lines.append(f"  * Topics: {count} ADR(s) analyzed "
                                 f"(top topics: {topic_summary})")
            
            # Check results
            if "check" in results:
                check_data = results["check"]
                if isinstance(check_data, list):
                    count = len(check_data)
                    scores = [r.get("template_adherence", {}).get("adherence_score", 0) 
                              for r in check_data 
                              if isinstance(r, dict) and "template_adherence" in r]
                    avg_score = sum(scores) / len(scores) if scores else 0
                    lines.append(f"  * Quality check: {count} ADR(s) checked "
                                 f"(avg adherence: {avg_score:.2f})")
                elif isinstance(check_data, dict):
                    inner = check_data.get("results", [])
                    mode = check_data.get("mode", "full")
                    count = len(inner) if isinstance(inner, list) else 0
                    lines.append(f"  * Quality check: {count} ADR(s) checked "
                                 f"(mode: {mode})")
            
            # Insights results
            if "insights" in results:
                insights = results["insights"]
                if isinstance(insights, dict):
                    lines.append(f"  * Insights: generated")
                elif isinstance(insights, list):
                    lines.append(f"  * Insights: {len(insights)} insight(s) generated")
        else:
            lines.append("- Available analyses: none yet")
        
        return "\n".join(lines)
    
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
            # Update context from session (picks up results from commands)
            self.context.load_from_session(self.session)
            
            # Build dynamic context summary and inject into message
            context_block = self._build_context_summary()
            enriched_input = f"{context_block}\n\n{user_input}"
            
            # Invoke agent with enriched message
            result = self.agent.invoke({
                "messages": [
                    {"role": "user", "content": enriched_input}
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
    
    def extract_tool_calls(self, result: Dict[str, Any]) -> List[str]:
        """
        Extract names of tools used in the agent result.
        
        Args:
            result: Result dictionary from agent processing
        
        Returns:
            List of tool names that were called
        """
        tool_names = []
        
        # Navigate through the agent result structure
        # LangChain agents store tool calls in messages
        messages = result.get("data", {}).get("messages", [])
        
        for message in messages:
            # Check if this is an AI message with tool calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.get('name', '')
                    if tool_name:
                        tool_names.append(tool_name)
        
        return tool_names
    
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