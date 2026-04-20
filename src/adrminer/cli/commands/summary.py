"""Summary CLI commands for ADR analysis and reporting."""

from concurrent.futures import as_completed, ThreadPoolExecutor
from datetime import datetime
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text

from adrminer.config import get_settings
from adrminer.services import InsightService

console = Console()


def summary(
    path: Path = typer.Argument(
        ...,
        help="Path to ADR file or directory",
        exists=True,
    ),
    output_summary: Optional[Path] = typer.Option(
        None,
        "--output-summary",
        "-s",
        help="Export summary report to Markdown file (if only filename provided, saves to parent of ADRs folder)",
    ),
    output_detailed: Optional[Path] = typer.Option(
        None,
        "--output-detailed",
        "-d",
        help="Export detailed report to Markdown file with insights (if only filename provided, saves to parent of ADRs folder)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="LLM model name",
    ),
    parallel: Optional[bool] = typer.Option(
        None,
        "--parallel",
        "-p",
        help="Enable parallel processing (default: from config)",
    ),
    force_rewrite: bool = typer.Option(
        False,
        "--force-rewrite",
        help="Regenerate all summaries (ignore cached sidecar files)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output",
    ),
) -> None:
    """
    Generate summaries and insights for ADRs.
    
    Analyze one or more ADRs and generate console summaries or Markdown reports
    with content summaries and AI-powered insights.
    
    \b
    Examples:
        # Display console summary only
        adrminer summary examples/pharmacy-food/adrs
        
        # Export summary report to parent folder (default location)
        adrminer summary examples/pharmacy-food/adrs --output-summary summary.md
        # Result: examples/pharmacy-food/summary.md
        
        # Export detailed report with full path
        adrminer summary examples/pharmacy-food/adrs --output-detailed ./reports/detailed.md
        
        # Export both reports
        adrminer summary examples/pharmacy-food/adrs -s summary.md -d detailed.md
    """
    # Find project-local config file
    config_path = None
    if path.is_dir():
        # Check for config in ADR directory or its parent
        for check_path in [path, path.parent]:
            for config_name in ["adrminer.yaml", ".adrminer.yaml", "config.yaml"]:
                potential_config = check_path / config_name
                if potential_config.exists():
                    config_path = potential_config
                    break
            if config_path:
                break
    
    # Load insight service
    try:
        from adrminer.models.llm_factory import reset_llm_cache
        from adrminer.config import reset_settings
        reset_settings()  # Reset settings cache
        reset_llm_cache()  # Reset LLM cache
        
        settings = get_settings(config_path=config_path)
        if config_path:
            console.print(f"[dim]Using config: {config_path}[/dim]")
        console.print(f"[blue]Loading insight service (provider: {settings.llm.provider}, model: {settings.llm.model})...[/blue]")
        
        service = InsightService()
        console.print(f"[green]✓ Service loaded (model: {service.model_name})[/green]")
    except Exception as e:
        console.print(f"[red]Failed to load insight service: {e}[/red]")
        raise typer.Exit(code=1)
    
    # Collect ADR files and metadata
    console.print("\n[blue]Collecting ADRs and metadata...[/blue]")
    adrs_data = _collect_adrs_with_metadata(path)
    
    if not adrs_data:
        console.print(f"[yellow]No ADR files found at {path}[/yellow]")
        raise typer.Exit(code=1)
    
    console.print(f"[green]✓ Found {len(adrs_data)} ADR(s) with metadata[/green]")
    
    # Display console summary
    _display_console_summary(adrs_data)
    
    # Generate and export reports if requested
    if output_summary or output_detailed:
        # Resolve output paths - save in parent folder by default to avoid mixing with ADRs
        if path.is_dir():
            # Input is ADR directory - save in parent folder
            default_output_dir = path.parent
        else:
            # Input is single ADR file - save in parent of parent folder
            default_output_dir = path.parent.parent
        
        resolved_summary = output_summary
        if output_summary and (not output_summary.parent.name or str(output_summary.parent) == "."):
            resolved_summary = default_output_dir / output_summary
        
        resolved_detailed = output_detailed
        if output_detailed and (not output_detailed.parent.name or str(output_detailed.parent) == "."):
            resolved_detailed = default_output_dir / output_detailed
        
        _generate_reports(
            adrs_data=adrs_data,
            service=service,
            output_summary=resolved_summary,
            output_detailed=resolved_detailed,
            parallel=parallel,
            force_rewrite=force_rewrite,
            verbose=verbose,
        )


def _collect_adrs_with_metadata(path: Path) -> list[dict]:
    """
    Collect ADR files and their metadata.
    
    Args:
        path: Path to ADR file or directory
        
    Returns:
        List of dictionaries with adr_file, adr_content, and metadata
    """
    # Collect ADR files
    if path.is_file():
        adr_files = [path]
    else:
        adr_files = list(path.glob("*.md")) + list(path.glob("*.MD"))
    
    adrs_data = []
    
    for adr_file in adr_files:
        # Read ADR content
        try:
            with open(adr_file, "r", encoding="utf-8") as f:
                adr_content = f.read()
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read {adr_file.name}: {e}[/yellow]")
            continue
        
        # Try to find metadata file
        metadata = None
        metadata_paths = [
            adr_file.with_suffix(".adrminer.checking.json"),
            adr_file.with_suffix(".metadata.json"),
            adr_file.with_suffix(".adrminer.classification.json"),
        ]
        
        for metadata_path in metadata_paths:
            if metadata_path.exists():
                try:
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                    break
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not read metadata for {adr_file.name}: {e}[/yellow]")
        
        adrs_data.append({
            "adr_file": adr_file,
            "adr_content": adr_content,
            "metadata": metadata,
        })
    
    return adrs_data


def _display_console_summary(adrs_data: list[dict]) -> None:
    """
    Display console summary of ADRs.
    
    Args:
        adrs_data: List of ADR data dictionaries
    """
    console.print("\n[bold]ADR Summary:[/bold]\n")
    
    # Build table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("File", style="green")
    table.add_column("Topic", style="yellow")
    table.add_column("Kruchten", justify="center")
    table.add_column("Zimmermann", justify="center")
    table.add_column("QA", justify="center")
    table.add_column("Quality", justify="center")
    
    for i, adr_data in enumerate(adrs_data, 1):
        adr_file = adr_data["adr_file"]
        metadata = adr_data["metadata"]
        
        # Extract topic
        if metadata and "topics" in metadata:
            topic = metadata["topics"].get("topic_label", "N/A")
        else:
            topic = "N/A"
        
        # Extract classifications
        kruchten = _get_classification(metadata, "kruchten")
        zimmermann = _get_classification(metadata, "zimmermann")
        qa = _get_classification(metadata, "quality_attributes")
        
        # Extract quality score
        if metadata and "check" in metadata:
            quality_score = metadata["check"].get("template_adherence", {}).get("adherence_score", "N/A")
        else:
            quality_score = "N/A"
        
        # Color code quality score
        if isinstance(quality_score, (int, float)):
            if quality_score >= 0.8:
                quality = f"[green]{quality_score:.1f}[/green]"
            elif quality_score >= 0.6:
                quality = f"[yellow]{quality_score:.1f}[/yellow]"
            else:
                quality = f"[red]{quality_score:.1f}[/red]"
        else:
            quality = quality_score
        
        table.add_row(
            str(i),
            adr_file.name,
            topic[:30] if topic != "N/A" else "N/A",
            kruchten[:20] if kruchten != "N/A" else "N/A",
            zimmermann[:20] if zimmermann != "N/A" else "N/A",
            qa[:15] if qa != "N/A" else "N/A",
            quality,
        )
    
    console.print(table)
    
    # Show summary statistics
    adrs_with_metadata = sum(1 for a in adrs_data if a["metadata"])
    console.print(f"\n[cyan]ADRs with metadata: {adrs_with_metadata}/{len(adrs_data)}[/cyan]")


def _get_classification(metadata: Optional[dict], framework: str) -> str:
    """
    Get primary category for a classification framework.
    
    Args:
        metadata: ADR metadata dictionary
        framework: Framework name (kruchten, zimmermann, quality_attributes)
        
    Returns:
        Primary category string or "N/A"
    """
    if not metadata or "classifications" not in metadata:
        return "N/A"
    
    classifications = metadata["classifications"]
    if framework not in classifications:
        return "N/A"
    
    return classifications[framework].get("primary_category", "N/A")


def _generate_reports(
    adrs_data: list[dict],
    service: InsightService,
    output_summary: Optional[Path],
    output_detailed: Optional[Path],
    parallel: Optional[bool] = None,
    force_rewrite: bool = False,
    verbose: bool = False,
) -> None:
    """
    Generate and export summary and detailed reports.
    
    Args:
        adrs_data: List of ADR data dictionaries
        service: InsightService instance
        output_summary: Path for summary report (optional)
        output_detailed: Path for detailed report (optional)
        parallel: Enable parallel processing (None = use config default)
        force_rewrite: Ignore cached summaries and regenerate
        verbose: Show detailed output
    """
    # Get parallel setting
    settings = get_settings()
    use_parallel = parallel if parallel is not None else settings.output.parallel
    
    if verbose:
        console.print(f"[cyan]Processing mode: {'parallel' if use_parallel else 'sequential'}[/cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        # Generate content summaries if needed
        if output_summary or output_detailed:
            task = progress.add_task("Generating content summaries...", total=len(adrs_data))
            
            content_summaries = _generate_content_summaries(
                adrs_data=adrs_data,
                service=service,
                progress=progress,
                task=task,
                parallel=use_parallel,
                force_rewrite=force_rewrite,
                verbose=verbose,
            )
        
        # Generate summary report
        if output_summary:
            progress.add_task("Writing summary report...", total=1)
            _write_summary_report(
                output_summary=output_summary,
                adrs_data=adrs_data,
                content_summaries=content_summaries,
            )
            console.print(f"\n[green]✓ Summary report exported to {output_summary}[/green]")
        
        # Generate detailed report
        if output_detailed:
            # Generate project insights
            progress.add_task("Generating project insights...", total=1)
            all_metadata = [a["metadata"] for a in adrs_data if a["metadata"]]
            if all_metadata:
                try:
                    project_insights = service.generate_project_insights(all_metadata)
                except Exception as e:
                    console.print(f"[red]Error generating project insights: {e}[/red]")
                    project_insights = None
            else:
                project_insights = None
            
            # Generate per-ADR insights
            task = progress.add_task("Generating ADR insights...", total=len(adrs_data))
            adr_insights = {}
            for adr_data in adrs_data:
                adr_file = adr_data["adr_file"]
                metadata = adr_data["metadata"]
                
                if metadata:
                    try:
                        insights = service.generate_adr_insights(metadata)
                        adr_insights[str(adr_file)] = insights
                    except Exception as e:
                        console.print(f"[yellow]Warning: Could not generate insights for {adr_file.name}: {e}[/yellow]")
                        adr_insights[str(adr_file)] = None
                
                progress.update(task, advance=1)
            
            # Write detailed report
            progress.add_task("Writing detailed report...", total=1)
            _write_detailed_report(
                output_detailed=output_detailed,
                adrs_data=adrs_data,
                content_summaries=content_summaries,
                project_insights=project_insights,
                adr_insights=adr_insights,
            )
            console.print(f"\n[green]✓ Detailed report exported to {output_detailed}[/green]")


def _generate_content_summaries(
    adrs_data: list[dict],
    service: InsightService,
    progress,
    task,
    parallel: bool = True,
    force_rewrite: bool = False,
    verbose: bool = False,
) -> dict[str, str]:
    """
    Generate content summaries with caching in metadata sidecar files.
    
    Args:
        adrs_data: List of ADR data dictionaries
        service: InsightService instance
        progress: Rich progress object
        task: Progress task ID
        parallel: Enable parallel processing
        force_rewrite: Ignore cached summaries
        verbose: Show detailed output
        
    Returns:
        Dictionary mapping ADR paths to summaries
    """
    content_summaries = {}
    
    def process_adr(adr_data, verbose=verbose):
        """Process a single ADR file."""
        adr_file = adr_data["adr_file"]
        adr_content = adr_data["adr_content"]
        metadata = adr_data["metadata"]
        
        # Find the metadata sidecar file to use for caching
        metadata_path = None
        if metadata:
            # Use the metadata file that was loaded
            # Try to find the actual file path from metadata
            adr_file_str = str(adr_file)
            
            # Look for metadata files in priority order
            metadata_paths = [
                adr_file.with_suffix('.adrminer.checking.json'),
                adr_file.with_suffix('.metadata.json'),
                adr_file.with_suffix('.adrminer.classification.json'),
            ]
            
            for path in metadata_paths:
                if path.exists():
                    metadata_path = path
                    break
        
        if not metadata_path:
            # No metadata file exists, can't cache
            try:
                summary = service.generate_content_summary(adr_content)
                if verbose:
                    console.print(f"[dim]  Generated summary for {adr_file.name} (no metadata file to cache)[/dim]")
                return (adr_file, summary.summary, False)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not generate summary for {adr_file.name}: {e}[/yellow]")
                return (adr_file, "Summary generation failed.", False)
        
        # Load metadata file to check for cached summary
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_data = json.load(f)
        except Exception as e:
            if verbose:
                console.print(f"[yellow]  Warning: Could not read metadata file {metadata_path.name}: {e}[/yellow]")
            metadata_data = {}
        
        # Check for cached summary
        cached_summary = None
        if not force_rewrite and 'summary' in metadata_data:
            cached_summary = metadata_data['summary']
            if verbose:
                console.print(f"[dim]  Using cached summary for {adr_file.name}[/dim]")
            return (adr_file, cached_summary, True)
        
        # Generate new summary
        try:
            summary = service.generate_content_summary(adr_content)
            
            # Update metadata with summary
            metadata_data['summary'] = summary.summary
            metadata_data['summary_generated_at'] = datetime.now().isoformat()
            metadata_data['summary_model'] = service.model_name
            
            # Save back to metadata file
            try:
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata_data, f, indent=2)
                
                if verbose:
                    console.print(f"[dim]  Cached summary in {metadata_path.name}[/dim]")
            except Exception as e:
                if verbose:
                    console.print(f"[yellow]  Warning: Could not save summary to {metadata_path.name}: {e}[/yellow]")
            
            return (adr_file, summary.summary, False)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not generate summary for {adr_file.name}: {e}[/yellow]")
            return (adr_file, "Summary generation failed.", False)
    
    if parallel:
        # Parallel processing
        with ThreadPoolExecutor() as executor:
            # Submit all tasks
            future_to_data = {
                executor.submit(process_adr, adr_data): adr_data 
                for adr_data in adrs_data
            }
            
            # Map file to index
            file_to_index = {adr_data["adr_file"]: i for i, adr_data in enumerate(adrs_data)}
            
            # Create list to store results in correct order
            ordered_results = [None] * len(adrs_data)
            
            # Collect results as they complete
            for future in as_completed(future_to_data):
                adr_data = future_to_data[future]
                result = future.result()
                
                adr_file, summary, from_cache = result
                idx = file_to_index[adr_file]
                ordered_results[idx] = (adr_file, summary)
                
                progress.update(task, advance=1)
            
            # Convert to dictionary
            for adr_file, summary in ordered_results:
                content_summaries[str(adr_file)] = summary
    else:
        # Sequential processing
        for adr_data in adrs_data:
            adr_file, summary, from_cache = process_adr(adr_data)
            content_summaries[str(adr_file)] = summary
            progress.update(task, advance=1)
    
    return content_summaries


def _write_summary_report(
    output_summary: Path,
    adrs_data: list[dict],
    content_summaries: dict[str, str],
) -> None:
    """
    Write summary report to Markdown file.
    
    Args:
        output_summary: Path for output file
        adrs_data: List of ADR data dictionaries
        content_summaries: Dictionary mapping ADR paths to summaries
    """
    output_summary.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "# ADR Summary Report\n",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total ADRs: {len(adrs_data)}\n",
    ]
    
    for adr_data in adrs_data:
        adr_file = adr_data["adr_file"]
        metadata = adr_data["metadata"]
        
        lines.append(f"## {adr_file.name}\n")
        
        # Content summary
        summary = content_summaries.get(str(adr_file), "Summary not available.")
        lines.append(summary)
        lines.append("")
        
        # Key metadata
        if metadata:
            lines.append("### Key Metadata\n")
            
            # Topic
            if "topics" in metadata:
                topic = metadata["topics"]
                lines.append(f"- **Topic**: {topic.get('topic_label', 'N/A')}")
                lines.append(f"  - **Probability**: {topic.get('probability', 0):.2%}")
            
            # Classifications
            if "classifications" in metadata:
                lines.append("\n**Classifications:**")
                for framework, cls in metadata["classifications"].items():
                    primary = cls.get("primary_category", "N/A")
                    confidence = cls.get("confidence", 0)
                    lines.append(f"- **{framework}**: {primary} ({confidence:.0%})")
            
            # Quality check
            if "check" in metadata:
                quality = metadata["check"]
                adherence = quality.get("template_adherence", {})
                score = adherence.get("adherence_score", "N/A")
                lines.append(f"\n**Quality Check:**")
                lines.append(f"- **Adherence Score**: {score}")
                
                # Section summary
                assessments = quality.get("section_assessments", [])
                if assessments:
                    present = sum(1 for a in assessments if a.get("presence") == "Yes")
                    lines.append(f"- **Sections Present**: {present}/{len(assessments)}")
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    with open(output_summary, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write_detailed_report(
    output_detailed: Path,
    adrs_data: list[dict],
    content_summaries: dict[str, str],
    project_insights,
    adr_insights: dict[str, any],
) -> None:
    """
    Write detailed report to Markdown file with insights.
    
    Args:
        output_detailed: Path for output file
        adrs_data: List of ADR data dictionaries
        content_summaries: Dictionary mapping ADR paths to summaries
        project_insights: ProjectInsights object
        adr_insights: Dictionary mapping ADR paths to ADRInsights objects
    """
    output_detailed.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "# ADR Analysis Report\n",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total ADRs: {len(adrs_data)}\n",
    ]
    
    # Project-wide insights (first section)
    if project_insights:
        lines.append("## 📊 Project-Wide Insights\n")
        lines.append(f"**{project_insights.overall_summary}**\n")
        
        lines.append("### Classification Patterns")
        for pattern in project_insights.classification_patterns[:5]:
            lines.append(f"- **{pattern.framework} - {pattern.category}**: {pattern.count} ADRs ({pattern.percentage:.1%})")
        
        lines.append("\n### Quality Trends")
        lines.append(f"- **Average Adherence Score**: {project_insights.quality_trends.average_adherence_score:.2f}")
        lines.append(f"- **Quality Distribution**: {project_insights.quality_trends.quality_distribution}")
        if project_insights.quality_trends.common_missing_sections:
            lines.append(f"- **Common Missing Sections**: {', '.join(project_insights.quality_trends.common_missing_sections[:3])}")
        
        lines.append("\n### Architectural Themes")
        for theme in project_insights.architectural_themes[:5]:
            lines.append(f"- **{theme.theme}**: {theme.adr_count} ADRs - {theme.description}")
        
        lines.append("\n### Risk Assessment")
        lines.append(f"**{project_insights.risk_assessment.risk_summary}**")
        if project_insights.risk_assessment.high_risk_adrs:
            lines.append(f"\n**High Risk ADRs:** {', '.join(project_insights.risk_assessment.high_risk_adrs)}")
        
        lines.append("\n### Consistency Analysis")
        lines.append(f"**Overall Consistency**: {project_insights.consistency_analysis.overall_consistency}")
        lines.append(f"{project_insights.consistency_analysis.analysis}")
        
        lines.append("\n### Project-Level Recommendations")
        for rec in project_insights.recommendations:
            lines.append(f"#### [{rec.priority} Priority] {rec.area}")
            lines.append(rec.recommendation)
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Per-ADR insights
    for adr_data in adrs_data:
        adr_file = adr_data["adr_file"]
        metadata = adr_data["metadata"]
        insights = adr_insights.get(str(adr_file))
        
        lines.append(f"## {adr_file.name}\n")
        
        # Content summary
        summary = content_summaries.get(str(adr_file), "Summary not available.")
        lines.append(summary)
        lines.append("")
        
        # Key metadata
        if metadata:
            lines.append("### Key Metadata\n")
            
            # Topic
            if "topics" in metadata:
                topic = metadata["topics"]
                lines.append(f"- **Topic**: {topic.get('topic_label', 'N/A')}")
                lines.append(f"  - **Probability**: {topic.get('probability', 0):.2%}")
            
            # Classifications
            if "classifications" in metadata:
                lines.append("\n**Classifications:**")
                for framework, cls in metadata["classifications"].items():
                    primary = cls.get("primary_category", "N/A")
                    confidence = cls.get("confidence", 0)
                    lines.append(f"- **{framework}**: {primary} ({confidence:.0%})")
            
            # Quality check
            if "check" in metadata:
                quality = metadata["check"]
                adherence = quality.get("template_adherence", {})
                score = adherence.get("adherence_score", "N/A")
                lines.append(f"\n**Quality Check:**")
                lines.append(f"- **Adherence Score**: {score}")
        
        # Insights
        if insights:
            lines.append("\n### 💡 Insights & Analysis\n")
            
            # Classification alignment
            lines.append(f"#### Classification Alignment ({insights.classification_alignment.alignment_level})")
            lines.append(insights.classification_alignment.analysis)
            
            # Quality assessment
            lines.append(f"\n#### Quality Assessment ({insights.quality_assessment.overall_quality})")
            lines.append(insights.quality_assessment.interpretation)
            if insights.quality_assessment.improvement_suggestions:
                lines.append("\n**Improvement Suggestions:**")
                for suggestion in insights.quality_assessment.improvement_suggestions:
                    lines.append(f"- {suggestion}")
            
            # Confidence assessment
            lines.append(f"\n#### Confidence Assessment ({insights.confidence_assessment.overall_confidence})")
            lines.append(insights.confidence_assessment.interpretation)
            
            # Topic-content match
            lines.append(f"\n#### Topic-Content Match ({insights.topic_content_match.alignment_level})")
            lines.append(insights.topic_content_match.analysis)
            
            # Recommendations
            lines.append("\n#### Actionable Recommendations")
            for rec in insights.recommendations:
                lines.append(f"**[{rec.priority} - {rec.category}]**: {rec.recommendation}")
            
            lines.append(f"\n**Overall Summary**: {insights.overall_summary}")
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    with open(output_detailed, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# Import datetime at module level
from datetime import datetime