# ADRMiner

A text mining and classification toolkit for analyzing Architecture Decision Records (ADRs) from open-source repositories. 

This is the reproducibility kit for the paper "_A Text Mining and Classification Approach for Analyzing
Architecture Decision Records: Evidence from Open-Source
Repositories_"

<p align="center">
  <img src="adrminer-logo.png" alt="ADRMiner Logo" width="40%">
</p>

## Table of Contents

- [Quick Start](#quick-start)
- [What is ADRMiner?](#what-is-adrminer)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Results](#results)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

Clone and set up:

```bash
git clone https://github.com/tommantonela/ADRminer.git
cd ADRminer
python -m venv venv
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\activate  # Windows
pip install --upgrade pip && pip install -r requirements.txt
```

**Next**: See [Usage](#usage) → Start with `notebooks/adrs_bertopic.ipynb`

## What is ADRMiner?

ADRMiner analyzes software architecture decisions captured in markdown ADR documents. It:

1. **Parses** ADR documents to extract structure/sections (e.g., titles, content, decision rationale)
2. **Discovers topics** using BERTopic + text embeddings
3. **Checks MADR adherence** using an LLM to assess whether each ADR follows the [MADR](https://adr.github.io/madr/) template — a global adherence score plus a per-section consistency analysis (Context, Decision, Consequences, Decision Drivers, Considered Options)
4. **Classifies ADRs** using an LLM-based approach across 3 existing taxonomies/frameworks of design decisions:
   - **Kruchten** (4 categories: Existence, Ban, Property, Executive)
   - **Quality Attributes** (10 categories: Performance, Reliability, Security, Maintainability, Scalability, Usability, Portability, Compatibility, Observability, Testability)
   - **Zimmermann** (9 categories: Design, Technology, Infrastructure, Organizational/Process, Constraint, Quality Attribute, Crosscutting Concerns, Implementation, Other)
5. **Visualizes** topics, classification distributions, and adherence heatmaps

**Use cases:**
- Research: Understand architectural patterns and decisions in open-source projects
- Analysis: Study decision concerns and quality attributes in your codebase
- Validation: Evaluate ADR classification and template-compliance methodologies

### Sample Outputs

**Top 20 ADR Topics:**

![ADR Topics Chart](https://github.com/tommantonela/ADRminer/blob/main/adr-topics.png)

[**Interactive visualization** (click for live version)](https://htmlpreview.github.io/?https://raw.githubusercontent.com/tommantonela/ADRminer/refs/heads/main/top20_adr_topics.html?token=GHSAT0AAAAAAC5L6NIAM5LCGNKGXTMITQS42LUHAMQ)

## Features

- **ADR Parsing**: Extracts structure from markdown ADRs with hierarchy support
- **Topic Modeling**: BERTopic with UMAP embeddings + KeyBERT/OpenAI representation
- **ADR Checking**: LLM-based MADR template adherence scoring + per-section consistency analysis
- **LLM Classification**: Multi-framework classification with zero-shot/few-shot learning
- **Evaluation**: Confusion matrices, precision, recall, correlation (comparing against a small baselines tagged by experts)
- **Visualization**: Interactive charts, heatmaps, topic distributions
- **Batch Processing**: Parallel execution for classifying/checking large datasets
- **Reproducible Notebooks**: Workflow from data ingestion to analysis

## Installation

**Requirements:** Python 3.8+, pip 20.0+

### Steps

1. **Clone repository**
   ```bash
   git clone https://github.com/tommantonela/ADRminer.git
   cd ADRminer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate          # macOS/Linux
   # .\venv\Scripts\activate          # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Set up LLM API (optional)**
   
   If using LLM classification, ADR checking, or OpenAI-based topic representation:
   ```bash
   # Create .env in repository root
   echo "OPENAI_API_KEY=sk-your-key-here" > .env
   echo "OPENAI_MODEL_NAME=gpt-4o-mini" >> .env
   ```

5. **Add your ADR dataset**

   The notebooks load ADRs from a pickle file (e.g., `data/LLM4ADR-adrs__adrs_english.pickle`). To use your own data, you can also organize ADRs as markdown files under `data/`:
   ```
   data/
   ├── organization1/project1/adr-001.md
   ├── organization1/project1/adr-002.md
   └── organization2/project-x/adr-001.md
   ```
   See [Input Format](docs/INPUT_FORMAT.md) for both formats.

## Usage

The canonical, runnable code lives under `notebooks/` (Jupyter notebooks + the `.py` modules they import). The `src/` directory is an in-progress refactor scaffold and is not required to run the workflow.

Run notebooks in this order:

### 1. Topic Modeling (`notebooks/adrs_bertopic.ipynb`)
- Input: Raw ADR texts
- Process: Train your own BERTopic model or use pre-trained model, generate embeddings
- Output: Topic dataframe + corpus (in `notebooks/saved_topicmodel/`)

### 2. ADR Checking / MADR Adherence (`notebooks/adrs_llm_checking.ipynb`)
- Input: ADRs (raw text)
- Process: Use `ADRChecker` to assess MADR template adherence — a global adherence score and a per-section consistency analysis (presence, content quality, purpose consistency) for Context, Decision, Consequences, Decision Drivers, Considered Options
- Output: JSON files with adherence scores + section assessments (e.g., `results/all_projects-checks_results.json`)

### 3. Classification
Per-framework notebooks:
- `notebooks/krutchen-adrs_llm_classification.ipynb` (Kruchten)
- `notebooks/qas-adrs_llm_classification.ipynb` (Quality Attributes)
- `notebooks/zimmermann-adrs_llm_classification.ipynb` (Zimmermann)
- Input: ADRs (raw text)
- Process: Classify using LLM across each framework (zero-shot, static few-shot, or dynamic few-shot)
- Output: JSON files with predictions + confidence scores (e.g., `results/all_projects-{framework}_classification_results.json`)

### 4. Analysis (`notebooks/classification_analysis.ipynb`)
- Input: Classification results + optional ground truth
- Process: Compute metrics, generate confusion matrices, visualizations
- Output: Classification reports, statistical analysis

A non-LLM baseline classifier is also available in `notebooks/adrs_catboost_classification.ipynb`.

**See [Usage](docs/USAGE.md) for detailed examples and Python API.**

## Results

**Study Dataset:**
- 550+ open-source projects
- 4,300+ ADRs analyzed
- Topics discovered: 30-50 (automatic)

**Key Findings:**
- ADRs capture diverse architectural concerns
- Quality attributes vary in coverage across projects
- LLM classification aligns with human assessment (to some extent)
- MADR template compliance varies widely across repositories (e.g., ~80% include a Status field, ~65% document decision drivers/rationale, ~50% include consequences, ~40% compare alternatives)

[See Approach](docs/APPROACH.md) for more details about methodology and results.

## Documentation

| Document | Purpose |
|----------|---------|
| [**Usage**](docs/USAGE.md) | Detailed workflow, API docs, configuration |
| [**Input Format**](docs/INPUT_FORMAT.md) | ADR markdown structure, dataset organization |
| [**Architecture**](docs/ARCHITECTURE.md) | System design, module dependencies |
| [**Approach**](docs/APPROACH.md) | Research methodology, frameworks, findings |

## Repository Structure

> Note: the canonical, runnable code lives under `notebooks/` (Jupyter notebooks + the `.py` modules they import). The `src/` directory is an in-progress refactor scaffold and is currently empty of sources.

```
ADRminer/
├── notebooks/                          # Canonical code: Jupyter workflow + modules
│   ├── adrs_bertopic.ipynb             # Stage 1: Topic modeling
│   ├── adrs_llm_checking.ipynb         # Stage 2: MADR adherence / ADR checking
│   ├── krutchen-adrs_llm_classification.ipynb   # Stage 3 (Kruchten)
│   ├── qas-adrs_llm_classification.ipynb        # Stage 3 (Quality Attributes)
│   ├── zimmermann-adrs_llm_classification.ipynb # Stage 3 (Zimmermann)
│   ├── classification_analysis.ipynb   # Stage 4: Evaluation & analysis
│   ├── adrs_catboost_classification.ipynb       # Non-LLM baseline
│   ├── adr.py                          # Core: ADR parser
│   ├── adr_topic_mining.py             # Topic modeling (BERTopic)
│   ├── adr_classification.py           # LLM classification
│   ├── adr_checking.py                 # LLM-based MADR adherence / consistency
│   ├── prompts.py                      # Classification + checking prompts
│   ├── custom_selector.py              # Few-shot example selection
│   ├── utils.py                        # Data processing / visualization helpers
│   └── saved_topicmodel/               # Persisted BERTopic model + corpus
├── data/                               # Input: ADR datasets (pickle) + cached LLM responses
├── sample/                             # Ground truth + few-shot examples + per-model results
├── results/                            # Output: classifications + checks (JSON)
├── figures/                            # Output: Visualizations
├── docs/                               # Documentation
│   ├── USAGE.md
│   ├── INPUT_FORMAT.md
│   ├── APPROACH.md
│   └── ARCHITECTURE.md
├── src/                                # In-progress package refactor (scaffold, no sources yet)
├── requirements.txt
├── README.md
└── LICENSE
```

## Contributing

Contributions welcome! Ways to help:

- **New datasets**: Add support for different ADR repositories
- **Methods**: Experiment with alternative topic/classification models
- **Improvements**: Better preprocessing, embedding strategies, or visualization
- **Bug reports**: Open an issue if you hit problems
- **Docs**: Enhance examples and guides

## License

This project is licensed under the **Apache License 2.0**. See [LICENSE](LICENSE) for details.

---

**Questions?** Open an [issue](https://github.com/tommantonela/ADRminer/issues) on GitHub.