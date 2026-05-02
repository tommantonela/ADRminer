"""Filesystem utilities for ADRminer."""

from pathlib import Path
from typing import List, Optional
from adrminer.config import get_settings


def discover_adrs(path: Path, recursive: bool = True) -> List[Path]:
    """
    Discover ADR files in a path with standard exclusions.
    
    Args:
        path: Path to ADR file or directory
        recursive: Whether to search recursively in directories
        
    Returns:
        List of Path objects for discovered ADR files
    """
    settings = get_settings()
    exclusions = settings.standard_exclusions
    
    adr_files = []
    
    if path.is_file():
        if path.suffix.lower() in ['.md', '.txt']:
            adr_files.append(path)
    elif path.is_dir():
        # Choose between rglob and glob based on recursive flag
        pattern = "**/*.md" if recursive else "*.md"
        
        # Initial discovery
        all_md = list(path.glob(pattern)) + list(path.glob(pattern.upper()))
        
        # Filter exclusions
        for p in all_md:
            # Check if any parent directory (relative to search path) is in exclusions
            # or if it's a hidden directory
            parts = p.relative_to(path).parts
            is_excluded = False
            for part in parts:
                if part.startswith('.') or part in exclusions:
                    is_excluded = True
                    break
            
            if not is_excluded:
                adr_files.append(p)
    
    return sorted(list(set(adr_files)))
