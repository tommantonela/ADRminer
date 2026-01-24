# Documentation Index

Complete guide to ADRMiner documentation.

## Quick Navigation

| Document | Audience | Purpose |
|----------|----------|---------|
| [**README.md**](../README.md) | Everyone | Quick start, features overview, setup instructions |
| **[USAGE.md](#usage)** | Developers | Detailed API reference, workflow examples, configuration |
| **[INPUT_FORMAT.md](#input)** | Data Managers | ADR structure, dataset organization, validation |
| **[APPROACH.md](#approach)** | Researchers | Methodology, frameworks, findings, research questions |
| **[ARCHITECTURE.md](#arch)** | Contributors | System design, modules, extensibility, performance |

---

## <a name="usage"></a>USAGE.md – Detailed Workflow

**When to read**: You're implementing the analysis pipeline

**Covers**:
- ✅ Complete notebook workflow (3 stages)
- ✅ Python API reference for all modules
- ✅ Configuration parameters
- ✅ Few-shot learning strategies
- ✅ Evaluation metrics explanation
- ✅ Complete working examples

**Sections**:
1. Notebook Workflow (Topic Modeling, Classification, Analysis)
2. Python API Reference (adr.py, adr_topic_mining.py, adr_classification.py)
3. Configuration (Environment variables, notebook parameters)
4. Tips & Best Practices
5. Complete end-to-end example

---

## <a name="input"></a>INPUT_FORMAT.md – Data Specifications

**When to read**: You're preparing ADR data for analysis

**Covers**:
- ✅ ADR markdown structure (minimal and full templates)
- ✅ Supported markdown elements
- ✅ Dataset directory organization
- ✅ Metadata extraction
- ✅ Data validation
- ✅ Ground truth annotation format

**Sections**:
1. ADR Markdown Structure (MADR template)
2. Dataset Organization (directory hierarchy)
3. Loading ADRs into Python
4. Extracting content for analysis
5. Ground truth annotation format
6. Data validation checks

---

## <a name="approach"></a>APPROACH.md – Research Methodology

**When to read**: You want to understand the research approach and methodology

**Covers**:
- ✅ Research questions (RQ1-RQ4)
- ✅ Methodology overview (topic modeling + LLM classification)
- ✅ Classification frameworks (Kruchten, Quality Attributes, Zimmermann)
- ✅ LLM approach and prompting strategies
- ✅ Results summary (findings, metrics, per-framework performance)
- ✅ Limitations and future work
- ✅ Foundational references

**Sections**:
1. Research Objectives & Questions
2. Methodology (data collection, analysis pipeline)
3. Classification Frameworks (3 approaches)
4. LLM Classification Strategy
5. Evaluation Methodology
6. Key Findings Summary
7. Limitations & Future Directions
8. Reproducibility Notes

---

## <a name="arch"></a>ARCHITECTURE.md – System Design

**When to read**: You're extending the code or understanding module interactions

**Covers**:
- ✅ High-level system architecture (diagram)
- ✅ Module breakdown (adr.py, adr_topic_mining.py, adr_classification.py, utils.py)
- ✅ Data flow (topic modeling, classification, evaluation)
- ✅ Dependencies (libraries and versions)
- ✅ Design patterns used
- ✅ Configuration system
- ✅ Extensibility points (custom frameworks, alternative models)
- ✅ Performance considerations (memory, compute time)

**Sections**:
1. High-Level Architecture (system diagram)
2. Module Breakdown (detailed class/method reference)
3. Data Flow (pipeline diagrams)
4. Dependencies
5. Design Patterns
6. Configuration
7. Extensibility Points
8. Performance Considerations

---

## Documentation Map

```
README.md (START HERE)
├── Quick Start → Installation
├── Features
└── Documentation (links to)
    ├── USAGE.md
    │   ├── Notebook workflow
    │   ├── API reference
    │   ├── Configuration
    │   └── Examples
    ├── INPUT_FORMAT.md
    │   ├── ADR structure
    │   ├── Dataset organization
    │   └── Data validation
    ├── PAPER.md
    │   ├── Research questions
    │   ├── Methodology
    │   ├── Frameworks
    │   └── Results
    └── ARCHITECTURE.md
        ├── System design
        ├── Modules
        ├── Data flow
        └── Extensibility
```

---

## Common Workflows

### "I want to analyze my ADRs"

1. Read: [README.md](../README.md) (Quick Start section)
2. Read: [INPUT_FORMAT.md](#input) (prepare your data)
3. Read: [USAGE.md](#usage) (run the notebooks)

### "I want to understand the research approach"

1. Read: [README.md](../README.md) (overview)
2. Read: [APPROACH.md](#approach) (full methodology)
3. Reference: [ARCHITECTURE.md](#arch) (if implementing yourself)

### "I want to extend ADRMiner"

1. Read: [ARCHITECTURE.md](#arch) (system design)
2. Read: [USAGE.md](#usage) (API reference)
3. Reference: [PAPER.md](#paper) (for domain knowledge)

### "I want to contribute"

1. Read: [README.md](../README.md) (contributing section)
2. Read: [ARCHITECTURE.md](#arch) (understand codebase)
3. Read: [APPROACH.md](#approach) (for domain knowledge)
4. Reference: All others as needed

---

## Key Concepts

**Architecture Decision Record (ADR)**: Lightweight documentation of design decisions, including context, decision, and consequences.

**Topic Modeling**: Unsupervised learning to discover main themes in a document collection (BERTopic).

**LLM Classification**: Using large language models to assign categories to text (GPT-4o-mini).

**Classification Framework**: A taxonomy of decision types:
- **Kruchten**: 4 meta-types (Existence, Ban, Property, Executive)
- **Quality Attributes**: 10 architectural qualities
- **Zimmermann**: 9 decision categories

**Cohen's Kappa**: Measure of inter-rater agreement accounting for chance (0=random, 1=perfect).

**Few-shot Learning**: Providing examples to improve LLM classification (vs. zero-shot).

---

## FAQ Quick Links

**Q: How do I run the analysis?**  
A: See [USAGE.md - Notebook Workflow](#usage)

**Q: What format should my ADRs be in?**  
A: See [INPUT_FORMAT.md - ADR Markdown Structure](#input)

**Q: How are ADRs classified?**  
A: See [APPROACH.md - Classification Frameworks](#approach)

**Q: Can I use a different LLM?**  
A: See [ARCHITECTURE.md - Extensibility Points](#arch)

**Q: What are the results quality?**  
A: See [APPROACH.md - Key Findings Summary](#approach)

**Q: How much does this cost?**  
A: See [ARCHITECTURE.md - Performance](#arch) (API call estimates)

---

## Acronyms

| Acronym | Meaning |
|---------|---------|
| **ADR** | Architecture Decision Record |
| **MADR** | Markdown Architecture Decision Records |
| **LLM** | Large Language Model (e.g., GPT-4) |
| **NLP** | Natural Language Processing |
| **QA** | Quality Attribute |
| **RQ** | Research Question |
| **UMAP** | Uniform Manifold Approximation and Projection |
| **Kappa** | Cohen's Kappa (agreement metric) |

---

## Version Information

- **Project**: ADRMiner reproducibility kit
- **Status**: Research methodology published
- **Python**: 3.8+
- **Last Updated**: January 2026

---

**Start with [README.md](../README.md) →**
