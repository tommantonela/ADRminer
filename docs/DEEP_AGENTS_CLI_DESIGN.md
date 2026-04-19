# ADRminer Deep Agents CLI Design

**Version:** 1.0  
**Date:** 2026-04-19  
**Status:** Design Phase - Ready for Implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Framework Selection](#framework-selection)
3. [Architecture Overview](#architecture-overview)
4. [Deep Agents Setup](#deep-agents-setup)
5. [Tool Wrappers](#tool-wrappers)
6. [Interactive CLI Design](#interactive-cli-design)
7. [Hybrid Command Interface](#hybrid-command-interface)
8. [Implementation Plan](#implementation-plan)
9. [Configuration](#configuration)
10. [Usage Examples](#usage-examples)
11. [Next Steps](#next-steps)

---

## Executive Summary

This document outlines the design for integrating **Deep Agents** into ADRminer's CLI to enable interactive, natural language-based exploration of Architectural Decision Records (ADRs).

### Key Features

- ✅ **Natural Language Interface**: Users can converse with ADRminer Assistant
- ✅ **Hybrid Commands**: Support both direct CLI commands (`/topics`) and natural language queries
- ✅ **Smart Orchestration**: Deep Agents automatically determines which tools to use
- ✅ **Human-in-the-Loop**: Approval workflows for LLM-based operations
- ✅ **Persistent Memory**: Context retained across sessions
- ✅ **Extensible**: Easy to add new commands and capabilities

### Design Decision

**Chosen Approach:** Deep Agents + LangGraph Hybrid

- **Deep Agents** handles natural language interface, planning, and high-level orchestration
- **LangGraph** provides structured workflows for common scenarios (optional, Phase 2)
- Existing CLI commands remain unchanged and accessible
- New `/chat` command provides interactive experience

---

## Framework Selection

### Decision Matrix

| Criterion | LangChain | LangGraph | Deep Agents |
|------------|-----------|------------|-------------|
| **Natural Language** | Medium | Manual | **Excellent** |
| **Control Flow** | Fixed | **Excellent** | Good |
| **Human-in-the-Loop** | Manual | Manual | **Built-in** |
| **Memory** | Manual | Checkpointer | **Built-in** |
| **Planning** | Manual | Manual | **TodoListMiddleware** |
| **File Management** | Manual | Manual | **FilesystemMiddleware** |
| **Setup Complexity** | Low | Medium | **Low** |

### Why Deep Agents?

1. **Interactive Exploration**: Primary use case is ad-hoc, user-driven analysis
2. **Human-in-the-Loop**: Need approval for LLM operations
3. **Memory**: Retain context across sessions
4. **Planning**: Multi-step analyses require task breakdown
5. **Middleware**: Built-in filesystem, memory, and delegation capabilities

### Why Not Just LangChain?

- Too basic for complex workflows
- No built-in human-in-the-loop
- No persistent memory
- Limited planning capabilities

### Why Not Just LangGraph?

- Overkill for simple queries
- Requires explicit graph design for every workflow
- No built-in natural language understanding
- Steeper learning curve

### Hybrid Strategy

- **Phase 1**: Deep Agents for interactive exploration
- **Phase 2**: LangGraph workflows for common, repeatable pipelines
- **Integration**: LangGraph workflows can be wrapped as Deep Agents subagents

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADRminer CLI (typer)                       │
├──────────────────────┬──────────────────────────────────────────┤
│  Existing Commands  │       New Interactive Command               │
│  • topics          │       • chat (Deep Agents)               │
│  • classify        │                                          │
│  • check          │                                          │
│  • init           │                                          │
└──────────────────────┴──────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              Deep Agent (Orchestrator)                      │
│                                                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ TodoListMiddleware (Planning)                      │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ FilesystemMiddleware (ADR Management)               │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ HumanInTheLoopMiddleware (Approvals)               │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ MemoryMiddleware (Persistence)                     │  │
│  └────────────────────────────────────────────────────────┘  │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Custom Tools                              │
├──────────────────┬───────────────────┬──────────────────┤
│   mine_topics    │   classify_adrs   │   check_quality   │
│   (BERTopic)     │   (LLM Class)     │   (MADR)         │
├──────────────────┼───────────────────┼──────────────────┤
│  load_adrs      │ generate_insights │ export_metadata   │
│  (File I/O)      │   (Analysis)      │   (JSON sidecar)  │
└──────────────────┴───────────────────┴──────────────────┘
```

### Data Flow

```
User Input → Parser → Command or Natural Language?
                     │
         ┌───────────┴───────────┐
         │                       │
    Direct Command          Natural Language
         │                       │
         ▼                       ▼
    Execute Handler      Deep Agent Tool Selection
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
            Service Execution
                     │
                     ▼
               Results Display
                     │
                     ▼
            Export (if requested)
```

---

## Deep Agents Setup

### Agent Factory

```python
# src/adrminer/agents/agent_factory.py

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from adrminer.config import get_settings
from .tools import (
    load_adrs, mine_topics, classify_adrs, 
    check_quality, generate_insights, export_metadata
)

def create_adrminer_agent(
    memory_enabled: bool = True,
    hitl_enabled: bool = True,
    skills_dir: str = None
):
    """
    Create a Deep Agent for ADRminer interactive analysis.
    
    Args:
        memory_enabled: Enable persistent memory across sessions
        hitl_enabled: Enable human-in-the-loop for approvals
        skills_dir: Path to skills directory (optional)
        
    Returns:
        Configured Deep Agent
    """
    settings = get_settings()
    
    # Collect all tools
    tools = [
        load_adrs,
        mine_topics,
        classify_adrs,
        check_quality,
        generate_insights,
        export_metadata
    ]
    
    # Configure middleware
    backend = FilesystemBackend(root_dir=".", virtual_mode=True)
    
    # Configure checkpointer and store
    checkpointer = MemorySaver() if hitl_enabled else None
    store = InMemoryStore() if memory_enabled else None
    
    # Configure interrupt for human-in-the-loop
    interrupt_on = {}
    if hitl_enabled:
        # Approve LLM-based operations
        interrupt_on["classify_adrs"] = True
        interrupt_on["check_quality"] = True
    
    # Create agent
    agent = create_deep_agent(
        name="adrminer-assistant",
        model=settings.llm.model,
        tools=tools,
        system_prompt="""You are ADRminer Assistant, an expert in analyzing Architectural Decision Records (ADRs).

Your capabilities:
- Extract topics from ADRs using BERTopic
- Classify ADRs using Kruchten, Quality Attributes, or Zimmermann frameworks
- Check ADR quality against MADR template standards
- Generate actionable insights and recommendations
- Export metadata as JSON sidecar files

Guidelines:
- Always ask for approval before running LLM-based operations (classification, checking)
- Use write_todos to plan multi-step analyses
- Be specific about what you're analyzing and why
- Provide clear, actionable insights
- Export results to sidecar files after analysis

You have access to ADR directory through filesystem tools.
""",
        backend=backend,
        skills=[skills_dir] if skills_dir else [],
        checkpointer=checkpointer,
        store=store,
        interrupt_on=interrupt_on if interrupt_on else None
    )
    
    return agent
```

### Configuration Requirements

```yaml
# .adrminer.yaml (enhanced)

agent:
  memory_enabled: true
  hitl_enabled: true
  skills_dir: "./skills"
  default_session_prefix: "adrminer-"

llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.0
  max_tokens: 2000
```

---

## Tool Wrappers

### Service Wrappers

Wrap existing ADRminer services as LangChain tools:

```python
# src/adrminer/agents/tools.py

from langchain.tools import tool
from pathlib import Path
from typing import List, Dict, Optional, Literal

from adrminer.services import TopicService, ClassificationService, CheckingService
from adrminer.services.insights_service import InsightsService
from adrminer.config import get_settings
from rich.console import Console

console = Console()

# Global service instances (lazy-loaded)
_services = {
    "topic": None,
    "classification": None,
    "check": None,
    "insights": None
}

def _get_service(name: str):
    """Lazy load service instances."""
    if _services[name] is None:
        settings = get_settings()
        
        if name == "topic":
            _services[name] = TopicService(model_path=settings.topic_model.path)
        elif name == "classification":
            _services[name] = ClassificationService(
                framework=settings.classification.framework,
                examples_path=settings.classification.examples,
                use_examples=settings.classification.use_examples
            )
        elif name == "check":
            _services[name] = CheckingService(mode="full")
        elif name == "insights":
            _services[name] = InsightsService()
    
    return _services[name]

@tool
def load_adrs(adr_path: str) -> Dict[str, List[str]]:
    """
    Load ADR files from a directory.
    
    Args:
        adr_path: Path to ADR directory
        
    Returns:
        Dictionary with file paths and contents
    """
    path = Path(adr_path)
    if not path.exists():
        raise ValueError(f"Path does not exist: {adr_path}")
    
    files = []
    for md_file in sorted(path.glob("*.md")):
        try:
            with open(md_file, 'r') as f:
                content = f.read()
            files.append(str(md_file))
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to read {md_file}: {e}[/yellow]")
    
    return {
        "file_paths": files,
        "count": len(files),
        "directory": str(path)
    }

@tool
def mine_topics(
    adr_contents: List[str],
    adr_paths: List[str],
    model: Optional[str] = None
) -> Dict:
    """
    Extract topics from ADRs using BERTopic.
    
    Args:
        adr_contents: List of ADR text contents
        adr_paths: List of ADR file paths (for metadata)
        model: Optional custom model path
        
    Returns:
        Topic mining results with labels, probabilities, keywords
    """
    service = _get_service("topic")
    
    results = []
    for content, path in zip(adr_contents, adr_paths):
        try:
            result = service.predict(content, metadata={"file": path})
            result["adr_file"] = path
            results.append(result)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to mine topics for {path}: {e}[/yellow]")
    
    return {
        "results": results,
        "count": len(results),
        "success": True
    }

@tool
def classify_adrs(
    adr_contents: List[str],
    adr_paths: List[str],
    framework: Literal["kruchten", "quality_attributes", "zimmermann"] = "kruchten",
    use_examples: bool = True
) -> Dict:
    """
    Classify ADRs using specified framework.
    
    Args:
        adr_contents: List of ADR text contents
        adr_paths: List of ADR file paths
        framework: Classification framework to use
        use_examples: Whether to use few-shot examples
        
    Returns:
        Classification results with categories and confidence scores
    """
    service = _get_service("classification")
    service.framework = framework  # Update framework
    
    results = []
    for content, path in zip(adr_contents, adr_paths):
        try:
            result = service.classify(content, metadata={"file": path})
            result["adr_file"] = path
            results.append(result)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to classify {path}: {e}[/yellow]")
    
    return {
        "results": results,
        "framework": framework,
        "count": len(results),
        "success": True
    }

@tool
def check_quality(
    adr_contents: List[str],
    adr_paths: List[str],
    mode: Literal["adherence", "sections", "full"] = "full"
) -> Dict:
    """
    Check ADRs for MADR template adherence and quality.
    
    Args:
        adr_contents: List of ADR text contents
        adr_paths: List of ADR file paths
        mode: Checking mode (adherence, sections, or full)
        
    Returns:
        Quality check results with scores and assessments
    """
    service = _get_service("check")
    
    # Update mode
    from adrminer.services.checking_service import CheckingService
    service.mode = mode
    
    metadata_list = [{"file": path, "name": Path(path).name} for path in adr_paths]
    
    results = service.check_batch(adr_contents, metadata_list, parallel=True)
    
    return {
        "results": results,
        "mode": mode,
        "count": len(results),
        "success": True
    }

@tool
def generate_insights(
    topic_results: Optional[Dict] = None,
    classification_results: Optional[Dict] = None,
    check_results: Optional[Dict] = None
) -> Dict:
    """
    Generate actionable insights from analysis results.
    
    Args:
        topic_results: Results from topic mining
        classification_results: Results from classification
        check_results: Results from quality checking
        
    Returns:
        Insights with quality issues, patterns, and recommendations
    """
    service = _get_service("insights")
    
    all_results = {}
    if topic_results:
        all_results["topics"] = topic_results
    if classification_results:
        all_results["classification"] = classification_results
    if check_results:
        all_results["checks"] = check_results
    
    insights = service.generate(all_results)
    
    return {
        "insights": insights,
        "success": True
    }

@tool
def export_metadata(
    adr_paths: List[str],
    topic_results: Optional[Dict] = None,
    classification_results: Optional[Dict] = None,
    check_results: Optional[Dict] = None,
    output_format: str = "sidecar"
) -> Dict:
    """
    Export analysis results to sidecar JSON files.
    
    Args:
        adr_paths: List of ADR file paths
        topic_results: Results from topic mining
        classification_results: Results from classification
        check_results: Results from quality checking
        output_format: Export format (sidecar or consolidated)
        
    Returns:
        Export results with file paths
    """
    from adrminer.exporters import JSONExporter
    
    exporter = JSONExporter()
    exported = []
    
    for adr_path in adr_paths:
        result_data = {}
        
        if topic_results:
            # Find topic result for this ADR
            for t in topic_results.get("results", []):
                if t["adr_file"] == adr_path:
                    result_data["topics"] = t
                    break
        
        if classification_results:
            # Find classification result for this ADR
            for c in classification_results.get("results", []):
                if c["adr_file"] == adr_path:
                    result_data["classification"] = c
                    break
        
        if check_results:
            # Find check result for this ADR
            for ch in check_results.get("results", []):
                if ch.get("metadata", {}).get("file") == adr_path:
                    result_data["check"] = ch
                    break
        
        if result_data:
            exporter.export_sidecar(
                adr_file=Path(adr_path),
                **result_data,
                model_versions={
                    "topic_model": "v1.0",
                    "classification_llm": "gpt-4o-mini",
                    "check_llm": "gpt-4o-mini"
                }
            )
            exported.append(adr_path)
    
    return {
        "exported_files": exported,
        "count": len(exported),
        "success": True
    }
```

---

## Interactive CLI Design

### Chat Command

```python
# src/adrminer/cli/commands/chat.py

import uuid
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.panel import Panel

from adrminer.agents.agent_factory import create_adrminer_agent
from adrminer.agents.commands import COMMAND_REGISTRY, ChatSession

console = Console()

@typer.command()
def chat(
    adr_path: Path = typer.Argument(
        ...,
        help="Path to ADR directory",
        exists=True,
    ),
    session: Optional[str] = typer.Option(
        None,
        "--session",
        "-s",
        help="Session ID for persistent memory (auto-generated if not provided)",
    ),
    no_memory: bool = typer.Option(
        False,
        "--no-memory",
        help="Disable persistent memory",
    ),
    no_hitl: bool = typer.Option(
        False,
        "--no-hitl",
        help="Disable human-in-the-loop approvals",
    ),
    skills: Optional[Path] = typer.Option(
        None,
        "--skills",
        help="Path to skills directory",
    ),
):
    """
    Interactive exploration of ADRs using natural language or direct commands.
    
    You can use:
    • [bold]Direct commands[/bold] starting with "/" (e.g., /topics, /classify)
    • [bold]Natural language[/bold] (e.g., "Analyze all ADRs")
    • [bold]Mixed[/bold] (e.g., "Use /topics to extract topics, then classify them")
    
    Examples:
        $ adrminer chat ./adrs/
        $ adrminer chat ./adrs/ --session project-123
        $ adrminer chat ./adrs/ --no-hitl --no-memory
    """
    # Generate or use session ID
    session_id = session or str(uuid.uuid4())
    
    # Create agent
    console.print("[blue]Initializing ADRminer Assistant...[/blue]\n")
    
    agent = create_adrminer_agent(
        memory_enabled=not no_memory,
        hitl_enabled=not no_hitl,
        skills_dir=str(skills) if skills else None
    )
    
    # Configure agent with ADR path
    config = {
        "configurable": {
            "thread_id": session_id
        }
    }
    
    # Create chat session
    session = ChatSession(
        adr_path=adr_path,
        agent=agent,
        config=config,
        command_registry=COMMAND_REGISTRY
    )
    
    # Welcome message
    console.print(Panel(
        f"""[bold green]ADRminer Assistant[/bold green]
        
Path: [cyan]{adr_path}[/cyan]
Session: [cyan]{session_id}[/cyan]
Memory: [cyan]{'Enabled' if not no_memory else 'Disabled'}[/cyan]
Approvals: [cyan]{'Enabled' if not no_hitl else 'Disabled'}[/cyan]

[bold]Available Commands:[/bold]
  • [cyan]/help[/cyan] - Show all commands
  • [cyan]/list[/cyan] - List ADRs
  • [cyan]/topics[/cyan] - Extract topics
  • [cyan]/classify[/cyan] - Classify ADRs
  • [cyan]/check[/cyan] - Check quality
  • [cyan]/insights[/cyan] - Generate insights
  • [cyan]/export[/cyan] - Export results

[bold]Or just chat naturally![/bold]
  "Analyze all ADRs"
  "Which ADRs are about security?"
  "Check quality and give me insights"

Type [bold]exit[/bold] or [bold]quit[/bold] to end session.
""",
        title="Welcome",
        border_style="blue"
    ))
    
    # Chat loop
    session.run_chat_loop()

# Add to main CLI
from adrminer.cli.main import cli
cli.command(name="chat", help="Interactive exploration of ADRs")(chat)
```

---

## Hybrid Command Interface

### Command Registry

```python
# src/adrminer/agents/commands.py

from typing import Dict, Optional
from pathlib import Path

COMMAND_REGISTRY = {
    "/topics": {
        "handler": "handle_topics_command",
        "description": "Analyze ADRs for topics",
        "help": "/topics [--model <path>] [--output <format>]"
    },
    "/classify": {
        "handler": "handle_classify_command",
        "description": "Classify ADRs using frameworks",
        "help": "/classify [--framework <kruchten|quality_attributes|zimmermann>]"
    },
    "/check": {
        "handler": "handle_check_command",
        "description": "Check ADR quality",
        "help": "/check [--mode <adherence|sections|full>]"
    },
    "/help": {
        "handler": "handle_help_command",
        "description": "Show available commands",
        "help": "/help [command]"
    },
    "/export": {
        "handler": "handle_export_command",
        "description": "Export analysis results",
        "help": "/export [--format <sidecar|consolidated>]"
    },
    "/list": {
        "handler": "handle_list_command",
        "description": "List ADRs in directory",
        "help": "/list"
    },
    "/insights": {
        "handler": "handle_insights_command",
        "description": "Generate insights from results",
        "help": "/insights"
    }
}

class ChatSession:
    """Manages interactive chat session."""
    
    def __init__(
        self,
        adr_path: Path,
        agent,
        config: dict,
        command_registry: dict
    ):
        self.adr_path = adr_path
        self.agent = agent
        self.config = config
        self.commands = command_registry
        self.context = {
            "loaded_adrs": [],
            "analysis_results": {}
        }
    
    def parse_input(self, user_input: str) -> tuple[bool, Optional[dict]]:
        """
        Parse user input to determine if it's a direct command or natural language.
        
        Returns:
            (is_command, command_info) or (False, None)
        """
        user_input = user_input.strip()
        
        # Check for command prefix
        if user_input.startswith("/"):
            parts = user_input.split()
            command_name = parts[0]
            
            if command_name in self.commands:
                # Extract arguments
                args = parts[1:] if len(parts) > 1 else []
                
                # Parse key-value arguments
                kwargs = {}
                i = 0
                while i < len(args):
                    if args[i].startswith("--"):
                        key = args[i][2:]
                        if i + 1 < len(args) and not args[i + 1].startswith("--"):
                            kwargs[key] = args[i + 1]
                            i += 2
                        else:
                            kwargs[key] = True
                            i += 1
                    else:
                        i += 1
                
                return True, {
                    "command": command_name,
                    "args": args,
                    "kwargs": kwargs,
                    "raw": user_input
                }
            else:
                # Unknown command - let agent handle it
                return False, None
        else:
            # Natural language - route to agent
            return False, None
    
    def run_chat_loop(self):
        """Run the main chat interaction loop."""
        from rich.console import Console
        from rich.prompt import Prompt
        
        console = Console()
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask(
                    "\n[bold cyan]You[/bold cyan]",
                    default="",
                    show_default=False
                )
                
                # Check for exit
                if user_input.lower() in ["exit", "quit", "q"]:
                    console.print("\n[yellow]Session ended. Goodbye![/yellow]\n")
                    break
                
                if not user_input.strip():
                    continue
                
                # Parse input
                is_command, command_info = self.parse_input(user_input)
                
                if is_command:
                    # Execute direct command
                    console.print(f"\n[blue]Executing command: {user_input}[/blue]\n")
                    self.execute_command(command_info, console)
                else:
                    # Natural language - route to agent
                    console.print(f"\n[blue]Processing...[/blue]\n")
                    self.process_natural_language(user_input, console)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]\nSession interrupted. Goodbye![/yellow]\n")
                break
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]\n")
                import traceback
                traceback.print_exc()
                continue
    
    def execute_command(self, command_info: dict, console):
        """Execute a direct command."""
        command_name = command_info["command"]
        handler_name = self.commands[command_name]["handler"]
        
        # Get handler method
        handler = getattr(self, handler_name, None)
        
        if not handler:
            console.print(f"[red]Error: Command '{command_name}' not implemented[/red]")
            return
        
        try:
            # Execute handler (async or sync)
            import asyncio
            result = asyncio.run(handler(**command_info["kwargs"]))
            console.print(Markdown(result))
        except Exception as e:
            console.print(f"[red]Error executing '{command_name}': {e}[/red]")
```

### Command Handlers

Implement handlers for each command in the `ChatSession` class:

```python
async def handle_help_command(self, command: Optional[str] = None) -> str:
    """Show help for commands."""
    if command:
        if command.startswith("/") and command in self.commands:
            cmd_info = self.commands[command]
            return f"""[bold cyan]{command}[/bold cyan]
{cmd_info['description']}

Usage: {cmd_info['help']}
"""
        else:
            return f"[yellow]Unknown command: {command}[/yellow]\nUse /help to see all commands."
    else:
        help_text = "[bold]Available Commands:[/bold]\n\n"
        for cmd_name, cmd_info in sorted(self.commands.items()):
            help_text += f"  [cyan]{cmd_name}[/cyan] - {cmd_info['description']}\n"
        help_text += "\n[bold]Or just chat naturally![/bold]"
        return help_text

async def handle_list_command(self) -> str:
    """List ADRs in directory."""
    import glob
    
    adr_files = sorted(self.adr_path.glob("*.md"))
    
    if not adr_files:
        return "[yellow]No ADRs found in directory[/yellow]"
    
    result = f"[bold]ADRs in {self.adr_path}:[/bold]\n\n"
    for i, adr_file in enumerate(adr_files, 1):
        result += f"  {i}. [cyan]{adr_file.name}[/cyan]\n"
    
    # Update context
    self.context["loaded_adrs"] = [str(f) for f in adr_files]
    
    return result

async def handle_topics_command(
    self,
    model: Optional[str] = None,
    output: Optional[str] = None
) -> str:
    """Extract topics from ADRs."""
    from adrminer.agents.tools import load_adrs, mine_topics
    
    # Load ADRs
    load_result = load_adrs(str(self.adr_path))
    if not load_result["file_paths"]:
        return "[yellow]No ADRs to analyze[/yellow]"
    
    # Read contents
    contents = []
    for path in load_result["file_paths"]:
        with open(path, 'r') as f:
            contents.append(f.read())
    
    # Mine topics
    topic_result = mine_topics(
        adr_contents=contents,
        adr_paths=load_result["file_paths"],
        model=model
    )
    
    # Store in context
    self.context["analysis_results"]["topics"] = topic_result
    
    # Format results
    result = f"[bold green]✓ Topic Mining Complete[/bold green]\n\n"
    result += f"Analyzed {topic_result['count']} ADRs\n\n"
    
    for t_result in topic_result["results"][:5]:  # Show first 5
        result += f"  • [cyan]{Path(t_result['adr_file']).name}[/cyan]\n"
        result += f"    Topic: {t_result.get('topic_label', 'N/A')}\n"
        result += f"    Confidence: {t_result.get('probability', 0):.2f}\n\n"
    
    if topic_result["count"] > 5:
        result += f"... and {topic_result['count'] - 5} more ADRs\n"
    
    return result

async def handle_classify_command(
    self,
    framework: str = "kruchten"
) -> str:
    """Classify ADRs."""
    from adrminer.agents.tools import classify_adrs
    
    if "loaded_adrs" not in self.context or not self.context["loaded_adrs"]:
        await self.handle_list_command()
    
    # Read contents
    contents = []
    for path in self.context["loaded_adrs"]:
        with open(path, 'r') as f:
            contents.append(f.read())
    
    # Classify
    classify_result = classify_adrs(
        adr_contents=contents,
        adr_paths=self.context["loaded_adrs"],
        framework=framework
    )
    
    # Store in context
    self.context["analysis_results"]["classification"] = classify_result
    
    # Format results
    result = f"[bold green]✓ Classification Complete[/bold green]\n\n"
    result += f"Framework: {framework}\n"
    result += f"Analyzed {classify_result['count']} ADRs\n\n"
    
    # Show distribution
    from collections import Counter
    categories = [r['primary_category'] for r in classify_result['results']]
    category_counts = Counter(categories)
    
    result += "[bold]Category Distribution:[/bold]\n"
    for category, count in category_counts.most_common():
        result += f"  • [cyan]{category}[/cyan]: {count} ADRs\n"
    
    return result

async def handle_check_command(
    self,
    mode: str = "full"
) -> str:
    """Check ADR quality."""
    from adrminer.agents.tools import check_quality
    
    if "loaded_adrs" not in self.context or not self.context["loaded_adrs"]:
        await self.handle_list_command()
    
    # Read contents
    contents = []
    for path in self.context["loaded_adrs"]:
        with open(path, 'r') as f:
            contents.append(f.read())
    
    # Check quality
    check_result = check_quality(
        adr_contents=contents,
        adr_paths=self.context["loaded_adrs"],
        mode=mode
    )
    
    # Store in context
    self.context["analysis_results"]["check"] = check_result
    
    # Format results
    result = f"[bold green]✓ Quality Check Complete[/bold green]\n\n"
    result += f"Mode: {mode}\n"
    result += f"Checked {check_result['count']} ADRs\n\n"
    
    # Show average adherence
    scores = [
        r.get('template_adherence', {}).get('adherence_score', 0)
        for r in check_result['results']
        if 'error' not in r
    ]
    if scores:
        avg_score = sum(scores) / len(scores)
        result += f"Average Adherence: [cyan]{avg_score:.2f}[/cyan]\n\n"
    
    # Show issues
    issues = []
    for r in check_result['results']:
        if 'error' not in r:
            template = r.get('template_adherence', {})
            if template.get('adherence_score', 1.0) < 0.8:
                issues.append(Path(r['metadata']['file']).name)
    
    if issues:
        result += "[bold red]⚠ Low Quality ADRs:[/bold red]\n"
        for issue in issues[:5]:
            result += f"  • [red]{issue}[/red]\n"
        if len(issues) > 5:
            result += f"  ... and {len(issues) - 5} more\n"
    
    return result

async def handle_export_command(
    self,
    format: str = "sidecar"
) -> str:
    """Export analysis results."""
    from adrminer.agents.tools import export_metadata
    
    if not self.context["loaded_adrs"]:
        return "[yellow]No ADRs loaded. Use /list first.[/yellow]"
    
    export_result = export_metadata(
        adr_paths=self.context["loaded_adrs"],
        **self.context["analysis_results"],
        output_format=format
    )
    
    return f"""[bold green]✓ Export Complete[/bold green]

Exported {export_result['count']} ADRs
Format: {format}
"""

async def handle_insights_command(self) -> str:
    """Generate insights."""
    from adrminer.agents.tools import generate_insights
    
    if not self.context["analysis_results"]:
        return "[yellow]No analysis results available. Run analysis first.[/yellow]"
    
    insights_result = generate_insights(**self.context["analysis_results"])
    
    result = "[bold green]✓ Insights Generated[/bold green]\n\n"
    
    for insight in insights_result.get("insights", [])[:5]:
        result += f"• [cyan]{insight.get('type', 'info').title()}[/cyan]\n"
        result += f"  {insight.get('message', 'N/A')}\n\n"
    
    return result
```

### Natural Language Processing

```python
def process_natural_language(self, user_input: str, console):
    """Process natural language queries through Deep Agent."""
    from rich.markdown import Markdown
    
    # Provide context to agent
    user_message = {
        "role": "user",
        "content": f"""I'm working with ADRs in directory: {self.adr_path}

Context:
- {len(self.context.get('loaded_adrs', []))} ADRs loaded
- Available analyses: {list(self.context.get('analysis_results', {}).keys())}

{user_input}

Note: You can use commands like /topics, /classify, /check, /insights, /export, /list if needed."""
    }
    
    result = self.agent.invoke(
        {"messages": [user_message]},
        config=self.config
    )
    
    # Display response
    if result.get("messages"):
        last_message = result["messages"][-1]
        if last_message.get("content"):
            console.print(Markdown(last_message["content"]))
    
    # Handle interruptions (human-in-the-loop)
    self.handle_interrupts(result, console)

def handle_interrupts(self, result: dict, console):
    """Handle human-in-the-loop interrupts."""
    from rich.prompt import Prompt
    
    while result.get("__interrupt__"):
        interrupt_data = result["__interrupt__"]
        
        console.print(f"\n[bold yellow]⚠ Approval Required[/bold yellow]")
        console.print(f"The agent wants to: {interrupt_data}\n")
        
        action = Prompt.ask(
            "[cyan]Continue?[/cyan]",
            choices=["yes", "no", "skip"],
            default="yes"
        )
        
        if action == "yes":
            # Resume with approval
            console.print("[green]✓ Approved[/green]\n")
            result = self.agent.invoke(
                {"messages": [{"role": "user", "content": "Continue"}]},
                config=self.config
            )
            
            # Display response
            if result.get("messages"):
                last_message = result["messages"][-1]
                if last_message.get("content"):
                    console.print(Markdown(last_message["content"]))
        elif action == "skip":
            # Skip this operation
            console.print("[yellow]Skipping operation[/yellow]\n")
            break
        else:
            # Cancel the operation
            console.print("[red]✗ Cancelled[/red]\n")
            break
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

**Objective**: Set up Deep Agents infrastructure

#### Tasks

1. **Create Agent Module Structure**
   - [ ] Create `src/adrminer/agents/` directory
   - [ ] Create `__init__.py`
   - [ ] Create `agent_factory.py`
   - [ ] Create `tools.py`
   - [ ] Create `commands.py`

2. **Implement Tool Wrappers**
   - [ ] Implement `load_adrs` tool
   - [ ] Implement `mine_topics` tool
   - [ ] Implement `classify_adrs` tool
   - [ ] Implement `check_quality` tool
   - [ ] Implement `generate_insights` tool
   - [ ] Implement `export_metadata` tool

3. **Create Agent Factory**
   - [ ] Implement `create_adrminer_agent()`
   - [ ] Configure middleware (TodoList, Filesystem, HITL, Memory)
   - [ ] Set up system prompt
   - [ ] Configure interrupt rules

4. **Dependencies**
   - [ ] Add `deepagents` to `pyproject.toml`
   - [ ] Add `langgraph` to `pyproject.toml`
   - [ ] Update dependencies

**Deliverables**:
- Functional agent factory
- All tools wrapped and tested
- Agent can be created and invoked

### Phase 2: Chat Command (Week 2-3)

**Objective**: Implement interactive CLI command

#### Tasks

1. **Command Registry**
   - [ ] Define `COMMAND_REGISTRY`
   - [ ] Implement command parser
   - [ ] Add help command

2. **Chat Session Class**
   - [ ] Implement `ChatSession` class
   - [ ] Implement `parse_input()`
   - [ ] Implement command handlers
   - [ ] Implement natural language routing

3. **CLI Integration**
   - [ ] Create `chat` command in `src/adrminer/cli/commands/chat.py`
   - [ ] Register command in `main.py`
   - [ ] Add command-line options
   - [ ] Implement welcome message

4. **Human-in-the-Loop**
   - [ ] Implement interrupt handling
   - [ ] Add approval prompts
   - [ ] Test interrupt flow

**Deliverables**:
- Working `/chat` command
- Command and natural language support
- Human-in-the-loop approvals

### Phase 3: Command Handlers (Week 3-4)

**Objective**: Implement all direct commands

#### Tasks

1. **Basic Commands**
   - [ ] Implement `/help` command
   - [ ] Implement `/list` command
   - [ ] Test basic command flow

2. **Analysis Commands**
   - [ ] Implement `/topics` command
   - [ ] Implement `/classify` command
   - [ ] Implement `/check` command
   - [ ] Test analysis commands

3. **Output Commands**
   - [ ] Implement `/insights` command
   - [ ] Implement `/export` command
   - [ ] Test output commands

**Deliverables**:
- All commands implemented
- Commands work with agent context
- Results properly formatted

### Phase 4: Integration & Testing (Week 4-5)

**Objective**: Integrate and test with existing CLI

#### Tasks

1. **Integration**
   - [ ] Register `/chat` command in main CLI
   - [ ] Ensure existing commands still work
   - [ ] Test command isolation

2. **Testing**
   - [ ] Write unit tests for tools
   - [ ] Write integration tests for chat
   - [ ] Test human-in-the-loop flow
   - [ ] Test memory persistence

3. **Documentation**
   - [ ] Update CLI guide
   - [ ] Add chat command documentation
   - [ ] Create usage examples
   - [ ] Update README

**Deliverables**:
- Fully integrated chat command
- Test suite
- Complete documentation

### Phase 5: Polish & Enhancement (Week 5-6)

**Objective**: Refine user experience

#### Tasks

1. **User Experience**
   - [ ] Improve error messages
   - [ ] Add progress indicators
   - [ ] Enhance output formatting
   - [ ] Add examples and hints

2. **Performance**
   - [ ] Optimize tool execution
   - [ ] Add caching for ADRs
   - [ ] Parallel processing improvements

3. **Features**
   - [ ] Add command history
   - [ ] Add session management
   - [ ] Add configuration options
   - [ ] Add skills directory support

**Deliverables**:
- Polished user experience
- Performance improvements
- Additional features

---

## Configuration

### Environment Variables

```bash
# .env
OPENAI_API_KEY=your_api_key_here
ANTHROPIC_API_KEY=your_api_key_here
ADRMINER_ADR_PATH=./adrs
ADRMINER_SKILLS_DIR=./skills
ADRMINER_MEMORY_ENABLED=true
ADRMINER_HITL_ENABLED=true
```

### YAML Configuration

```yaml
# .adrminer.yaml (enhanced)

agent:
  memory_enabled: true
  hitl_enabled: true
  skills_dir: "./skills"
  default_session_prefix: "adrminer-"
  
  # Middleware configuration
  middleware:
    todo_list:
      enabled: true
    filesystem:
      enabled: true
      virtual_mode: true
    memory:
      enabled: true
      backend: "memory"  # or "store"
    hitl:
      enabled: true
      approve_commands:
        - "classify_adrs"
        - "check_quality"
      
# LLM configuration (shared with existing)
llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.0
  max_tokens: 2000
  
# Existing configurations remain unchanged
topic_model:
  path: "./models/topic_model"
  # ... existing config ...

classification:
  framework: kruchten
  # ... existing config ...

check:
  mode: full
  # ... existing config ...
```

---

## Usage Examples

### Basic Usage

```bash
# Start interactive session
$ adrminer chat ./adrs/

# Direct command
You: /list
[cyan]Executing command: /list[/cyan]

[bold]ADRs in ./adrs/:[/bold]

  1. [cyan]ADR-001.md[/cyan]
  2. [cyan]ADR-002.md[/cyan]
  3. [cyan]ADR-003.md[/cyan]

# Natural language
You: Analyze these ADRs for topics
[blue]Processing...[/blue]

[green]I'll analyze 3 ADRs for topics using the mine_topics tool.[/green]
[green]✓ Topic Mining Complete[/green]

Analyzed 3 ADRs

  • [cyan]ADR-001.md[/cyan]
    Topic: Database Migration
    Confidence: 0.87

  • [cyan]ADR-002.md[/cyan]
    Topic: API Gateway
    Confidence: 0.92

  • [cyan]ADR-003.md[/cyan]
    Topic: Authentication
    Confidence: 0.89

# Mixed usage
You: Use /classify with framework quality_attributes, then check quality
[blue]Processing...[/blue]

[green]I'll classify ADRs using Quality Attributes framework and then check their quality.[/green]
[green]✓ Classification Complete[/green]

Framework: quality_attributes
Analyzed 3 ADRs

[bold]Category Distribution:[/bold]
  • [cyan]Security[/cyan]: 2 ADRs
  • [cyan]Performance[/cyan]: 1 ADR

[blue]Executing command: /check[/blue]

[green]✓ Quality Check Complete[/green]

Mode: full
Checked 3 ADRs

Average Adherence: [cyan]0.82[/cyan]
```

### Advanced Usage

```bash
# Session with memory
$ adrminer chat ./adrs/ --session project-alpha

# Analyze in first session
You: Analyze all ADRs for topics and classification
[blue]Processing...[/blue]
[green]✓ Analysis complete[/green]

# Exit and resume later
You: exit
[yellow]Session ended. Goodbye![/yellow]

$ adrminer chat ./adrs/ --session project-alpha
[blue]Resuming session project-alpha...[/blue]

You: What did we find about security decisions?
[blue]Processing...[/blue]
[green]Based on previous analysis, we found 2 ADRs classified as Security:[/green]
  • ADR-001: Authentication Strategy
  • ADR-003: Encryption Implementation

# Disable approvals for automated runs
$ adrminer chat ./adrs/ --no-hitl

You: Analyze all ADRs
[blue]Processing...[/blue]
[green]✓ Analysis complete[/green]  # No approval prompts

# Use skills directory
$ adrminer chat ./adrs/ --skills ./skills

You: Use the madr-template skill to review ADR-001
[blue]Processing...[/blue]
[green]Loading madr-template skill...[/green]
[green]ADR-001 follows MADR template correctly with all required sections.[/green]
```

### Complex Queries

```bash
You: Find all ADRs with quality score below 0.8 and classify them using different frameworks
[blue]Processing...[/blue]

[green]I'll analyze quality scores and re-classify low-quality ADRs.[/green]

[bold]Low Quality ADRs:[/bold]
  • ADR-002 (score: 0.76)
  • ADR-005 (score: 0.71)

⚠ Approval Required
The agent wants to classify 2 ADRs using LLM. Continue? [Y/n]: y

[green]✓ Re-classification complete[/green]

ADR-002:
  Kruchten: Existence (0.89)
  Quality Attributes: Performance (0.91)
  Zimmermann: Technology (0.87)

ADR-005:
  Kruchten: Property (0.85)
  Quality Attributes: Maintainability (0.88)
  Zimmermann: Process (0.82)

You: Which framework gives the highest confidence for these ADRs?
[blue]Processing...[/blue]

[green]Quality Attributes framework gives the highest average confidence (0.895) for low-quality ADRs.[/green]

You: Generate insights about why these ADRs have low quality
[blue]Processing...[/blue]

[green]✓ Insights generated[/green]

[bold]Quality Issues:[/bold]
  • Both ADRs missing "alternatives" section
  • Incomplete "consequences" documentation
  • Limited decision drivers listed

[bold]Recommendations:[/bold]
  • Add detailed alternatives analysis
  • Document consequences for stakeholders
  • Expand decision drivers to include business context
```

---

## Next Steps

### Immediate Actions

1. **Review and Approve**
   - [ ] Review this design document
   - [ ] Approve architecture and implementation plan
   - [ ] Discuss any concerns or modifications

2. **Environment Setup**
   - [ ] Install dependencies (`deepagents`, `langgraph`)
   - [ ] Set up development environment
   - [ ] Configure `.env` file with API keys

3. **Start Implementation**
   - [ ] Begin Phase 1 (Foundation)
   - [ ] Create module structure
   - [ ] Implement tool wrappers

### Future Enhancements

1. **LangGraph Workflows** (Phase 2)
   - Create predefined analysis workflows
   - Implement full analysis graph
   - Add quality improvement workflow

2. **Advanced Features**
   - Command history and autocomplete
   - Multi-session management
   - Collaboration features
   - Real-time notifications

3. **UI Enhancements**
   - Progress bars for long operations
   - Rich output formatting
   - Interactive visualizations
   - Export to multiple formats

4. **Performance**
   - Caching for ADR contents
   - Parallel tool execution
   - Background job processing
   - Incremental analysis

### Documentation

1. **User Documentation**
   - Complete CLI guide with chat command
   - Usage examples and tutorials
   - Troubleshooting guide

2. **Developer Documentation**
   - Architecture documentation
   - API reference
   - Extension guide

3. **Examples**
   - Sample ADR collections
   - Example workflows
   - Skills directory examples

---

## Appendix

### File Structure

```
adrminer/
├── src/adrminer/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── agent_factory.py          # Deep Agent creation
│   │   ├── tools.py                 # LangChain tool wrappers
│   │   └── commands.py              # Chat session and handlers
│   ├── cli/
│   │   ├── commands/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py              # New chat command
│   │   │   ├── topics.py            # Existing
│   │   │   ├── classify.py          # Existing
│   │   │   ├── check.py             # Existing
│   │   │   └── ...
│   │   └── main.py                  # Updated to register chat
│   ├── services/                     # Existing services
│   │   ├── topic_service.py
│   │   ├── classification_service.py
│   │   ├── checking_service.py
│   │   └── insights_service.py      # May need to implement
│   └── ...
├── skills/                         # Optional skills directory
│   ├── madr-template/
│   │   └── SKILL.md
│   └── architectural-patterns/
│       └── SKILL.md
├── docs/
│   ├── DEEP_AGENTS_CLI_DESIGN.md    # This document
│   └── ...
└── ...
```

### Dependencies

```toml
# pyproject.toml (additions)

[project]
dependencies = [
    # ... existing dependencies ...
    "deepagents>=0.1.0",
    "langgraph>=0.2.0",
    "langchain>=0.3.0",
]

[project.optional-dependencies]
agent = [
    "deepagents>=0.1.0",
    "langgraph>=0.2.0",
]
```

### Testing Strategy

1. **Unit Tests**
   - Test each tool independently
   - Mock service calls
   - Verify input/output

2. **Integration Tests**
   - Test agent creation
   - Test command parsing
   - Test natural language routing

3. **E2E Tests**
   - Test full chat sessions
   - Test human-in-the-loop
   - Test memory persistence

4. **Manual Testing**
   - User acceptance testing
   - Performance testing
   - Usability testing

---

## Conclusion

This design provides a comprehensive roadmap for integrating Deep Agents into ADRminer's CLI, enabling interactive, natural language-based exploration of ADRs while maintaining the precision and control of direct commands.

The hybrid approach offers:

- **Flexibility**: Users can choose commands or natural language
- **Power**: Deep Agents orchestrate complex workflows
- **Control**: Human-in-the-loop for sensitive operations
- **Extensibility**: Easy to add new commands and capabilities
- **Compatibility**: Existing CLI commands remain unchanged

With this design, ADRminer will offer a modern, intuitive interface for analyzing architectural decisions while maintaining the robust functionality of existing tools.

---

**Document History:**
- v1.0 - Initial design document (2026-04-19)