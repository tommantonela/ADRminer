"""Classification command handlers."""

from pathlib import Path
from typing import Dict, List, Any
from collections import Counter
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
        
        # Load service
        service = self.session.classification_service
        
        # Update framework if specified
        if framework:
            service.framework = framework
        
        # Build parser config
        parser_config = {}
        if strict:
            parser_config["strict"] = True
        if no_language_detect:
            parser_config["detect_language"] = False
        
        # Process ADRs
        self.session.console.print(f"\nFound {len(adr_files)} ADR file(s) to analyze\n")
        self.session.console.print(f"Framework: {service.framework}\n")
        
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.session.console,
        ) as progress:
            task = progress.add_task("Classifying ADRs...", total=len(adr_files))
            
            for adr_file in adr_files:
                try:
                    with open(adr_file, 'r') as f:
                        text = f.read()
                    
                    result = service.classify(
                        text,
                        metadata={"file": str(adr_file)}
                    )
                    result["adr_file"] = str(adr_file)
                    results.append(result)
                    
                    progress.update(task, advance=1)
                except Exception as e:
                    self.session.console.print(
                        f"[yellow]Warning: Failed to classify {adr_file}: {e}[/yellow]"
                    )
                    progress.update(task, advance=1)
        
        # Display results
        self._display_results(results)
        
        # Export results
        self._export_results(results, output)
        
        # Store in session
        self.session.store_analysis_result("classification", results)
    
    def _display_results(self, results: List[Dict]):
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
        
        for result in results[:10]:  # Show first 10
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
        
        if len(results) > 10:
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
    
    def _export_results(self, results: List[Dict], output_format: str):
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
