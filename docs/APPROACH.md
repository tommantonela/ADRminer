# Approach & Methodology

Overview of the analysis methodology for ADR content classification, topic discovery, and MADR adherence checking.

---

## Research Objectives

This work conducts an empirical analysis of Architecture Decision Record (ADR) contents using data mining techniques to:

1. **Identify main design concerns** captured in ADRs via topic modeling
2. **Assess alignment** with established taxonomies/frameworks of design decision types
3. **Check adherence** to the [MADR](https://adr.github.io/madr/) (Markdown Architecture Decision Records) template structure
4. **Develop automated pipeline** that combines topic modeling + LLM-based checking + LLM-based classification
5. **Evaluate performance** of LLM classification approaches

---

## Research Questions

**RQ1**: What types of concerns (as topics) are captured in ADRs?

**RQ2**: How well does the captured content align with the taxonomies from the literature (Kruchten, Quality Attributes, Zimmermann)?

**RQ3**: Are there mismatches or inconsistent practices in the usage of the ADR structure (i.e., MADR sections)?


## Data Collection

- **Scope**: 550+ open-source repositories from GitHub
- **Total ADRs**: ~4,300 architectural decision records
- **Filtering**: Projects with ≥5 ADRs, documents ≥500 characters
- **Format**: Primarily markdown (MADR-compliant and similar)

Key indicators:
- Average ADRs per project: 8-10
- Average ADR length: 800-1,200 characters
- Date range: 2015-2025 (projects with ADR adoption)

---

## Analysis Pipeline

The approach combines **topic modeling**, **LLM-based ADR checking (MADR adherence)**,
and **LLM-based classification**:

```
Raw ADR Documents
    ↓
[1] Text Preprocessing & Parsing
    - Extract structure (titles, sections, content)
    - Clean text, remove code blocks
    - Normalize whitespace and formatting
    ↓
[2] Topic Modeling (BERTopic)                         → RQ1
    - Sentence embeddings (all-MiniLM-L6-v2)
    - UMAP dimensionality reduction
    - Auto-detect topics (typically 30-70)
    - Dual representation: KeyBERT + LLM-based labels
    ↓
[3] ADR Checking / MADR Adherence                     → RQ3
    - Overall template-adherence assessment (LLM)
    - Per-section consistency analysis:
      Context, Decision, Consequences,
      Decision Drivers, Considered Options
    - Adherence score + section presence/quality
    ↓
[4] LLM Classification                                → RQ2
    - Zero-shot / Few-shot learning
    - 3 classification frameworks:
      * Kruchten (4 categories)
      * Quality Attributes (10 categories)
      * Zimmermann (9 categories)
    ↓
[5] Evaluation
    - Confusion matrices
    - Per-class metrics (precision, recall, F1)
    ↓
Results & Insights
```

---

## Classification Frameworks

### Framework 1: Kruchten's Architecture Types

Based on Kruchten's taxonomy of architectural decision types:

- **Existence (ontocrisis)**: Adding new capabilities to the system
- **Ban/Non-Existence (anticrisis)**: Removing options or avoiding certain approaches
- **Property (diacrisis)**: Modifying quality properties (performance, scalability)
- **Executive (pericrisis)**: Managing organizational and process aspects

**Use case**: Classifying decisions by the type of architectural change they represent.

---

### Framework 2: Quality Attributes

ISO/IEC 25010 system quality attributes and related concerns:

- **Performance**: Response time, throughput, efficiency, optimization
- **Reliability**: Fault tolerance, availability, error recovery, redundancy
- **Security**: Access control, encryption, vulnerability protection, data privacy
- **Maintainability**: Code quality, documentation, extensibility, refactoring
- **Scalability**: Capacity growth, load handling, horizontal/vertical scaling
- **Usability**: User experience, interface design, accessibility
- **Portability**: Platform independence, deployment flexibility, cross-platform support
- **Compatibility**: Integration, interoperability, API compatibility
- **Observability**: Monitoring, logging, tracing, debugging capabilities
- **Testability**: Unit testing, integration testing, automated test capabilities
- **Other/Functional Concern**: Non-quality aspects, feature-related decisions

**Use case**: Understanding which quality attributes drive architectural decisions.

---

### Framework 3: Zimmermann's Decision Types

Based on Zimmermann et al.'s classification of architectural decisions:

- **Design**: Software architecture and design patterns
- **Technology**: Tool, framework, language, and library choices
- **Infrastructure**: Deployment, cloud services, hardware, networking
- **Organizational/Process**: Team structure, development methodology, workflows
- **Constraint**: Legal, regulatory, business, or environmental constraints
- **Quality Attribute**: Explicit decisions about quality requirements
- **Crosscutting Concerns**: Security, logging, monitoring, transaction handling
- **Implementation**: Code-level decisions and patterns
- **Other**: Unclassifiable or miscellaneous decisions

**Use case**: Categorizing decisions by their scope and nature.

---

## ADR Checking Approach (MADR Adherence)

ADR Checking directly addresses **RQ3** (mismatches/inconsistent practices in
ADR/MADR structure). It is implemented in `notebooks/adr_checking.py`
(`ADRChecker`) and driven by `notebooks/adrs_llm_checking.ipynb`.

The LLM is prompted to assess each ADR against the
[MADR](https://adr.github.io/madr/) template at two granularities:

### 1. Global Adherence Assessment

`ADRChecker.check_madr_adherence(adr_text)` produces an overall assessment of
whether the ADR conforms to the MADR template, including:
- `template_match`: whether the document follows the expected structure
- `purpose_match`: whether each present section fulfills its intended purpose
- `adherence_score`: an overall score (0–1)
- `problems`: list of identified structural/content issues
- `suggestions`: recommended improvements

### 2. Per-Section Consistency Analysis

`ADRChecker.check_sections(adr_text)` evaluates, for each of the five core
MADR sections, whether the section is present and whether its content is
consistent with its purpose:

| Section | Expected purpose |
|---------|------------------|
| Context | Background, problem statement, forces/constraints |
| Decision | The chosen solution and its rationale |
| Consequences | Positive/negative impacts and trade-offs |
| Decision Drivers | Key requirements/constraints driving the decision |
| Considered Options | Alternatives evaluated before deciding |

For each section the checker reports presence, a content-quality score, a
purpose-consistency flag, and specific issues. `ADRChecker.check()` runs both
assessments and merges the results.

### Outputs

Batch runs are saved as JSON (e.g., `results/all_projects-checks_results*.json`).
These outputs support aggregate analyses such as the MADR-adherence statistics
reported below (~80% Status field, ~65% decision drivers, ~50% consequences,
~40% alternatives) and the adherence heatmap in `figures/`.

See [Architecture → ADR Checking Flow](ARCHITECTURE.md#adr-checking-flow) for
the component-level pipeline.

---

## LLM Classification Approach

### Model Configuration

- **Base Model**: GPT-4o-mini (cost-effective + good accuracy)
- **Temperature**: 0.0 (deterministic outputs)

### Prompting Strategies

#### 1. Zero-shot Classification
No examples provided; LLM relies on framework definitions.

**Pros**: Fast, requires no training data  
**Cons**: Lower accuracy, more inconsistent

#### 2. Few-shot Classification (Static)
Pre-defined examples (5-7 per category) included in prompt.

**Pros**: Improved consistency, straightforward implementation  
**Cons**: Manual example selection, limited adaptation

#### 3. Dynamic Few-shot Classification
Semantic similarity-based selection of most relevant examples per prediction.

**Pros**: Adaptive to each ADR, improved accuracy  
**Cons**: Computational overhead, requires ground truth examples

### Output Structure

LLM produces structured JSON:

```json
{
  "framework": "quality_attributes",
  "primary_category": "Maintainability",
  "explanation": "Describes why this category was chosen based on ADR content",
  "primary_score": 0.87,
  "alternative_categories": ["Performance", "Scalability"],
  "alternative_confidence_scores": [0.08, 0.05]
}
```


---

## Evaluation Methodology

### Ground Truth Collection

- Manual annotation of ~200 ADR samples
- Stratified sampling covering all decision categories
- Multiple annotators for inter-rater reliability assessment


### Analysis Approach

1. **Alignment Assessment**: Compare LLM predictions to ground truth labels
2. **Category-wise Analysis**: Evaluate performance per framework category
3. **Error Pattern Analysis**: Identify which category pairs are confused

---

## Key Findings Summary

### Topic Discovery Results

- **Topics discovered**: ~70 depending on corpus and configuration
- **Topic coherence**: 0.65-0.75 (good internal consistency)
- **Topic diversity**: 0.60-0.70 (adequate distinctiveness)

**Top topic themes** (by frequency):
- Technology/framework choices (~25%)
- Architectural patterns (~20%)
- Performance/scalability (~18%)
- Testing/CI/CD (~15%)
- Other concerns (~22%)

### Classification Performance

**Overall Metrics** (across all frameworks):
- **Accuracy**: 72-80% depending on framework
- **Matthews Correlation**: 0.65-0.70


### Quality Attribute Coverage

**Well-represented** in ADRs:
- Performance, Scalability, Security
- Reliability, Maintainability

**Underrepresented** in ADRs:
- Usability, Portability, Observability
- Testability

### MADR Template Adherence (RQ3)

- ~80%: Include Status field
- ~65%: Document decision drivers/rationale
- ~50%: Include consequences section
- ~40%: Compare/discuss alternatives
- **Variability**: High differences across projects


---

## Limitations

1. **Scope Limitation**: Open-source projects only (may not represent enterprise/proprietary ADRs)
2. **Language**: English-language ADRs only
3. **Template Bias**: Primarily MADR-style documents; other formats not extensively tested
4. **LLM Dependency**: Results tied to specific LLM model performance; may vary with alternatives
5. **Ground Truth Size**: Limited manual annotation due to effort constraints
6. **Temporal Aspect**: Static snapshot; doesn't track ADR or decision evolution over time
7. **Project Diversity**: GitHub projects may not represent full diversity of software domains

---

## Future Research Directions

### Short-term
1. **Multi-language Support**: Extend to non-English ADRs
2. **Template Compliance**: Detailed analysis of MADR section completeness
3. **Cross-model Comparison**: Evaluate with different LLM providers
4. **Confidence Calibration**: Improve confidence score reliability

### Medium-term
1. **Decision Evolution**: Track how decisions change over time
2. **Cross-project Patterns**: Identify decision patterns by project type/domain
3. **Fine-tuned Models**: Train domain-specific classifiers
4. **Consequence Analysis**: Predict decision consequences from context

### Long-term
1. **Consequence Validation**: Measure actual outcomes of documented decisions
2. **Decision Quality Assessment**: Score decisions on quality/soundness
3. **Tool Integration**: IDE/GitHub plugins for real-time ADR analysis
4. **Knowledge Graphs**: Build decision relationship graphs

---

## Reproducibility

All code, notebooks, and analysis scripts are available in the ADRMiner repository:
- **License**: Apache 2.0
- **Reproducibility Kit**: Includes all code, notebooks, and analysis workflows
- **Requirements**: See [requirements.txt](../requirements.txt)


---


This research provides architects and teams with insights into how architectural decisions are documented and classified in practice.