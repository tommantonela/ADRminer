"""Utility command handlers."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from adrminer.chat.handlers.base import BaseHandler
from adrminer.chat.commands import (
    COMMAND_REGISTRY,
    get_command_info,
    get_subcommand_info
)


class HelpHandler(BaseHandler):
    """Handler for /help command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any],
        silent: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Show help for commands.
        
        Args:
            args: [command_name] or [command_name, subcommand_name] (optional)
            options: None
        """
        if args:
            # Show help for specific command
            command = args[0].lower()
            if not command.startswith("/"):
                command = f"/{command}"
            
            # Check if subcommand is provided (e.g., /help topics predict)
            if len(args) >= 2:
                subcommand = args[1].lower()
                self._show_subcommand_help(command, subcommand)
            else:
                self._show_command_help(command)
        else:
            # Show general help
            self._show_general_help()
    
    def _show_general_help(self):
        """Show general help for all commands."""
        self.session.console.print("\n[bold cyan]Available Commands:[/bold cyan]\n")
        
        for cmd_name in sorted(COMMAND_REGISTRY.keys()):
            cmd_info = COMMAND_REGISTRY[cmd_name]
            self.session.console.print(
                f"  [cyan]{cmd_name}[/cyan] - {cmd_info['description']}"
            )
        
        self.session.console.print("\n[bold]Usage:[/bold]")
        self.session.console.print("  /command subcommand [args] [options]")
        self.session.console.print("  /help <command> - Show help for specific command\n")
    
    def _show_command_help(self, command: str):
        """Show help for specific command."""
        cmd_info = get_command_info(command)
        
        if not cmd_info:
            self.print_error(f"Unknown command: {command}")
            self.session.console.print(
                f"Use /help to see available commands"
            )
            return
        
        self.session.console.print(f"\n[bold cyan]{command}[/bold cyan]")
        self.session.console.print(f"{cmd_info['description']}\n")
        self.session.console.print(f"[bold]Usage:[/bold] {cmd_info['help']}\n")
        
        # Show subcommands if available
        if "subcommands" in cmd_info and cmd_info["subcommands"]:
            self.session.console.print("[bold]Subcommands:[/bold]")
            for subcmd_name in sorted(cmd_info["subcommands"].keys()):
                subcmd_info = cmd_info["subcommands"][subcmd_name]
                self.session.console.print(
                    f"  [cyan]{subcmd_name}[/cyan] - {subcmd_info['description']}"
                )
            
            self.session.console.print("\n[bold]Options:[/bold]")
            self.session.console.print("  Use /help <command> <subcommand> for detailed options\n")
        else:
            # Show args and options
            args = cmd_info.get("args", [])
            options = cmd_info.get("options", [])
            
            if args:
                self.session.console.print("[bold]Arguments:[/bold]")
                for arg in args:
                    req = "required" if arg.get("required", True) else "optional"
                    self.session.console.print(
                        f"  <{arg['name']}> ({req}) - {arg['help']}"
                    )
            
            if options:
                self.session.console.print("\n[bold]Options:[/bold]")
                for opt in options:
                    default = opt.get("default")
                    default_str = f" [default: {default}]" if default is not None else ""
                    self.session.console.print(
                        f"  --{opt['name']}{default_str} - {opt['help']}"
                    )
    
    def _show_subcommand_help(self, command: str, subcommand: str):
        """Show help for specific subcommand."""
        cmd_info = get_command_info(command)
        
        if not cmd_info:
            self.print_error(f"Unknown command: {command}")
            self.session.console.print(
                f"Use /help to see available commands"
            )
            return
        
        # Check if command has subcommands
        if "subcommands" not in cmd_info or not cmd_info["subcommands"]:
            self.print_error(f"Command {command} has no subcommands")
            return
        
        # Get subcommand info
        subcmd_info = get_subcommand_info(command, subcommand)
        
        if not subcmd_info:
            self.print_error(f"Unknown subcommand: {subcommand}")
            self.session.console.print(
                f"Available subcommands: {', '.join(sorted(cmd_info['subcommands'].keys()))}"
            )
            return
        
        # Display subcommand help
        self.session.console.print(f"\n[bold cyan]{command} {subcommand}[/bold cyan]")
        self.session.console.print(f"{subcmd_info['description']}\n")
        self.session.console.print(f"[bold]Usage:[/bold] {cmd_info['help']} {subcommand} [args] [options]\n")
        
        # Show args and options for subcommand
        args = subcmd_info.get("args", [])
        options = subcmd_info.get("options", [])
        
        if args:
            self.session.console.print("[bold]Arguments:[/bold]")
            for arg in args:
                req = "required" if arg.get("required", True) else "optional"
                self.session.console.print(
                    f"  <{arg['name']}> ({req}) - {arg['help']}"
                )
        
        if options:
            self.session.console.print("\n[bold]Options:[/bold]")
            for opt in options:
                default = opt.get("default")
                default_str = f" [default: {default}]" if default is not None else ""
                self.session.console.print(
                    f"  --{opt['name']}{default_str} - {opt['help']}"
                )


class ListHandler(BaseHandler):
    """Handler for /list command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any],
        silent: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        List ADRs in directory.
        
        Args:
            args: [path] (optional)
            options: None
        """
        if args:
            path = Path(args[0])
        else:
            path = self.session.current_dir
        
        if not path.exists():
            self.print_error(f"Path does not exist: {path}")
            return
        
        # Load ADR files
        adr_files = self.session.load_adr_files(path)
        
        if not adr_files:
            self.print_warning(f"No ADRs found in {path}")
            return
        
        # Display list
        self.session.console.print(f"\n[bold]ADRs in {path}:[/bold]\n")
        for i, adr_file in enumerate(adr_files, 1):
            self.session.console.print(f"  {i}. [cyan]{adr_file.name}[/cyan]")
        
        self.session.console.print(f"\nTotal: {len(adr_files)} ADR(s)\n")


class LLMHandler(BaseHandler):
    """Handler for /util llm command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any],
        silent: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Test LLM configuration.
        
        Args:
            args: [prompt] (optional)
            options: None
        """
        from adrminer.models.llm_factory import create_llm, reset_llm_cache
        from adrminer.config import reset_settings, get_settings
        from rich.table import Table
        
        # Get prompt from args or use default
        prompt_text = args[0] if args else "How are you doing?"
        
        # Reset caches to ensure fresh configuration
        reset_settings()
        reset_llm_cache()
        
        # Load settings
        settings = get_settings()
        
        # Display configuration
        self.session.console.print("\n[bold cyan]🔧 Current LLM Configuration[/bold cyan]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="green")
        table.add_column("Value", style="yellow")
        
        table.add_row("Provider", settings.llm.provider)
        table.add_row("Model", settings.llm.model)
        table.add_row("Temperature", str(settings.llm.temperature))
        table.add_row("Max Tokens", str(settings.llm.max_tokens))
        if settings.llm.provider == "ollama":
            table.add_row("Ollama Base URL", settings.llm.ollama_base_url or "default")
        
        self.session.console.print(table)
        
        # Create LLM instance
        self.session.console.print("\n[blue]Creating LLM instance...[/blue]")
        try:
            llm = create_llm()
            self.session.console.print(f"[green]✓ LLM created successfully[/green]")
            self.session.console.print(f"[dim]Type: {type(llm).__module__}.{type(llm).__name__}[/dim]\n")
        except Exception as e:
            self.print_error(f"Failed to create LLM: {e}")
            return
        
        # Send test prompt
        self.session.console.print(f"[blue]Sending test prompt...[/blue]")
        self.session.console.print(f'[dim]Prompt: "{prompt_text}"[/dim]\n')
        
        try:
            response = llm.invoke(prompt_text)
            from rich.panel import Panel
            self.session.console.print(Panel(
                f"[bold]Response:[/bold]\n{response.content}",
                title="[green]✓ LLM Response[/green]",
                border_style="green"
            ))
        except Exception as e:
            self.print_error(f"Failed to get response: {e}")


class InspectHandler(BaseHandler):
    """Handler for /util inspect command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any],
        silent: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Inspect and display an ADR with Rich Markdown rendering.
        
        Args:
            args: [path] (required)
            options: --metadata, --raw, --width
        """
        from rich.markdown import Markdown
        from rich.panel import Panel
        
        if not args:
            self.print_error("Path to ADR file is required")
            self.session.console.print("Usage: /util inspect <path> [--metadata] [--raw] [--width <width>]")
            return
        
        path = Path(args[0])
        
        # Get options
        show_metadata = options.get("metadata", False)
        raw_mode = options.get("raw", False)
        width = options.get("width")
        
        # Validate file is a markdown file
        if not path.exists():
            self.print_error(f"File does not exist: {path}")
            return
        
        if path.suffix not in [".md", ".MD", ".markdown"]:
            self.print_error(f"{path.name} is not a markdown file")
            return
        
        # Read ADR content
        try:
            with open(path, "r", encoding="utf-8") as f:
                adr_content = f.read()
        except Exception as e:
            self.print_error(f"Failed to read {path.name}: {e}")
            return
        
        # Display ADR header
        self.session.console.print(f"\n[bold cyan]📄 {path.name}[/bold cyan]\n")
        
        # Create console with custom width if specified
        if width:
            from rich.console import Console
            display_console = Console(width=int(width))
        else:
            display_console = self.session.console
        
        # Render content
        if raw_mode:
            # Display raw content
            display_console.print(adr_content)
        else:
            # Display with Rich Markdown
            display_console.print(Panel(
                Markdown(adr_content),
                title="[bold]ADR Content[/bold]",
                border_style="cyan",
                padding=(1, 2),
            ))
        
        # Display metadata if requested
        if show_metadata:
            self._display_metadata(path, display_console)
    
    def _display_metadata(self, adr_path: Path, console) -> None:
        """Display metadata for an ADR if available in sidecar files."""
        # Try to find metadata file
        metadata = None
        metadata_paths = [
            adr_path.with_suffix('.adrminer.checking.json'),
            adr_path.with_suffix('.metadata.json'),
            adr_path.with_suffix('.adrminer.classification.json'),
        ]
        
        for metadata_path in metadata_paths:
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    break
                except Exception as e:
                    self.session.console.print(f"[yellow]⚠ Warning: Could not read {metadata_path.name}: {e}[/yellow]")
                    continue
        
        if not metadata:
            self.session.console.print("\n[yellow]⚠ No metadata found for this ADR[/yellow]")
            return
        
        # Display metadata in table
        self.session.console.print("\n[bold cyan]📊 Metadata[/bold cyan]\n")
        
        from rich.table import Table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Category", style="green", width=20)
        table.add_column("Value", style="yellow")
        
        # Topic
        if "topics" in metadata:
            topic = metadata["topics"]
            table.add_row("Topic", topic.get("topic_label", "N/A"))
            table.add_row("Probability", f"{topic.get('probability', 0):.2%}")
        
        # Classifications
        if "classifications" in metadata:
            for framework, cls in metadata["classifications"].items():
                primary = cls.get("primary_category", "N/A")
                confidence = cls.get("confidence", 0)
                table.add_row(framework.capitalize(), f"{primary} ({confidence:.0%})")
        
        # Quality check
        if "check" in metadata:
            quality = metadata["check"]
            adherence = quality.get("template_adherence", {})
            score = adherence.get("adherence_score", "N/A")
            table.add_row("Quality Score", str(score))
            
            # Section summary
            assessments = quality.get("section_assessments", [])
            if assessments:
                present = sum(1 for a in assessments if a.get("presence") == "Yes")
                table.add_row("Sections Present", f"{present}/{len(assessments)}")
        
        console.print(table)


class EnhancedListHandler(BaseHandler):
    """Handler for /util list command with enhanced features."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any],
        silent: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        List ADRs in directory with optional filtering and details.
        
        Args:
            args: [path] (optional)
            options: --has-metadata, --details, --compact
        """
        from rich.table import Table
        
        if args:
            path = Path(args[0])
        else:
            path = self.session.current_dir
        
        if not path.exists():
            self.print_error(f"Path does not exist: {path}")
            return
        
        # Get options
        has_metadata_only = options.get("has-metadata", False)
        show_details = options.get("details", False)
        compact = options.get("compact", False)
        
        # Load ADR files
        adr_files = self.session.load_adr_files(path)
        
        if not adr_files:
            self.print_warning(f"No ADRs found in {path}")
            return
        
        # Filter by metadata if requested
        if has_metadata_only:
            adr_files = [f for f in adr_files if self._has_metadata(f)]
            if not adr_files:
                self.print_warning(f"No ADRs with metadata found in {path}")
                return
        
        # Compact mode: just list filenames
        if compact:
            self.session.console.print(f"[cyan]Found {len(adr_files)} ADR(s):[/cyan]\n")
            for adr_file in adr_files:
                self.session.console.print(f"  • {adr_file.name}")
            return
        
        # Display in table
        if show_details:
            # Detailed table
            table = Table(title=f"ADRs ({len(adr_files)} found)")
            table.add_column("#", style="cyan", width=4)
            table.add_column("File", style="green", no_wrap=True)
            table.add_column("Title", style="yellow")
            table.add_column("Has Metadata", justify="center", width=14)
            table.add_column("Topic", style="magenta")
            
            for idx, adr_file in enumerate(adr_files, 1):
                # Read ADR content
                try:
                    with open(adr_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    title = self._extract_title(content)
                except Exception:
                    title = "Error reading"
                
                # Check for metadata
                has_meta = self._has_metadata(adr_file)
                meta_status = "[green]✓[/green]" if has_meta else "[dim]–[/dim]"
                
                # Load topic if available
                topic = "N/A"
                if has_meta:
                    metadata = self._load_metadata(adr_file)
                    if metadata and "topics" in metadata:
                        topic_data = metadata["topics"]
                        topic = topic_data.get("topic_label", "N/A")
                        # Truncate if too long
                        topic = topic[:25] + '...' if len(topic) > 25 else topic
                
                table.add_row(str(idx), adr_file.name, title, meta_status, topic)
            
            self.session.console.print(table)
        else:
            # Simple table
            table = Table(title=f"ADRs ({len(adr_files)} found)")
            table.add_column("#", style="cyan", width=4)
            table.add_column("File", style="green", no_wrap=True)
            table.add_column("Has Metadata", justify="center", width=14)
            
            for idx, adr_file in enumerate(adr_files, 1):
                has_meta = self._has_metadata(adr_file)
                meta_status = "[green]✓[/green]" if has_meta else "[dim]–[/dim]"
                table.add_row(str(idx), adr_file.name, meta_status)
            
            self.session.console.print(table)
    
    def _has_metadata(self, adr_path: Path) -> bool:
        """Check if an ADR has metadata file."""
        metadata_paths = [
            adr_path.with_suffix('.adrminer.checking.json'),
            adr_path.with_suffix('.metadata.json'),
            adr_path.with_suffix('.adrminer.classification.json'),
        ]
        return any(mp.exists() for mp in metadata_paths)
    
    def _load_metadata(self, adr_path: Path) -> dict | None:
        """Load metadata for an ADR."""
        metadata_paths = [
            adr_path.with_suffix('.adrminer.checking.json'),
            adr_path.with_suffix('.metadata.json'),
            adr_path.with_suffix('.adrminer.classification.json'),
        ]
        
        for metadata_path in metadata_paths:
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    continue
        
        return None
    
    def _extract_title(self, content: str) -> str:
        """Extract title from ADR content."""
        # Try to find first heading
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                # Remove # and trim
                title = line.lstrip('#').strip()
                return title[:60] + '...' if len(title) > 60 else title
        return "No title"


class SummaryHandler(BaseHandler):
    """Handler for /summary command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any],
        silent: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Generate summaries and insights for ADRs.
        
        Args:
            args: [path] (required)
            options: --output-summary, --output-detailed, --verbose, --force-rewrite
            silent: If True, suppress console output and return structured data
        """
        from adrminer.services import InsightService
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
        from rich.table import Table
        
        if not args:
            if not silent:
                self.print_error("Path to ADR file or directory is required")
                self.session.console.print("Usage: /summary <path> [--output-summary <file>] [--output-detailed <file>]")
            return None
        
        path = Path(args[0])
        
        # Get options
        output_summary_path = options.get("output-summary")
        output_detailed_path = options.get("output-detailed")
        verbose = options.get("verbose", False)
        force_rewrite = options.get("force-rewrite", False)
        
        if not path.exists():
            if not silent:
                self.print_error(f"Path does not exist: {path}")
            return None
        
        # Collect ADR files and metadata
        adrs_data = self._collect_adrs_with_metadata(path)
        
        if not adrs_data:
            if not silent:
                self.print_warning(f"No ADR files found at {path}")
            return None
        
        # Ask for confirmation (skip if silent)
        file_count = len(adrs_data)
        if not silent and not self.confirm_batch_operation(
            operation="Generate summaries and insights",
            file_count=file_count,
            threshold=1
        ):
            self.session.console.print("[yellow]Operation cancelled.[/yellow]")
            return None
        
        # Use session's insight service (lazy-loaded)
        service = self.session.insights_service
        
        if not silent:
            # Display console summary
            self._display_console_summary(adrs_data)
            
            # Display project-level insights if available
            all_metadata = [a["metadata"] for a in adrs_data if a["metadata"]]
            if all_metadata:
                self._display_project_insights(all_metadata)
            
            # Generate and export reports if requested
            if output_summary_path or output_detailed_path:
                # Resolve output paths
                if path.is_dir():
                    default_output_dir = path.parent
                else:
                    default_output_dir = path.parent.parent
                
                resolved_summary = output_summary_path
                if output_summary_path and (not Path(output_summary_path).parent.name or str(Path(output_summary_path).parent) == "."):
                    resolved_summary = default_output_dir / output_summary_path
                
                resolved_detailed = output_detailed_path
                if output_detailed_path and (not Path(output_detailed_path).parent.name or str(Path(output_detailed_path).parent) == "."):
                    resolved_detailed = default_output_dir / output_detailed_path
                
                self._generate_reports(
                    adrs_data=adrs_data,
                    service=service,
                    output_summary=resolved_summary,
                    output_detailed=resolved_detailed,
                    force_rewrite=force_rewrite,
                    verbose=verbose,
                )
            return None
        else:
            # Return structured data in silent mode
            all_metadata = [a["metadata"] for a in adrs_data if a["metadata"]]
            return {
                "adr_count": len(adrs_data),
                "has_metadata_count": len(all_metadata),
                "adrs": [{"file": a["adr_file"].name, "has_metadata": a["metadata"] is not None} for a in adrs_data]
            }
    
    def _collect_adrs_with_metadata(self, path: Path) -> list[dict]:
        """Collect ADR files and their metadata."""
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
                self.session.console.print(f"[yellow]Warning: Could not read {adr_file.name}: {e}[/yellow]")
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
                    except Exception:
                        continue
            
            adrs_data.append({
                "adr_file": adr_file,
                "adr_content": adr_content,
                "metadata": metadata,
            })
        
        return adrs_data
    
    def _display_console_summary(self, adrs_data: list[dict]) -> None:
        """Display console summary of ADRs."""
        from rich.table import Table
        
        self.session.console.print("\n[bold]ADR Summary:[/bold]\n")
        
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
            kruchten = self._get_classification(metadata, "kruchten")
            zimmermann = self._get_classification(metadata, "zimmermann")
            qa = self._get_classification(metadata, "quality_attributes")
            
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
        
        self.session.console.print(table)
        
        # Show summary statistics
        adrs_with_metadata = sum(1 for a in adrs_data if a["metadata"])
        self.session.console.print(f"\n[cyan]ADRs with metadata: {adrs_with_metadata}/{len(adrs_data)}[/cyan]")
    
    def _get_classification(self, metadata: dict | None, framework: str) -> str:
        """Get primary category for a classification framework."""
        if not metadata or "classifications" not in metadata:
            return "N/A"
        
        classifications = metadata["classifications"]
        if framework not in classifications:
            return "N/A"
        
        return classifications[framework].get("primary_category", "N/A")
    
    def _display_project_insights(self, all_metadata: list[dict]) -> None:
        """Display project-level insights in console."""
        from rich.table import Table
        from rich.spinner import Spinner
        from rich.live import Live
        
        # Show progress indicator while generating insights (LLM call)
        with Live(Spinner("dots", text="Generating project insights..."), console=self.session.console) as live:
            try:
                project_insights = self.session.insights_service.generate_project_insights(all_metadata)
            except Exception as e:
                live.stop()
                self.session.console.print(f"[yellow]Warning: Could not generate project insights: {e}[/yellow]")
                return
        
        self.session.console.print("\n[bold cyan]📊 Project-Level Insights[/bold cyan]\n")
        
        # Overall summary
        self.session.console.print(f"[bold]Overview:[/bold] {project_insights.overall_summary}\n")
        
        # Classification patterns
        if project_insights.classification_patterns:
            self.session.console.print("[bold]Top Classification Patterns:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Framework", style="cyan")
            table.add_column("Category", style="green")
            table.add_column("Count", justify="right")
            table.add_column("Percentage", justify="right")
            
            for pattern in project_insights.classification_patterns[:5]:
                table.add_row(
                    pattern.framework,
                    pattern.category,
                    str(pattern.count),
                    f"{pattern.percentage:.1f}%"
                )
            
            self.session.console.print(table)
            self.session.console.print()
        
        # Quality trends
        self.session.console.print("[bold]Quality Trends:[/bold]")
        trends = project_insights.quality_trends
        self.session.console.print(f"  Average Adherence Score: {trends.average_adherence_score:.2f}")
        self.session.console.print(f"  Quality Distribution: {trends.quality_distribution}")
        if trends.common_missing_sections:
            missing = ", ".join(trends.common_missing_sections[:3])
            self.session.console.print(f"  Common Missing Sections: {missing}")
        self.session.console.print()
        
        # Architectural themes
        if project_insights.architectural_themes:
            self.session.console.print("[bold]Architectural Themes:[/bold]")
            for theme in project_insights.architectural_themes[:5]:
                self.session.console.print(f"  • [cyan]{theme.theme}[/cyan]: {theme.description} ({theme.adr_count} ADRs)")
            self.session.console.print()
        
        # Risk assessment
        self.session.console.print("[bold]Risk Assessment:[/bold]")
        self.session.console.print(f"  {project_insights.risk_assessment.risk_summary}")
        self.session.console.print()
        
        # Top recommendations
        if project_insights.recommendations:
            self.session.console.print("[bold]Top Recommendations:[/bold]")
            for rec in project_insights.recommendations[:3]:
                priority_color = "red" if rec.priority == "High" else "yellow" if rec.priority == "Medium" else "green"
                self.session.console.print(
                    f"  [{priority_color}]{rec.priority}[/{priority_color}] [cyan]{rec.area}[/cyan]: {rec.recommendation}"
                )
            self.session.console.print()
    
    def _generate_reports(
        self,
        adrs_data: list[dict],
        service,
        output_summary: Path | None,
        output_detailed: Path | None,
        force_rewrite: bool = False,
        verbose: bool = False,
    ) -> None:
        """Generate and export summary and detailed reports."""
        from datetime import datetime
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
        
        if verbose:
            self.session.console.print(f"[cyan]Generating reports...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.session.console,
        ) as progress:
            # Generate content summaries if needed
            if output_summary or output_detailed:
                task = progress.add_task("Generating content summaries...", total=len(adrs_data))
                
                content_summaries = self._generate_content_summaries(
                    adrs_data=adrs_data,
                    service=service,
                    progress=progress,
                    task=task,
                    force_rewrite=force_rewrite,
                    verbose=verbose,
                )
            
            # Generate summary report
            if output_summary:
                progress.add_task("Writing summary report...", total=1)
                self._write_summary_report(
                    output_summary=output_summary,
                    adrs_data=adrs_data,
                    content_summaries=content_summaries,
                )
                self.session.console.print(f"\n[green]✓ Summary report exported to {output_summary}[/green]")
            
            # Generate detailed report
            if output_detailed:
                # Generate project insights
                progress.add_task("Generating project insights...", total=1)
                all_metadata = [a["metadata"] for a in adrs_data if a["metadata"]]
                project_insights = None
                if all_metadata:
                    try:
                        project_insights = service.generate_project_insights(all_metadata)
                    except Exception as e:
                        self.session.console.print(f"[red]Error generating project insights: {e}[/red]")
                
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
                            self.session.console.print(f"[yellow]Warning: Could not generate insights for {adr_file.name}: {e}[/yellow]")
                            adr_insights[str(adr_file)] = None
                    
                    progress.update(task, advance=1)
                
                # Write detailed report
                progress.add_task("Writing detailed report...", total=1)
                self._write_detailed_report(
                    output_detailed=output_detailed,
                    adrs_data=adrs_data,
                    content_summaries=content_summaries,
                    project_insights=project_insights,
                    adr_insights=adr_insights,
                )
                self.session.console.print(f"\n[green]✓ Detailed report exported to {output_detailed}[/green]")
    
    def _generate_content_summaries(
        self,
        adrs_data: list[dict],
        service,
        progress,
        task,
        force_rewrite: bool = False,
        verbose: bool = False,
    ) -> dict[str, str]:
        """Generate content summaries with caching in metadata sidecar files."""
        content_summaries = {}
        
        for adr_data in adrs_data:
            adr_file = adr_data["adr_file"]
            adr_content = adr_data["adr_content"]
            metadata = adr_data["metadata"]
            
            # Generate summary
            try:
                summary = service.generate_content_summary(adr_content)
                content_summaries[str(adr_file)] = summary.summary
                if verbose:
                    self.session.console.print(f"[dim]  Generated summary for {adr_file.name}[/dim]")
            except Exception as e:
                self.session.console.print(f"[yellow]Warning: Could not generate summary for {adr_file.name}: {e}[/yellow]")
                content_summaries[str(adr_file)] = "Summary generation failed."
            
            progress.update(task, advance=1)
        
        return content_summaries
    
    def _write_summary_report(
        self,
        output_summary: Path,
        adrs_data: list[dict],
        content_summaries: dict[str, str],
    ) -> None:
        """Write summary report to Markdown file."""
        from datetime import datetime
        
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
        self,
        output_detailed: Path,
        adrs_data: list[dict],
        content_summaries: dict[str, str],
        project_insights,
        adr_insights: dict[str, any],
    ) -> None:
        """Write detailed report to Markdown file with insights."""
        from datetime import datetime
        
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


class ResetMemoryHandler(BaseHandler):
    """Handler for /reset_memory command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any],
        silent: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Reset all session memory and analysis results."""
        # Reset session memory
        summary = self.session.reset_memory()
        
        # Display what was reset
        self.session.console.print("\n[green]✓ Memory reset complete[/green]")
        self.session.console.print(f"  [dim]Analysis results cleared:[/dim] {len(summary['analysis_results'])}")
        self.session.console.print(f"  [dim]Loaded ADRs cleared:[/dim] {summary['loaded_adrs_count']}")
        self.session.console.print(f"  [dim]Command history cleared:[/dim] Yes")
        
        # Note about agent conversation
        if summary['has_agent']:
            self.session.console.print(
                "  [dim]Note:[/dim] Agent conversation history persists in checkpointer. "
                "Use natural language to start fresh."
            )
        else:
            self.session.console.print(
                "  [dim]Note:[/dim] Agent not initialized. No conversation history to clear."
            )


class QuitHandler(BaseHandler):
    """Handler for /quit command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any],
        silent: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Exit interactive session.
        
        Args:
            args: None
            options: None
        """
        # This is handled by the chat loop, not here
        # We just set a flag that the loop will check
        pass