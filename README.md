# ADRMiner

A text mining and classification toolkit for analyzing Architecture Decision Records (ADRs) from open-source repositories.

**Methodology**: [Research Approach & Methodology](docs/APPROACH.md)

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

Clone and set up in 2 minutes:

```bash
git clone https://github.com/tommantonela/ADRminer.git
cd ADRminer
python -m venv venv
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\activate  # Windows
pip install --upgrade pip && pip install -r requirements.txt
```

**Next**: See [Usage](#usage) → Start with `adrs_bertopic.ipynb`

## What is ADRMiner?

ADRMiner analyzes software architecture decisions captured in markdown ADR documents. It:

1. **Parses** ADR documents to extract structure (titles, content, decision rationale)
2. **Discovers topics** using BERTopic + semantic embeddings  
3. **Classifies ADRs** using LLM-based approaches across 3 frameworks:
   - **Kruchten** (4 categories: Existence, Ban, Property, Executive)
   - **Quality Attributes** (10 categories: Performance, Reliability, Security, Maintainability, Scalability, Usability, Portability, Compatibility, Observability, Testability)
   - **Zimmermann** (9 categories: Design, Technology, Infrastructure, Organizational/Process, Constraint, Quality Attribute, Crosscutting Concerns, Implementation, Other)
4. **Evaluates** classifications with statistical metrics (Cohen's Kappa, Matthews Correlation)
5. **Visualizes** topics and classification distributions

**Use cases:**
- Research: Understand architectural patterns in open-source projects
- Analysis: Study decision concerns and quality attributes in your codebase
- Validation: Evaluate ADR classification methodologies

### Sample Outputs

**Top 20 ADR Topics:**

![ADR Topics Chart](https://github.com/tommantonela/ADRminer/blob/main/adr-topics.png)

[**Interactive visualization** (click for live version)](https://htmlpreview.github.io/?https://raw.githubusercontent.com/tommantonela/ADRminer/refs/heads/main/top20_adr_topics.html?token=GHSAT0AAAAAAC5L6NIAM5LCGNKGXTMITQS42LUHAMQ)

## Features

- **ADR Parsing**: Extracts structure from markdown ADRs with hierarchy support
- **Topic Modeling**: BERTopic with UMAP embeddings + KeyBERT/OpenAI representation
- **LLM Classification**: Multi-framework classification with zero-shot/few-shot learning
- **Statistical Evaluation**: Confusion matrices, inter-rater agreement (Kappa), correlation metrics
- **Visualization**: Interactive charts, heatmaps, topic distributions
- **Batch Processing**: Parallel execution for large datasets
- **Reproducible Notebooks**: Complete workflow from data ingestion to analysis

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
   
   If using LLM classification or OpenAI-based topic representation:
   ```bash
   # Create .env in repository root
   echo "OPENAI_API_KEY=sk-your-key-here" > .env
   echo "OPENAI_MODEL_NAME=gpt-4o-mini" >> .env
   ```

5. **Add your ADR dataset**

   Organize ADRs in `data/` folder:
   ```
   data/
   ├── organization1/project1/adr-001.md
   ├── organization1/project1/adr-002.md
   └── organization2/project-x/adr-001.md
   ```

## Usage

Run notebooks in this order:

### 1. Topic Modeling (`adrs_bertopic.ipynb`)
- Input: Raw ADR texts
- Process: Train BERTopic model, generate embeddings
- Output: Topic dataframe + corpus (in `saved_topicmodel/`)
- Runtime: ~5 minutes for typical corpus

### 2. Classification (`adr_llm_classification.ipynb`)  
- Input: ADRs (raw or topic-enhanced)
- Process: Classify using LLM across 3 frameworks
- Output: JSON files with predictions + confidence scores
- Runtime: ~30-60 sec per ADR depending on LLM API

### 3. Analysis (`classification_analysis.ipynb`)
- Input: Classification results + optional ground truth
- Process: Compute metrics, generate confusion matrices, visualizations
- Output: Classification reports, statistical analysis
- Runtime: < 1 minute

**See [USAGE.md](docs/USAGE.md) for detailed examples and Python API.**

## Results

**Study Dataset:**
- 550+ open-source projects
- 4,300+ ADRs analyzed
- Topics discovered: 30-50 (automatic)

**Key Findings:**
- ADRs capture diverse architectural concerns
- Quality attributes vary in coverage across projects
- LLM classification aligns with human assessment (~0.7 Kappa)
- MADR template compliance varies across repositories

[See APPROACH.md](docs/APPROACH.md) for complete methodology and results.

## Documentation

| Document | Purpose |
|----------|---------|
| [**USAGE.md**](docs/USAGE.md) | Detailed workflow, API docs, configuration |
| [**INPUT_FORMAT.md**](docs/INPUT_FORMAT.md) | ADR markdown structure, dataset organization |
| [**ARCHITECTURE.md**](docs/ARCHITECTURE.md) | System design, module dependencies |

## Repository Structure

```
ADRminer/
├── notebooks/                          # Jupyter workflow
│   ├── adrs_bertopic.ipynb
│   ├── adr_llm_classification.ipynb
│   ├── classification_analysis.ipynb
│   ├── adr.py                          # Core: ADR parser
│   ├── adr_topic_mining.py             # Topic modeling
│   ├── adr_classification.py           # LLM classification
│   ├── utils.py, prompts.py, ...       # Utilities
├── data/                               # Input: ADR datasets
├── results/                            # Output: Classifications
├── figures/                            # Output: Visualizations
├── docs/                               # Documentation
│   ├── USAGE.md
│   ├── INPUT_FORMAT.md
│   ├── PAPER.md
│   └── ARCHITECTURE.md
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
