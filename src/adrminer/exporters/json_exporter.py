"""JSON exporter for saving ADR analysis results."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class JSONExporter:
    """Export analysis results to JSON sidecar files."""
    
    def __init__(self, version: str = "1.0.0"):
        """
        Initialize JSON exporter.
        
        Args:
            version: Metadata schema version
        """
        self.version = version
    
    def export_sidecar(
        self,
        adr_file: Path,
        topics: Optional[Dict] = None,
        classification: Optional[Dict] = None,
        check: Optional[Dict] = None,
        insights: Optional[List[Dict]] = None,
        model_versions: Optional[Dict] = None,
    ) -> Path:
        """
        Export analysis results to a JSON sidecar file.
        Merges with existing file if it exists.
        
        Args:
            adr_file: Path to ADR file
            topics: Topic mining results
            classification: Classification results
            check: Check service results
            insights: Generated insights
            model_versions: Model versions used
        
        Returns:
            Path to the created/updated sidecar file
        """
        # Determine sidecar file path
        sidecar_path = self._get_sidecar_path(adr_file)
        
        # Load existing metadata if file exists
        existing_metadata = {}
        if sidecar_path.exists():
            existing_metadata = self.load_sidecar(sidecar_path)
        
        # Build/update metadata
        metadata = {
            "version": self.version,
            "adr_file": str(adr_file),
            "analyzed_at": datetime.utcnow().isoformat() + "Z",
        }
        
        # Update with existing model_versions and merge with new ones
        existing_model_versions = existing_metadata.get("model_versions", {})
        if model_versions:
            existing_model_versions.update(model_versions)
        metadata["model_versions"] = existing_model_versions
        
        # Add/update sections with new data
        if topics:
            metadata["topics"] = topics
        elif "topics" in existing_metadata:
            metadata["topics"] = existing_metadata["topics"]
        
        # Handle classifications with nested structure
        if classification:
            framework = classification.get("framework", "unknown")
            
            # Initialize classifications dict if not exists
            if "classifications" not in metadata:
                metadata["classifications"] = existing_metadata.get("classifications", {})
            
            # Add or update framework classification
            metadata["classifications"][framework] = classification
        elif "classification" in existing_metadata:
            # Migrate old format to new nested structure
            old_classification = existing_metadata["classification"]
            framework = old_classification.get("framework", "unknown")
            
            if "classifications" not in metadata:
                metadata["classifications"] = {}
            
            # Add to nested structure
            metadata["classifications"][framework] = old_classification
        
        # Remove old flat classification key if it exists
        if "classification" in metadata:
            del metadata["classification"]
        
        if check:
            metadata["check"] = check
        elif "check" in existing_metadata:
            metadata["check"] = existing_metadata["check"]
        
        if insights:
            metadata["insights"] = insights
        elif "insights" in existing_metadata:
            metadata["insights"] = existing_metadata["insights"]
        
        # Preserve existing classifications if not already added
        if "classifications" in existing_metadata and "classifications" not in metadata:
            metadata["classifications"] = existing_metadata["classifications"]
        
        # Write to file
        sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        with open(sidecar_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        return sidecar_path
    
    def _get_sidecar_path(self, adr_file: Path) -> Path:
        """
        Get the path for the sidecar file.
        
        Args:
            adr_file: Path to the ADR file
        
        Returns:
            Path for the sidecar file
        """
        # Replace extension with .metadata.json
        return adr_file.with_suffix(".metadata.json")
    
    def export_consolidated(
        self,
        results: List[Dict],
        output_path: Path,
    ) -> Path:
        """
        Export all analysis results to a single consolidated JSON file.
        
        Args:
            results: List of analysis result dictionaries
            output_path: Path to save the consolidated file
        
        Returns:
            Path to the created file
        """
        # Add metadata header
        consolidated = {
            "version": self.version,
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "total_adrs": len(results),
            "results": results,
        }
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(consolidated, f, indent=2)
        
        return output_path
    
    def export_insights(
        self,
        insights: List[Dict],
        collection_id: str,
        summary: Optional[Dict] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Export insights to a JSON file.
        
        Args:
            insights: List of insight dictionaries
            collection_id: ID for the ADR collection
            summary: Optional summary statistics
            output_path: Path to save the file (defaults to insights.json)
        
        Returns:
            Path to the created file
        """
        if output_path is None:
            output_path = Path("insights.json")
        
        # Build insights document
        insights_doc = {
            "version": self.version,
            "collection_id": collection_id,
            "analyzed_at": datetime.utcnow().isoformat() + "Z",
            "adr_count": summary.get("adr_count", 0) if summary else 0,
            "summary": summary or {},
            "insights": insights,
        }
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(insights_doc, f, indent=2)
        
        return output_path
    
    def load_sidecar(self, sidecar_file: Path) -> Dict:
        """
        Load analysis results from a sidecar file.
        
        Args:
            sidecar_file: Path to the sidecar file
        
        Returns:
            Dictionary with analysis metadata
        
        Raises:
            FileNotFoundError: If sidecar file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        if not sidecar_file.exists():
            raise FileNotFoundError(f"Sidecar file not found: {sidecar_file}")
        
        with open(sidecar_file, "r") as f:
            return json.load(f)
    
    def needs_update(
        self,
        adr_file: Path,
        sidecar_file: Optional[Path] = None,
    ) -> bool:
        """
        Check if ADR needs re-analysis.
        
        Args:
            adr_file: Path to the ADR file
            sidecar_file: Path to the sidecar file (derived if not provided)
        
        Returns:
            True if ADR needs re-analysis, False otherwise
        """
        if sidecar_file is None:
            sidecar_file = self._get_sidecar_path(adr_file)
        
        # If no sidecar file, needs analysis
        if not sidecar_file.exists():
            return True
        
        # Compare modification times
        adr_mtime = adr_file.stat().st_mtime
        sidecar_mtime = sidecar_file.stat().st_mtime
        
        return adr_mtime > sidecar_mtime