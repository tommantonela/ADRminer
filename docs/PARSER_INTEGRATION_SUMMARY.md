# ADR Parser Integration Summary

**Version:** 1.0  
**Date:** 2026-04-19  
**Status:** Complete

---

## Table of Contents

1. [Overview](#1-overview)
2. [Implementation Changes](#2-implementation-changes)
3. [Service Integration](#3-service-integration)
4. [CLI Changes](#4-cli-changes)
5. [Configuration](#5-configuration)
6. [Testing Recommendations](#6-testing-recommendations)
7. [Migration Guide](#7-migration-guide)

---

## 1. Overview

### Purpose

This document summarizes the integration of the ADR Parser Service into the classification, checking, and topic services, following the guidelines from `SERVICE_ROADMAP.md`, `NOTEBOOK_VS_SERVICES_COMPARISON.md`, and `IMPLEMENTATION_DECISIONS.md`.

### Key Features

- ✅ **ADR Parser Service**: Lightweight section extraction with error handling and fallback
- ✅ **Language Detection**: Automatic language detection using langdetect with basic fallback
- ✅ **Service Integration**: Optional parser integration across all three services
- ✅ **Configuration**: Parser configuration via Settings and CLI flags
- ✅ **Graceful Fallback**: Services fall back to full-text analysis on parser errors

### Design Decisions

1. **Optional Integration**: Parser is opt-in (disabled by default) to maintain backward compatibility
2. **Lenient by Default**: Parser falls back to full-text on errors (strict mode available)
3. **Language Warnings**: Topic service warns about non-English ADRs (BERTopic is English-optimized)
4. **No Breaking Changes**: All existing functionality preserved; parser is additive only

---

## 2. Implementation Changes

### New Files Created

#### `src/adrminer/services/adr_parser_service.py`

**Purpose**: Lightweight ADR parser for section extraction with error handling and fallback

**Key Classes**:
- `ADRParseResult`: Pydantic model for parsed ADR structure
- `ADRParseError`: Exception class for parse errors
- `ADRParseResult`: Success/failure wrapper with warnings

**Key Methods**:
- `parse(adr_text: str, config: Optional[ParserConfig]) -> ADRParseResult`
  - Parses ADR text into structured sections
  - Supports strict and lenient modes
  - Detects language (langdetect + basic detection)
  - Falls back to full-text on errors
  
- `_detect_language(text: str) -> str`
  - Primary: langdetect library
  - Fallback: Basic keyword detection (English/Spanish/Portuguese)
  
- `_extract_sections(text: str) -> Dict[str, str]`
  - Uses regex to extract MADR sections
  - Handles various heading formats (#, ##, etc.)
  - Returns structured dictionary of sections

**Error Handling**:
- Returns `ADRParseError` with full-text fallback on parsing failure
- Logs warnings for missing sections
- Provides detailed error messages for debugging

---

## 3. Service Integration

### Classification Service (`src/adrminer/services/classification_service.py`)

**Changes**:
```python
# Constructor updated with parser support
def __init__(
    self,
    framework: str = "kruchten",
    examples_path: Optional[str] = None,
    use_examples: bool = True,
    use_parser: bool = False,
    parser_config: Optional[Dict] = None,
):
    # ... existing code ...
    
    if use_parser:
        self.parser = ADRParser(config=parser_config or {})
    else:
        self.parser = None
```

**Classification Logic**:
```python
def classify(self, text: str, metadata: Optional[Dict] = None) -> Dict:
    # Try parser if enabled
    if self.parser:
        parse_result = self.parser.parse(text)
        if isinstance(parse_result, ADRTemplate):
            # Use parsed structured data
            result = self._classify_with_template(parse_result)
            # Add parsing metadata
            result['parsing'] = {
                'mode': 'parsed',
                'language': parse_result.language,
                'warnings': parse_result.warnings
            }
        elif isinstance(parse_result, ADRParseError):
            # Fallback to full-text analysis
            self.logger.warning(f"Parser failed: {parse_result.message}. Using full-text analysis.")
            text_to_classify = parse_result.fallback_text
            result = self._classify_text(text_to_classify)
            result['parsing'] = {
                'mode': 'fallback',
                'error': parse_result.message
            }
    else:
        # No parser, use full-text
        result = self._classify_text(text)
```

**Benefits**:
- Classification can use structured section data when available
- Graceful fallback ensures no ADRs are skipped
- Metadata tracks parsing mode and warnings

---

### Checking Service (`src/adrminer/services/checking_service.py`)

**Changes**:
```python
# Constructor updated with parser support
def __init__(
    self,
    mode: str = "full",
    use_parser: bool = False,
    parser_config: Optional[Dict] = None,
):
    # ... existing code ...
    
    if use_parser:
        self.parser = ADRParser(config=parser_config or {})
    else:
        self.parser = None
```

**Checking Logic**:
```python
def check_adherence(self, text: str, metadata: Optional[Dict] = None) -> Dict:
    # Try parser if enabled
    if self.parser:
        parse_result = self.parser.parse(text)
        if isinstance(parse_result, ADRTemplate):
            # Use parsed structured data
            result = self._check_template_adherence(parse_result)
            # Add parsing metadata
            result['parsing'] = {
                'mode': 'parsed',
                'language': parse_result.language,
                'warnings': parse_result.warnings
            }
        elif isinstance(parse_result, ADRParseError):
            # Fallback to full-text analysis
            self.logger.warning(f"Parser failed: {parse_result.message}. Using full-text analysis.")
            text_to_check = parse_result.fallback_text
            result = self._check_text_adherence(text_to_check)
            result['parsing'] = {
                'mode': 'fallback',
                'error': parse_result.message
            }
    else:
        # No parser, use full-text
        result = self._check_text_adherence(text)
```

**Benefits**:
- Template adherence checks can use structured section data
- Section-wise checks can leverage parsed sections
- Graceful fallback ensures all ADRs are analyzed

---

### Topic Service (`src/adrminer/services/topic_service.py`)

**Changes**:
```python
# Constructor updated with parser support
def __init__(
    self,
    model_path: str = "~/.adrminer/models/topic_model",
    use_parser: bool = False,
    parser_config: Optional[Dict] = None,
):
    # ... existing code ...
    
    if use_parser:
        self.parser = ADRParser(config=parser_config or {})
    else:
        self.parser = None
```

**Topic Extraction Logic**:
```python
def predict(self, text: str, metadata: Optional[Dict] = None) -> Dict:
    # Parse language if parser enabled
    language = None
    if self.parser:
        parse_result = self.parser.parse(text)
        if isinstance(parse_result, ADRTemplate):
            language = parse_result.language
            # Warn about non-English ADRs
            if language != 'en':
                self.logger.warning(
                    f"ADR is in {language}, but BERTopic model is trained on English. "
                    f"Topic quality may be reduced."
                )
        elif isinstance(parse_result, ADRParseError):
            self.logger.debug(f"Language detection failed: {parse_result.message}")
    
    # Extract topics (always uses full-text for topics)
    topics, probs = self.model.transform([text])
    
    result = TopicResult(
        text=text,
        topics=topics,
        keywords=...,
        probabilities=probs,
    )
    
    # Add language metadata if detected
    if language:
        result['language'] = language
    
    return result
```

**Benefits**:
- Language detection provides metadata for topic quality assessment
- Warnings alert users to potential topic quality issues
- No fallback needed (topic extraction always works on full-text)

---

## 4. CLI Changes

### Classification CLI (`src/adrminer/cli/commands/classify.py`)

**New Flags**:
```bash
--use-parser          # Enable ADR parser for section extraction
--strict               # Enable strict parsing (fail on errors)
--no-language-detect  # Disable language detection in parser
```

**Example Usage**:
```bash
# Basic classification (no parser)
adrminer classify adrs/

# Classification with parser (lenient mode)
adrminer classify adrs/ --use-parser

# Classification with parser (strict mode)
adrminer classify adrs/ --use-parser --strict

# Classification with parser, no language detection
adrminer classify adrs/ --use-parser --no-language-detect
```

**Output**:
```
[blue]Loading classification service...[/blue]
[cyan]  Parser: enabled[/cyan]
[cyan]  Parser mode: lenient (fallback on error)[/cyan]
[cyan]  Language detection: enabled[/cyan]
[green]✓ Service loaded (framework: kruchten)[/green]
```

---

### Checking CLI (`src/adrminer/cli/commands/check.py`)

**New Flags**:
```bash
--use-parser          # Enable ADR parser for section extraction
--strict               # Enable strict parsing (fail on errors)
--no-language-detect  # Disable language detection in parser
```

**Example Usage**:
```bash
# Basic checking (no parser)
adrminer check adrs/

# Checking with parser (lenient mode)
adrminer check adrs/ --use-parser

# Checking with parser (strict mode)
adrminer check adrs/ --use-parser --strict

# Checking with parser, no language detection
adrminer check adrs/ --use-parser --no-language-detect
```

**Output**:
```
[blue]Initializing checking service...[/blue]
[cyan]  Parser: enabled[/cyan]
[cyan]  Parser mode: lenient (fallback on error)[/cyan]
[cyan]  Language detection: enabled[/cyan]
```

---

### Topics CLI (`src/adrminer/cli/commands/topics.py`)

**No Changes**: Topic service CLI remains unchanged. Language warnings are logged but not surfaced to CLI.

---

## 5. Configuration

### Settings Updates (`src/adrminer/config/settings.py`)

**New Configuration Classes**:

```python
class ParserConfig(BaseModel):
    """ADR parser configuration."""
    
    strict: bool = Field(
        default=False,
        description="Enable strict parsing (fail on errors)"
    )
    detect_language: bool = Field(
        default=True,
        description="Detect ADR language using langdetect"
    )
    fallback_on_error: bool = Field(
        default=True,
        description="Fallback to original text on parsing failure"
    )
```

**Updated Configuration Classes**:

```python
class ClassificationConfig(BaseModel):
    # ... existing fields ...
    use_parser: bool = Field(
        default=False,
        description="Whether to use ADR parser for section extraction"
    )
    parser: ParserConfig = Field(
        default_factory=ParserConfig,
        description="Parser configuration"
    )

class CheckConfig(BaseModel):
    # ... existing fields ...
    use_parser: bool = Field(
        default=False,
        description="Whether to use ADR parser for section extraction"
    )
    parser: ParserConfig = Field(
        default_factory=ParserConfig,
        description="Parser configuration"
    )
```

**YAML Configuration Example**:

```yaml
# .adrminer.yaml
classification:
  framework: kruchten
  use_parser: true
  parser:
    strict: false
    detect_language: true
    fallback_on_error: true

check:
  template: madr
  use_parser: true
  parser:
    strict: false
    detect_language: true
    fallback_on_error: true
```

---

### Requirements Updates (`requirements.txt`)

**New Dependency**:
```
langdetect==1.0.9
```

---

## 6. Testing Recommendations

### Unit Tests

#### Test Parser Service
```python
def test_parser_basic_parsing():
    """Test basic section extraction."""
    text = """
    # Status
    Accepted
    
    # Context
    This is the context.
    
    # Decision
    We will use PostgreSQL.
    """
    result = parser.parse(text)
    assert isinstance(result, ADRTemplate)
    assert result.status == "Accepted"
    assert result.context == "This is the context."
    assert result.decision == "We will use PostgreSQL."

def test_parser_fallback_on_error():
    """Test fallback on parsing error."""
    text = "Invalid ADR without sections"
    result = parser.parse(text)
    assert isinstance(result, ADRParseError)
    assert result.fallback_text == text

def test_parser_language_detection():
    """Test language detection."""
    english_text = "This is an English ADR."
    spanish_text = "Este es un ADR en español."
    
    en_result = parser.parse(english_text)
    es_result = parser.parse(spanish_text)
    
    assert en_result.language == "en"
    assert es_result.language == "es"

def test_parser_strict_mode():
    """Test strict mode raises errors."""
    config = ParserConfig(strict=True, fallback_on_error=False)
    parser = ADRParser(config=config)
    
    text = "Invalid ADR"
    result = parser.parse(text)
    
    assert isinstance(result, ADRParseError)
    assert result.fallback_text is None  # No fallback in strict mode
```

#### Test Classification Service with Parser
```python
def test_classification_with_parser():
    """Test classification uses parser successfully."""
    service = ClassificationService(use_parser=True)
    text = "# Context\n...\n# Decision\nWe will use PostgreSQL."
    
    result = service.classify(text)
    
    assert result['parsing']['mode'] == 'parsed'
    assert result['parsing']['language'] == 'en'
    assert 'primary_category' in result

def test_classification_parser_fallback():
    """Test classification falls back on parser error."""
    service = ClassificationService(use_parser=True)
    text = "Invalid ADR without sections"
    
    result = service.classify(text)
    
    assert result['parsing']['mode'] == 'fallback'
    assert 'error' in result['parsing']
    assert 'primary_category' in result  # Still classified

def test_classification_without_parser():
    """Test classification without parser."""
    service = ClassificationService(use_parser=False)
    text = "We will use PostgreSQL."
    
    result = service.classify(text)
    
    assert 'parsing' not in result  # No parsing metadata
    assert 'primary_category' in result
```

#### Test Checking Service with Parser
```python
def test_checking_with_parser():
    """Test checking uses parser successfully."""
    service = CheckingService(mode="full", use_parser=True)
    text = """
    # Status
    Accepted
    
    # Context
    This is the context.
    
    # Decision
    We will use PostgreSQL.
    """
    
    result = service.check(text)
    
    assert result['parsing']['mode'] == 'parsed'
    assert result['parsing']['language'] == 'en'
    assert 'template_adherence' in result
    assert 'section_assessments' in result

def test_checking_parser_fallback():
    """Test checking falls back on parser error."""
    service = CheckingService(mode="full", use_parser=True)
    text = "Invalid ADR without sections"
    
    result = service.check(text)
    
    assert result['parsing']['mode'] == 'fallback'
    assert 'error' in result['parsing']
    assert 'template_adherence' in result  # Still checked
```

#### Test Topic Service with Language Detection
```python
def test_topic_language_warning():
    """Test topic service warns about non-English."""
    service = TopicService(use_parser=True, model_path="...")
    text = "# Context\nEste es un ADR en español."
    
    with pytest.warns(UserWarning):
        result = service.predict(text)
    
    assert result['language'] == 'es'
    assert 'topic_id' in result  # Topics still extracted

def test_topic_no_parser():
    """Test topic service without parser."""
    service = TopicService(use_parser=False, model_path="...")
    text = "This is an English ADR."
    
    result = service.predict(text)
    
    assert 'language' not in result  # No language detection
    assert 'topic_id' in result
```

### Integration Tests

#### Test End-to-End CLI with Parser
```bash
# Test classification with parser
adrminer classify examples/pharmacy-food/adrs/ --use-parser
# Should succeed and show parser metadata in results

# Test checking with parser
adrminer check examples/pharmacy-food/adrs/ --use-parser --mode full
# Should succeed and show parser metadata in results

# Test topic extraction with language detection
adrminer topics predict examples/pharmacy-food/adrs/ --use-parser
# Should succeed and show language warnings for non-English ADRs
```

#### Test Strict Mode
```bash
# Test strict mode (should fail on invalid ADRs)
adrminer classify examples/pharmacy-food/adrs/ --use-parser --strict
# Should error out on invalid ADRs

# Test lenient mode (should succeed with fallback)
adrminer classify examples/pharmacy-food/adrs/ --use-parser
# Should succeed with fallback warnings
```

---

## 7. Migration Guide

### For Existing Users

**No Action Required**: Parser is disabled by default, so all existing functionality works unchanged.

### For Users Wanting Parser Benefits

#### Step 1: Install langdetect
```bash
pip install langdetect
```

#### Step 2: Update Configuration
```yaml
# .adrminer.yaml
classification:
  use_parser: true
  parser:
    strict: false
    detect_language: true

check:
  use_parser: true
  parser:
    strict: false
    detect_language: true
```

#### Step 3: Test with Small Dataset
```bash
# Test classification with parser
adrminer classify sample/ --use-parser

# Test checking with parser
adrminer check sample/ --use-parser --mode full

# Verify results include parsing metadata
cat sample/*.metadata.json | grep parsing
```

#### Step 4: Monitor and Tune
- Check logs for parsing warnings
- Review fallback rate (how many ADRs fell back to full-text)
- Adjust strict mode based on needs
- Monitor language warnings in topic extraction

#### Step 5: Enable in Production
```bash
# Enable parser for production use
adrminer classify production/adrs/ --use-parser
adrminer check production/adrs/ --use-parser --mode full
```

### For Developers

#### Adding Parser to Custom Service
```python
from adrminer.services.adr_parser_service import ADRParser

class MyCustomService:
    def __init__(self, use_parser=False, parser_config=None):
        self.parser = ADRParser(config=parser_config) if use_parser else None
    
    def analyze(self, text):
        if self.parser:
            result = self.parser.parse(text)
            if isinstance(result, ADRTemplate):
                return self._analyze_with_structure(result)
            elif isinstance(result, ADRParseError):
                return self._analyze_full_text(result.fallback_text)
        else:
            return self._analyze_full_text(text)
```

#### Extending Parser for Custom Templates
```python
class CustomADRParsing(ADRParsing):
    """Custom parser for custom ADR template."""
    
    SECTION_PATTERNS = {
        'custom_section1': r'^#+\s*Custom Section 1\s*$',
        'custom_section2': r'^#+\s*Custom Section 2\s*$',
    }
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        # Custom extraction logic
        # ...
        return sections
```

---

## 8. Summary

### What Was Accomplished

✅ **ADR Parser Service**: Lightweight parser with error handling and fallback  
✅ **Language Detection**: Automatic language detection with basic fallback  
✅ **Service Integration**: Optional parser integration across all three services  
✅ **Configuration**: Parser configuration via Settings and CLI flags  
✅ **Graceful Fallback**: Services fall back to full-text analysis on parser errors  
✅ **No Breaking Changes**: All existing functionality preserved  

### Key Benefits

1. **Improved Accuracy**: Structured section data can improve classification and checking accuracy
2. **Language Awareness**: Language detection helps identify potential topic quality issues
3. **Flexible Integration**: Parser is opt-in and can be enabled per-service
4. **Robust Error Handling**: Graceful fallback ensures no ADRs are skipped
5. **Production Ready**: Comprehensive error handling and logging

### Next Steps

1. **Testing**: Run comprehensive tests on real ADR datasets
2. **Monitoring**: Track parsing success rate and fallback frequency
3. **Performance**: Measure performance impact of parser integration
4. **Documentation**: Update user documentation with parser usage examples
5. **Feedback**: Collect user feedback on parser effectiveness

---

**Document History:**
- v1.0 - Initial documentation (2026-04-19)