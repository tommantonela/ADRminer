"""Test configuration management."""

import pytest
from pathlib import Path

from adrminer.config import Settings, get_settings, reset_settings


def test_default_settings():
    """Test default settings creation."""
    settings = Settings()
    
    assert settings.llm.provider == "openai"
    assert settings.llm.model == "gpt-4.1-mini"
    assert settings.classification.framework == "kruchten"
    assert settings.output.format == "json-sidecar"
    assert settings.output.parallel is True


def test_get_settings():
    """Test global settings instance."""
    reset_settings()
    
    settings1 = get_settings()
    settings2 = get_settings()
    
    # Should return same instance
    assert settings1 is settings2


def test_settings_with_yaml():
    """Test loading settings from YAML file."""
    import tempfile
    import yaml
    
    # Create a temporary YAML config file
    config_data = {
        "llm": {
            "provider": "anthropic",
            "model": "claude-3-haiku-20240307"
        },
        "topic_model": {
            "path": "/tmp/test_model"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = Path(f.name)
    
    try:
        # Reset settings first
        reset_settings()
        
        # Load settings from temporary file
        settings = get_settings(config_path)
        
        assert settings.llm.provider == "anthropic"
        assert settings.llm.model == "claude-3-haiku-20240307"
        assert settings.topic_model.path == "/tmp/test_model"
    finally:
        # Clean up
        config_path.unlink()
        reset_settings()


def test_llm_config_validation():
    """Test LLM configuration validation."""
    settings = Settings()
    
    assert settings.llm.temperature >= 0.0
    assert settings.llm.temperature <= 2.0
    assert settings.llm.max_tokens > 0


def test_topic_model_config():
    """Test topic model configuration."""
    settings = Settings()
    
    assert "topic_model" in settings.topic_model.path
    assert "MiniLM" in settings.topic_model.embedding_model


def test_classification_config():
    """Test classification configuration."""
    settings = Settings()
    
    assert settings.classification.framework in ["kruchten", "quality_attributes", "zimmermann"]
    assert isinstance(settings.classification.use_examples, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])