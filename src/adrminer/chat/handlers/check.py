"""Check command handlers."""

from pathlib import Path
from typing import Dict, List, Any
import csv
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from adrminer.chat.handlers.base import BaseHandler
from adrminer.exporters import JSONExporter


class CheckPredictHandler(BaseHandler):
    """Handler for /check predict command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any]
    ) -> None:
        """
        Check ADR quality against MADR template.
        
        Args:
            args: [path]
            options: mode, parallel, use-parser, strict, no-language-detect
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
        if not self.confirm_batch_operation("check quality of", len(adr_files)):
            self.print_info("Operation cancelled")
            return
        
        # Get options
        mode = options.get("mode", "full")
        parallel = options.get("parallel", True)
        use_parser = options.get("use-parser", False)
        strict = options.get("strict", False)
        no_language_detect = options.get("no-language-detect", False)
        csv_output = options.get("csv")
        
        # Load service
        service = self.session.checking_service
        
        # Build parser config
        parser_config = None
        if use_parser:
            parser_config = {}
            if strict:
                parser_config["strict"] = True
            if no_language_detect:
                parser_config["detect_language"] = False
        
        # Extract texts and metadata
        texts = []
        metadata_list = []
        
        for adr_file in adr_files:
            try:
                with open(adr_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                texts.append(text)
                
                # Create metadata
                if adr_file.is_absolute():
                    try:
                        file_path = str(adr_file.relative_to(Path.cwd()))
                    except ValueError:
                        file_path = str(adr_file)
                else:
                    file_path = str(adr_file)
                
                metadata_list.append({
                    "file": file_path,
                    "name": adr_file.name
                })
            except Exception as e:
                self.session.console.print(
                    f"[yellow]Warning: Failed to read {adr_file}: {e}[/yellow]"
                )
        
        if not texts:
            self.print_error("No ADR texts to check")
            return
        
        # Run checks
        self.session.console.print(f"\nFound {len(texts)} ADR file(s) to analyze")
        self.session.console.print(f"Mode: {mode}\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.session.console,
        ) as progress:
            task = progress.add_task(f"Checking {len(texts)} ADR(s)...", total=len(texts))
            
            if mode == "adherence":
                results = service.check_adherence_batch(texts, metadata_list, parallel)
            elif mode == "sections":
                results = service.check_sections_batch(texts, metadata_list, parallel)
            else:  # full
                results = service.check_batch(texts, metadata_list, parallel)
            
            progress.update(task, completed=len(results))
        
        # Display results
        self._display_results(results, mode)
        
        # Export results
        self._export_results(results, csv_output)
        
        # Store in session
        self.session.store_analysis_result("check", results)
    
    def _display_results(self, results: List[Dict], mode: str):
        """Display check results."""
        if not results:
            self.print_warning("No results to display")
            return
        
        self.session.console.print("\n[bold]Results:[/bold]\n")
        
        # Create summary table
        if len(results) > 1:
            self._display_summary_table(results, mode)
        else:
            self._display_single_result(results[0], mode)
    
    def _display_summary_table(self, results: List[Dict], mode: str):
        """Display summary table for multiple ADRs."""
        table = Table(title="ADR Quality Assessment")
        table.add_column("ADR", style="cyan", no_wrap=True)
        
        if mode == "full":
            table.add_column("Adherence score")
            table.add_column("Section presence")
            table.add_column("Section quality")
            table.add_column("Section consistency")
        elif mode == "sections":
            table.add_column("Section presence")
            table.add_column("Section quality")
            table.add_column("Section consistency")
        else:  # adherence
            table.add_column("Score")
        
        for result in results:
            if "error" in result:
                if mode == "full":
                    table.add_row(
                        result.get("file", "Unknown"),
                        "[red]N/A[/red]",
                        "[red]Error[/red]",
                        "[red]Error[/red]",
                        "[red]Error[/red]"
                    )
                elif mode == "sections":
                    table.add_row(
                        result.get("file", "Unknown"),
                        "[red]Error[/red]",
                        "[red]Error[/red]",
                        "[red]Error[/red]"
                    )
                else:
                    table.add_row(
                        result.get("file", "Unknown"),
                        "[red]N/A[/red]"
                    )
            else:
                if mode == "full":
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
                    
                    if assessments:
                        present = sum(1 for s in assessments if s.get("presence") == "Yes")
                        quality = sum(1 for s in assessments if s.get("content_quality") == "Yes")
                        consistent = sum(1 for s in assessments if s.get("purpose_consistency") == "Yes")
                        
                        # Color-code ratios
                        def _score_color(value: int, total: int) -> str:
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
                        present_str = "[dim]N/A[/dim]"
                        quality_str = "[dim]N/A[/dim]"
                        consistent_str = "[dim]N/A[/dim]"
                    
                    table.add_row(
                        result.get("file", "Unknown"),
                        score_display,
                        present_str,
                        quality_str,
                        consistent_str
                    )
                elif mode == "sections":
                    assessments = result.get("section_assessments", [])
                    
                    if assessments:
                        present = sum(1 for s in assessments if s.get("presence") == "Yes")
                        quality = sum(1 for s in assessments if s.get("content_quality") == "Yes")
                        consistent = sum(1 for s in assessments if s.get("purpose_consistency") == "Yes")
                        
                        def _score_color(value: int, total: int) -> str:
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
                            result.get("file", "Unknown"),
                            _score_color(present, len(assessments)),
                            _score_color(quality, len(assessments)),
                            _score_color(consistent, len(assessments))
                        )
                    else:
                        table.add_row(
                            result.get("file", "Unknown"),
                            "[dim]N/A[/dim]",
                            "[dim]N/A[/dim]",
                            "[dim]N/A[/dim]"
                        )
                else:  # adherence
                    template = result.get("template_adherence", {})
                    score = template.get("adherence_score", 0.0)
                    
                    if score >= 0.8:
                        score_display = f"[green]{score:.2f}[/green]"
                    elif score >= 0.6:
                        score_display = f"[yellow]{score:.2f}[/yellow]"
                    elif score >= 0.4:
                        score_display = f"[orange1]{score:.2f}[/orange1]"
                    else:
                        score_display = f"[red]{score:.2f}[/red]"
                    
                    table.add_row(
                        result.get("file", "Unknown"),
                        score_display
                    )
        
        self.session.console.print(table)
    
    def _display_single_result(self, result: Dict, mode: str):
        """Display detailed result for single ADR."""
        if "error" in result:
            self.print_error(f"Error checking ADR: {result.get('error', 'Unknown error')}")
            return
        
        if mode == "full" or mode == "adherence":
            template = result.get("template_adherence", {})
            score = template.get("adherence_score", 0.0)
            assessment = template.get("assessment", "")
            
            # Determine score color
            if score >= 0.8:
                score_display = f"[green]{score:.2f}[/green]"
            elif score >= 0.6:
                score_display = f"[yellow]{score:.2f}[/yellow]"
            elif score >= 0.4:
                score_display = f"[orange1]{score:.2f}[/orange1]"
            else:
                score_display = f"[red]{score:.2f}[/red]"
            
            # Display adherence
            self.session.console.print(f"[bold]Template Adherence:[/bold] {score_display}")
            self.session.console.print(f"Assessment: {assessment}\n")
        
        if mode == "full" or mode == "sections":
            assessments = result.get("section_assessments", [])
            
            if assessments:
                table = Table(title="Section Details")
                table.add_column("Section", style="cyan")
                table.add_column("Present")
                table.add_column("Quality")
                table.add_column("Consistent")
                
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
                    
                    table.add_row(
                        section_name,
                        presence_color,
                        quality_color,
                        consistency_color
                    )
                
                self.session.console.print(table)
    
    def _export_results(self, results: List[Dict], csv_output: str = None):
        """Export results to sidecar files."""
        if not results:
            return
        
        exporter = JSONExporter()
        
        self.session.console.print("\n[blue]Exporting sidecar files...[/blue]")
        exported_count = 0
        
        for result in results:
            if "error" not in result:
                # Get model versions from service
                model_versions = {
                    "check_llm": self.session.checking_service.llm.model_name
                }
                
                # Get file path from result metadata
                file_path = result.get("metadata", {}).get("file")
                if file_path:
                    adr_file = Path(file_path)
                    exporter.export_sidecar(
                        adr_file=adr_file,
                        check=result,
                        model_versions=model_versions,
                    )
                    exported_count += 1
        
        self.print_success(f"Exported {exported_count} sidecar file(s)")
        
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
                writer.writerow([
                    'File',
                    'Adherence Score',
                    'Section Presence',
                    'Section Quality',
                    'Section Consistency'
                ])
                
                # Rows
                for result in results:
                    if "error" in result:
                        writer.writerow([
                            result.get("file", "Unknown"),
                            "N/A",
                            "Error",
                            "Error",
                            "Error"
                        ])
                    else:
                        # Get adherence score
                        template = result.get("template_adherence", {})
                        score = template.get("adherence_score", 0.0)
                        
                        # Get section statistics
                        assessments = result.get("section_assessments", [])
                        
                        if assessments:
                            present = sum(1 for s in assessments if s.get("presence") == "Yes")
                            quality = sum(1 for s in assessments if s.get("content_quality") == "Yes")
                            consistent = sum(1 for s in assessments if s.get("purpose_consistency") == "Yes")
                            
                            present_str = f"{present}/{len(assessments)}"
                            quality_str = f"{quality}/{len(assessments)}"
                            consistent_str = f"{consistent}/{len(assessments)}"
                        else:
                            present_str = "N/A"
                            quality_str = "N/A"
                            consistent_str = "N/A"
                        
                        writer.writerow([
                            result.get("file", "Unknown"),
                            f"{score:.2f}",
                            present_str,
                            quality_str,
                            consistent_str
                        ])
            
            self.print_success(f"Exported CSV to {csv_file}")
        except Exception as e:
            self.print_error(f"Failed to export CSV: {e}")
