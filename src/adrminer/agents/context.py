"""Agent context management for Deep Agents integration.

This module provides the AgentContext class that maintains state
across agent interactions and synchronizes with the SessionManager.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentContext(BaseModel):
    """Context maintained by the Deep Agent.
    
    This class tracks the agent's state including current directory,
    loaded ADRs, analysis results, and command history. It synchronizes
    with the SessionManager to maintain consistency across the CLI.
    """
    
    available_directories: List[Path] = Field(
        default_factory=list,
        description="List of available directories (root + subdirectories)"
    )
    loaded_adrs: List[Path] = Field(
        default_factory=list,
        description="List of loaded ADR file paths"
    )
    analysis_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Stored analysis results (topics, classification, check, insights)"
    )
    command_history: List[str] = Field(
        default_factory=list,
        description="History of commands and queries"
    )
    session_id: str = Field(
        default="",
        description="Unique session identifier"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )
    
    def load_from_session(self, session) -> None:
        """Load context from SessionManager.
        
        Args:
            session: SessionManager instance
        """
        from adrminer.config import get_settings
        settings = get_settings()
        exclusions = settings.standard_exclusions

        # Load available directories (root + subdirectories)
        root_dir = Path.cwd()
        self.available_directories = [root_dir]
        
        # Add immediate subdirectories (non-hidden, excluding __pycache__, etc.)
        for item in root_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in exclusions:
                self.available_directories.append(item)
        
        # Sort directories for consistent ordering
        self.available_directories.sort()
        
        self.session_id = getattr(session, 'session_id', '')
        
        # Load ADRs from session if available
        if hasattr(session, 'loaded_adrs'):
            self.loaded_adrs = list(session.loaded_adrs) if session.loaded_adrs else []
        
        # Load analysis results if available
        if hasattr(session, 'analysis_results'):
            self.analysis_results = dict(session.analysis_results) if session.analysis_results else {}
    
    def sync_to_session(self, session) -> None:
        """Synchronize context to SessionManager.
        
        Args:
            session: SessionManager instance
        """
        # Update session with agent context
        if hasattr(session, 'loaded_adrs'):
            session.loaded_adrs = self.loaded_adrs
        
        if hasattr(session, 'analysis_results'):
            session.analysis_results = self.analysis_results
        
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to dictionary for persistence.
        
        Returns:
            Dictionary representation of context
        """
        return {
            "available_directories": [str(p) for p in self.available_directories],
            "loaded_adrs": [str(p) for p in self.loaded_adrs],
            "analysis_results": self.analysis_results,
            "command_history": self.command_history,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat()
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load context from dictionary.
        
        Args:
            data: Dictionary containing context data
        """
        self.available_directories = [Path(p) for p in data.get("available_directories", [])]
        self.loaded_adrs = [Path(p) for p in data.get("loaded_adrs", [])]
        self.analysis_results = data.get("analysis_results", {})
        self.command_history = data.get("command_history", [])
        self.session_id = data.get("session_id", "")
        
        timestamp_str = data.get("timestamp")
        if timestamp_str:
            try:
                self.timestamp = datetime.fromisoformat(timestamp_str)
            except (ValueError, TypeError):
                self.timestamp = datetime.now()
    
    def add_command(self, command: str) -> None:
        """Add a command to the history.
        
        Args:
            command: Command or query string
        """
        self.command_history.append(command)
        # Keep only last 100 commands
        if len(self.command_history) > 100:
            self.command_history = self.command_history[-100:]
    
    def get_loaded_adr_count(self) -> int:
        """Get the number of loaded ADRs.
        
        Returns:
            Number of loaded ADRs
        """
        return len(self.loaded_adrs)
    
    def has_analysis_results(self, analysis_type: str) -> bool:
        """Check if specific analysis results exist.
        
        Args:
            analysis_type: Type of analysis (e.g., "topics", "classification")
        
        Returns:
            True if results exist for this type
        """
        return analysis_type in self.analysis_results
    
    def get_analysis_result(self, analysis_type: str) -> Any:
        """Get analysis results for a specific type.
        
        Args:
            analysis_type: Type of analysis (e.g., "topics", "classification")
        
        Returns:
            Analysis results or None
        """
        return self.analysis_results.get(analysis_type)
    
    def set_analysis_result(self, analysis_type: str, result: Any) -> None:
        """Store analysis results for a specific type.
        
        Args:
            analysis_type: Type of analysis (e.g., "topics", "classification")
            result: Analysis results to store
        """
        self.analysis_results[analysis_type] = result
        self.timestamp = datetime.now()