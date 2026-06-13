# adrchecker — Standalone ADR Quality Checker

A lightweight, standalone service for checking the quality of Architectural
Decision Records (ADRs) against the [MADR template](https://adr.github.io/madr/).
It uses LLM-based analysis to assess template adherence and section-wise
consistency.

This is a **sibling sub-project** of `adrminer`, living at `src/adrchecker/`.
It has **no dependency** on the full `adrminer` package and requires only a
minimal set of libraries.

---

## Features

- **MADR template adherence**: Extracts ADR sections and scores adherence (0.0–1.0).
- **Section-wise consistency**: Evaluates each MADR section for presence, content quality, and purpose consistency.
- **Batch processing**: Check multiple ADRs at once (with optional parallel execution).
- **Three usage modes**: CLI command, Python API, and module entry point.
- **Configurable**: Model, temperature, max tokens via `.env` or environment variables.
- **Minimal dependencies**: No pandas, bertopic, scikit-learn, or other heavy data-science stack.

---

## Installation

### Standalone install (recommended)

```bash
# From the repository root, install only the checker package
pip install -e . --config-settings pyproject.toml=pyproject.adrchecker.toml
```

Or, if you have the dependencies already and just want to use it from the source tree:

```bash
# Add src/ to your PYTHONPATH
export PYTHONPATH="src:$PYTHONPATH"

# Install minimal runtime dependencies
pip install typer rich pydantic pydantic-settings langchain-openai tiktoken python-dotenv
```

### Verify installation

```bash
adrchecker version
# adrchecker v0.1.0
```

---

## Configuration

Copy the example env file and set your API key:

```bash
cp .env.adrchecker.example .env
```

Edit `.env`:

```dotenv
ADRCHECKER_OPENAI_API_KEY=sk-your-key-here
ADRCHECKER_MODEL=gpt-4o-mini
ADRCHECKER_TEMPERATURE=0.0
```

| Variable | Default | Description |
|----------|---------|-------------|
| `ADRCHECKER_OPENAI_API_KEY` | — | Your OpenAI API key (required) |
| `ADRCHECKER_MODEL` | `gpt-4o-mini` | Model name |
| `ADRCHECKER_TEMPERATURE` | `0.0` | Generation temperature |
| `ADRCHECKER_MAX_TOKENS` | `None` | Max tokens to generate |
| `ADRCHECKER_OPENAI_BASE_URL` | `None` | Custom OpenAI-compatible base URL |
| `ADRCHECKER_DEFAULT_MODE` | `full` | Default check mode |
| `ADRCHECKER_PARALLEL` | `true` | Enable parallel batch processing |

---

## Usage

### 1. CLI

```bash
# Check a single ADR file (full assessment)
adrchecker check path/to/adr.md

# Check all ADRs in a directory
adrchecker check path/to/adrs/

# Template adherence only
adrchecker check path/to/adrs/ --mode adherence

# Section consistency only
adrchecker check path/to/adrs/ --mode sections

# Parallel batch processing
adrchecker check path/to/adrs/ --parallel

# Save results to JSON
adrchecker check path/to/adrs/ --json results.json
```

**CLI Options:**

| Flag | Description |
|------|-------------|
| `--mode, -m` | Checking mode: `full`, `adherence`, or `sections` (default: `full`) |
| `--parallel, -p` | Enable parallel processing for batch checks |
| `--json` | Save results to a JSON file |

### 2. Python API

```python
from adrchecker import ADRChecker

checker = ADRChecker()

# Full check (adherence + sections)
result = checker.check(adr_text)
print(f"Adherence score: {result['template_adherence']['adherence_score']}")

# MADR adherence only
adherence = checker.check_madr_adherence(adr_text)

# Section consistency only
sections = checker.check_sections(adr_text)
for assessment in sections["section_assessments"]:
    print(f"  {assessment['section_name']}: present={assessment['presence']}")
```

### 3. Batch processing (Python API)

```python
from adrchecker import ADRChecker

checker = ADRChecker()

# Batch check multiple ADRs
adr_texts = {
    "adr-001.md": "# ADR 001: Use PostgreSQL\n...",
    "adr-002.md": "# ADR 002: Adopt microservices\n...",
}

# Full check with metadata
results = checker.check_batch(
    adr_texts,
    organization="my-org",
    project="my-project",
    parallel=True,
    json_file="results.json",
)
```

### 4. Module entry point

```bash
python -m adrchecker check path/to/adrs/ --mode full
```

---

## Checking Modes

### `full` (default)
Combines both template adherence and section-wise consistency into a single
`ADRAssessmentReport`. This is the most comprehensive assessment.

### `adherence`
Evaluates the ADR's overall alignment with the MADR template, producing:
- Extracted section contents (title, status, context, decision, etc.)
- An adherence score (0.0–1.0)
- A textual assessment justifying the score

### `sections`
Evaluates each MADR section individually for:
- **Presence**: Is the section heading present in the ADR?
- **Content quality**: Is the content meaningful and project-specific?
- **Purpose consistency**: Does the content fulfill only this section's role?
- **Alternate titles**: Other headings that may serve this section's purpose

---

## Output Format

### Full check result (`ADRAssessmentReport`)

```json
{
  "section_assessments": [
    {
      "section_name": "Context",
      "presence": "Yes",
      "content_quality": "Yes",
      "purpose_consistency": "Yes",
      "justification": "...",
      "alternate_title": []
    }
  ],
  "template_adherence": {
    "title": "Use PostgreSQL for Data Persistence",
    "status": "accepted",
    "context": "...",
    "decision_drivers": "...",
    "decision": "...",
    "consequences": "...",
    "alternatives": [
      {"description": "MongoDB", "pros": ["..."], "cons": ["..."]}
    ],
    "date": "2024-01-15",
    "adherence_score": 0.85,
    "assessment": "..."
  }
}
```

---

## Development

### Install dev dependencies

```bash
pip install -e ".[dev]" --config-settings pyproject.toml=pyproject.adrchecker.toml
```

### Run tests

```bash
pytest tests/test_adrchecker/ -v
```

### Lint and format

```bash
ruff check src/adrchecker/
black src/adrchecker/
```

---

## Architecture

```
src/adrchecker/
├── __init__.py      # Public API exports
├── __main__.py      # `python -m adrchecker` entry
├── cli.py           # Typer CLI with `check` and `version` commands
├── checker.py       # ADRChecker class (core logic)
├── schemas.py       # Pydantic models (ADRTemplate, ADRConsistencyResult, etc.)
├── prompts.py       # LLM prompt templates and section metadata
└── config.py        # Environment-based settings (pydantic-settings)
```

The `ADRChecker` class uses LangChain chains with structured output:
- `global_consistency_chain`: Prompt → LLM → `ADRTemplate`
- `section_wise_consistency_chain`: Prompt → LLM → `ADRConsistencyResult`

---

## Relationship to `adrminer`

`adrchecker` is derived from the notebook code at `notebooks/adr_checking.py`.
It shares the same core logic, prompts, and schemas, but:

- **Has no dependency** on the full `adrminer` package.
- **Has minimal dependencies** (no bertopic, pandas, scikit-learn).
- **Can be installed and deployed independently**.
- Uses the **same MADR checking methodology** as the `adrminer check` command.