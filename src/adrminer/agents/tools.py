"""LangChain tools for Deep Agents integration.

This module provides tool wrappers that allow the Deep Agent to interact
with ADRminer services for loading ADRs, mining topics, classification,
quality checking, and generating insights.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from adrminer.models.classification_schemas import (
    KruchtenClassificationResult,
    QualityAttributeClassificationResult,
    ZimmermannClassificationResult
)


class ToolResult(BaseModel):
    """Standard result from tool execution."""
    
    success: bool = Field(
        default=True,
        description="Whether the tool executed successfully"
    )
    message: str = Field(
        description="Human-readable result message"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured result data"
    )
    requires_approval: bool = Field(
        default=False,
        description="Whether this operation requires user approval"
    )
    batch_operation: bool = Field(
        default=False,
        description="Whether this is a batch operation"
    )
    num_affected: int = Field(
        default=0,
        description="Number of ADRs affected by this operation"
    )


# Global session reference (set by agent factory)
_session = None


def set_session(session):
    """Set the global session reference for tools.
    
    Args:
        session: SessionManager instance
    """
    global _session
    _session = session


def get_session():
    """Get the global session reference.
    
    Returns:
        SessionManager instance or None
    """
    return _session


@tool(parse_docstring=True)
def load_adrs(path: str) -> Dict[str, Any]:
    """Load ADR files from a directory.
    
    This tool loads ADR files from the specified directory path.
    The path can be absolute or relative to the current working directory.
    
    Args:
        path: Directory path containing ADR files (absolute or relative)
    
    Returns:
        Dictionary with loading results including loaded file paths
    
    Example:
        >>> load_adrs("adrs/")
        >>> load_adrs("/path/to/adrs")
    """
    session = get_session()
    if session is None:
        return ToolResult(
            success=False,
            message="Session not initialized",
            requires_approval=False
        ).model_dump()
    
    # Log tool invocation
    if hasattr(session, 'console'):
        session.console.print("\n[dim]→ Tool called: load_adrs[/dim]")
        session.console.print(f"  [dim]path: {path}[/dim]")
    
    try:
        # Resolve path
        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = Path.cwd() / path_obj
        
        # Get ADR paths
        adr_paths = []
        if path_obj.is_file():
            # Single file
            if path_obj.suffix in ['.md', '.txt']:
                adr_paths.append(path_obj)
        elif path_obj.is_dir():
            # Directory - load all markdown files
            adr_paths = list(path_obj.glob("**/*.md"))
            # Filter out common non-ADR files
            adr_paths = [
                p for p in adr_paths 
                if not any(excl in str(p) for excl in ['node_modules', '.git', '__pycache__'])
            ]
        
        if not adr_paths:
            return ToolResult(
                success=False,
                message=f"No ADR files found at {path_obj}",
                requires_approval=False
            ).model_dump()
        
        # Store in session context
        session.loaded_adrs = adr_paths
        
        result = ToolResult(
            success=True,
            message=f"Loaded {len(adr_paths)} ADR file(s) from {path_obj}",
            data={
                "loaded_count": len(adr_paths),
                "paths": [str(p) for p in adr_paths],
                "directory": str(path_obj)
            },
            requires_approval=False,
            batch_operation=True,
            num_affected=len(adr_paths)
        ).model_dump()
        
        # Log completion
        if hasattr(session, 'console'):
            session.console.print(f"[green]✓[/green] {result['message']}")
        
        return result
        
    except Exception as e:
        result = ToolResult(
            success=False,
            message=f"Failed to load ADRs: {str(e)}",
            requires_approval=False
        ).model_dump()
        
        # Log error
        if hasattr(session, 'console'):
            session.console.print(f"[red]✗[/red] {result['message']}")
        
        return result


@tool(parse_docstring=True)
def get_topics_info(
    topic_id: Optional[int] = None,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """Show information about topics in model (equivalent to "topics info" command).
    
    This tool displays details about topics in the BERTopic model,
    either all topics or a specific topic by ID. This corresponds
    to the CLI command "topics info".
    
    Args:
        topic_id: Optional specific topic ID to show details for. None means to show all topics
        model: Optional model path (uses default if not specified)
    
    Returns:
        Dictionary with topic information
    
    Example:
        >>> get_topics_info()  # Show all topics
        >>> get_topics_info(topic_id=5)  # Show specific topic
    """
    session = get_session()
    if session is None:
        return ToolResult(
            success=False,
            message="Session not initialized",
            requires_approval=False
        ).model_dump()
    
    # Log tool invocation
    if hasattr(session, 'console'):
        session.console.print("\n[dim]→ Tool called: get_topics_info[/dim]")
        session.console.print(f"  [dim]topic_id: {topic_id}, model: {model}[/dim]")
    
    try:
        # Get topic service
        topic_service = session.topic_service
        
        if topic_id is not None:
            # Show specific topic
            topic_info = topic_service.get_topic_info(topic_id)
            
            if not topic_info:
                result = ToolResult(
                    success=False,
                    message=f"Topic {topic_id} not found",
                    data={},
                    requires_approval=False
                ).model_dump()
            else:
                result = ToolResult(
                    success=True,
                    message=f"Retrieved information for topic {topic_id}",
                    data=topic_info,
                    requires_approval=False
                ).model_dump()
        else:
            # Show all topics
            topic_df = topic_service.model.get_topic_info()
            
            # Format topic list
            topics_data = []
            for _, row in topic_df.iterrows():
                tid = int(row["Topic"])
                topic_info = topic_service.get_topic_info(tid)
                if topic_info:
                    topics_data.append({
                        "topic_id": tid,
                        "name": topic_info.get("name", row["Name"]),
                        "count": int(row["Count"]),
                        "keywords": [w for w, _ in topic_info.get("representation", [])[:5]]
                    })
            
            result = ToolResult(
                success=True,
                message=f"Retrieved information for {len(topics_data)} topics",
                data={
                    "total_topics": len(topics_data),
                    "topics": topics_data
                },
                requires_approval=False
            ).model_dump()
        
        # Log completion
        if hasattr(session, 'console'):
            session.console.print(f"[green]✓[/green] {result['message']}")
        
        return result
        
    except Exception as e:
        result = ToolResult(
            success=False,
            message=f"Failed to get topics information: {str(e)}",
            requires_approval=False
        ).model_dump()
        
        # Log error
        if hasattr(session, 'console'):
            session.console.print(f"[red]✗[/red] {result['message']}")
        
        return result


@tool(parse_docstring=True)
def get_classification_info(
    framework: Optional[str] = None
) -> Dict[str, Any]:
    """Show information about classification frameworks.
    
    This tool displays details about available classification frameworks
    (Kruchten, Quality Attributes, Zimmermann).
    
    Args:
        framework: Optional specific framework to show details for
    
    Returns:
        Dictionary with framework information
    
    Example:
        >>> get_classification_info()  # Show all frameworks
        >>> get_classification_info(framework="kruchten")  # Show specific framework
    """
    session = get_session()
    if session is None:
        return ToolResult(
            success=False,
            message="Session not initialized",
            requires_approval=False
        ).model_dump()
    
    # Log tool invocation
    if hasattr(session, 'console'):
        session.console.print("\n[dim]→ Tool called: get_classification_info[/dim]")
        session.console.print(f"  [dim]framework: {framework}[/dim]")
    
    try:
        from adrminer.services.classification_service import FRAMEWORKS
        
        if framework:
            # Show specific framework
            if framework not in FRAMEWORKS:
                result = ToolResult(
                    success=False,
                    message=f"Unknown framework: {framework}. Available: {', '.join(FRAMEWORKS.keys())}",
                    data={},
                    requires_approval=False
                ).model_dump()
            else:
                framework_info = FRAMEWORKS[framework]
                result = ToolResult(
                    success=True,
                    message=f"Retrieved information for {framework} framework",
                    data={
                        "code": framework,
                        "name": framework_info["name"],
                        "description": framework_info["description"],
                        "categories": framework_info["categories"],
                        "category_descriptions": framework_info.get("category_descriptions", {})
                    },
                    requires_approval=False
                ).model_dump()
        else:
            # Show all frameworks
            frameworks_data = []
            for code, info in FRAMEWORKS.items():
                frameworks_data.append({
                    "code": code,
                    "name": info["name"],
                    "categories_count": len(info["categories"]),
                    "description": info["description"]
                })
            
            result = ToolResult(
                success=True,
                message=f"Retrieved information for {len(frameworks_data)} frameworks",
                data={
                    "total_frameworks": len(frameworks_data),
                    "frameworks": frameworks_data
                },
                requires_approval=False
            ).model_dump()
        
        # Log completion
        if hasattr(session, 'console'):
            session.console.print(f"[green]✓[/green] {result['message']}")
        
        return result
        
    except Exception as e:
        result = ToolResult(
            success=False,
            message=f"Failed to get classification information: {str(e)}",
            requires_approval=False
        ).model_dump()
        
        # Log error
        if hasattr(session, 'console'):
            session.console.print(f"[red]✗[/red] {result['message']}")
        
        return result


@tool(parse_docstring=True)
def list_adr_files(
    path: str
) -> Dict[str, Any]:
    """List ADR files in a directory.
    
    This tool discovers and lists ADR files in specified directory.
    Useful for exploring the filesystem before loading ADRs.
    
    Args:
        path: Directory path to search for ADR files (absolute or relative)
    
    Returns:
        Dictionary with discovered ADR files
    
    Example:
        >>> list_adr_files("adrs/")
        >>> list_adr_files("/path/to/adrs")
    """
    session = get_session()
    if session is None:
        return ToolResult(
            success=False,
            message="Session not initialized",
            requires_approval=False
        ).model_dump()
    
    # Log tool invocation
    if hasattr(session, 'console'):
        session.console.print("\n[dim]→ Tool called: list_adr_files[/dim]")
        session.console.print(f"  [dim]path: {path}[/dim]")
    
    try:
        # Resolve path
        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = Path.cwd() / path_obj
        
        # Find ADR files
        adr_files = []
        if path_obj.is_file():
            if path_obj.suffix in ['.md', '.MD', '.txt', '.TXT']:
                adr_files.append(path_obj)
        elif path_obj.is_dir():
            # Search recursively
            adr_files = list(path_obj.glob("**/*.md")) + list(path_obj.glob("**/*.MD"))
            # Filter out common non-ADR files
            adr_files = [
                p for p in adr_files 
                if not any(excl in str(p) for excl in ['node_modules', '.git', '__pycache__'])
            ]
        
        result = ToolResult(
            success=True,
            message=f"Found {len(adr_files)} ADR file(s) in {path_obj}",
            data={
                "directory": str(path_obj),
                "file_count": len(adr_files),
                "files": [str(p) for p in adr_files]
            },
            requires_approval=False
        ).model_dump()
        
        # Log completion
        if hasattr(session, 'console'):
            session.console.print(f"[green]✓[/green] {result['message']}")
        
        return result
        
    except Exception as e:
        result = ToolResult(
            success=False,
            message=f"Failed to list ADR files: {str(e)}",
            requires_approval=False
        ).model_dump()
        
        # Log error
        if hasattr(session, 'console'):
            session.console.print(f"[red]✗[/red] {result['message']}")
        
        return result


@tool(parse_docstring=True)
def mine_topics(
    path: Optional[str] = None,
    model: Optional[str] = None,
    threshold: float = 0.0
) -> Dict[str, Any]:
    """Extract topics from a batch of ADRs using a BERTopic model.
    
    This tool analyzes a batch of ADRs and extracts topics using the
    pre-trained BERTopic model. Topics are identified based on
    semantic similarity of ADR content.
    
    Args:
        path: Optional path (folder) to load ADRs from (if not already loaded)
        model: Optional model path (uses default if not specified)
        threshold: Probability threshold for topic assignment (0.0-1.0)
    
    Returns:
        Dictionary with topic predictions for each ADR
    
    Example:
        >>> mine_topics("adrs/", threshold=0.5)
        >>> mine_topics()  # Uses previously loaded ADRs
    """
    session = get_session()
    if session is None:
        return ToolResult(
            success=False,
            message="Session not initialized",
            requires_approval=False
        ).model_dump()
    
    # Log tool invocation
    if hasattr(session, 'console'):
        session.console.print("\n[dim]→ Tool called: mine_topics[/dim]")
        session.console.print(f"  [dim]path: {path}, threshold: {threshold}[/dim]")
    
    try:
        # Load ADRs if path provided
        if path is not None:
            load_result = load_adrs.invoke({"path": path})
            if not load_result["success"]:
                return ToolResult(
                    success=False,
                    message=f"Failed to load ADRs: {load_result['message']}",
                    requires_approval=False
                ).model_dump()
        
        # Check if ADRs are loaded
        if not hasattr(session, 'loaded_adrs') or not session.loaded_adrs:
            return ToolResult(
                success=False,
                message="No ADRs loaded. Use load_adrs first or provide a path.",
                requires_approval=False
            ).model_dump()
        
        # Get topic service
        topic_service = session.topic_service
        
        # Read ADR contents
        texts = []
        for adr_path in session.loaded_adrs:
            with open(adr_path, 'r', encoding='utf-8') as f:
                texts.append(f.read())
        
        # Predict topics
        results = topic_service.predict_batch(texts, parallel=True)
        
        # Filter by threshold if specified
        if threshold > 0:
            results = [r for r in results if r["probability"] >= threshold]
        
        # Store in session
        session.analysis_results["topics"] = results
        
        # Get distribution
        distribution = topic_service.get_topic_distribution(results)
        
        result = ToolResult(
            success=True,
            message=f"Analyzed {len(results)} ADR(s) for topics",
            data={
                "results": results,
                "distribution": distribution,
                "threshold": threshold
            },
            requires_approval=False,
            batch_operation=True,
            num_affected=len(session.loaded_adrs)
        ).model_dump()
        
        # Log completion
        if hasattr(session, 'console'):
            session.console.print(f"[green]✓[/green] {result['message']}")
        
        return result
        
    except Exception as e:
        result = ToolResult(
            success=False,
            message=f"Failed to mine topics: {str(e)}",
            requires_approval=False
        ).model_dump()
        
        # Log error
        if hasattr(session, 'console'):
            session.console.print(f"[red]✗[/red] {result['message']}")
        
        return result


@tool(parse_docstring=True)
def classify_adrs(
    path: Optional[str] = None,
    framework: str = "kruchten",
    use_examples: bool = True
) -> Dict[str, Any]:
    """Classify a batch of ADRs using a specified classification framework.
    
    This tool classifies a batch of ADRs according to architectural decision
    classification frameworks. Supports multiple frameworks with different
    classification schemes.
    
    Args:
        path: Optional path (directory) to load ADRs from (if not already loaded)
        framework: Classification framework (kruchten, quality_attributes, zimmermann)
        use_examples: Whether to use few-shot examples for better accuracy
    
    Returns:
        Dictionary with classification results for each ADR
    
    Example:
        >>> classify_adrs("adrs/", framework="kruchten")
        >>> classify_adrs(framework="zimmermann", use_examples=False)
    """
    session = get_session()
    if session is None:
        return ToolResult(
            success=False,
            message="Session not initialized",
            requires_approval=False
        ).model_dump()
    
    # Log tool invocation
    if hasattr(session, 'console'):
        session.console.print("\n[dim]→ Tool called: classify_adrs[/dim]")
        session.console.print(f"  [dim]framework: {framework}, use_examples: {use_examples}[/dim]")
    
    try:
        # Load ADRs if path provided
        if path is not None:
            load_result = load_adrs.invoke({"path": path})
            if not load_result["success"]:
                return ToolResult(
                    success=False,
                    message=f"Failed to load ADRs: {load_result['message']}",
                    requires_approval=False
                ).model_dump()
        
        # Check if ADRs are loaded
        if not hasattr(session, 'loaded_adrs') or not session.loaded_adrs:
            return ToolResult(
                success=False,
                message="No ADRs loaded. Use load_adrs first or provide a path.",
                requires_approval=False
            ).model_dump()
        
        # Get classification service
        classification_service = session.classification_service
        
        # Read ADR contents
        texts = []
        for adr_path in session.loaded_adrs:
            with open(adr_path, 'r', encoding='utf-8') as f:
                texts.append(f.read())
        
        # Classify
        classification_service.set_framework(framework)
        results = classification_service.classify_batch(
            texts,
            use_examples=use_examples
        )
        
        # Store in session
        session.analysis_results["classification"] = {
            "framework": framework,
            "results": results
        }
        
        # Count classifications
        classification_counts = {}
        for result in results:
            cls = result.get("classification", {})
            for category, value in cls.items():
                if value:
                    classification_counts[category] = classification_counts.get(category, 0) + 1
        
        result = ToolResult(
            success=True,
            message=f"Classified {len(results)} ADR(s) using {framework} framework",
            data={
                "results": results,
                "counts": classification_counts,
                "framework": framework
            },
            requires_approval=True,
            batch_operation=True,
            num_affected=len(session.loaded_adrs)
        ).model_dump()
        
        # Log completion
        if hasattr(session, 'console'):
            session.console.print(f"[green]✓[/green] {result['message']}")
        
        return result
        
    except Exception as e:
        result = ToolResult(
            success=False,
            message=f"Failed to classify ADRs: {str(e)}",
            requires_approval=False
        ).model_dump()
        
        # Log error
        if hasattr(session, 'console'):
            session.console.print(f"[red]✗[/red] {result['message']}")
        
        return result


@tool(parse_docstring=True)
def check_quality(
    path: Optional[str] = None,
    mode: str = "full",
    template: str = "madr"
) -> Dict[str, Any]:
    """Check the quality of a batch of ADRs against a template.
    
    This tool evaluates the quality and completeness of ADRs by checking
    them against a specified template (e.g., MADR). It identifies missing
    sections, consistency issues, and provides quality scores.
    
    Args:
        path: Optional path (folder) to load ADRs from (if not already loaded)
        mode: Check mode - 'full' (comprehensive) or 'section' (per-section)
        template: Template to check against (e.g., 'madr')
    
    Returns:
        Dictionary with quality check results for each ADR
    
    Example:
        >>> check_quality("adrs/", mode="full")
        >>> check_quality(mode="section", template="madr")
    """
    session = get_session()
    if session is None:
        return ToolResult(
            success=False,
            message="Session not initialized",
            requires_approval=False
        ).model_dump()
    
    # Log tool invocation
    if hasattr(session, 'console'):
        session.console.print("\n[dim]→ Tool called: check_quality[/dim]")
        session.console.print(f"  [dim]mode: {mode}, template: {template}[/dim]")
    
    try:
        # Load ADRs if path provided
        if path is not None:
            load_result = load_adrs.invoke({"path": path})
            if not load_result["success"]:
                return ToolResult(
                    success=False,
                    message=f"Failed to load ADRs: {load_result['message']}",
                    requires_approval=False
                ).model_dump()
        
        # Check if ADRs are loaded
        if not hasattr(session, 'loaded_adrs') or not session.loaded_adrs:
            return ToolResult(
                success=False,
                message="No ADRs loaded. Use load_adrs first or provide a path.",
                requires_approval=False
            ).model_dump()
        
        # Get checking service
        checking_service = session.checking_service
        
        # Read ADR contents
        texts = []
        for adr_path in session.loaded_adrs:
            with open(adr_path, 'r', encoding='utf-8') as f:
                texts.append(f.read())
        
        # Check quality
        if mode == "adherence":
            results = checking_service.check_adherence_batch(texts)
        elif mode == "sections":
            results = checking_service.check_sections_batch(texts)
        else:  # full
            results = checking_service.check_batch(texts)
        
        # Store in session
        session.analysis_results["check"] = {
            "mode": mode,
            "template": template,
            "results": results
        }
        
        # Calculate aggregate scores
        total_score = sum(r.get("overall_score", 0) for r in results)
        avg_score = total_score / len(results) if results else 0
        
        # Count issues
        total_issues = sum(len(r.get("issues", [])) for r in results)
        
        result = ToolResult(
            success=True,
            message=f"Checked quality of {len(results)} ADR(s)",
            data={
                "results": results,
                "average_score": avg_score,
                "total_issues": total_issues,
                "mode": mode,
                "template": template
            },
            requires_approval=True,
            batch_operation=True,
            num_affected=len(session.loaded_adrs)
        ).model_dump()
        
        # Log completion
        if hasattr(session, 'console'):
            session.console.print(f"[green]✓[/green] {result['message']}")
        
        return result
        
    except Exception as e:
        result = ToolResult(
            success=False,
            message=f"Failed to check quality: {str(e)}",
            requires_approval=False
        ).model_dump()
        
        # Log error
        if hasattr(session, 'console'):
            session.console.print(f"[red]✗[/red] {result['message']}")
        
        return result


@tool(parse_docstring=True)
def generate_insights(
    include_topics: bool = True,
    include_classification: bool = True,
    include_check: bool = True
) -> Dict[str, Any]:
    """Generate actionable insights from analysis results.
    
    This tool analyzes previously-stored analysis results (topics, classification,
    quality checks) and generates actionable insights, patterns, and
    recommendations for the ADR collection.
    
    Args:
        include_topics: Include topic-based insights
        include_classification: Include classification-based insights
        include_check: Include quality-based insights
    
    Returns:
        Dictionary with generated insights and recommendations
    
    Example:
        >>> generate_insights()
        >>> generate_insights(include_topics=False, include_classification=True)
    """
    session = get_session()
    if session is None:
        return ToolResult(
            success=False,
            message="Session not initialized",
            requires_approval=False
        ).model_dump()
    
    # Log tool invocation
    if hasattr(session, 'console'):
        session.console.print("\n[dim]→ Tool called: generate_insights[/dim]")
        session.console.print(f"  [dim]include_topics: {include_topics}, include_classification: {include_classification}, include_check: {include_check}[/dim]")
    
    try:
        # Check if analysis results exist
        insights = {}
        
        if include_topics and "topics" in session.analysis_results:
            topic_results = session.analysis_results["topics"]
            # Generate topic insights
            topic_distribution = {}
            for result in topic_results:
                label = result.get("topic_label", "Unknown")
                if label not in topic_distribution:
                    topic_distribution[label] = 0
                topic_distribution[label] += 1
            
            insights["topics"] = {
                "total_topics": len(topic_distribution),
                "top_topics": sorted(
                    topic_distribution.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                "distribution": topic_distribution
            }
        
        if include_classification and "classification" in session.analysis_results:
            class_results = session.analysis_results["classification"]
            # Generate classification insights
            insights["classification"] = {
                "framework": class_results.get("framework"),
                "count": len(class_results.get("results", []))
            }
        
        if include_check and "check" in session.analysis_results:
            check_results = session.analysis_results["check"]
            # Generate quality insights
            total_score = sum(
                r.get("overall_score", 0) 
                for r in check_results.get("results", [])
            )
            avg_score = total_score / len(check_results.get("results", [])) if check_results.get("results") else 0
            
            insights["check"] = {
                "average_score": avg_score,
                "total_adrs": len(check_results.get("results", [])),
                "mode": check_results.get("mode")
            }
        
        if not insights:
            return ToolResult(
                success=False,
                message="No analysis results available. Run analysis tools first.",
                requires_approval=False
            ).model_dump()
        
        # Get insight service for detailed insights
        insight_service = session.insight_service
        
        # Generate detailed insights if service available
        try:
            detailed_insights = insight_service.generate_project_insights(
                session.analysis_results
            )
            insights["detailed"] = detailed_insights
        except Exception as e:
            # Service might not support this, continue with basic insights
            pass
        
        result = ToolResult(
            success=True,
            message="Generated insights from analysis results",
            data=insights,
            requires_approval=False,
            batch_operation=False,
            num_affected=0
        ).model_dump()
        
        # Log completion
        if hasattr(session, 'console'):
            session.console.print(f"[green]✓[/green] {result['message']}")
        
        return result
        
    except Exception as e:
        result = ToolResult(
            success=False,
            message=f"Failed to generate insights: {str(e)}",
            requires_approval=False
        ).model_dump()
        
        # Log error
        if hasattr(session, 'console'):
            session.console.print(f"[red]✗[/red] {result['message']}")
        
        return result


@tool(parse_docstring=True)
def reset_memory() -> Dict[str, Any]:
    """Reset all agent memory and analysis results.
    
    This tool clears all accumulated state including:
    - Analysis results (topics, classification, checks, insights)
    - Loaded ADR files
    - Session state
    
    Note: This does NOT affect to LangGraph checkpointer conversation history.
    The agent will continue with the same conversation context.
    
    Example:
        >>> reset_memory()  # Clear all session state
    """
    session = get_session()
    if session is None:
        return ToolResult(
            success=False,
            message="Session not initialized. Reset cannot be performed.",
            requires_approval=False
        ).model_dump()
    
    # Log tool invocation
    if hasattr(session, 'console'):
        session.console.print("\n[dim]→ Tool called: reset_memory[/dim]")
    
    try:
        # Get summary before reset
        summary = {
            "analysis_results": list(session.analysis_results.keys()),
            "loaded_adrs_count": len(session.loaded_adrs),
            "has_agent": session._agent is not None and session._agent is not False
        }
        
        # Clear session state
        session.analysis_results.clear()
        session.loaded_adrs.clear()
        
        # Clear command history
        session.command_history.clear()
        session.history_index = -1
        
        result = ToolResult(
            success=True,
            message=f"Reset complete: {len(summary['analysis_results'])} analysis results, "
                    f"{summary['loaded_adrs_count']} loaded ADRs, and command history cleared",
            data=summary,
            requires_approval=False,
            batch_operation=False,
            num_affected=0
        ).model_dump()
        
        # Log completion
        if hasattr(session, 'console'):
            session.console.print(f"[green]✓[/green] {result['message']}")
            if not summary['has_agent']:
                session.console.print("  [dim]Note: Agent not initialized. No conversation history to clear.[/dim]")
        
        return result
        
    except Exception as e:
        result = ToolResult(
            success=False,
            message=f"Failed to reset memory: {str(e)}",
            requires_approval=False
        ).model_dump()
        
        # Log error
        if hasattr(session, 'console'):
            session.console.print(f"[red]✗[/red] {result['message']}")
        
        return result


# @tool(parse_docstring=True)
# def export_metadata(
#     format: str = "json-sidecar",
#     output_dir: Optional[str] = None
# ) -> Dict[str, Any]:
#     """Export analysis results to files.
    
#     This tool exports stored analysis results to files in various formats.
#     Supports sidecar JSON (separate files alongside ADRs) or consolidated
#     JSON (all results in one file).
    
#     Args:
#         format: Export format - 'json-sidecar' or 'consolidated-json'
#         output_dir: Optional output directory (uses current directory if not specified)
    
#     Returns:
#         Dictionary with export results including file paths
    
#     Example:
#         >>> export_metadata(format="json-sidecar")
#         >>> export_metadata(format="consolidated-json", output_dir="results/")
#     """
#     session = get_session()
#     if session is None:
#         return ToolResult(
#             success=False,
#             message="Session not initialized",
#             requires_approval=False
#         ).model_dump()
    
#     # Log tool invocation
#     if hasattr(session, 'console'):
#         session.console.print("\n[dim]→ Tool called: export_metadata[/dim]")
#         session.console.print(f"  [dim]format: {format}, output_dir: {output_dir}[/dim]")
    
#     try:
#         # Check if analysis results exist
#         if not session.analysis_results:
#             return ToolResult(
#                 success=False,
#                 message="No analysis results to export. Run analysis tools first.",
#                 requires_approval=False
#             ).model_dump()
        
#         # Determine output directory
#         if output_dir:
#             output_path = Path(output_dir)
#         else:
#             output_path = Path.cwd()
        
#         output_path.mkdir(parents=True, exist_ok=True)
        
#         exported_files = []
        
#         if format == "json-sidecar":
#             # Export sidecar files alongside each ADR
#             for adr_path in session.loaded_adrs:
#                 sidecar_path = adr_path.with_suffix('.adrminer.json')
                
#                 # Collect results for this ADR
#                 adr_results = {}
#                 if "topics" in session.analysis_results:
#                     adr_results["topics"] = session.analysis_results["topics"][
#                         session.loaded_adrs.index(adr_path)
#                     ]
#                 if "classification" in session.analysis_results:
#                     adr_results["classification"] = session.analysis_results["classification"]["results"][
#                         session.loaded_adrs.index(adr_path)
#                     ]
#                 if "check" in session.analysis_results:
#                     adr_results["check"] = session.analysis_results["check"]["results"][
#                         session.loaded_adrs.index(adr_path)
#                     ]
                
#                 # Write sidecar file
#                 import json
#                 with open(sidecar_path, 'w', encoding='utf-8') as f:
#                     json.dump(adr_results, f, indent=2)
                
#                 exported_files.append(str(sidecar_path))
        
#         elif format == "consolidated-json":
#             # Export all results to single file
#             import json
#             output_file = output_path / "adrminer_results.json"
            
#             export_data = {
#                 "analysis": session.analysis_results,
#                 "adrs": [str(p) for p in session.loaded_adrs]
#             }
            
#             with open(output_file, 'w', encoding='utf-8') as f:
#                 json.dump(export_data, f, indent=2)
            
#             exported_files.append(str(output_file))
        
#         else:
#             return ToolResult(
#                 success=False,
#                 message=f"Unsupported format: {format}. Use 'json-sidecar' or 'consolidated-json'.",
#                 requires_approval=False
#             ).model_dump()
        
#         result = ToolResult(
#             success=True,
#             message=f"Exported {len(exported_files)} file(s) to {output_path}",
#             data={
#                 "format": format,
#                 "output_directory": str(output_path),
#                 "exported_files": exported_files
#             },
#             requires_approval=False,
#             batch_operation=True,
#             num_affected=len(exported_files)
#         ).model_dump()
        
#         # Log completion
#         if hasattr(session, 'console'):
#             session.console.print(f"[green]✓[/green] {result['message']}")
        
#         return result
        
#     except Exception as e:
#         result = ToolResult(
#             success=False,
#             message=f"Failed to export metadata: {str(e)}",
#             requires_approval=False
#         ).model_dump()
        
#         # Log error
#         if hasattr(session, 'console'):
#             session.console.print(f"[red]✗[/red] {result['message']}")
        
#         return result
