"""Classification CLI commands."""

import csv
from concurrent.futures import as_completed, ThreadPoolExecutor
from pathlib import Path
from typing import Literal, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from adrminer.config import get_settings
from adrminer.services import ClassificationService
from adrminer.exporters import JSONExporter

console = Console()

# Create classify app
classify_app = typer.Typer(help="Classification commands")


@classify_app.command("predict")
def predict(
    path: Path = typer.Argument(
        ...,
        help="Path to ADR file or directory",
        exists=True,
    ),
    framework: Literal["kruchten", "quality_attributes", "zimmermann"] = typer.Option(
        None,
        "--framework",
        "-f",
        help="Classification framework",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="LLM model name",
    ),
    examples: Optional[str] = typer.Option(
        None,
        "--examples",
        "-e",
        help="Path to examples JSON file",
    ),
    no_examples: bool = typer.Option(
        False,
        "--no-examples",
        help="Disable few-shot learning (zero-shot)",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format (sidecar, consolidated)",
    ),
    csv_output: Optional[Path] = typer.Option(
        None,
        "--csv",
        help="Export results to CSV file",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output",
    ),
) -> None:
    """
    Classify ADRs using LLM models.
    
    Analyze one or more ADRs and classify them using specified framework.
    """
    # Load classification service
    try:
        # Use settings for defaults if not provided
        settings = get_settings()
        framework = framework or settings.classification.framework
        examples_path = examples or settings.classification.examples
        use_examples = not no_examples if no_examples else settings.classification.use_examples
        
        console.print("[blue]Loading classification service...[/blue]")
        service = ClassificationService(
            framework=framework,
            examples_path=examples_path,
            use_examples=use_examples,
        )
        console.print(f"[green]✓ Service loaded (framework: {service.framework})[/green]")
    except Exception as e:
        console.print(f"[red]Failed to load classification service: {e}[/red]")
        raise typer.Exit(code=1)
    
    # Collect ADR files
    if path.is_file():
        adr_files = [path]
    else:
        adr_files = list(path.glob("*.md")) + list(path.glob("*.MD"))
    
    if not adr_files:
        console.print(f"[yellow]No ADR files found at {path}[/yellow]")
        raise typer.Exit(code=1)
    
    console.print(f"\nFound {len(adr_files)} ADR file(s) to analyze\n")
    
    # Get parallel setting from config
    use_parallel = settings.output.parallel
    
    # Define processing function
    def process_adr(adr_file):
        """Process a single ADR file."""
        try:
            with open(adr_file, "r") as f:
                text = f.read()
            
            result = service.classify(text, metadata={"file": str(adr_file)})
            result["adr_file"] = str(adr_file)
            return result, None
        except Exception as e:
            return None, (adr_file, e)
    
    # Process ADRs
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing ADRs...", total=len(adr_files))
        
        if use_parallel:
            # Parallel processing
            with ThreadPoolExecutor() as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(process_adr, adr_file): adr_file 
                    for adr_file in adr_files
                }
                
                # Create list to store results in correct order
                ordered_results = [None] * len(adr_files)
                
                # Map file to index
                file_to_index = {adr_file: i for i, adr_file in enumerate(adr_files)}
                
                # Collect results as they complete and place in correct position
                for future in as_completed(future_to_file):
                    adr_file = future_to_file[future]
                    result, error = future.result()
                    
                    if error:
                        adr_file, e = error
                        console.print(f"[yellow]Warning: Failed to classify {adr_file}: {e}[/yellow]")
                    elif result:
                        # Place result in correct position
                        idx = file_to_index[adr_file]
                        ordered_results[idx] = result
                    
                    progress.update(task, advance=1)
                
                # Filter out None values (errors) and assign to results
                results = [r for r in ordered_results if r is not None]
        else:
            # Sequential processing
            for adr_file in adr_files:
                result, error = process_adr(adr_file)
                
                if error:
                    adr_file, e = error
                    console.print(f"[yellow]Warning: Failed to classify {adr_file}: {e}[/yellow]")
                elif result:
                    results.append(result)
                
                progress.update(task, advance=1)
    
    # Display results
    if verbose or len(results) <= 10:
        _display_results_detailed(results)
    else:
        _display_results_summary(results)
    
    # Export results
    output_format = output or "sidecar"
    exporter = JSONExporter()
    
    if output_format == "sidecar":
        console.print("\n[blue]Exporting sidecar files...[/blue]")
        for result in results:
            adr_file = Path(result["adr_file"])
            exporter.export_sidecar(
                adr_file=adr_file,
                classification=result,
                model_versions={"classification_llm": service.llm.model_name},
            )
        console.print(f"[green]✓ Exported {len(results)} sidecar file(s)[/green]")
    
    elif output_format == "consolidated":
        output_path = path / "classification_results.json"
        exporter.export_consolidated(results, output_path)
        console.print(f"\n[green]✓ Exported consolidated results to {output_path}[/green]")
    
    # Show category distribution (skip for single ADR)
    if results and len(results) > 1:
        console.print("\n[bold]Category Distribution:[/bold]")
        distribution = service.get_category_distribution(results)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")
        table.add_column("Avg Confidence", justify="right")
        
        for category, data in distribution["distribution"].items():
            table.add_row(
                category,
                str(data["count"]),
                f"{data['percentage']:.1%}",
                f"{data['avg_confidence']:.2f}",
            )
        
        console.print(table)
        
        # Show overall statistics
        console.print("\n[bold]Statistics:[/bold]")
        console.print(f"  Total ADRs: {distribution['total_adrs']}")
        console.print(f"  Average Confidence: {distribution['avg_confidence']:.2f}")
        console.print(f"  High Confidence (>0.8): {distribution['high_confidence_count']} ({distribution['high_confidence_percentage']:.1%})")
    
    # Export to CSV if requested
    if csv_output and results:
        console.print(f"\n[blue]Exporting results to CSV: {csv_output}[/blue]")
        csv_output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(csv_output, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "ADR_File",
                "Primary_Category",
                "Confidence",
                "Alternatives",
                "Explanation"
            ])
            
            # Write data rows
            for result in results:
                writer.writerow([
                    Path(result["adr_file"]).name,
                    result["primary_category"],
                    f"{result['confidence']:.2f}",
                    ", ".join(result["alternatives"][:3]),
                    result.get("explanation", "")[:200]  # Truncate long explanations
                ])
        
        console.print(f"[green]✓ Exported {len(results)} result(s) to {csv_output}[/green]")


@classify_app.command("info")
def info(
    framework: Optional[Literal["kruchten", "quality_attributes", "zimmermann"]] = typer.Option(
        None,
        "--framework",
        "-f",
        help="Classification framework",
    ),
) -> None:
    """
    Show information about classification frameworks.
    
    Display details about available classification frameworks.
    """
    from adrminer.services.classification_service import FRAMEWORKS
    
    if framework:
        # Show specific framework
        if framework not in FRAMEWORKS:
            console.print(f"[yellow]Unknown framework: {framework}[/yellow]")
            console.print(f"Available frameworks: {', '.join(FRAMEWORKS.keys())}")
            raise typer.Exit(code=1)
        
        framework_info = FRAMEWORKS[framework]
        
        console.print(Panel(
            f"[bold]Name:[/bold] {framework_info['name']}\n"
            f"[bold]Code:[/bold] {framework}\n"
            f"[bold]Categories:[/bold] {len(framework_info['categories'])}\n\n"
            f"[bold]Description:[/bold]\n{framework_info['description']}\n\n"
            f"[bold]Categories:[/bold]",
            title=f"{framework_info['name']} Framework",
            border_style="cyan",
        ))
        
        # Display categories with descriptions
        category_descriptions = framework_info.get("category_descriptions", {})
        for i, category in enumerate(framework_info["categories"], 1):
            console.print(f"\n  {i}. [cyan]{category}[/cyan]")
            if category in category_descriptions:
                desc = category_descriptions[category]
                # Word wrap description
                import textwrap
                wrapped = textwrap.fill(desc, width=76, initial_indent="    ", subsequent_indent="    ")
                console.print(wrapped)
    else:
        # Show all frameworks
        console.print(Panel(
            f"[bold]Available Frameworks:[/bold] {len(FRAMEWORKS)}",
            title="Classification Frameworks",
            border_style="cyan",
        ))
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Code", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Categories", justify="right")
        table.add_column("Description")
        
        for code, info in FRAMEWORKS.items():
            table.add_row(
                code,
                info["name"],
                str(len(info["categories"])),
                info["description"],
            )
        
        console.print(table)


def _display_results_detailed(results):
    """Display detailed results for small sets."""
    console.print("\n[bold]Results:[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("File", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Confidence", justify="right")
    table.add_column("Alternatives")
    
    for result in results:
        alternatives = ", ".join(result["alternatives"][:3])
        confidence_color = "green" if result["confidence"] > 0.8 else "yellow" if result["confidence"] > 0.5 else "red"
        
        table.add_row(
            Path(result["adr_file"]).name,
            result["primary_category"],
            f"[{confidence_color}]{result['confidence']:.2f}[/{confidence_color}]",
            alternatives,
        )
    
    console.print(table)


def _display_results_summary(results):
    """Display summary for large sets."""
    console.print("\n[bold]Results Summary:[/bold]\n")
    console.print(f"✓ Successfully classified {len(results)} ADR(s)")
    
    # Count unique categories
    unique_categories = len(set(r["primary_category"] for r in results))
    console.print(f"✓ Found {unique_categories} unique category/categories")
    
    # Count high confidence classifications
    high_conf = sum(1 for r in results if r["confidence"] > 0.8)
    console.print(f"✓ High confidence classifications: {high_conf} ({high_conf/len(results):.1%})")
    
    # Show most common categories
    from collections import Counter
    
    category_counts = Counter(r["primary_category"] for r in results)
    console.print("\n[bold]Most Common Categories:[/bold]")
    
    for category, count in category_counts.most_common(5):
        console.print(f"  • {category} ({count} ADRs)")