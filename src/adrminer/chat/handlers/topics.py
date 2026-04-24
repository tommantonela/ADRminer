"""Topics command handlers."""

from pathlib import Path
from typing import Dict, List, Any
import csv
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from adrminer.chat.handlers.base import BaseHandler
from adrminer.exporters import JSONExporter


class TopicsPredictHandler(BaseHandler):
    """Handler for /topics predict command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any]
    ) -> None:
        """
        Predict topics for ADRs.
        
        Args:
            args: [path]
            options: model, output, parallel, threshold, multiple, verbose, csv
        """
        path_str = args[0]
        path = Path(path_str)
        
        if not path.exists():
            self.print_error(f"Path does not exist: {path}")
            return
        
        # Load ADR files
        adr_files = self.session.load_adr_files(path)
        
        if not adr_files:
            self.print_warning(f"No ADRs found in {path}")
            return
        
        # Confirm batch operation
        if not self.confirm_batch_operation("predict topics for", len(adr_files)):
            self.print_info("Operation cancelled")
            return
        
        # Get options
        model = options.get("model")
        output = options.get("output", "sidecar")
        parallel = options.get("parallel", True)
        threshold = options.get("threshold", 0.0)
        multiple = options.get("multiple", False)
        verbose = options.get("verbose", False)
        csv_output = options.get("csv")
        
        # Load service
        service = self.session.topic_service
        
        # Process ADRs
        self.session.console.print(f"\nFound {len(adr_files)} ADR file(s) to analyze\n")
        
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.session.console,
        ) as progress:
            task = progress.add_task("Processing ADRs...", total=len(adr_files))
            
            for adr_file in adr_files:
                try:
                    with open(adr_file, 'r') as f:
                        text = f.read()
                    
                    result = service.predict(
                        text,
                        metadata={"file": str(adr_file)}
                    )
                    result["adr_file"] = str(adr_file)
                    
                    # Filter by threshold
                    if result["probability"] >= threshold:
                        results.append(result)
                    
                    progress.update(task, advance=1)
                except Exception as e:
                    self.session.console.print(
                        f"[yellow]Warning: Failed to analyze {adr_file}: {e}[/yellow]"
                    )
                    progress.update(task, advance=1)
        
        # Display results
        self._display_results(results, service, verbose)
        
        # Export results
        self._export_results(results, output, csv_output)
        
        # Store in session
        self.session.store_analysis_result("topics", results)
    
    def _display_results(self, results: List[Dict], service, verbose: bool = False):
        """Display topic results."""
        if not results:
            self.print_warning("No results to display")
            return
        
        self.session.console.print("\n[bold]Results:[/bold]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File", style="cyan")
        table.add_column("Topic", style="green")
        table.add_column("Probability", justify="right")
        table.add_column("Keywords")
        
        # Show all results if verbose, otherwise show first 10
        results_to_show = results if verbose else results[:10]
        
        for result in results_to_show:
            keywords = ", ".join(result["keywords"][:5])
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
        
        self.session.console.print(table)
        
        if not verbose and len(results) > 10:
            self.session.console.print(f"\n... and {len(results) - 10} more ADRs")
    
    def _export_results(self, results: List[Dict], output_format: str, csv_output: str = None):
        """Export results to files."""
        if not results:
            return
        
        exporter = JSONExporter()
        
        if output_format == "sidecar":
            self.session.console.print("\n[blue]Exporting sidecar files...[/blue]")
            for result in results:
                adr_file = Path(result["adr_file"])
                
                # Use LLM-generated topic names if enabled
                if self.session.topic_service.use_llm_representation:
                    topic_id = result["topic_id"]
                    topic_info = self.session.topic_service.get_topic_info(topic_id)
                    if topic_info:
                        # Override topic_label with LLM name
                        result = result.copy()  # Don't modify original
                        result["topic_label"] = topic_info["name"]
                
                exporter.export_sidecar(
                    adr_file=adr_file,
                    topics=result,
                    model_versions={"topic_model": "v1.0"},
                )
            self.print_success(f"Exported {len(results)} sidecar file(s)")
        
        elif output_format == "consolidated":
            # Save to current directory
            output_path = self.session.current_dir / "topics_results.json"
            exporter.export_consolidated(results, output_path)
            self.print_success(f"Exported consolidated results to {output_path}")
        
        # Export to CSV if requested
        if csv_output:
            self._export_csv(results, csv_output)
    
    def _export_csv(self, results: List[Dict], csv_path: str):
        """Export results to CSV file."""
        try:
            # Resolve path - use current directory if only filename provided
            csv_file = Path(csv_path)
            if not csv_file.parent.name or str(csv_file.parent) == ".":
                csv_file = self.session.current_dir / csv_file
            
            # Write CSV
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(['File', 'Topic ID', 'Topic Name', 'Probability', 'Keywords'])
                
                # Rows
                for result in results:
                    file_name = Path(result["adr_file"]).name
                    topic_id = result.get("topic_id", "")
                    topic_name = result.get("topic_label", "")
                    probability = result.get("probability", 0.0)
                    keywords = ", ".join(result.get("keywords", []))
                    
                    writer.writerow([file_name, topic_id, topic_name, probability, keywords])
            
            self.print_success(f"Exported CSV to {csv_file}")
        except Exception as e:
            self.print_error(f"Failed to export CSV: {e}")


class TopicsInfoHandler(BaseHandler):
    """Handler for /topics info command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any]
    ) -> None:
        """
        Show information about topics.
        
        Args:
            args: []
            options: topic-id
        """
        topic_id = options.get("topic-id")
        
        # Load service
        service = self.session.topic_service
        
        if topic_id is not None:
            # Show specific topic
            topic_info = service.get_topic_info(int(topic_id))
            
            if not topic_info:
                self.print_error(f"Topic {topic_id} not found")
                return
            
            self.session.console.print(f"\n[bold cyan]Topic ID:[/bold cyan] {topic_info['topic_id']}")
            self.session.console.print(f"[bold]Name:[/bold] {topic_info['name']}")
            self.session.console.print(f"[bold]Count:[/bold] {topic_info['count']}\n")
            self.session.console.print("[bold]Top Keywords:[/bold]")
            
            for word, prob in topic_info['representation'][:10]:
                self.session.console.print(f"  • {word} ({prob:.3f})")
        else:
            # Show all topics
            topic_df = service.model.get_topic_info()
            
            use_llm = service.use_llm_representation
            
            self.session.console.print(
                f"\n[bold]Total Topics:[/bold] {len(topic_df)}"
            )
            self.session.console.print(f"[bold]Model Path:[/bold] {service.model_path}")
            self.session.console.print(
                f"[bold]Topic Names:[/bold] {'LLM-generated' if use_llm else 'KeyBERT'}\n"
            )
            
            # Display topic table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("Topic Name", style="green")
            table.add_column("Count", justify="right")
            
            for _, row in topic_df.iterrows():
                tid = int(row["Topic"])
                count = int(row["Count"])
                
                # Get topic info with proper naming
                topic_info = service.get_topic_info(tid)
                if topic_info:
                    name = topic_info.get("name", row["Name"])
                else:
                    name = row["Name"]
                
                table.add_row(str(tid), name, str(count))
            
            self.session.console.print(table)


class TopicsTrainHandler(BaseHandler):
    """Handler for /topics train command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any]
    ) -> None:
        """
        Train a new topic model.
        
        Note: This command is not supported in interactive mode.
        
        Args:
            args: [path]
            options: All training options
        """
        self.print_error(
            "Topic model training is not supported in interactive mode.\n"
            "Please use the non-interactive CLI command:\n"
            "  adrminer topics train <path> [options]\n\n"
            "For more information, run:\n"
            "  adrminer topics train --help"
        )
