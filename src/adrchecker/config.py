"""Configuration for the ADR Checker service using environment variables.

Settings are loaded from environment variables (or a `.env` file) with the
`ADRCHECKER_` prefix.
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-based configuration for the ADR Checker.

    All values can be overridden via environment variables prefixed with
    `ADRCHECKER_` (e.g., `ADRCHECKER_MODEL`, `ADRCHECKER_OPENAI_API_KEY`)
    or via a `.env` file. As a fallback, ``OPENAI_API_KEY`` is used if
    ``ADRCHECKER_OPENAI_API_KEY`` is not set.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ADRCHECKER_",
        extra="ignore",
    )

    # LLM configuration
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None

    def resolved_api_key(self) -> Optional[str]:
        """Return the best available API key.

        Prefers ``ADRCHECKER_OPENAI_API_KEY`` and falls back to
        ``OPENAI_API_KEY`` so the tool works out of the box when the
        standard OpenAI key is already in the environment.
        """
        return self.openai_api_key or os.getenv("OPENAI_API_KEY")

    # Checking defaults
    default_mode: str = "full"  # "full", "adherence", or "sections"
    parallel: bool = True


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global Settings instance.

    Returns:
        Settings instance loaded from environment / .env file.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset the global settings instance (useful for testing)."""
    global _settings
    _settings = None