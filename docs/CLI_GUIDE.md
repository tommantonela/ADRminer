# ADRminer CLI Guide

**Version:** 1.0  
**Date:** 2026-04-18  
**Status:** Planning Phase

---

## Table of Contents

1. [Installation](#1-installation)
2. [Getting Started](#2-getting-started)
3. [Configuration](#3-configuration)
4. [Command Reference](#4-command-reference)
5. [Common Workflows](#5-common-workflows)
6. [Output Formats](#6-output-formats)
7. [Error Handling](#7-error-handling)
8. [Advanced Usage](#8-advanced-usage)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Installation

### 1.1 Install from PyPI (Recommended)

```bash
pip install adrminer
```

### 1.2 Install from Source (Development)

```bash
git clone https://github.com/tommantonela/ADRminer.git
cd ADRminer
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -e ".[dev,tui]"
```

### 1.3 Verify Installation

```bash
adrminer --version
adrminer --help
```

**Expected Output:**
```
╭──────────────────────────────────╮
│ ADRminer v0.1.0               │
│ Analyze your ADRs              │
╰──────────────────────────────────╯
```

---

## 2. Getting Started

### 2.1 Initialize Configuration

First-time users should run the init command:

```bash
adrminer init
```

This creates:
- `.env` file for API keys
- `.adrminer.yaml` for configuration
- Validates default model availability

### 2.2 Quick Start Example

```bash
# Analyze a single ADR
adrminer topics predict adr-001.md

# Analyze a directory of ADRs
adrminer classify predict ./adrs/ --framework kruchten --parallel

# Combined analysis
adrminer analyze ./adrs/ --topics --classify kruchten --check
```

---

## 3. Configuration

### 3.1 Environment Variables (.env)

Create a `.env` file in your project directory or home directory:

```bash
# LLM Provider Keys
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# Optional: Override default paths
TOPIC_MODEL_PATH=/custom/path/to/model
CLASSIFICATION_EXAMPLES=/custom/examples.json
```

### 3.2 YAML Configuration (.adrminer.yaml)

Default configuration location: `~/.adrminer.yaml`

```yaml
# LLM Configuration
llm:
  provider: openai  # openai, anthropic, ollama, azure, google
  model: gpt-4o-mini
  temperature: 0.0
  max_tokens: 2000

# Topic Model Configuration
topic_model:
  path: ~/.adrminer/models/topic_model
  embedding_model: all-MiniLM-L6-v2
  n_topics: auto

# Classification Configuration
classification:
  framework: kruchten  # kruchten, quality_attributes, zimmermann
  examples: ~/.adrminer/examples/kruchten_examples.json
  use_examples: true

# Check Service Configuration
check:
  template: madr
  model: gpt-4o-mini

# Output Configuration
output:
  format: json-sidecar  # json-sidecar, consolidated-json, markdown
  parallel: true
  verbose: false
```

### 3.3 Custom Configuration Location

```bash
adrminer --config /path/to/config.yaml topics predict adr-001.md
```

---

## 4. Command Reference

### 4.1 Main Commands

```bash
adrminer [OPTIONS] COMMAND [ARGS]...

Options:
  --config, -c    Path to configuration file
  --verbose, -v    Verbose output
  --version        Show version and exit
  --help          Show help message

Commands:
  init         Initialize ADRminer configuration
  topics        Topic mining with BERTopic
  classify      Classify ADRs using LLM
  check         Check ADR quality and template adherence
  analyze       Run combined analysis
  export        Export results and reports
  model         Model management
```

### 4.2 init Command

Initialize ADRminer configuration.

```bash
adrminer init [OPTIONS]

Options:
  --interactive, -i    Interactive configuration
  --config, -c         Configuration file path
  --verbose, -v         Verbose output
```

**Example:**
```bash
adrminer init --interactive
```

### 4.3 topics Command

Topic mining with BERTopic.

#### 4.3.1 topics predict

Predict topics for ADR(s).

```bash
adrminer topics predict [OPTIONS] INPUT

Arguments:
  INPUT    ADR file or directory

Options:
  --model, -m           Path to topic model
  --output, -o          Output JSON file path
  --parallel, -p        Enable parallel processing
  --threshold, -t        Topic probability threshold (default: 0.0)
  --multiple             Allow multiple topics per ADR
  --verbose, -v          Verbose output
```

**Examples:**
```bash
# Single ADR
adrminer topics predict adr-001.md

# Directory with parallel processing
adrminer topics predict ./adrs/ --parallel

# Custom model with threshold
adrminer topics predict ./adrs/ --model ./models/custom --threshold 0.5

# Multiple topics
adrminer topics predict adr-001.md --multiple
```

#### 4.3.2 topics train

Train new topic model.

```bash
adrminer topics train [OPTIONS] INPUT OUTPUT

Arguments:
  INPUT     Directory with ADR files for training
  OUTPUT    Output model directory

Options:
  --n-topics, -n         Number of topics (default: auto)
  --embedding, -e        Embedding model (default: all-MiniLM-L6-v2)
  --openai               Use OpenAI for topic labels
  --verbose, -v          Verbose output
```

**Example:**
```bash
adrminer topics train ./training_data/ ./models/custom --n-topics 15
```

#### 4.3.3 topics list

List available topic models.

```bash
adrminer topics list
```

#### 4.3.4 topics info

Show model details.

```bash
adrminer topics info MODEL_NAME

Arguments:
  MODEL_NAME    Model name or path
```

**Example:**
```bash
adrminer topics info topic-model-v1.0
```

### 4.4 classify Command

Classify ADRs using LLM.

#### 4.4.1 classify predict

Classify ADR(s) using specified framework.

```bash
adrminer classify predict [OPTIONS] INPUT

Arguments:
  INPUT    ADR file or directory

Options:
  --framework, -f        Classification framework (kruchten, quality_attributes, zimmermann)
  --examples, -e         Path to custom examples JSON file
  --no-examples          Zero-shot classification (no examples)
  --parallel, -p         Enable parallel processing
  --output, -o           Output JSON file path
  --verbose, -v           Verbose output
```

**Examples:**
```bash
# Kruchten framework
adrminer classify predict adr-001.md --framework kruchten

# Quality Attributes framework
adrminer classify predict ./adrs/ --framework quality_attributes --parallel

# Zero-shot classification
adrminer classify predict adr-001.md --framework zimmermann --no-examples

# Custom examples
adrminer classify predict ./adrs/ --examples /path/to/custom.json
```

#### 4.4.2 classify list

List supported frameworks.

```bash
adrminer classify list
```

#### 4.4.3 classify examples

Show available example sets.

```bash
adrminer classify examples
```

### 4.5 check Command

Check ADR quality and template adherence.

#### 4.5.1 check predict

Check ADR quality.

```bash
adrminer check predict [OPTIONS] INPUT

Arguments:
  INPUT    ADR file or directory

Options:
  --template, -t         Template to check against (default: madr)
  --sections              Run section-wise analysis
  --parallel, -p          Enable parallel processing
  --output, -o            Output JSON file path
  --verbose, -v            Verbose output
```

**Examples:**
```bash
# Single ADR
adrminer check predict adr-001.md

# Directory with parallel processing
adrminer check predict ./adrs/ --parallel

# Section-wise analysis
adrminer check predict adr-001.md --sections

# Custom template
adrminer check predict adr-001.md --template custom_template.yaml
```

#### 4.5.2 check templates

List supported templates.

```bash
adrminer check templates
```

### 4.6 analyze Command

Run combined analysis.

```bash
adrminer analyze [OPTIONS] [INPUT]

Arguments:
  INPUT    ADR file or directory (default: current directory)

Options:
  --topics               Enable topic mining
  --classify, -f         Enable classification with framework
  --check                Enable quality checking
  --insights             Generate cross-service insights
  --format, -f           Output format (json-sidecar, consolidated-json, markdown)
  --output, -o           Output directory or file
  --parallel, -p         Enable parallel processing
  --verbose, -v           Verbose output
```

**Examples:**
```bash
# Run all services
adrminer analyze ./adrs/ --topics --classify kruchten --check --insights

# Use default configuration
adrminer analyze ./adrs/

# Export to consolidated JSON
adrminer analyze ./adrs/ --format consolidated-json --output ./results/summary.json

# Generate Markdown report
adrminer analyze ./adrs/ --format markdown --output ./report.md
```

### 4.7 export Command

Export results and reports.

```bash
adrminer export [OPTIONS]

Options:
  --format, -f           Output format (json-sidecar, consolidated-json, markdown)
  --type, -t             Analysis type to export (topics, classification, check, all)
  --input, -i            Input results directory
  --output, -o            Output directory or file
  --include-insights     Include generated insights
```

**Examples:**
```bash
# Export to JSON sidecars
adrminer export --format json-sidecar --input ./results/ --output ./adrs/

# Consolidated JSON export
adrminer export --format consolidated-json --input ./results/ --output ./summary.json

# Markdown report
adrminer export --format markdown --input ./results/ --output ./report.md

# Export only topics
adrminer export --type topics --format json-sidecar --input ./results/
```

### 4.8 model Command

Model management.

#### 4.8.1 model list

List available models.

```bash
adrminer model list
```

#### 4.8.2 model info

Show model details.

```bash
adrminer model info MODEL_NAME

Arguments:
  MODEL_NAME    Model name or path
```

**Example:**
```bash
adrminer model info topic-model-v1.0
```

#### 4.8.3 model validate

Validate model file integrity.

```bash
adrminer model validate [OPTIONS]

Options:
  --model, -m            Model path to validate
```

**Example:**
```bash
adrminer model validate --model ./models/custom
```

---

## 5. Common Workflows

### 5.1 First-Time Setup

```bash
# 1. Install
pip install adrminer

# 2. Initialize
adrminer init

# 3. Configure API keys in .env
# Edit ~/.adrminer/.env
OPENAI_API_KEY=sk-xxx

# 4. Test with single ADR
adrminer topics predict adr-001.md
```

### 5.2 Batch Processing

```bash
# Process entire directory
adrminer topics predict ./adrs/ --parallel --output ./results/topics.json

# Classify all ADRs
adrminer classify predict ./adrs/ --framework kruchten --parallel --output ./results/classification.json

# Check quality
adrminer check predict ./adrs/ --parallel --output ./results/checks.json
```

### 5.3 Combined Analysis

```bash
# Run all services with insights
adrminer analyze ./adrs/ \
  --topics \
  --classify kruchten \
  --check \
  --insights \
  --format json-sidecar \
  --output ./results
```

### 5.4 CI/CD Integration

```bash
#!/bin/bash
# ci-analyze-adrs.sh

set -e

# Analyze ADRs
adrminer analyze ./docs/adrs/ \
  --topics \
  --classify kruchten \
  --check \
  --format consolidated-json \
  --output ./analysis-results.json

# Check exit code
if [ $? -ne 0 ]; then
  echo "❌ ADR analysis failed"
  exit 1
fi

echo "✅ ADR analysis complete"
```

### 5.5 Custom Model Training

```bash
# 1. Prepare training data
mkdir -p ./training_data
cp ./adrs/*.md ./training_data/

# 2. Train model
adrminer topics train \
  ./training_data/ \
  ./models/custom \
  --n-topics 20 \
  --embedding all-MiniLM-L6-v2

# 3. Use custom model
adrminer topics predict ./adrs/ --model ./models/custom
```

---

## 6. Output Formats

### 6.1 JSON Sidecar Files

Creates `.metadata.json` files alongside each ADR:

```
adrs/
├── adr-001.md
├── adr-001.metadata.json
├── adr-002.md
└── adr-002.metadata.json
```

**Example metadata.json:**
```json
{
  "version": "1.0.0",
  "adr_file": "adr-001.md",
  "analyzed_at": "2026-04-18T12:00:00Z",
  "model_versions": {
    "topic_model": "v1.0",
    "classification_llm": "gpt-4o-mini",
    "check_llm": "gpt-4o-mini"
  },
  "topics": [
    {
      "id": 5,
      "label": "Database Migration",
      "probability": 0.85,
      "keywords": ["database", "migration", "schema"]
    }
  ],
  "classification": {
    "kruchten": {
      "primary_category": "Existence",
      "confidence": 0.92,
      "alternatives": ["Property"],
      "explanation": "This ADR describes a structural change..."
    }
  },
  "check": {
    "template_adherence": 0.78,
    "missing_sections": ["alternatives"],
    "section_assessments": [...]
  }
}
```

### 6.2 Consolidated JSON

All ADRs in a single JSON file:

```bash
adrminer analyze ./adrs/ --format consolidated-json --output ./summary.json
```

**Example structure:**
```json
{
  "collection_id": "my-project-adrs",
  "analyzed_at": "2026-04-18T12:00:00Z",
  "adr_count": 25,
  "results": [
    {
      "adr_file": "adr-001.md",
      "topics": [...],
      "classification": {...},
      "check": {...}
    },
    ...
  ],
  "summary": {
    "topics": {...},
    "classification": {...},
    "checks": {...}
  }
}
```

### 6.3 Markdown Report

Human-readable report:

```bash
adrminer analyze ./adrs/ --format markdown --output ./report.md
```

**Example report:**
```markdown
# ADR Analysis Report

**Project:** my-project-adrs  
**Analyzed:** 2026-04-18T12:00:00Z  
**Total ADRs:** 25

## Overview

- Quality Score: 0.72
- Total Topics: 8
- Primary Framework: Kruchten

## Classification Results

### Kruchten Framework

| Category | Count | Percentage |
|----------|--------|------------|
| Existence | 15 | 60% |
| Property | 6 | 24% |
| Executive | 3 | 12% |
| Ban | 1 | 4% |

## Topics

| Topic | Count | Top Keywords |
|-------|-------|--------------|
| Database Migration | 5 | database, migration, schema |
| API Design | 4 | api, rest, endpoint |
| Authentication | 3 | auth, login, security |
```

---

## 7. Error Handling

### 7.1 Exit Codes

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Input file not found
- `4`: Model load error
- `5`: API error

### 7.2 Common Errors

#### Configuration Error
```bash
Error: Configuration file not found. Run 'adrminer init' first.
```

**Solution:**
```bash
adrminer init
```

#### API Key Missing
```bash
Error: OPENAI_API_KEY not found in environment or .env file
```

**Solution:**
```bash
# Add to .env file
echo "OPENAI_API_KEY=sk-xxx" >> ~/.adrminer/.env
```

#### Model Load Error
```bash
Error: Failed to load model at /path/to/model
```

**Solution:**
```bash
# Check model path
adrminer model list

# Or use default model
adrminer topics predict adr-001.md
```

#### File Not Found
```bash
Error: File not found: adr-001.md
```

**Solution:**
```bash
# Check file exists
ls -la adr-001.md

# Or use correct path
adrminer topics predict ./docs/adrs/adr-001.md
```

### 7.3 Verbose Mode

Use verbose mode for debugging:

```bash
adrminer topics predict adr-001.md --verbose
```

This shows detailed logs including:
- Configuration values
- Model loading steps
- Processing progress
- API call details

---

## 8. Advanced Usage

### 8.1 Parallel Processing

Enable parallel processing for batch operations:

```bash
adrminer topics predict ./adrs/ --parallel
adrminer classify predict ./adrs/ --parallel
adrminer check predict ./adrs/ --parallel
```

**Note:** Parallel processing uses ThreadPoolExecutor and is recommended for 10+ ADRs.

### 8.2 Custom Examples

Create custom examples for classification:

```json
{
  "kruchten_examples": [
    {
      "adr_text": "We decided to use PostgreSQL...",
      "category": "Existence",
      "explanation": "This ADR describes the existence of a technology choice..."
    }
  ]
}
```

Use custom examples:

```bash
adrminer classify predict ./adrs/ --examples ./custom/examples.json
```

### 8.3 Topic Thresholding

Filter topics by probability threshold:

```bash
# Only show topics with > 0.5 probability
adrminer topics predict adr-001.md --threshold 0.5

# Only show topics with > 0.7 probability
adrminer topics predict ./adrs/ --threshold 0.7 --parallel
```

### 8.4 Multiple Topics

Allow multiple topics per ADR:

```bash
adrminer topics predict adr-001.md --multiple
```

This returns all topics above the threshold, not just the top one.

### 8.5 Custom Configuration

Override configuration per command:

```bash
# Use different LLM provider
export LLM_PROVIDER=anthropic
export LLM_MODEL=claude-3-sonnet
adrminer classify predict ./adrs/

# Use custom model path
export TOPIC_MODEL_PATH=/custom/path/to/model
adrminer topics predict ./adrs/

# Use different examples
export CLASSIFICATION_EXAMPLES=/custom/examples.json
adrminer classify predict ./adrs/
```

### 8.6 Shell Completion

Enable shell completion for faster command entry:

```bash
# Bash
echo 'eval "$(_ADRMINER_COMPLETE=bash_source adrminer)"' >> ~/.bashrc

# Zsh
echo 'eval "$(_ADRMINER_COMPLETE=zsh_source adrminer)"' >> ~/.zshrc

# Fish
echo '_ADRMINER_COMPLETE=fish_source adrminer | source' >> ~/.config/fish/config.fish
```

---

## 9. Troubleshooting

### 9.1 Installation Issues

**Problem:** `pip install adrminer` fails

**Solutions:**
1. Upgrade pip:
   ```bash
   pip install --upgrade pip
   ```

2. Use virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install adrminer
   ```

3. Install from source:
   ```bash
   git clone https://github.com/tommantonela/ADRminer.git
   cd ADRminer
   pip install -e .
   ```

### 9.2 Model Loading Issues

**Problem:** Model fails to load

**Solutions:**
1. Verify model exists:
   ```bash
   adrminer model list
   ```

2. Check file permissions:
   ```bash
   ls -la ~/.adrminer/models/topic_model/
   ```

3. Re-download model:
   ```bash
   rm -rf ~/.adrminer/models/
   adrminer init
   ```

### 9.3 API Rate Limits

**Problem:** API rate limit errors

**Solutions:**
1. Reduce parallel processing:
   ```bash
   adrminer classify predict ./adrs/  # Without --parallel
   ```

2. Add delays between requests (advanced):
   ```python
   # Edit classification_service.py to add time.sleep()
   import time
   time.sleep(1)  # 1 second delay
   ```

3. Use different LLM provider:
   ```bash
   export LLM_PROVIDER=anthropic
   adrminer classify predict ./adrs/
   ```

### 9.4 Memory Issues

**Problem:** Out of memory errors with large datasets

**Solutions:**
1. Process in batches:
   ```bash
   # Process 50 ADRs at a time
   for i in {0..50..100}; do
     mkdir -p ./batch_$i
     cp $(ls *.md | sed -n "${i},+49p") ./batch_$i/
     adrminer analyze ./batch_$i/ --topics --classify --check
   done
   ```

2. Disable parallel processing:
   ```bash
   adrminer topics predict ./adrs/  # Without --parallel
   ```

3. Use smaller embedding model:
   ```yaml
   # In .adrminer.yaml
   topic_model:
     embedding_model: all-MiniLM-L6-v2  # Smaller than mpnet
   ```

### 9.5 Performance Optimization

**Tips for faster processing:**

1. **Enable parallel processing:**
   ```bash
   adrminer topics predict ./adrs/ --parallel
   ```

2. **Use faster LLM:**
   ```yaml
   llm:
     model: gpt-4o-mini  # Faster than gpt-4o
   ```

3. **Use smaller embedding model:**
   ```yaml
   topic_model:
     embedding_model: all-MiniLM-L6-v2
   ```

4. **Cache results:**
   ```bash
   # First run creates metadata files
   adrminer analyze ./adrs/ --topics --classify --check
   
   # Subsequent runs skip unchanged ADRs
   adrminer analyze ./adrs/ --topics --classify --check
   ```

### 9.6 Getting Help

**Built-in help:**
```bash
# General help
adrminer --help

# Command-specific help
adrminer topics --help
adrminer topics predict --help
```

**Online resources:**
- GitHub Issues: https://github.com/tommantonela/ADRminer/issues
- Documentation: https://github.com/tommantonela/ADRminer/blob/main/docs/
- Examples: https://github.com/tommantonela/ADRminer/tree/main/sample

**Verbose logging:**
```bash
adrminer topics predict adr-001.md --verbose 2>&1 | tee debug.log
```

---

## Appendix

### A. Supported LLM Providers

| Provider | Models | Notes |
|----------|---------|--------|
| OpenAI | gpt-4o-mini, gpt-4o | Recommended for speed/cost |
| Anthropic | claude-3-haiku, claude-3-sonnet | Good for complex reasoning |
| Ollama | llama3, mistral | Local, no API costs |
| Azure OpenAI | gpt-4o, gpt-35-turbo | Enterprise deployment |
| Google | gemini-pro, gemini-flash | Experimental |

### B. Supported Classification Frameworks

| Framework | Categories | Description |
|-----------|-------------|-------------|
| Kruchten | 4 | Ontocrisis, diacrisis, pericrisis, anticrisis |
| Quality Attributes | 10 | Performance, security, usability, etc. |
| Zimmermann | 9 | Architectural decision types |

### C. Supported Templates

| Template | Sections | Description |
|----------|-----------|-------------|
| MADR | 7 | Context, decision, consequences, etc. |
| Custom | Variable | User-defined templates |

### D. File Extensions

| Extension | Description |
|------------|-------------|
| `.md` | ADR files (Markdown) |
| `.metadata.json` | Analysis results (sidecar) |
| `.json` | Consolidated results |
| `.yaml` | Configuration files |

---

**Document History:**
- v1.0 - Initial CLI guide (2026-04-18)