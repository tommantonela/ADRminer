"""LLM factory using LangChain's init_chat_model()."""

from typing import Optional

from langchain.chat_models.base import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from adrminer.config import get_settings, Settings


# Global LLM cache
_llm_cache: Optional[BaseChatModel] = None


def create_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    settings: Optional[Settings] = None,
) -> BaseChatModel:
    """
    Create an LLM instance using LangChain's init_chat_model().
    
    Args:
        provider: LLM provider (openai, anthropic, ollama, azure, google)
        model: Model name (e.g., gpt-4.1-mini, claude-3-sonnet)
        temperature: Temperature for generation (0.0 to 2.0)
        max_tokens: Maximum tokens to generate
        settings: Settings instance (uses global if not provided)
    
    Returns:
        BaseChatModel instance
    
    Raises:
        ValueError: If provider or model is invalid
        ImportError: If required dependencies are missing
    """
    if settings is None:
        settings = get_settings()
    
    # Use settings values if not explicitly provided
    llm_provider = provider or settings.llm.provider
    llm_model = model or settings.llm.model
    llm_temperature = temperature if temperature is not None else settings.llm.temperature
    llm_max_tokens = max_tokens if max_tokens is not None else settings.llm.max_tokens
    
    # Validate provider
    valid_providers = ["openai", "anthropic", "ollama", "azure", "google"]
    if llm_provider not in valid_providers:
        raise ValueError(
            f"Invalid LLM provider: {llm_provider}. "
            f"Valid providers: {', '.join(valid_providers)}"
        )
    
    # Create LLM using LangChain's factory function
    try:
        llm = init_chat_model(
            model=llm_model,
            temperature=llm_temperature,
            max_tokens=llm_max_tokens,
        )
        return llm
    except ImportError as e:
        raise ImportError(
            f"Missing dependencies for {llm_provider} provider: {e}. "
            f"Install required package: pip install adrminer[{llm_provider}]"
        ) from e
    except Exception as e:
        raise ValueError(
            f"Failed to create LLM: {e}. "
            f"Check your API keys and model configuration."
        ) from e


def get_llm(
    settings: Optional[Settings] = None,
    force_refresh: bool = False,
) -> BaseChatModel:
    """
    Get cached LLM instance or create new one.
    
    Args:
        settings: Settings instance (uses global if not provided)
        force_refresh: Force recreation of LLM even if cached
    
    Returns:
        BaseChatModel instance
    """
    global _llm_cache
    
    if _llm_cache is None or force_refresh:
        _llm_cache = create_llm(settings=settings)
    
    return _llm_cache


def reset_llm_cache():
    """Reset cached LLM instance (for testing)."""
    global _llm_cache
    _llm_cache = None