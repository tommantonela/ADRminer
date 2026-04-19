"""Test topic service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from pathlib import Path


@pytest.fixture
def mock_bertopic_model():
    """Create a mock BERTopic model."""
    model = Mock()
    
    # Mock get_topic_info
    topic_info_df = pd.DataFrame({
        "Topic": [0, 1, -1],
        "Name": ["Database Migration", "API Design", "Outlier"],
        "Count": [10, 5, 2],
    })
    model.get_topic_info = Mock(return_value=topic_info_df)
    
    # Mock transform
    model.transform = Mock(return_value=([0, 1, -1], [0.85, 0.75, 0.10]))
    
    # Mock get_topic
    def mock_get_topic(topic_id):
        if topic_id == 0:
            return [("database", 0.9), ("migration", 0.8), ("schema", 0.7)][:5]
        elif topic_id == 1:
            return [("api", 0.85), ("design", 0.8), ("rest", 0.75)][:5]
        return []
    
    model.get_topic = Mock(side_effect=mock_get_topic)
    
    return model


@pytest.fixture
def mock_settings(tmp_path):
    """Create mock settings with temporary model path."""
    from adrminer.config import Settings
    
    # Create a temporary model directory
    model_dir = tmp_path / "models" / "topic_model"
    model_dir.mkdir(parents=True)
    
    settings = Settings()
    settings.topic_model.path = str(model_dir)
    
    return settings


def test_topic_service_init(mock_bertopic_model, mock_settings, tmp_path):
    """Test topic service initialization."""
    from adrminer.services import TopicService
    
    # Create a dummy model file to bypass FileNotFoundError
    model_path = Path(mock_settings.topic_model.path)
    (model_path / "dummy").touch()
    
    with patch('adrminer.services.topic_service.BERTopic.load', return_value=mock_bertopic_model):
        service = TopicService(settings=mock_settings)
        assert service.model is not None


def test_topic_service_predict(mock_bertopic_model, mock_settings, tmp_path):
    """Test single ADR prediction."""
    from adrminer.services import TopicService
    
    # Create a dummy model file
    model_path = Path(mock_settings.topic_model.path)
    (model_path / "dummy").touch()
    
    with patch('adrminer.services.topic_service.BERTopic.load', return_value=mock_bertopic_model):
        service = TopicService(settings=mock_settings)
        text = "This is about database migration and schema changes."
        
        result = service.predict(text)
        
        assert "topic_id" in result
        assert "topic_label" in result
        assert "probability" in result
        assert "keywords" in result
        assert result["topic_id"] == 0


def test_topic_service_predict_batch(mock_bertopic_model, mock_settings, tmp_path):
    """Test batch prediction."""
    from adrminer.services import TopicService
    
    # Create a dummy model file
    model_path = Path(mock_settings.topic_model.path)
    (model_path / "dummy").touch()
    
    with patch('adrminer.services.topic_service.BERTopic.load', return_value=mock_bertopic_model):
        service = TopicService(settings=mock_settings)
        texts = [
            "Database migration strategy.",
            "API design decisions.",
            "Outlier content.",
        ]
        
        results = service.predict_batch(texts)
        
        assert len(results) == 3
        assert all("topic_id" in r for r in results)
        assert all("topic_label" in r for r in results)


def test_topic_service_distribution(mock_bertopic_model, mock_settings, tmp_path):
    """Test topic distribution calculation."""
    from adrminer.services import TopicService
    
    # Create a dummy model file
    model_path = Path(mock_settings.topic_model.path)
    (model_path / "dummy").touch()
    
    with patch('adrminer.services.topic_service.BERTopic.load', return_value=mock_bertopic_model):
        service = TopicService(settings=mock_settings)
        
        # Mock results
        results = [
            {"topic_id": 0, "topic_label": "Database Migration", "probability": 0.85},
            {"topic_id": 0, "topic_label": "Database Migration", "probability": 0.90},
            {"topic_id": 1, "topic_label": "API Design", "probability": 0.75},
        ]
        
        distribution = service.get_topic_distribution(results)
        
        assert distribution["total_adrs"] == 3
        assert distribution["unique_topics"] == 2
        assert "Database Migration" in distribution["distribution"]
        assert "API Design" in distribution["distribution"]


def test_topic_service_info(mock_bertopic_model, mock_settings, tmp_path):
    """Test getting topic information."""
    from adrminer.services import TopicService
    
    # Create a dummy model file
    model_path = Path(mock_settings.topic_model.path)
    (model_path / "dummy").touch()
    
    with patch('adrminer.services.topic_service.BERTopic.load', return_value=mock_bertopic_model):
        service = TopicService(settings=mock_settings)
        
        info = service.get_topic_info(0)
        
        assert info["topic_id"] == 0
        assert "name" in info
        assert "count" in info
        assert "representation" in info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])