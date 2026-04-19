"""Configuration settings using Pydantic."""

import os
from pathlib import Path
from typing import Optional, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()

# Suppress huggingface/tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"


class LLMConfig(BaseModel):
    """LLM configuration."""
    
    provider: Literal["openai", "anthropic", "ollama", "azure", "google"] = Field(
        default="openai",
        description="LLM provider"
    )
    model: str = Field(
        default="gpt-4.1-mini",
        description="LLM model name"
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Temperature for generation"
    )
    max_tokens: int = Field(
        default=2000,
        ge=1,
        description="Maximum tokens to generate"
    )


class TopicModelConfig(BaseModel):
    """Topic model configuration."""
    
    path: str = Field(
        default="~/.adrminer/models/topic_model",
        description="Path to topic model"
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Embedding model name"
    )
    n_topics: Optional[int] = Field(
        default=None,
        description="Number of topics (None for auto)"
    )
    use_llm_representation: bool = Field(
        default=False,
        description="Use LLM to generate human-readable topic names"
    )
    reduce_topics: bool = Field(
        default=False,
        description="Reduce number of topics after training"
    )
    language: str = Field(
        default="english",
        description="Language for stop words in vectorizer"
    )
    umap_n_neighbors: int = Field(
        default=15,
        description="UMAP n_neighbors parameter"
    )
    umap_n_components: int = Field(
        default=5,
        description="UMAP n_components parameter"
    )
    umap_min_dist: float = Field(
        default=0.0,
        description="UMAP min_dist parameter"
    )
    umap_metric: str = Field(
        default="cosine",
        description="UMAP metric parameter"
    )


class ClassificationConfig(BaseModel):
    """Classification configuration."""
    
    framework: Literal["kruchten", "quality_attributes", "zimmermann"] = Field(
        default="kruchten",
        description="Classification framework"
    )
    examples: str = Field(
        default="~/.adrminer/examples/kruchten_examples.json",
        description="Path to examples JSON file"
    )
    use_examples: bool = Field(
        default=True,
        description="Whether to use examples (few-shot)"
    )


class CheckConfig(BaseModel):
    """Check service configuration."""
    
    template: str = Field(
        default="madr",
        description="Template to check against"
    )
    model: str = Field(
        default="gpt-4.1-mini",
        description="LLM model for checking"
    )


class OutputConfig(BaseModel):
    """Output configuration."""
    
    format: Literal["json-sidecar", "consolidated-json", "markdown"] = Field(
        default="json-sidecar",
        description="Output format"
    )
    parallel: bool = Field(
        default=True,
        description="Enable parallel processing"
    )
    verbose: bool = Field(
        default=False,
        description="Verbose output"
    )


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ADRMINER_",
        extra="allow"
    )
    
    # LLM Configuration
    llm: LLMConfig = Field(default_factory=LLMConfig)
    
    # Topic Model Configuration
    topic_model: TopicModelConfig = Field(default_factory=TopicModelConfig)
    
    # Classification Configuration
    classification: ClassificationConfig = Field(default_factory=ClassificationConfig)
    
    # Check Configuration
    check: CheckConfig = Field(default_factory=CheckConfig)
    
    # Output Configuration
    output: OutputConfig = Field(default_factory=OutputConfig)
    
    # Path to config file (for reference)
    config_path: Optional[Path] = None
    
    @field_validator("topic_model")
    @classmethod
    def expand_path(cls, v: TopicModelConfig) -> TopicModelConfig:
        """Expand user home directory in path."""
        v.path = str(Path(v.path).expanduser())
        return v
    
    @field_validator("classification")
    @classmethod
    def expand_examples_path(cls, v: ClassificationConfig) -> ClassificationConfig:
        """Expand user home directory in examples path."""
        v.examples = str(Path(v.examples).expanduser())
        return v


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(config_path: Optional[Path] = None) -> Settings:
    """
    Get or create settings instance.
    
    Args:
        config_path: Path to YAML config file (optional)
    
    Returns:
        Settings instance
    """
    global _settings
    
    if _settings is not None and config_path is None:
        return _settings
    
    # Determine config path
    if config_path is None:
        # Check for project-local config files (multiple possible names)
        config_names = [
            "adrminer.yaml",
            "adrminer.yml",
            ".adrminer.yaml",
            ".adrminer.yml",
            "config.yaml",
            "config.yml"
        ]
        
        for config_name in config_names:
            local_config = Path.cwd() / config_name
            if local_config.exists():
                config_path = local_config
                break
        
        # If no local config found, check global config
        if config_path is None:
            global_config = Path.home() / ".adrminer.yaml"
            if global_config.exists():
                config_path = global_config
    
    # If config_path exists, load from YAML
    if config_path is not None and config_path.exists():
        import yaml
        
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
        
        _settings = Settings(**config_data)
        _settings.config_path = config_path
    else:
        # Use default settings
        _settings = Settings()
        _settings.config_path = None
    
    return _settings


def reset_settings():
    """Reset global settings instance (for testing)."""
    global _settings
    _settings = None