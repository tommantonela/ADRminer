"""CLI command for ADR quality checking."""

import csv
from pathlib import Path
from typing import Literal, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text

from adrminer.services.checking_service import CheckingService, MADR_SECTIONS
from adrminer.exporters import JSONExporter

# Rich console
console = Console()


def _load_adr_files(adr_path: Path) -> list[tuple[Path, str]]:
    """
    Load ADR files from a path.
    
    Args:
        adr_path: Path to ADR file or directory
    
    Returns:
        List of (path, content) tuples
    """
    files = []
    
    if adr_path.is_file():
        # Single ADR file
        try:
            with open(adr_path, 'r', encoding='utf-8') as f:
                content = f.read()
            files.append((adr_path, content))
        except Exception as e:
            console.print(f"[red]Error reading {adr_path}: {e}[/red]")
    elif adr_path.is_dir():
        # Directory: load all .md files
        for md_file in sorted(adr_path.glob("*.md")):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                files.append((md_file, content))
            except Exception as e:
                console.print(f"[red]Error reading {md_file}: {e}[/red]")
    
    return files


def _parse_assessment_sections(assessment: str) -> dict[str, str]:
    """
    Parse assessment text to extract section information.
    
    Args:
        assessment: The full assessment text
        
    Returns:
        Dictionary mapping section names to their status descriptions
    """
    sections_data = {}
    
    # Core MADR sections to look for
    core_sections = [
        "Title", "Context", "Decision Drivers", "Decision", 
        "Consequences", "Alternatives", "Status"
    ]
    
    # Try to find section information in assessment
    lines = assessment.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        
        # Check if this line starts a section
        for section in core_sections:
            if line.startswith(f"- {section}:") or line.startswith(f"{section}:"):
                # Save previous section if exists
                if current_section and current_content:
                    sections_data[current_section] = ' '.join(current_content)
                
                # Start new section
                current_section = section
                # Extract status after colon
                colon_pos = line.find(':')
                if colon_pos != -1:
                    status = line[colon_pos + 1:].strip()
                    if status:
                        current_content = [status]
                    else:
                        current_content = []
                else:
                    current_content = []
                break
        else:
            # Continue collecting content for current section (but limit to one line)
            if current_section and line and not line.startswith('-') and not current_content:
                # Only take the first line after the section header
                current_content.append(line.split('.')[0] + '.' if '.' in line else line)
    
    # Don't forget the last section
    if current_section and current_content:
        sections_data[current_section] = ' '.join(current_content)
    
    return sections_data


def _display_adherence_results(results: list[dict], adr_files: list[Path]):
    """
    Display adherence check results in a table.
    
    Args:
        results: List of checking results
        adr_files: List of ADR file paths
    """
    from rich.table import Table
    
    # For batch, show unified message
    if len(adr_files) > 1:
        console.print("[cyan]Combines adherence to MADR template and section consistency assessment (presence, quality, purpose)[/cyan]")
    else:
        console.print("[cyan]Evaluates overall MADR template adherence with a score (0.0-1.0)[/cyan]")
    
    # For batch, show consolidated table with section info
    if len(adr_files) > 1:
        table = Table(title="ADR Quality Assessment")
        table.add_column("ADR", style="cyan", no_wrap=True)
        table.add_column("Adherence score")
        table.add_column("Section presence")
        table.add_column("Section quality")
        table.add_column("Section consistency")
        
        for (adr_path, _), result in zip(adr_files, results):
            if "error" in result:
                table.add_row(
                    adr_path.name,
                    "[red]N/A[/red]",
                    "[red]Error[/red]",
                    "[red]Error[/red]",
                    "[red]Error[/red]"
                )
                continue
            
            # Get adherence score
            template = result.get("template_adherence", {})
            score = template.get("adherence_score", 0.0)
            
            # Color-code score
            if score >= 0.8:
                score_display = f"[green]{score:.2f}[/green]"
            elif score >= 0.6:
                score_display = f"[yellow]{score:.2f}[/yellow]"
            elif score >= 0.4:
                score_display = f"[orange1]{score:.2f}[/orange1]"
            else:
                score_display = f"[red]{score:.2f}[/red]"
            
            # Get section statistics (only available in sections/full modes)
            assessments = result.get("section_assessments", [])
            
            if assessments:
                # Calculate section statistics
                present = sum(1 for s in assessments if s.get("presence") == "Yes")
                quality = sum(1 for s in assessments if s.get("content_quality") == "Yes")
                consistent = sum(1 for s in assessments if s.get("purpose_consistency") == "Yes")
                
                # Color-code ratios
                def _score_color(value: int, total: int) -> str:
                    """Get color based on score ratio."""
                    if total == 0:
                        return "[red]0/0[/red]"
                    ratio = value / total
                    if ratio >= 0.8:
                        return f"[green]{value}/{total}[/green]"
                    elif ratio >= 0.6:
                        return f"[yellow]{value}/{total}[/yellow]"
                    else:
                        return f"[red]{value}/{total}[/red]"
                
                present_str = _score_color(present, len(assessments))
                quality_str = _score_color(quality, len(assessments))
                consistent_str = _score_color(consistent, len(assessments))
            else:
                # No section data available
                present_str = "[dim]N/A[/dim]"
                quality_str = "[dim]N/A[/dim]"
                consistent_str = "[dim]N/A[/dim]"
            
            table.add_row(
                adr_path.name,
                score_display,
                present_str,
                quality_str,
                consistent_str
            )
        
        console.print(table)
    else:
        # For single ADR, show simple table
        table = Table(title="ADR Template Adherence Results")
        table.add_column("ADR", style="cyan", no_wrap=True)
        table.add_column("Score")
        
        for (adr_path, _), result in zip(adr_files, results):
            if "error" in result:
                table.add_row(
                    adr_path.name,
                    "[red]N/A[/red]"
                )
            else:
                template = result.get("template_adherence", {})
                score = template.get("adherence_score", 0.0)
                assessment = template.get("assessment", "")
                
                # Determine score color based on score
                if score >= 0.8:
                    score_display = f"[green]{score:.2f}[/green]"
                elif score >= 0.6:
                    score_display = f"[yellow]{score:.2f}[/yellow]"
                elif score >= 0.4:
                    score_display = f"[orange1]{score:.2f}[/orange1]"
                else:
                    score_display = f"[red]{score:.2f}[/red]"
                
                table.add_row(
                    adr_path.name,
                    score_display
                )
        
        console.print(table)
    
    # Display section breakdown and assessment for single ADR
    if len(adr_files) == 1:
        result = results[0]
        if "error" not in result:
            template = result.get("template_adherence", {})
            assessment = template.get("assessment", "")
            
            if assessment:
                # Parse assessment to extract section information
                sections_data = _parse_assessment_sections(assessment)
                
                # Create 2nd table for core MADR sections
                if sections_data:
                    core_sections = ["Title", "Context", "Decision Drivers", "Decision", "Consequences", "Alternatives", "Status"]
                    core_table = Table(title="MADR Core Sections")
                    core_table.add_column("Section", style="cyan")
                    core_table.add_column("Assessment")
                    
                    for section in core_sections:
                        if section in sections_data:
                            status_color = "[green]" if "Present" in sections_data[section] or "present" in sections_data[section].lower() else "[red]"
                            core_table.add_row(section, f"{status_color}{sections_data[section]}[/{status_color}]")
                        else:
                            core_table.add_row(section, "[red]Not found[/red]")
                    
                    console.print(core_table)


def _display_section_results(results: list[dict], adr_files: list[Path]):
    """
    Display section consistency results in a table.
    
    Args:
        results: List of checking results
        adr_files: List of ADR file paths
    """
    from rich.table import Table
    
    # For batch, show unified message
    if len(adr_files) > 1:
        console.print("[cyan]Combines adherence to MADR template and section consistency assessment (presence, quality, purpose)[/cyan]")
    else:
        console.print("[cyan]Evaluates section-wise MADR consistency (presence, quality, purpose)[/cyan]")
    
    # Create summary table
    summary_table = Table(title="ADR Quality Assessment")
    summary_table.add_column("ADR", style="cyan", no_wrap=True)
    summary_table.add_column("Adherence score")
    summary_table.add_column("Section presence")
    summary_table.add_column("Section quality")
    summary_table.add_column("Section consistency")
    
    for (adr_path, _), result in zip(adr_files, results):
        if "error" in result:
            summary_table.add_row(
                adr_path.name,
                "[red]N/A[/red]",
                "[red]Error[/red]",
                "[red]Error[/red]",
                "[red]Error[/red]"
            )
            continue
        
        # Get adherence score (if available)
        template = result.get("template_adherence", {})
        score = template.get("adherence_score", 0.0)
        
        # Color-code score
        if score > 0:
            if score >= 0.8:
                score_display = f"[green]{score:.2f}[/green]"
            elif score >= 0.6:
                score_display = f"[yellow]{score:.2f}[/yellow]"
            elif score >= 0.4:
                score_display = f"[orange1]{score:.2f}[/orange1]"
            else:
                score_display = f"[red]{score:.2f}[/red]"
        else:
            score_display = "[dim]N/A[/dim]"
        
        assessments = result.get("section_assessments", [])
        
        # Count statistics
        present = sum(1 for s in assessments if s.get("presence") == "Yes")
        quality = sum(1 for s in assessments if s.get("content_quality") == "Yes")
        consistent = sum(1 for s in assessments if s.get("purpose_consistency") == "Yes")
        
        # Color coding based on ratio
        def _score_color(value: int, total: int) -> str:
            """Get color based on score ratio."""
            if total == 0:
                return "[red]0/0[/red]"
            ratio = value / total
            if ratio >= 0.8:
                return f"[green]{value}/{total}[/green]"
            elif ratio >= 0.6:
                return f"[yellow]{value}/{total}[/yellow]"
            else:
                return f"[red]{value}/{total}[/red]"
        
        summary_table.add_row(
            adr_path.name,
            score_display,
            _score_color(present, len(assessments)),
            _score_color(quality, len(assessments)),
            _score_color(consistent, len(assessments))
        )
    
    console.print(summary_table)
    
    # Create detailed table for first ADR (or if only one ADR)
    if len(adr_files) == 1:
        result = results[0]
        if "error" not in result:
            assessments = result.get("section_assessments", [])
            
            # adr_files is list of (path, content) tuples
            first_path = adr_files[0][0]
            detailed_table = Table(title=f"Section Details: {first_path.name}")
            detailed_table.add_column("Section", style="cyan")
            detailed_table.add_column("Present")
            detailed_table.add_column("Quality")
            detailed_table.add_column("Consistent")
            
            for assessment in assessments:
                section_name = assessment.get("section_name", "")
                presence = assessment.get("presence", "No")
                content_quality = assessment.get("content_quality", "No")
                purpose_consistency = assessment.get("purpose_consistency", "No")
                
                # Color coding
                presence_color = "[green]Yes[/green]" if presence == "Yes" else "[red]No[/red]"
                quality_color = "[green]Yes[/green]" if content_quality == "Yes" else "[red]No[/red]"
                
                if purpose_consistency == "Yes":
                    consistency_color = "[green]Yes[/green]"
                elif purpose_consistency == "Partial":
                    consistency_color = "[yellow]Partial[/yellow]"
                else:
                    consistency_color = "[red]No[/red]"
                
                detailed_table.add_row(
                    section_name,
                    presence_color,
                    quality_color,
                    consistency_color
                )
            
            console.print(detailed_table)
            
            # Display justifications below table
            console.print("\n[bold]Section Justifications:[/bold]")
            for assessment in assessments:
                section_name = assessment.get("section_name", "")
                justification = assessment.get("justification", "")
                alternate_title = assessment.get("alternate_title", [])
                
                console.print(f"\n[cyan]• {section_name}[/cyan]")
                console.print(f"  {justification}")
                
                if alternate_title:
                    console.print(f"  [yellow]Alternate titles:[/yellow] {', '.join(alternate_title)}")


def _display_full_results(results: list[dict], adr_files: list[Path]):
    """
    Display full assessment results.
    
    Args:
        results: List of checking results
        adr_files: List of ADR file paths
    """
    # For batch, show unified message
    if len(adr_files) > 1:
        console.print("[cyan]Combines adherence to MADR template and section consistency assessment (presence, quality, purpose)[/cyan]")
    else:
        console.print("[cyan]Combines adherence and sections checks for comprehensive assessment[/cyan]")
    
    # For batch checks, show consolidated table
    if len(adr_files) > 1:
        from rich.table import Table
        
        table = Table(title="ADR Quality Assessment")
        table.add_column("ADR", style="cyan", no_wrap=True)
        table.add_column("Adherence score")
        table.add_column("Section presence")
        table.add_column("Section quality")
        table.add_column("Section consistency")
        
        for (adr_path, _), result in zip(adr_files, results):
            if "error" in result:
                table.add_row(
                    adr_path.name,
                    "[red]N/A[/red]",
                    "[red]Error[/red]",
                    "[red]Error[/red]",
                    "[red]Error[/red]"
                )
                continue
            
            # Get adherence score
            template = result.get("template_adherence", {})
            score = template.get("adherence_score", 0.0)
            
            # Color-code score
            if score >= 0.8:
                score_display = f"[green]{score:.2f}[/green]"
            elif score >= 0.6:
                score_display = f"[yellow]{score:.2f}[/yellow]"
            elif score >= 0.4:
                score_display = f"[orange1]{score:.2f}[/orange1]"
            else:
                score_display = f"[red]{score:.2f}[/red]"
            
            # Get section statistics
            assessments = result.get("section_assessments", [])
            present = sum(1 for s in assessments if s.get("presence") == "Yes")
            quality = sum(1 for s in assessments if s.get("content_quality") == "Yes")
            consistent = sum(1 for s in assessments if s.get("purpose_consistency") == "Yes")
            
            # Color-code ratios
            def _score_color(value: int, total: int) -> str:
                """Get color based on score ratio."""
                if total == 0:
                    return "[red]0/0[/red]"
                ratio = value / total
                if ratio >= 0.8:
                    return f"[green]{value}/{total}[/green]"
                elif ratio >= 0.6:
                    return f"[yellow]{value}/{total}[/yellow]"
                else:
                    return f"[red]{value}/{total}[/red]"
            
            table.add_row(
                adr_path.name,
                score_display,
                _score_color(present, len(assessments)),
                _score_color(quality, len(assessments)),
                _score_color(consistent, len(assessments))
            )
        
        console.print(table)
    else:
        # For single ADR, show detailed breakdown
        console.print("\n[bold]Template Adherence:[/bold]")
        _display_adherence_results(results, adr_files)
        
        console.print("\n[bold]Section Consistency:[/bold]")
        _display_section_results(results, adr_files)


def _export_to_csv(results: list[dict], adr_files: list[Path], mode: str, csv_path: Path):
    """
    Export checking results to CSV file.
    
    Args:
        results: List of checking results
        adr_files: List of ADR file paths
        mode: Checking mode
        csv_path: Path to output CSV file
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    if mode == "adherence":
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ADR", "Score", "Status", "Date", "Title", "Assessment"])
            
            for (adr_path, _), result in zip(adr_files, results):
                if "error" in result:
                    writer.writerow([adr_path.name, "N/A", "Error", "", "", result.get("error", "")])
                else:
                    template = result.get("template_adherence", {})
                    writer.writerow([
                        adr_path.name,
                        template.get("adherence_score", 0.0),
                        template.get("status", ""),
                        template.get("date", ""),
                        template.get("title", ""),
                        template.get("assessment", "")
                    ])
    
    elif mode == "sections":
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ADR", "Section", "Presence", "Quality", "Consistency", "Justification"])
            
            for (adr_path, _), result in zip(adr_files, results):
                if "error" in result:
                    writer.writerow([adr_path.name, "Error", "", "", "", result.get("error", "")])
                else:
                    assessments = result.get("section_assessments", [])
                    for assessment in assessments:
                        writer.writerow([
                            adr_path.name,
                            assessment.get("section_name", ""),
                            assessment.get("presence", ""),
                            assessment.get("content_quality", ""),
                            assessment.get("purpose_consistency", ""),
                            assessment.get("justification", "")
                        ])
    
    else:  # full mode
        # Adherence summary
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ADR", "Score", "Status", "Date", "Title", "Assessment"])
            
            for (adr_path, _), result in zip(adr_files, results):
                if "error" in result:
                    writer.writerow([adr_path.name, "N/A", "Error", "", "", result.get("error", "")])
                else:
                    template = result.get("template_adherence", {})
                    writer.writerow([
                        adr_path.name,
                        template.get("adherence_score", 0.0),
                        template.get("status", ""),
                        template.get("date", ""),
                        template.get("title", ""),
                        template.get("assessment", "")
                    ])
        
        # Section details (separate file)
        sections_csv_path = csv_path.parent / f"{csv_path.stem}_sections.csv"
        with open(sections_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ADR", "Section", "Presence", "Quality", "Consistency", "Justification"])
            
            for (adr_path, _), result in zip(adr_files, results):
                if "error" not in result:
                    assessments = result.get("section_assessments", [])
                    for assessment in assessments:
                        writer.writerow([
                            adr_path.name,
                            assessment.get("section_name", ""),
                            assessment.get("presence", ""),
                            assessment.get("content_quality", ""),
                            assessment.get("purpose_consistency", ""),
                            assessment.get("justification", "")
                        ])
        
        console.print(f"[green]✓ Exported sections to {sections_csv_path}[/green]")


def check(
    adr_path: Path = typer.Argument(
        ...,
        help="Path to ADR file or directory",
        exists=True,
    ),
    mode: Literal["adherence", "sections", "full"] = typer.Option(
        "full",
        "--mode",
        "-m",
        help="Checking mode (adherence|sections|full)",
    ),
    parallel: bool = typer.Option(
        True,
        "--parallel",
        "-p",
        help="Enable parallel processing",
    ),
    csv: Optional[Path] = typer.Option(
        None,
        "--csv",
        help="Export results to CSV file",
    ),
) -> None:
    """
    Check ADR quality against MADR template.
    
    Evaluates ADRs for:
    - Template adherence (overall score 0.0-1.0)
    - Section consistency (presence, quality, purpose)
    - Full assessment (both above)
    
    Results are exported to sidecar files (.metadata.json)
    alongside each ADR.
    """
    # Load ADR files
    console.print(f"[blue]Loading ADR files...[/blue]")
    adr_files = _load_adr_files(adr_path)
    
    if not adr_files:
        console.print("[red]No ADR files found[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Found {len(adr_files)} ADR file(s)[/cyan]")
    
    # Initialize checking service
    console.print(f"[blue]Initializing checking service...[/blue]")
    service = CheckingService(mode=mode)
    
    # Extract texts and metadata
    texts = [content for _, content in adr_files]
    
    # Create metadata with file information
    metadata_list = []
    for path, _ in adr_files:
        # Use relative path if possible, otherwise use full path
        if path.is_absolute():
            # Make it relative to current directory if it's a subpath
            try:
                file_path = str(path.relative_to(Path.cwd()))
            except ValueError:
                file_path = str(path)
        else:
            # Already relative
            file_path = str(path)
        
        metadata_list.append({
            "file": file_path,
            "name": path.name
        })
    
    # Run checks
    console.print(f"[blue]Checking ADRs (mode: {mode}, parallel: {parallel})...[/blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Processing {len(texts)} ADR(s)...", total=len(texts))
        
        if mode == "adherence":
            results = service.check_adherence_batch(texts, metadata_list, parallel)
            progress.update(task, completed=len(results))
        elif mode == "sections":
            results = service.check_sections_batch(texts, metadata_list, parallel)
            progress.update(task, completed=len(results))
        else:  # full
            results = service.check_batch(texts, metadata_list, parallel)
            progress.update(task, completed=len(results))
    
    # Display results
    console.print("\n[bold]Results:[/bold]")
    
    if mode == "adherence":
        _display_adherence_results(results, adr_files)
    elif mode == "sections":
        _display_section_results(results, adr_files)
    else:
        _display_full_results(results, adr_files)
    
    # Export to sidecar files using JSONExporter
    console.print("\n[blue]Exporting sidecar files...[/blue]")
    exported_count = 0
    exporter = JSONExporter()
    
    for (adr_path, _), result in zip(adr_files, results):
        if "error" not in result:
            # Get model versions from service
            model_versions = {
                "check_llm": service.llm.model_name
            }
            
            # Export using JSONExporter (standardizes to .metadata.json)
            exporter.export_sidecar(
                adr_file=adr_path,
                check=result,
                model_versions=model_versions,
            )
            exported_count += 1
    
    console.print(f"[green]✓ Exported {exported_count} sidecar file(s)[/green]")
    
    # Export to CSV if requested
    if csv:
        console.print(f"[blue]Exporting to CSV: {csv}[/blue]")
        _export_to_csv(results, adr_files, mode, csv)
        console.print(f"[green]✓ Exported results to {csv}[/green]")
    
    console.print("[green]✓ Checking completed successfully![/green]")