"""Base service class with shared functionality."""

import logging
from pathlib import Path
from typing import Optional


class BaseService:
    """Base class for ADRminer services with shared functionality."""
    
    def __init__(self, settings=None):
        """Initialize base service.
        
        Args:
            settings: Settings instance (optional, will load if None)
        """
        if settings is None:
            from adrminer.config import get_settings
            settings = get_settings()
        
        self.settings = settings
        
        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Default prompts directory
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
    
    def load_prompt(self, prompt_name: str, fallback_prompt: Optional[str] = None) -> Optional[str]:
        """
        Load prompt from external markdown file.
        
        Args:
            prompt_name: Name of prompt file (e.g., 'kruchten_classification_v2')
            fallback_prompt: Fallback prompt string if file not found
        
        Returns:
            Prompt content as string, or None if file not found and no fallback provided
        
        Note:
            When None is returned, calling code should handle this appropriately
            and raise an appropriate exception to avoid silent errors with empty prompts.
        """
        prompt_path = self.prompts_dir / f"{prompt_name}.md"
        
        if prompt_path.exists():
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    prompt = f.read()
                return prompt
            except Exception as e:
                print(f"Warning: Failed to load prompt from {prompt_path}: {e}")
        
        # Use fallback if provided
        if fallback_prompt:
            print(f"Using fallback prompt for {prompt_name}")
            return fallback_prompt
        
        # Return None if file not found and no fallback
        print(f"Warning: Prompt file not found: {prompt_path}")
        return None
    
    def _num_tokens_from_text(self, text: str, encoding_name: str = "cl100k_base") -> int:
        """
        Returns the number of tokens in a text string.
        
        Args:
            text: Text to count tokens for
            encoding_name: Name of tiktoken encoding
        
        Returns:
            Number of tokens
        """
        import tiktoken
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(text))
        return num_tokens