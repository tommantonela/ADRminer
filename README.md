# ADRminer

**AI-powered analysis of Architectural Decision Records (ADRs)** — discover topics, classify decisions, check quality, and generate insights.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Modes](#usage-modes)
  - [Non-Interactive CLI](#non-interactive-cli)
  - [Interactive CLI](#interactive-cli)
- [Configuration](#configuration)
  - [LLM Providers](#configuring-llm-providers)
  - [YAML Configuration](#yaml-configuration)
  - [Environment Variables](#environment-variables)
- [Architecture](#architecture)
- [Experimental Work (Notebooks)](#experimental-work-notebooks)
- [Development](#development)
- [Roadmap](#roadmap)
- [Citation](#citation)

---

## Features

### Topic Mining
Discover the main themes and topics across your ADR collection using **BERTopic** with sentence-transformer embeddings. Topic labels can be generated automatically via KeyBERT or enhanced with LLM-based representations for human-readable names. Includes support for UMAP dimensionality reduction, topic hierarchy visualization, and coherence/diversity metrics.

### Classification
Categorize architectural decisions using established frameworks via LLM-based zero-shot and few-shot classification:

| Framework | Description |
|---|---|
| **Kruchten** | Classifies ADRs into Kruchten's decision types (e.g., Architecture, Design, Technology) |
| **Quality Attributes** | Maps decisions to quality attribute categories (e.g., Performance, Security, Scalability) |
| **Zimmermann** | Categorizes using Zimmermann's architectural decision taxonomy |

Few-shot examples are loaded from configurable JSON files and can be disabled for pure zero-shot classification.

### Quality Checking
Evaluate ADRs against the **MADR template** with three assessment modes:
- **Adherence** — overall template adherence score (0.0–1.0)
- **Sections** — section-wise consistency analysis (presence, content quality, purpose)
- **Full** — comprehensive assessment combining both

Results include per-section justifications and color-coded quality indicators.

### Summaries & Insights
Generate AI-powered content summaries and project-level insights:
- **Content Summaries** — concise natural-language summaries of individual ADRs
- **ADR Insights** — classification alignment, quality assessment, confidence evaluation, topic-content match, and actionable recommendations per ADR
- **Project Insights** — classification patterns, quality trends, architectural themes, risk assessment, and project-wide recommendations

Reports can be exported as Markdown files (summary or detailed format).

### Interactive Chat CLI
A prompt_toolkit-based interactive session with command auto-completion, history navigation, and an optional AI assistant agent that can answer questions about your ADRs. Supports all analysis commands via `/`-prefixed syntax.

### Flexible Configuration
Pydantic-validated settings loaded from YAML config files (project-local or global), environment variables, and `.env` files. Supports multiple LLM providers through a unified factory built on LangChain.

---

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/tommantonela/ADRminer.git
cd ADRminer

# Install in development mode
pip install -e .

# Or install with optional LLM provider dependencies
pip install -e ".[openai]"       # OpenAI support
pip install -e ".[anthropic]"    # Anthropic support
pip install -e ".[ollama]"       # Ollama (local) support
pip install -e ".[all]"          # All providers + dev tools
```

### Requirements

- Python 3.10 or higher
- See `pyproject.toml` for full dependencies

---

## Quick Start

### 1. Set Up API Keys

Copy the example environment file and add your keys:

```bash
cp .env.example .env
# Edit .env with your API key
```

Or export directly:

```bash
# OpenAI (default provider)
export OPENAI_API_KEY=sk-your-key-here
```

### 2. Analyze ADRs

```bash
# Discover topics
adrminer topics predict ./docs/adrs

# Classify using Kruchten framework
adrminer classify predict ./docs/adrs --framework kruchten

# Check quality against MADR template
adrminer check ./docs/adrs

# Generate summaries and insights
adrminer summary ./docs/adrs --output-detailed report.md
```

### 3. Try the Interactive Mode

```bash
adrminer chat ./docs/adrs
# Type /help for available commands
```

---

## Usage Modes

ADRminer offers two usage modes: a **non-interactive CLI** for scripted/batch processing, and an **interactive chat CLI** for exploratory analysis.

### Non-Interactive CLI

Use individual commands directly from the terminal. Ideal for automation, CI/CD pipelines, and batch processing.

```bash
# Global options
adrminer --version                   # Show version
adrminer --config custom.yaml ...    # Use custom config file
```

#### Topic Mining

```bash
# Predict topics for all ADRs in a directory
adrminer topics predict ./docs/adrs

# Use a specific pre-trained model
adrminer topics predict ./docs/adrs --model ./models/topic_model

# Export to consolidated JSON
adrminer topics predict ./docs/adrs --output consolidated

# Export to CSV
adrminer topics predict ./docs/adrs --csv topics.csv

# Verbose output with details
adrminer topics predict ./docs/adrs --verbose

# View topic information
adrminer topics info
adrminer topics info --topic-id 0
```

#### Classification

```bash
# Classify using different frameworks
adrminer classify predict ./docs/adrs --framework kruchten
adrminer classify predict ./docs/adrs --framework quality_attributes
adrminer classify predict ./docs/adrs --framework zimmermann

# Zero-shot classification (no few-shot examples)
adrminer classify predict ./docs/adrs --no-examples

# Use custom examples file
adrminer classify predict ./docs/adrs --examples ./custom_examples.json

# Use ADR parser for section extraction
adrminer classify predict ./docs/adrs --use-parser

# Export results
adrminer classify predict ./docs/adrs --output consolidated
adrminer classify predict ./docs/adrs --csv results.csv

# View framework information
adrminer classify info
adrminer classify info --framework kruchten
```

#### Quality Checking

```bash
# Full assessment (default)
adrminer check ./docs/adrs

# Specific modes
adrminer check ./docs/adrs --mode adherence    # Overall score only
adrminer check ./docs/adrs --mode sections     # Section consistency only

# With ADR parser
adrminer check ./docs/adrs --use-parser --strict

# Export to CSV
adrminer check ./docs/adrs --csv quality_report.csv
```

#### Summaries & Insights

```bash
# Display console summary
adrminer summary ./docs/adrs

# Export summary report
adrminer summary ./docs/adrs --output-summary summary.md

# Export detailed report with AI-powered insights
adrminer summary ./docs/adrs --output-detailed detailed.md

# Export both reports
adrminer summary ./docs/adrs -s summary.md -d detailed.md

# Force regeneration of cached summaries
adrminer summary ./docs/adrs -d detailed.md --force-rewrite
```

#### Utility Commands

```bash
# Test LLM connection
adrminer util llm "Hello, can you analyze ADRs?"

# Inspect a specific ADR with formatting
adrminer util inspect ./docs/adrs/adr-001.md
adrminer util inspect ./docs/adrs/adr-001.md --metadata

# List ADRs with details
adrminer util list ./docs/adrs --details
adrminer util list ./docs/adrs --has-metadata
```

#### Initialization

```bash
# Create default configuration file
adrminer init config
# Creates ~/.adrminer.yaml with default settings
```

### Interactive CLI

Launch an interactive session for exploratory ADR analysis with auto-completion, command history, and an optional AI assistant.

```bash
# Start interactive session in a directory
adrminer chat ./docs/adrs

# Start without AI assistant (commands only)
adrminer chat --no-agent

# Start in current directory
adrminer chat
```

Once inside the interactive session:

```
ADRminer > /help                          # Show all commands
ADRminer > /list                          # List ADRs in current directory
ADRminer > /cd ./other-adrs              # Change working directory

# Run any analysis command
ADRminer > /topics predict .              # Discover topics
ADRminer > /classify predict . --framework kruchten
ADRminer > /check predict . --mode full
ADRminer > /summary . --output-detailed report.md

# Utility commands
ADRminer > /util inspect adr-001.md --metadata
ADRminer > /util llm "What is this ADR about?"

# Session management
ADRminer > /reset_memory                  # Clear session state
ADRminer > /quit                          # Exit
```

**Interactive mode features:**
- **Tab completion** for commands and options
- **Arrow key history** navigation
- **AI assistant** (enabled by default) — ask natural-language questions about your ADRs
- **Session state** — loaded ADRs and results persist across commands
- Use `--no-agent` or set `agent.agent_enabled: false` in config to disable the AI assistant

---

## Configuration

### Configuring LLM Providers

ADRminer supports six LLM providers through LangChain's unified interface. Configure the provider and model in your YAML config or rely on defaults.

#### OpenAI (default)

```yaml
llm:
  provider: openai
  model: gpt-4.1-mini
```

```bash
export OPENAI_API_KEY=sk-your-key
```

Other models: `gpt-4o`, `gpt-4o-mini`, `o3-mini`, etc.

#### Anthropic

```yaml
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
```

```bash
export ANTHROPIC_API_KEY=your-key
```

Other models: `claude-3-haiku-20240307`, `claude-3-5-sonnet-20241022`, etc.

#### Ollama (local models)

```yaml
llm:
  provider: ollama
  model: llama3.2
  ollama_base_url: http://localhost:11434
```

No API key required. Install [Ollama](https://ollama.ai) and pull a model (`ollama pull llama3.2`). Other models: `phi4-mini`, `mistral`, `qwen2.5`, etc.

#### Azure OpenAI

```yaml
llm:
  provider: azure
  model: gpt-4o
```

```bash
export AZURE_OPENAI_API_KEY=your-key
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
export AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

#### Google Vertex AI

```yaml
llm:
  provider: google
  model: gemini-pro
```

```bash
export GOOGLE_API_KEY=your-key
export GOOGLE_PROJECT=your-project-id
```

#### Groq (fast inference)

```yaml
llm:
  provider: groq
  model: llama-3.3-70b-versatile
```

```bash
export GROQ_API_KEY=gsk-your-key
```

### YAML Configuration

ADRminer looks for configuration files in this order:
1. Project-local: `adrminer.yaml`, `.adrminer.yaml`, `config.yaml` in the current directory
2. Global: `~/.adrminer.yaml`

You can also specify a config file explicitly: `adrminer --config path/to/config.yaml`

```yaml
# LLM Configuration
llm:
  provider: openai        # openai, anthropic, ollama, azure, google, groq
  model: gpt-4.1-mini
  temperature: 0.0
  max_tokens: 2000
  max_input_tokens: 500000   # Context window size (for summarization middleware)

# Topic Model Configuration
topic_model:
  path: ~/.adrminer/models/topic_model
  embedding_model: all-MiniLM-L6-v2   # sentence-transformers model
  n_topics: null                        # null for auto-detection
  use_llm_representation: true          # Use LLM for topic naming
  language: english                     # Stop words language

# Classification Configuration
classification:
  framework: kruchten         # kruchten, quality_attributes, zimmermann
  examples: ~/.adrminer/examples/kruchten_examples.json
  use_examples: true           # Few-shot classification
  use_parser: false            # Enable ADR section parser

# Quality Check Configuration
check:
  template: madr               # Template to check against
  use_parser: false            # Enable ADR section parser

# Agent Configuration (interactive mode)
agent:
  agent_enabled: true          # Enable AI assistant in chat mode
  middleware:
    summarization_trigger_fraction: 0.8
    summarization_trigger_messages: 30

# Output Configuration
output:
  format: json-sidecar         # json-sidecar, consolidated-json, markdown
  parallel: true               # Enable parallel processing
  verbose: false
```

### Environment Variables

Only LLM API keys and provider-specific settings should be set via environment variables. All other settings belong in the YAML config.

```bash
# Copy the example file and fill in your keys
cp .env.example .env
```

See [`.env.example`](.env.example) for all available environment variables.

### Output Formats

| Format | Flag | Description |
|---|---|---|
| **JSON Sidecar** (default) | `--output sidecar` | Creates a `.metadata.json` file next to each ADR |
| **Consolidated JSON** | `--output consolidated` | All results in a single `topics_results.json` file |
| **CSV** | `--csv path.csv` | Export tabular results to CSV |
| **Markdown** | `--output-summary` / `--output-detailed` | Summary or detailed Markdown reports |

---

## Architecture

ADRminer follows a modular, layered architecture:

```
src/adrminer/
├── cli/                  # Typer-based non-interactive CLI commands
│   └── commands/         # Individual command implementations
├── chat/                 # Interactive CLI (prompt_toolkit)
│   ├── commands.py       # Command registry
│   ├── dispatcher.py     # Command dispatching
│   ├── handlers/         # Command handlers
│   └── session.py        # Session management
├── agents/               # AI assistant agents
│   ├── langchain_agent.py  # LangChain-based agent
│   ├── deep_agent.py       # Deep Agent implementation
│   └── tools.py            # Agent tools
├── services/             # Business logic layer
│   ├── topic_service.py        # BERTopic topic mining
│   ├── classification_service.py  # LLM-based classification
│   ├── checking_service.py     # MADR quality checking
│   ├── insight_service.py      # Summary & insight generation
│   └── adr_parser_service.py   # ADR section parsing
├── models/               # Model wrappers & schemas
│   ├── llm_factory.py          # LLM provider factory (LangChain)
│   ├── classification_schemas.py  # Pydantic output schemas
│   └── insight_schemas.py      # Insight output schemas
├── prompts/              # LLM prompt templates (Markdown)
├── exporters/            # Output format exporters
└── config/               # Configuration management
    └── settings.py       # Pydantic settings with YAML/env support
```

**Key design principles:**
- **Service Layer** isolates business logic from CLI presentation
- **LLM Factory** provides a unified interface across providers via LangChain's `init_chat_model()`
- **Pydantic schemas** ensure structured, validated LLM outputs
- **Config layer** supports layered configuration (defaults → YAML → env vars → CLI flags)

---

## Experimental Work (Notebooks)

The [`notebooks/`](notebooks/) directory contains the experimental work and research that underpins ADRminer's analysis capabilities. These notebooks were used to develop, evaluate, and validate each analysis module.

### Topic Mining
| Notebook | Description |
|---|---|
| [`adrs_bertopic.ipynb`](notebooks/adrs_bertopic.ipynb) | Core topic mining with BERTopic: corpus preparation, model training/loading, topic prediction, and visualizations (topic maps, hierarchies, barcharts, heatmaps, word clouds) |
| [`performance_adrs_bertopic.ipynb`](notebooks/performance_adrs_bertopic.ipynb) | Performance evaluation of BERTopic configurations on the ADR dataset |

### Classification
| Notebook | Description |
|---|---|
| [`krutchen-adrs_llm_classification.ipynb`](notebooks/krutchen-adrs_llm_classification.ipynb) | LLM-based classification using the Kruchten framework — includes zero-shot, static few-shot, and dynamic few-shot experiments |
| [`qas-adrs_llm_classification.ipynb`](notebooks/qas-adrs_llm_classification.ipynb) | LLM-based classification using Quality Attributes categories |
| [`zimmermann-adrs_llm_classification.ipynb`](notebooks/zimmermann-adrs_llm_classification.ipynb) | LLM-based classification using the Zimmermann taxonomy |
| [`classification_analysis.ipynb`](notebooks/classification_analysis.ipynb) | Cross-framework classification analysis and comparison |
| [`adrs_catboost_classification.ipynb`](notebooks/adrs_catboost_classification.ipynb) | CatBoost-based (traditional ML) classification as a baseline comparison |

### Quality Checking
| Notebook | Description |
|---|---|
| [`adrs_llm_checking.ipynb`](notebooks/adrs_llm_checking.ipynb) | LLM-based quality checking of ADRs against MADR template — adherence scoring and section consistency |

### Supporting Files
| File | Description |
|---|---|
| [`adr_topic_mining.py`](notebooks/adr_topic_mining.py) | Topic mining module (ADRTopicModel class) |
| [`adr_classification.py`](notebooks/adr_classification.py) | Classification module used in notebooks |
| [`adr_checking.py`](notebooks/adr_checking.py) | Quality checking module |
| [`utils.py`](notebooks/utils.py) | Shared utilities for data loading and processing |
| [`prompts.py`](notebooks/prompts.py) | Prompt templates |
| [`custom_selector.py`](notebooks/custom_selector.py) | Custom model selection utilities |

### Research Data

The [`sample/`](sample/) directory contains ground truth datasets and experimental results for classification and checking tasks, including comparisons across different models (OpenAI GPT-4o-mini, GPT-5-nano) and prompting strategies (zero-shot, static few-shot, dynamic few-shot).

---

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
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
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
```

---

## Roadmap

See [docs/SERVICE_ROADMAP.md](docs/SERVICE_ROADMAP.md) for the complete product roadmap.

### Current Phase (MVP)

- ✅ Topic mining service (BERTopic)
- ✅ LLM-based classification (Kruchten, Quality Attributes, Zimmermann)
- ✅ Quality checking service (MADR template)
- ✅ Summaries & AI-powered insights
- ✅ Non-interactive CLI (Typer)
- ✅ Interactive CLI with AI assistant
- ✅ Multiple LLM providers (OpenAI, Anthropic, Ollama, Azure, Google, Groq)
- ✅ JSON sidecar, consolidated JSON, CSV, and Markdown exports

### Future Phases

- REST API
- Streamlit web UI
- CI/CD integration
- Advanced pattern detection
- Multi-user collaboration
- Custom model training UI

---

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## License

MIT License — see [LICENSE](LICENSE) file for details.

## Citation

If you use ADRminer in your research, please cite:

```bibtex
@software{adrminer2024,
  title={ADRminer: AI-Powered Analysis of Architectural Decision Records},
  author={Tommasini, Antonella and others},
  year={2024},
  url={https://github.com/tommantonela/ADRminer}
}
```

## Acknowledgments

- [BERTopic](https://github.com/MaartenGr/BERTopic) for topic modeling
- [LangChain](https://github.com/langchain-ai/langchain) for LLM integration
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [Typer](https://github.com/tiangolo/typer) for CLI framework
- [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for interactive CLI

## Support

- **Issues**: [https://github.com/tommantonela/ADRminer/issues](https://github.com/tommantonela/ADRminer/issues)
- **Documentation**: [https://github.com/tommantonela/ADRminer/docs](https://github.com/tommantonela/ADRminer/docs)