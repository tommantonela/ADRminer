"""Session manager for interactive chat CLI."""

from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console

from adrminer.config import get_settings
from adrminer.services import TopicService, ClassificationService
from adrminer.services.checking_service import CheckingService
from adrminer.services.insight_service import InsightService


class SessionManager:
    """Manages shared resources and state across a chat session."""
    
    def __init__(self, console: Console, initial_dir: Optional[Path] = None):
        """
        Initialize session manager.
        
        Args:
            console: Rich console instance for output
            initial_dir: Initial working directory (defaults to cwd)
        """
        self.console = console
        self.current_dir = initial_dir or Path.cwd()
        
        # Lazy-loaded services
        self._services: Dict[str, Any] = {}
        
        # Session state
        self.command_history: List[str] = []
        self.history_index: int = -1
        self.analysis_results: Dict[str, Any] = {}
        self.loaded_adrs: List[Path] = []
    
    @property
    def topic_service(self) -> TopicService:
        """Lazy-load TopicService."""
        if "topic" not in self._services:
            self.console.print("[blue]Loading topic model...[/blue]")
            settings = get_settings()
            self._services["topic"] = TopicService(
                model_path=settings.topic_model.path
            )
            self.console.print("[green]✓ Topic model loaded[/green]")
        return self._services["topic"]
    
    @property
    def classification_service(self) -> ClassificationService:
        """Lazy-load ClassificationService."""
        if "classification" not in self._services:
            self.console.print("[blue]Loading classification service...[/blue]")
            settings = get_settings()
            self._services["classification"] = ClassificationService(
                framework=settings.classification.framework,
                examples_path=settings.classification.examples,
                use_examples=settings.classification.use_examples
            )
            self.console.print(f"[green]✓ Classification service loaded (framework: {settings.classification.framework})[/green]")
        return self._services["classification"]
    
    @property
    def checking_service(self) -> CheckingService:
        """Lazy-load CheckingService."""
        if "check" not in self._services:
            self.console.print("[blue]Loading checking service...[/blue]")
            self._services["check"] = CheckingService(mode="full")
            self.console.print("[green]✓ Checking service loaded[/green]")
        return self._services["check"]
    
    @property
    def insights_service(self) -> InsightService:
        """Lazy-load InsightsService."""
        if "insights" not in self._services:
            self.console.print("[blue]Loading insights service...[/blue]")
            self._services["insights"] = InsightService()
            self.console.print("[green]✓ Insights service loaded[/green]")
        return self._services["insights"]
    
    def load_adr_files(self, path: Path) -> List[Path]:
        """
        Load ADR files from a path.
        
        Args:
            path: Path to ADR file or directory
            
        Returns:
            List of ADR file paths
        """
        if path.is_file():
            adr_files = [path]
        elif path.is_dir():
            adr_files = list(path.glob("*.md")) + list(path.glob("*.MD"))
        else:
            return []
        
        self.loaded_adrs = sorted(adr_files)
        return self.loaded_adrs
    
    def get_adr_contents(self, adr_files: Optional[List[Path]] = None) -> Dict[str, str]:
        """
        Read contents of ADR files.
        
        Args:
            adr_files: List of ADR file paths (defaults to loaded_adrs)
            
        Returns:
            Dictionary mapping file paths to contents
        """
        if adr_files is None:
            adr_files = self.loaded_adrs
        
        contents = {}
        for adr_file in adr_files:
            try:
                with open(adr_file, 'r', encoding='utf-8') as f:
                    contents[str(adr_file)] = f.read()
            except Exception as e:
                self.console.print(f"[yellow]Warning: Failed to read {adr_file}: {e}[/yellow]")
        
        return contents
    
    def store_analysis_result(self, result_type: str, result: Any):
        """
        Store analysis results in session.
        
        Args:
            result_type: Type of analysis (topics, classification, check, etc.)
            result: Analysis results to store
        """
        self.analysis_results[result_type] = result
    
    def get_analysis_result(self, result_type: str) -> Optional[Any]:
        """
        Retrieve stored analysis results.
        
        Args:
            result_type: Type of analysis to retrieve
            
        Returns:
            Stored results or None if not found
        """
        return self.analysis_results.get(result_type)
    
    def add_to_history(self, command: str):
        """Add command to history."""
        if command.strip():
            self.command_history.append(command.strip())
            self.history_index = len(self.command_history)
    
    def get_previous_command(self) -> Optional[str]:
        """Get previous command from history."""
        if self.history_index > 0:
            self.history_index -= 1
            return self.command_history[self.history_index]
        return None
    
    def get_next_command(self) -> Optional[str]:
        """Get next command from history."""
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            return self.command_history[self.history_index]
        elif self.history_index == len(self.command_history) - 1:
            self.history_index = len(self.command_history)
            return ""  # Clear input when at end of history
        return None
    
    def reset_history_navigation(self):
        """Reset history navigation index to current position."""
        self.history_index = len(self.command_history)