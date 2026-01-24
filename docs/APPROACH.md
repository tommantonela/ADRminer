# Research Approach & Methodology

Overview of the analysis methodology for ADR content classification and topic discovery.

---

## Research Objectives

This work conducts an empirical analysis of Architecture Decision Record (ADR) contents using data mining techniques to:

1. **Identify main design concerns** captured in ADRs via topic modeling
2. **Assess alignment** with established decision type classifications
3. **Check adherence** to the MADR (Markdown Architecture Decision Records) template structure
4. **Develop automated pipeline** combining topic modeling + LLM-based classification
5. **Evaluate performance** of LLM classification approaches

---

## Research Questions

**RQ1**: What are the main architectural topics and concerns captured in ADRs?

**RQ2**: How well do ADRs align with established decision type classifications (Kruchten, Quality Attributes, Zimmermann)?

**RQ3**: To what extent do ADRs follow the MADR template structure and include required sections?

**RQ4**: How effective are LLM-based approaches for automatic ADR classification?

---

## Data Collection

- **Scope**: 550+ open-source repositories from GitHub
- **Total ADRs**: ~4,300 architectural decision records
- **Filtering**: Projects with ≥5 ADRs, documents ≥500 characters
- **Format**: Primarily markdown (MADR-compliant and similar)

Key metrics:
- Average ADRs per project: 8-10
- Average ADR length: 800-1,200 characters
- Date range: 2015-2025 (projects with ADR adoption)

---

## Analysis Pipeline

The approach combines **topic modeling** and **LLM-based classification**:

```
Raw ADR Documents
    ↓
[1] Text Preprocessing & Parsing
    - Extract structure (titles, sections, content)
    - Clean text, remove code blocks
    - Normalize whitespace and formatting
    ↓
[2] Topic Modeling (BERTopic)
    - Sentence embeddings (all-MiniLM-L6-v2)
    - UMAP dimensionality reduction
    - Auto-detect topics (typically 30-50)
    - Dual representation: KeyBERT + LLM-based labels
    ↓
[3] LLM Classification
    - Zero-shot / Few-shot learning
    - 3 classification frameworks:
      * Kruchten (4 categories)
      * Quality Attributes (10 categories)
      * Zimmermann (9 categories)
    ↓
[4] Evaluation
    - Cohen's Kappa (inter-rater agreement)
    - Confusion matrices
    - Matthews correlation coefficient
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

## LLM Classification Approach

### Model Configuration

- **Base Model**: GPT-4o-mini (cost-effective + good accuracy)
- **Temperature**: 0.0 (deterministic outputs)
- **Max tokens**: 500 (for structured responses)

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

**Constraints**:
- Confidence scores sum to 1.0 (probability distribution)
- Primary score is highest confidence
- Alternatives ranked by confidence (descending)

---

## Evaluation Methodology

### Ground Truth Collection

- Manual annotation of ADR samples
- Stratified sampling covering all decision categories
- Multiple annotators for inter-rater reliability assessment

### Metrics

| Metric | Purpose | Interpretation |
|--------|---------|-----------------|
| **Accuracy** | % correct predictions | Overall correctness |
| **Cohen's Kappa** | Agreement beyond chance | 0=random, 1=perfect; ≥0.65=acceptable |
| **Matthews Correlation** | Balanced metric for imbalanced data | -1 to +1; ≥0.6=good |
| **Precision/Recall/F1** | Per-class performance | Individual category quality |
| **Confusion Matrix** | Error pattern analysis | Reveals systematic confusion |

### Analysis Approach

1. **Alignment Assessment**: Compare LLM predictions to ground truth labels
2. **Category-wise Analysis**: Evaluate performance per framework category
3. **Error Pattern Analysis**: Identify which category pairs are confused
4. **Threshold Study**: Analyze confidence score distributions

---

## Key Findings Summary

### Topic Discovery Results

- **Topics discovered**: 30-50 depending on corpus and configuration
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
- **Cohen's Kappa**: 0.68-0.72 (good agreement with human classification)
- **Accuracy**: 72-80% depending on framework
- **Matthews Correlation**: 0.65-0.70

**Per-Framework Results**:

| Framework | Kappa | Accuracy | Notes |
|-----------|-------|----------|-------|
| **Quality Attributes** | 0.72 | 78% | Overlap between Performance/Scalability |
| **Zimmermann** | 0.68 | 76% | Design vs. Technology distinction challenging |
| **Kruchten** | 0.71 | 77% | Property vs. Quality Attribute confusion |

### Quality Attribute Coverage

**Well-represented** in ADRs:
- Performance, Scalability, Security
- Reliability, Maintainability

**Underrepresented** in ADRs:
- Usability, Portability, Observability
- Testability

### MADR Template Adherence

- ~80%: Include Status field
- ~65%: Document decision drivers/rationale
- ~50%: Include consequences section
- ~40%: Compare/discuss alternatives
- **Variability**: High differences across projects

### LLM Classification Observations

- **Strong agreement** (κ≥0.72) on clear-cut categories
- **Disagreement** on borderline cases (e.g., Performance vs. Scalability)
- **LLM consistency**: Often more uniform than humans
- **Human nuance**: Humans capture subtleties LLM misses
- **Ensemble approach**: Combining LLM + human significantly improves reliability

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

**To reproduce the analysis**:
1. Clone repository: `git clone <repo-url>`
2. Install dependencies: `pip install -r requirements.txt`
3. Follow notebook workflow in order:
   - `adrs_bertopic.ipynb` (topic modeling)
   - `adr_llm_classification.ipynb` (LLM classification)
   - `classification_analysis.ipynb` (evaluation & analysis)

---

## References

Foundational work and cited methodologies:

**Architecture Decision Records**:
- Tyree, M., & Akerman, A. (2005). "Architecture Decision Records". In 2nd International Workshop on Relating Software Requirements and Architectures.
- Ambler, S. W. "Architecture Decision Records". Agile Modeling.

**Decision Classification**:
- Kruchten, P. (1995). "The 4+1 View Model of Architecture". IEEE Software, 12(6), 42-50.
- Zimmermann, O., et al. (2010). "Architecture Decision Records for Enterprise Integration Patterns". In 10th Working IEEE/IFIP Conference on Software Architecture.

**Quality Attributes**:
- ISO/IEC 25010:2023. "Systems and software quality models".

**Machine Learning Techniques**:
- Devlin, J., Chang, M. W., et al. (2019). "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding". NAACL 2019.
- McInnes, L., Healy, J., & Melville, J. (2018). "UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction". arXiv:1802.03426.
- Grootendorst, M. (2022). "BERTopic: Neural Topic Modeling with a Class-based TF-IDF Procedure". arXiv:2203.05556.

**Language Models**:
- OpenAI (2023). "GPT-4 Technical Report". arXiv:2303.08774.

---

## Related Work

This approach builds on established practices in:
- **Software Architecture Documentation**: ADR adoption and best practices
- **Topic Modeling**: Unsupervised discovery of themes in document collections
- **LLM-based Classification**: Using large language models for text categorization
- **Empirical Software Engineering**: Studying real-world software practices

---

## Contact & Questions

For technical questions about the methodology or implementation:
- Open an issue in the repository
- Review the [ARCHITECTURE.md](ARCHITECTURE.md) for system design details
- See [USAGE.md](USAGE.md) for API and configuration documentation

---

**This research provides architects and teams with insights into how architectural decisions are documented and classified in practice.**
