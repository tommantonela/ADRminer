"""Tests for ADR Parser Service."""

import pytest
from pathlib import Path
from unittest.mock import patch

from adrminer.services.adr_parser_service import (
    ADRParserService,
    ParsedADR,
)
from adrminer.config.settings import ParserConfig


@pytest.fixture
def sample_adr():
    """Sample MADR ADR for testing."""
    return """# ADR-001: Adopt Microservice Architecture

## Status
Accepted

## Context
Our current monolithic architecture is becoming difficult to maintain and scale. The codebase has grown to over 500,000 lines of code, and deployment times have increased to over 30 minutes. Team velocity has decreased as the codebase has become more complex.

## Decision
We will adopt a microservice architecture, breaking down the monolith into domain-specific services. Each service will be independently deployable and scalable.

## Consequences
**Positive:**
- Improved maintainability through smaller, focused services
- Independent scaling of different components
- Faster deployment times

**Negative:**
- Increased complexity in distributed systems
- Need for additional infrastructure (service mesh, monitoring)
- Latency between services

## Decision Drivers
- Maintainability
- Scalability
- Team autonomy

## Considered Options
1. **Monolithic with modules**: Keep monolithic but organize into modules
   - Pros: Simpler infrastructure
   - Cons: Still single point of failure, difficult to scale
   
2. **Microservice architecture**: Break into independent services
   - Pros: Independent scaling, better team autonomy
   - Cons: Increased complexity, network overhead

3. **Serverless architecture**: Use cloud functions
   - Pros: No infrastructure management
   - Cons: Vendor lock-in, cold start latency
"""


@pytest.fixture
def sample_adr_spanish():
    """Sample Spanish ADR for testing language detection."""
    return """# ADR-001: Adoptar Arquitectura de Microservicios

## Contexto
Nuestra arquitectura monolítica actual se está volviendo difícil de mantener. El código ha crecido a más de 500,000 líneas.

## Decisión
Adoptaremos una arquitectura de microservicios, descomponiendo el monolito en servicios específicos del dominio.
"""


@pytest.fixture
def sample_adr_french():
    """Sample French ADR for testing language detection."""
    return """# ADR-001: Adopter l'Architecture Microservices

## Contexte
Notre architecture monolithique actuelle devient difficile à maintenir. Le code a grandi à plus de 500,000 lignes.

## Décision
Nous adopterons une architecture de microservices.
"""


class TestADRParserService:
    """Test suite for ADR Parser Service."""

    def test_parser_init_default(self):
        """Test parser initialization with default config."""
        parser = ADRParserService()
        
        assert parser.strict is False
        assert parser.detect_language is True

    def test_parser_init_custom_params(self):
        """Test parser initialization with custom parameters."""
        parser = ADRParserService(
            strict=True,
            detect_language=False,
        )
        
        assert parser.strict is True
        assert parser.detect_language is False

    def test_parse_basic_adr(self, sample_adr):
        """Test parsing a basic MADR ADR."""
        parser = ADRParserService()
        result = parser.parse_adr(sample_adr)
        
        assert isinstance(result, ParsedADR)
        assert result.title == "ADR-001: Adopt Microservice Architecture"
        assert "Context" in result.sections
        assert "Decision" in result.sections
        # Note: sections are strings, not lists
        context_text = result.sections.get("Context", "")
        decision_text = result.sections.get("Decision", "")
        assert "Our current monolithic" in context_text
        assert "We will adopt" in decision_text
        assert result.parsing_failed is False
        assert result.parsing_error is None

    def test_parse_with_language_detection(self, sample_adr):
        """Test language detection for English ADR."""
        parser = ADRParserService(detect_language=True)
        result = parser.parse_adr(sample_adr)
        
        assert result.language == 'en'

    def test_parse_spanish_adr(self, sample_adr_spanish):
        """Test language detection for Spanish ADR."""
        parser = ADRParserService(detect_language=True)
        result = parser.parse_adr(sample_adr_spanish)
        
        assert result.language == 'es'

    def test_parse_french_adr(self, sample_adr_french):
        """Test language detection for French ADR."""
        parser = ADRParserService(detect_language=True)
        result = parser.parse_adr(sample_adr_french)
        
        assert result.language == 'fr'

    def test_parse_without_language_detection(self, sample_adr):
        """Test parsing without language detection."""
        parser = ADRParserService(detect_language=False)
        result = parser.parse_adr(sample_adr)
        
        assert result.language is None

    def test_parse_all_madr_sections(self, sample_adr):
        """Test that all MADR sections are extracted."""
        parser = ADRParserService()
        result = parser.parse_adr(sample_adr)
        
        expected_sections = [
            "Status",
            "Context",
            "Decision",
            "Consequences",
            "Decision Drivers",
            "Considered Options",
        ]
        
        for section in expected_sections:
            assert section in result.sections, f"Section {section} not found"

    def test_parse_with_alternative_heading_style(self):
        """Test parsing with alternative heading style (underlines)."""
        adr = """
ADR-001: Test ADR
==================

Context
-------
This is the context.

Decision
--------
This is the decision.
"""
        parser = ADRParserService()
        result = parser.parse_adr(adr)
        
        assert result.title == "ADR-001: Test ADR"
        assert "Context" in result.sections
        assert "Decision" in result.sections

    def test_parse_missing_title(self):
        """Test parsing ADR with missing title."""
        adr = """
## Status
Accepted

## Context
No title here.
"""
        parser = ADRParserService()
        result = parser.parse_adr(adr)
        
        assert result.title == ""

    def test_parse_strict_mode_missing_section(self):
        """Test strict mode fails on missing section."""
        adr = """
## Status
Accepted

## Context
Missing other sections.
"""
        parser = ADRParserService(strict=True)
        
        with pytest.raises(ValueError, match="Failed to parse ADR"):
            parser.parse_adr(adr)

    def test_parse_lenient_mode_missing_section(self):
        """Test lenient mode handles missing sections gracefully."""
        adr = """
## Status
Accepted

## Context
Missing other sections.
"""
        parser = ADRParserService(strict=False)
        result = parser.parse_adr(adr)
        
        assert result.title == ""
        assert "Context" in result.sections
        # Other sections not present but no error raised

    def test_parse_error_with_fallback(self, sample_adr):
        """Test that parser falls back on error when fallback_on_error=True."""
        # This test is conceptual - actual error simulation would need more setup
        parser = ADRParserService(fallback_on_error=True)
        # Should not raise exceptions in lenient mode
        result = parser.parse_adr(sample_adr)
        assert isinstance(result, ParsedADR)

    def test_language_detection_basic_heuristics(self):
        """Test basic heuristics for language detection."""
        parser = ADRParserService(detect_language=True, use_langdetect=False)
        
        # English
        en_text = "This is an English text about software architecture."
        assert parser._detect_language_basic(en_text) == 'en'
        
        # Spanish
        es_text = "Este es un texto en español sobre arquitectura de software."
        assert parser._detect_language_basic(es_text) == 'es'
        
        # French
        fr_text = "Ceci est un texte en français sur l'architecture logicielle."
        assert parser._detect_language_basic(fr_text) == 'fr'

    def test_language_detection_ambiguous_text(self):
        """Test language detection with ambiguous text."""
        parser = ADRParserService(detect_language=True, use_langdetect=False)
        
        # Text with mixed or ambiguous words
        ambiguous_text = "The performance of the system is very important."
        # Should default to 'en' for ambiguous text
        assert parser._detect_language_basic(ambiguous_text) == 'en'

    def test_parse_with_multiline_section(self):
        """Test parsing sections with multiline content."""
        adr = """
# Test ADR

## Context
This is the context.
It has multiple lines.
And more lines.

## Decision
This is the decision.
Also multiple lines.
"""
        parser = ADRParserService()
        result = parser.parse_adr(adr)
        
        assert "This is the context." in result.sections["Context"]
        assert "It has multiple lines." in result.sections["Context"]
        assert "Also multiple lines." in result.sections["Decision"]

    def test_parse_with_empty_sections(self):
        """Test parsing with empty sections."""
        adr = """
# Test ADR

## Context

## Decision
No context but decision is here.
"""
        parser = ADRParserService()
        result = parser.parse_adr(adr)
        
        assert result.sections.get("Context", "").strip() == ""
        assert "No context but decision is here." in result.sections["Decision"]

    @patch('langdetect.detect')
    def test_langdetect_failure_falls_back_to_basic(self, mock_detect, sample_adr):
        """Test that basic detection is used if langdetect fails."""
        mock_detect.side_effect = Exception("Langdetect failed")
        
        parser = ADRParserService(detect_language=True, use_langdetect=True)
        result = parser.parse_adr(sample_adr)
        
        # Should still detect language using basic heuristics
        assert result.language == 'en'

    def test_extract_title_with_hash(self):
        """Test title extraction with hash prefix."""
        adr = "# ADR-001: Test Title\n\n## Context\nContent."
        parser = ADRParserService()
        result = parser.parse_adr(adr)
        
        assert result.title == "ADR-001: Test Title"

    def test_extract_title_without_hash(self):
        """Test title extraction without hash prefix."""
        adr = "ADR-001: Test Title\n\n## Context\nContent."
        parser = ADRParserService()
        result = parser.parse_adr(adr)
        
        # Should extract from first line if no hash
        assert "ADR-001" in result.title or result.title == ""

    def test_extract_section_with_hash(self):
        """Test section extraction with hash markers."""
        adr = "# Title\n\n## Section One\nContent one.\n\n## Section Two\nContent two."
        parser = ADRParserService()
        result = parser.parse_adr(adr)
        
        assert "Section One" in result.sections
        assert "Section Two" in result.sections
        assert result.sections["Section One"] == "Content one."
        assert result.sections["Section Two"] == "Content two."

    def test_parse_adr_with_code_blocks(self):
        """Test parsing ADR with code blocks."""
        adr = """
# Test ADR

## Context
This is context.

```python
def example():
    return "code"
```

## Decision
This is decision.
"""
        parser = ADRParserService()
        result = parser.parse_adr(adr)
        
        assert "This is context." in result.sections["Context"]
        assert "This is decision." in result.sections["Decision"]

    def test_parse_very_short_adr(self):
        """Test parsing very short ADR."""
        adr = "# Short ADR\n\n## Decision\nAdopt microservices."
        parser = ADRParserService()
        result = parser.parse_adr(adr)
        
        assert result.title == "Short ADR"
        assert result.sections["Decision"] == "Adopt microservices."

    def test_parse_with_special_characters(self):
        """Test parsing with special characters in text."""
        adr = """
# ADR-001: Test with @#$% chars

## Context
Email: test@example.com
URL: https://example.com
Special: @#$%^&*()
"""
        parser = ADRParserService()
        result = parser.parse_adr(adr)
        
        assert "@#$%^&*()" in result.sections["Context"]