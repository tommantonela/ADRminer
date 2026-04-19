# ADRminer

Analyze your Architectural Decision Records (ADRs) using AI-powered topic mining, classification, and quality checking.

## Features

- **Topic Mining**: Discover main themes in your ADRs using BERTopic
- **Classification**: Categorize decisions using established frameworks (Kruchten, Quality Attributes, Zimmermann)
- **Quality Checking**: Ensure ADRs follow templates and best practices
- **Rich CLI**: Modern, beautiful terminal interface with progress bars
- **Flexible Configuration**: YAML config files + environment variables
- **Multiple LLM Providers**: OpenAI, Anthropic, Ollama, Azure, Google
- **Export Options**: JSON sidecar files or consolidated JSON exports

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/tommantonela/ADRminer.git
cd ADRminer

# Install in development mode
pip install -e .

# Or install with optional dependencies
pip install -e ".[all]"
```

### Requirements

- Python 3.10 or higher
- See `pyproject.toml` for full dependencies

## Quick Start

### 1. Initialize Configuration

```bash
# Create default configuration file
adrminer init config

# This creates ~/.adrminer.yaml with default settings
```

### 2. Set Up API Keys

```bash
# OpenAI (default)
export OPENAI_API_KEY=sk-your-key-here

# Or Anthropic
export ANTHROPIC_API_KEY=your-key-here

# Or use Ollama (local, no API key needed)
# Just install Ollama and it will work automatically
```

### 3. Analyze ADRs

```bash
# Topic mining
adrminer topics predict ./docs/adrs

# Classification (Kruchten framework)
adrminer classify predict ./docs/adrs --framework kruchten

# Classification (Quality Attributes)
adrminer classify predict ./docs/adrs --framework quality_attributes

# View all available frameworks
adrminer classify info
```

## Usage

### Topic Mining

```bash
# Predict topics for all ADRs in a directory
adrminer topics predict ./docs/adrs

# Use a specific model
adrminer topics predict ./docs/adrs --model ~/.adrminer/models/topic_model

# Export to consolidated JSON
adrminer topics predict ./docs/adrs --output consolidated

# Show detailed output
adrminer topics predict ./docs/adrs --verbose

# Get information about topics
adrminer topics info
adrminer topics info --topic-id 0
```

### Classification

```bash
# Classify ADRs using Kruchten framework
adrminer classify predict ./docs/adrs --framework kruchten

# Use Quality Attributes framework
adrminer classify predict ./docs/adrs --framework quality_attributes

# Use Zimmermann framework
adrminer classify predict ./docs/adrs --framework zimmermann

# Zero-shot classification (no examples)
adrminer classify predict ./docs/adrs --no-examples

# Use custom examples file
adrminer classify predict ./docs/adrs --examples ./custom_examples.json

# Export to consolidated JSON
adrminer classify predict ./docs/adrs --output consolidated

# View framework information
adrminer classify info
adrminer classify info --framework kruchten
```

### Output Formats

#### JSON Sidecar (default)

Creates a `.metadata.json` file next to each ADR:

```json
{
  "version": "1.0.0",
  "adr_file": "adr-001.md",
  "analyzed_at": "2026-04-18T12:00:00Z",
  "model_versions": {
    "topic_model": "v1.0"
  },
  "topics": [
    {
      "topic_id": 5,
      "topic_label": "Database Migration",
      "probability": 0.85,
      "keywords": ["database", "migration", "schema"]
    }
  ]
}
```

#### Consolidated JSON

All results in a single file:

```bash
adrminer topics predict ./docs/adrs --output consolidated
# Creates: ./docs/adrs/topics_results.json
```

## Configuration

### YAML Configuration

Edit `~/.adrminer.yaml` to customize settings:

```yaml
# LLM Configuration
llm:
  provider: openai  # openai, anthropic, ollama, azure, google
  model: gpt-4.1-mini
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

# Output Configuration
output:
  format: json-sidecar  # json-sidecar, consolidated-json, markdown
  parallel: true
  verbose: false
```

### Environment Variables

Only LLM API keys and provider-specific settings:

```bash
# OpenAI
export OPENAI_API_KEY=sk-your-key

# Anthropic
export ANTHROPIC_API_KEY=your-key

# Azure OpenAI
export AZURE_OPENAI_API_KEY=your-key
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
export AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Google Vertex AI
export GOOGLE_API_KEY=your-key
export GOOGLE_PROJECT=your-project-id

# Ollama
export OLLAMA_BASE_URL=http://localhost:11434
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit      # Unit tests only
pytest -m integration # Integration tests only
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Run all checks
pre-commit run --all-files
```

### Building Package

```bash
# Build wheel and source distribution
python -m build

# Test installation
pip install dist/adrminer-0.1.0-py3-none-any.whl
```

## Architecture

ADRminer follows a modular architecture:

- **CLI Layer**: Typer-based command-line interface with Rich output
- **Service Layer**: Business logic for topics, classification, and checking
- **Model Layer**: Wrappers for BERTopic and LLM models
- **Config Layer**: Pydantic-based settings with YAML and env var support
- **Export Layer**: JSON and Markdown exporters

```
src/adrminer/
├── cli/              # Command-line interface
├── services/         # Business logic
├── models/           # Model wrappers
├── exporters/        # Output formats
└── config/           # Configuration management
```

## Roadmap

See [docs/SERVICE_ROADMAP.md](docs/SERVICE_ROADMAP.md) for the complete product roadmap.

### Phase 1: MVP (Current)

- ✅ Topic mining service
- ✅ Classification service
- ✅ CLI interface
- ✅ JSON sidecar export
- ⏳ Quality checking service
- ⏳ Insights generation
- ⏳ Streamlit web UI

### Future Phases

- Advanced insights and pattern detection
- REST API
- CI/CD integration
- Multi-user collaboration
- Custom model training UI

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## License

MIT License - see LICENSE file for details

## Citation

If you use ADRminer in your research, please cite:

```bibtex
@software{adrminer2024,
  title={ADRminer: Analyze Your Architectural Decision Records},
  author={ADRminer Team},
  year={2024},
  url={https://github.com/tommantonela/ADRminer}
}
```

## Acknowledgments

- BERTopic for topic modeling
- LangChain for LLM integration
- Rich for beautiful terminal output
- Typer for CLI framework

## Support

- GitHub Issues: [https://github.com/tommantonela/ADRminer/issues](https://github.com/tommantonela/ADRminer/issues)
- Documentation: [https://github.com/tommantonela/ADRminer/docs](https://github.com/tommantonela/ADRminer/docs)