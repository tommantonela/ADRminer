"""Classification command handlers."""

from pathlib import Path
from typing import Dict, List, Any
from collections import Counter
import csv
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from adrminer.chat.handlers.base import BaseHandler
from adrminer.exporters import JSONExporter


class ClassifyPredictHandler(BaseHandler):
    """Handler for /classify predict command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any]
    ) -> None:
        """
        Classify ADRs using specified framework.
        
        Args:
            args: [path]
            options: framework, examples, no-examples, use-parser, strict,
                     no-language-detect, output, parallel
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
        if not self.confirm_batch_operation("classify", len(adr_files)):
            self.print_info("Operation cancelled")
            return
        
        # Get options
        framework = options.get("framework")
        examples = options.get("examples")
        no_examples = options.get("no-examples", False)
        use_parser = options.get("use-parser", False)
        strict = options.get("strict", False)
        no_language_detect = options.get("no-language-detect", False)
        output = options.get("output", "sidecar")
        verbose = options.get("verbose", False)
        csv_output = options.get("csv")
        
        # Load service
        service = self.session.classification_service
        
        # Update framework if specified
        if framework:
            current_framework = service.framework
            if framework != current_framework:
                self.session.console.print(
                    f"[blue]Switching framework from {current_framework} to {framework}[/blue]"
                )
                service.framework = framework
        
        # Build parser config
        parser_config = {}
        if strict:
            parser_config["strict"] = True
        if no_language_detect:
            parser_config["detect_language"] = False
        
        # Process ADRs - use smart selection based on count
        self.session.console.print(f"\nFound {len(adr_files)} ADR file(s) to analyze\n")
        self.session.console.print(f"[bold]Framework:[/bold] {service.framework}\n")
        
        results = []
        
        if len(adr_files) == 1:
            # Single ADR: use direct classify() for efficiency
            adr_file = adr_files[0]
            try:
                with open(adr_file, 'r') as f:
                    text = f.read()
                
                result = service.classify(
                    text,
                    metadata={"file": str(adr_file)}
                )
                result["adr_file"] = str(adr_file)
                results.append(result)
            except Exception as e:
                self.session.console.print(
                    f"[yellow]Warning: Failed to classify {adr_file}: {e}[/yellow]"
                )
        else:
            # Multiple ADRs: use batch method for parallel processing
            texts = []
            for adr_file in adr_files:
                try:
                    with open(adr_file, 'r') as f:
                        texts.append(f.read())
                except Exception as e:
                    self.session.console.print(
                        f"[yellow]Warning: Failed to read {adr_file}: {e}[/yellow]"
                    )
            
            if texts:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=self.session.console,
                ) as progress:
                    task = progress.add_task("Classifying ADRs...", total=len(texts))
                    
                    results = service.classify_batch(texts, parallel=True)
                    
                    progress.update(task, completed=len(results))
                
                # Add file paths to results
                for i, result in enumerate(results):
                    result["adr_file"] = str(adr_files[i])
        
        # Display results
        self._display_results(results, verbose)
        
        # Export results
        self._export_results(results, output, csv_output)
        
        # Store in session
        self.session.store_analysis_result("classification", results)
        
        # Sync agent context with updated session
        if self.session.agent_context:
            self.session.agent_context.load_from_session(self.session)
    
    def _display_results(self, results: List[Dict], verbose: bool = False):
        """Display classification results."""
        if not results:
            self.print_warning("No results to display")
            return
        
        self.session.console.print("\n[bold]Results:[/bold]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Confidence", justify="right")
        table.add_column("Alternatives")
        
        # Show all results if verbose, otherwise show first 10
        results_to_show = results if verbose else results[:10]
        
        for result in results_to_show:
            alternatives = ", ".join(result.get("alternatives", [])[:3])
            confidence = result.get("confidence", 0.0)
            confidence_color = (
                "green" if confidence > 0.8 else
                "yellow" if confidence > 0.5 else
                "red"
            )
            
            table.add_row(
                Path(result["adr_file"]).name,
                result.get("primary_category", "N/A"),
                f"[{confidence_color}]{confidence:.2f}[/{confidence_color}]",
                alternatives,
            )
        
        self.session.console.print(table)
        
        if not verbose and len(results) > 10:
            self.session.console.print(f"\n... and {len(results) - 10} more ADRs")
        
        # Show category distribution if multiple results
        if len(results) > 1:
            self._show_category_distribution(results)
    
    def _show_category_distribution(self, results: List[Dict]):
        """Show category distribution."""
        self.session.console.print("\n[bold]Category Distribution:[/bold]\n")
        
        categories = [r.get('primary_category', 'Unknown') for r in results]
        category_counts = Counter(categories)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")
        
        for category, count in category_counts.most_common():
            percentage = (count / len(results)) * 100
            table.add_row(
                category,
                str(count),
                f"{percentage:.1f}%"
            )
        
        self.session.console.print(table)
        
        # Show overall statistics
        confidences = [r.get('confidence', 0.0) for r in results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        high_conf = sum(1 for r in results if r.get('confidence', 0.0) > 0.8)
        
        self.session.console.print("\n[bold]Statistics:[/bold]")
        self.session.console.print(f"  Total ADRs: {len(results)}")
        self.session.console.print(f"  Average Confidence: {avg_confidence:.2f}")
        self.session.console.print(
            f"  High Confidence (>0.8): {high_conf} ({high_conf/len(results):.1%})"
        )
    
    def _export_results(self, results: List[Dict], output_format: str, csv_output: str = None):
        """Export results to files."""
        if not results:
            return
        
        exporter = JSONExporter()
        
        if output_format == "sidecar":
            self.session.console.print("\n[blue]Exporting sidecar files...[/blue]")
            for result in results:
                adr_file = Path(result["adr_file"])
                exporter.export_sidecar(
                    adr_file=adr_file,
                    classification=result,
                    model_versions={
                        "classification_llm": self.session.classification_service.llm.model_name
                    },
                )
            self.print_success(f"Exported {len(results)} sidecar file(s)")
        
        elif output_format == "consolidated":
            output_path = self.session.current_dir / "classification_results.json"
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
                writer.writerow(['File', 'Framework', 'Primary Category', 'Confidence', 'Alternatives'])
                
                # Rows
                for result in results:
                    file_name = Path(result["adr_file"]).name
                    framework = result.get("framework", "")
                    primary_category = result.get("primary_category", "")
                    confidence = result.get("confidence", 0.0)
                    alternatives = ", ".join(result.get("alternatives", []))
                    
                    writer.writerow([file_name, framework, primary_category, confidence, alternatives])
            
            self.print_success(f"Exported CSV to {csv_file}")
        except Exception as e:
            self.print_error(f"Failed to export CSV: {e}")


class ClassifyInfoHandler(BaseHandler):
    """Handler for /classify info command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any]
    ) -> None:
        """
        Show information about classification frameworks.
        
        Args:
            args: []
            options: framework
        """
        from adrminer.services.classification_service import FRAMEWORKS
        
        framework = options.get("framework")
        
        if framework:
            # Show specific framework
            if framework not in FRAMEWORKS:
                self.print_error(f"Unknown framework: {framework}")
                self.session.console.print(
                    f"Available frameworks: {', '.join(FRAMEWORKS.keys())}"
                )
                return
            
            framework_info = FRAMEWORKS[framework]
            
            self.session.console.print(
                f"\n[bold cyan]{framework_info['name']} Framework[/bold cyan]"
            )
            self.session.console.print(f"Code: {framework}")
            self.session.console.print(
                f"Categories: {len(framework_info['categories'])}\n"
            )
            self.session.console.print("[bold]Description:[/bold]")
            self.session.console.print(f"{framework_info['description']}\n")
            self.session.console.print("[bold]Categories:[/bold]")
            
            # Display categories with descriptions
            category_descriptions = framework_info.get("category_descriptions", {})
            for i, category in enumerate(framework_info["categories"], 1):
                self.session.console.print(f"\n  {i}. [cyan]{category}[/cyan]")
                if category in category_descriptions:
                    desc = category_descriptions[category]
                    # Word wrap description
                    import textwrap
                    wrapped = textwrap.fill(
                        desc,
                        width=76,
                        initial_indent="    ",
                        subsequent_indent="    "
                    )
                    self.session.console.print(wrapped)
        else:
            # Show all frameworks
            self.session.console.print(
                "\n[bold cyan]Available Frameworks:[/bold cyan]\n"
            )
            
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
            
            self.session.console.print(table)
