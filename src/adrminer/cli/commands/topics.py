"""Topic mining CLI commands."""

import csv
from concurrent.futures import as_completed, ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from adrminer.config import get_settings
from adrminer.services import TopicService
from adrminer.exporters import JSONExporter

console = Console()

# Create topics app
topics_app = typer.Typer(help="Topic mining commands")


@topics_app.command("predict")
def predict(
    path: Path = typer.Argument(
        ...,
        help="Path to ADR file or directory",
        exists=True,
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Path to topic model",
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
    Predict topics for ADRs.
    
    Analyze one or more ADRs and extract topics using BERTopic.
    """
    # Load topic service
    try:
        # Use model from command line if provided, otherwise use config
        model_path = model or get_settings().topic_model.path
        console.print("[blue]Loading topic model...[/blue]")
        service = TopicService(model_path=model_path)
        console.print("[green]✓ Model loaded[/green]")
    except Exception as e:
        console.print(f"[red]Failed to load topic model: {e}[/red]")
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
    settings = get_settings()
    use_parallel = settings.output.parallel
    
    # Define processing function
    def process_adr(adr_file):
        """Process a single ADR file."""
        try:
            with open(adr_file, "r") as f:
                text = f.read()
            
            result = service.predict(text, metadata={"file": str(adr_file)})
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
                
                # Collect results as they complete
                for future in as_completed(future_to_file):
                    result, error = future.result()
                    
                    if error:
                        adr_file, e = error
                        console.print(f"[yellow]Warning: Failed to analyze {adr_file}: {e}[/yellow]")
                    elif result:
                        results.append(result)
                    
                    progress.update(task, advance=1)
        else:
            # Sequential processing
            for adr_file in adr_files:
                result, error = process_adr(adr_file)
                
                if error:
                    adr_file, e = error
                    console.print(f"[yellow]Warning: Failed to analyze {adr_file}: {e}[/yellow]")
                elif result:
                    results.append(result)
                
                progress.update(task, advance=1)
    
    # Display results
    if verbose or len(results) <= 10:
        _display_results_detailed(results, service)
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
                topics=result,
                model_versions={"topic_model": "v1.0"},
            )
        console.print(f"[green]✓ Exported {len(results)} sidecar file(s)[/green]")
    
    elif output_format == "consolidated":
        output_path = path / "topics_results.json"
        exporter.export_consolidated(results, output_path)
        console.print(f"\n[green]✓ Exported consolidated results to {output_path}[/green]")
    
    # Show topic distribution (skip for single ADR)
    if results and len(results) > 1:
        console.print("\n[bold]Topic Distribution:[/bold]")
        distribution = service.get_topic_distribution(results)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Topic", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")
        
        for topic_label, data in distribution["distribution"].items():
            # Extract topic ID from label (format: "ID_name" or "ID_name_truncated")
            parts = topic_label.split("_")
            topic_id = int(parts[0])
            
            # Get proper topic name using service
            topic_info = service.get_topic_info(topic_id)
            if topic_info:
                topic_name = topic_info.get("name", topic_label)
            else:
                topic_name = topic_label
            
            table.add_row(
                topic_name,
                str(data["count"]),
                f"{data['percentage']:.1%}",
            )
        
        console.print(table)
    
    # Export to CSV if requested
    if csv_output and results:
        console.print(f"\n[blue]Exporting results to CSV: {csv_output}[/blue]")
        csv_output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(csv_output, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "ADR_File",
                "Topic_ID",
                "Topic_Name",
                "Probability",
                "Keywords"
            ])
            
            # Write data rows
            for result in results:
                topic_info = service.get_topic_info(result["topic_id"])
                if topic_info:
                    topic_name = topic_info.get("name", result["topic_label"])
                else:
                    topic_name = result["topic_label"]
                
                writer.writerow([
                    Path(result["adr_file"]).name,
                    result["topic_id"],
                    topic_name,
                    f"{result['probability']:.3f}",
                    ", ".join(result["keywords"][:5])
                ])
        
        console.print(f"[green]✓ Exported {len(results)} result(s) to {csv_output}[/green]")


@topics_app.command("train")
def train(
    path: Path = typer.Argument(
        ...,
        help="Path to ADR directory",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for trained model (default: config path)",
    ),
    embedding_model: Optional[str] = typer.Option(
        None,
        "--embedding-model",
        "-e",
        help="Embedding model name",
    ),
    n_topics: Optional[int] = typer.Option(
        None,
        "--n-topics",
        "-n",
        help="Number of topics (default: auto)",
    ),
    no_llm: bool = typer.Option(
        False,
        "--no-llm",
        help="Disable LLM representation",
    ),
    language: Optional[str] = typer.Option(
        None,
        "--language",
        "-l",
        help="Language for stop words",
    ),
    reduce_topics: bool = typer.Option(
        False,
        "--reduce-topics",
        "-r",
        help="Reduce topics after training",
    ),
    csv_output: Optional[Path] = typer.Option(
        None,
        "--csv",
        help="Export topics to CSV file",
    ),
) -> None:
    """
    Train a new topic model on ADRs.
    
    Create a BERTopic model from ADR documents and save it to disk.
    """
    from adrminer.config import get_settings
    from adrminer.services import TopicService
    
    settings = get_settings()
    
    # Collect ADR files
    if path.is_file():
        adr_files = [path]
    else:
        adr_files = list(path.glob("*.md")) + list(path.glob("*.MD"))
    
    if not adr_files:
        console.print(f"[yellow]No ADR files found at {path}[/yellow]")
        raise typer.Exit(code=1)
    
    console.print(f"\nFound {len(adr_files)} ADR file(s) for training\n")
    
    # Read ADR contents
    docs = []
    for adr_file in adr_files:
        try:
            with open(adr_file, "r") as f:
                text = f.read()
            docs.append(text)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to read {adr_file}: {e}[/yellow]")
    
    if not docs:
        console.print("[red]No documents to train on[/red]")
        raise typer.Exit(code=1)
    
    # Determine output path
    if output:
        output_path = output
    else:
        # Use config path
        output_path = Path(settings.topic_model.path)
    
    # Determine parameters
    use_llm = not no_llm
    embedding = embedding_model or settings.topic_model.embedding_model
    lang = language or settings.topic_model.language
    reduce = reduce_topics or settings.topic_model.reduce_topics
    num_topics = n_topics or settings.topic_model.n_topics
    
    # UMAP parameters from config
    umap_n_neighbors = settings.topic_model.umap_n_neighbors
    umap_n_components = settings.topic_model.umap_n_components
    umap_min_dist = settings.topic_model.umap_min_dist
    umap_metric = settings.topic_model.umap_metric
    
    # Train model
    try:
        metrics = TopicService.train(
            docs=docs,
            output_path=output_path,
            use_llm=use_llm,
            reduce_topics=reduce,
            n_topics=num_topics,
            embedding_model=embedding,
            language=lang,
            umap_n_neighbors=umap_n_neighbors,
            umap_n_components=umap_n_components,
            umap_min_dist=umap_min_dist,
            umap_metric=umap_metric,
        )
        
        # Display summary
        console.print("\n[bold]Training Summary:[/bold]")
        console.print(f"  Documents: {len(docs)}")
        console.print(f"  Topics: {metrics['n_topics']}")
        console.print(f"  Coherence: {metrics['coherence']:.3f}")
        console.print(f"  Diversity: {metrics['diversity']:.3f}")
        console.print(f"  Output: {metrics['output_path']}")
        
        console.print("\n[green]✓ Training completed successfully![/green]")
        console.print(f"[cyan]Note: To use this model, update your config file's topic_model.path to: {metrics['output_path']}[/cyan]")
        
        # Load model and display topics
        console.print("\n[bold]Discovered Topics:[/bold]\n")
        
        # Load the trained model
        service = TopicService(model_path=output_path)
        
        # Display topic table
        topic_table = Table(show_header=True, header_style="bold magenta")
        topic_table.add_column("ID", justify="right", style="cyan")
        topic_table.add_column("Topic Name", style="green")
        topic_table.add_column("Count", justify="right")
        topic_table.add_column("Top Keywords")
        
        topic_df = service.model.get_topic_info()
        
        # Collect topic data for CSV export
        topics_data = []
        
        for _, row in topic_df.iterrows():
            topic_id = int(row["Topic"])
            count = int(row["Count"])
            
            # Get topic info with proper naming
            topic_info = service.get_topic_info(topic_id)
            if topic_info:
                topic_name = topic_info.get("name", row["Name"])
                # Get top keywords
                keywords = [word for word, _ in topic_info.get("representation", [])[:5]]
            else:
                topic_name = row["Name"]
                keywords = []
            
            # Add to table
            topic_table.add_row(
                str(topic_id),
                topic_name,
                str(count),
                ", ".join(keywords),
            )
            
            # Collect for CSV export
            topics_data.append({
                "Topic_ID": topic_id,
                "Topic_Name": topic_name,
                "Count": count,
                "Keywords": ", ".join(keywords),
            })
        
        console.print(topic_table)
        
        # Export to CSV if requested
        if csv_output:
            console.print(f"\n[blue]Exporting topics to CSV: {csv_output}[/blue]")
            csv_output.parent.mkdir(parents=True, exist_ok=True)
            
            with open(csv_output, "w", newline="") as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(["Topic_ID", "Topic_Name", "Count", "Keywords"])
                # Write data rows
                for topic_data in topics_data:
                    writer.writerow([
                        topic_data["Topic_ID"],
                        topic_data["Topic_Name"],
                        topic_data["Count"],
                        topic_data["Keywords"]
                    ])
            
            console.print(f"[green]✓ Exported {len(topics_data)} topic(s) to {csv_output}[/green]")
        
    except Exception as e:
        console.print(f"[red]Training failed: {e}[/red]")
        raise typer.Exit(code=1)


@topics_app.command("info")
def info(
    topic_id: Optional[int] = typer.Option(
        None,
        "--topic-id",
        "-t",
        help="Show information about a specific topic",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Path to topic model",
    ),
) -> None:
    """
    Show information about topics.
    
    Display details about topics in the model or a specific topic.
    """
    # Load topic service
    try:
        # Use model from command line if provided, otherwise use config
        model_path = model or get_settings().topic_model.path
        service = TopicService(model_path=model_path)
    except Exception as e:
        console.print(f"[red]Failed to load topic model: {e}[/red]")
        raise typer.Exit(code=1)
    
    if topic_id is not None:
        # Show specific topic
        topic_info = service.get_topic_info(topic_id)
        
        if not topic_info:
            console.print(f"[yellow]Topic {topic_id} not found[/yellow]")
            raise typer.Exit(code=1)
    
        console.print(Panel(
            f"[bold]Topic ID:[/bold] {topic_info['topic_id']}\n"
            f"[bold]Name:[/bold] {topic_info['name']}\n"
            f"[bold]Count:[/bold] {topic_info['count']}\n\n"
            f"[bold]Top Keywords:[/bold]\n",
            title=f"Topic {topic_id}",
            border_style="cyan",
        ))
        
        for word, prob in topic_info['representation'][:10]:
            console.print(f"  • {word} ({prob:.3f})")
    else:
        # Show all topics
        topic_df = service.model.get_topic_info()
        
        # Check if LLM representation is enabled
        use_llm = service.use_llm_representation
        
        console.print(Panel(
            f"[bold]Total Topics:[/bold] {len(topic_df)}\n"
            f"[bold]Model Path:[/bold] {service.model_path}\n"
            f"[bold]Topic Names:[/bold] {'LLM-generated' if use_llm else 'KeyBERT'}",
            title="Topic Model Information",
            border_style="cyan",
        ))
        
        # Display topic table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Topic Name", style="green")
        table.add_column("Count", justify="right")
        
        for _, row in topic_df.iterrows():
            topic_id = int(row["Topic"])
            count = int(row["Count"])
            
            # Use service.get_topic_info to get LLM name if enabled
            topic_info = service.get_topic_info(topic_id)
            if topic_info:
                name = topic_info.get("name", row["Name"])
            else:
                name = row["Name"]
            
            table.add_row(str(topic_id), name, str(count))
        
        console.print(table)


def _display_results_detailed(results, service):
    """Display detailed results for small sets."""
    console.print("\n[bold]Results:[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("File", style="cyan")
    table.add_column("Topic", style="green")
    table.add_column("Probability", justify="right")
    table.add_column("Keywords")
    
    for result in results:
        keywords = ", ".join(result["keywords"][:5])
        # Use service to get proper topic name (LLM or KeyBERT)
        topic_info = service.get_topic_info(result["topic_id"])
        if topic_info:
            topic_name = topic_info.get("name", result["topic_label"])
        else:
            topic_name = result["topic_label"]
        
        table.add_row(
            Path(result["adr_file"]).name,
            topic_name,
            f"{result['probability']:.3f}",
            keywords,
        )
    
    console.print(table)


def _display_results_summary(results):
    """Display summary for large sets."""
    console.print("\n[bold]Results Summary:[/bold]\n")
    console.print(f"✓ Successfully analyzed {len(results)} ADR(s)")
    
    # Count unique topics
    unique_topics = len(set(r["topic_label"] for r in results))
    console.print(f"✓ Found {unique_topics} unique topic(s)")
    
    # Show most common topics
    from collections import Counter
    
    topic_counts = Counter(r["topic_label"] for r in results)
    console.print("\n[bold]Most Common Topics:[/bold]")
    
    for topic, count in topic_counts.most_common(5):
        console.print(f"  • {topic} ({count} ADRs)")