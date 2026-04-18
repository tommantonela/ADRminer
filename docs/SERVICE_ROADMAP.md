# ADRminer as a Service - Product Vision & Architecture

**Version:** 1.0  
**Date:** 2026-04-17  
**Status:** Planning Phase

---

## Table of Contents

1. [Product Vision](#1-product-vision)
2. [Key Features & Requirements](#2-key-features--requirements)
3. [Product Roadmap](#3-product-roadmap)
4. [Architecture Design](#4-architecture-design)
5. [Technology Stack](#5-technology-stack)
6. [Data Models](#6-data-models)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Summary](#8-summary)

---

## 1. Product Vision

### Vision Statement

Transform ADRminer from a research toolkit into an accessible, actionable tool that helps teams analyze, improve, and maintain their architectural decision records.

### Mission

Empower software teams to extract insights from their ADRs, ensure quality and consistency, and make more informed architectural decisions through automated analysis and intelligent recommendations.

### Value Proposition

- 📊 **Visibility**: Understand what decisions your team makes and why
- 🔍 **Quality**: Ensure ADRs follow best practices and templates
- 💡 **Insights**: Discover patterns, gaps, and improvement opportunities
- ⚡ **Efficiency**: Automate tedious analysis tasks
- 🎯 **Actionability**: Get specific recommendations to improve your ADRs

### Target Users

1. **Software Architects**: Understand decision patterns across projects
2. **Engineering Teams**: Ensure ADR quality and completeness
3. **Tech Leads**: Review and improve decision documentation
4. **Researchers**: Analyze architectural decisions in open-source projects

---

## 2. Key Features & Requirements

### Core Features (MVP)

#### F1: Topic Mining Service

**User Stories:**
- As a software architect, I want to discover the main topics in my ADRs to understand what my team focuses on
- As a researcher, I want to classify ADRs into topics to analyze architectural patterns

**Requirements:**
- [ ] Load pre-trained BERTopic model
- [ ] Predict topics for single ADR
- [ ] Predict topics for batch of ADRs
- [ ] Support custom topic model training
- [ ] Generate topic distribution visualizations
- [ ] Export topic metadata to JSON sidecar files

**Acceptance Criteria:**
- Process 100 ADRs in under 2 minutes
- Return topic labels, probabilities, and keywords
- Support at least 3 embedding models (MiniLM, all-mpnet, custom)

#### F2: Classification Service

**User Stories:**
- As a tech lead, I want to classify ADRs using established frameworks to categorize decisions
- As a researcher, I want to compare different classification approaches

**Requirements:**
- [ ] Support Kruchten framework (4 categories)
- [ ] Support Quality Attributes framework (10 categories)
- [ ] Support Zimmermann framework (9 categories)
- [ ] Zero-shot classification (no examples)
- [ ] Few-shot classification with custom examples
- [ ] Few-shot classification with built-in examples
- [ ] Batch classification with parallel processing
- [ ] Multiple LLM providers (via LangChain)
- [ ] Confidence scores and alternative categories

**Acceptance Criteria:**
- Classification accuracy > 80% (based on ground truth)
- Support OpenAI, Anthropic, and local models
- Process 50 ADRs with GPT-4o-mini in under 5 minutes

#### F3: ADR Checking Service

**User Stories:**
- As an engineering manager, I want to ensure all ADRs follow the MADR template
- As a developer, I want to know which sections are missing or incomplete in my ADRs

**Requirements:**
- [ ] Check MADR template adherence (global analysis)
- [ ] Check individual section quality and completeness
- [ ] Section-wise consistency analysis
- [ ] Generate adherence scores (0.0-1.0)
- [ ] Identify missing sections
- [ ] Provide improvement suggestions
- [ ] Batch checking with parallel processing

**Acceptance Criteria:**
- Detect missing sections with 95% accuracy
- Provide adherence scores within 0.1 of human assessment
- Process 50 ADRs in under 3 minutes

#### F4: Insights Generation

**User Stories:**
- As a software architect, I want actionable recommendations to improve my ADR collection
- As a tech lead, I want to understand patterns and trends in my team's decisions

**Requirements:**
- [ ] Generate quality/completeness insights
- [ ] Detect patterns across ADRs
- [ ] Provide improvement recommendations
- [ ] Generate statistical summaries
- [ ] Identify outliers and anomalies
- [ ] Cross-service insights (topics × classification × checking)

**Acceptance Criteria:**
- Generate at least 3 unique insights per ADR collection
- Insights should be actionable and specific
- Support insight filtering by type and priority

#### F5: Metadata Export

**User Stories:**
- As a developer, I want analysis results stored alongside my ADRs for easy reference
- As a CI/CD pipeline, I want machine-readable output for automated processing

**Requirements:**
- [ ] JSON sidecar export (one `.metadata.json` per ADR)
- [ ] Consolidated JSON export (all ADRs in single file)
- [ ] Human-readable report generation (Markdown)
- [ ] Incremental updates (re-analyze only changed ADRs)
- [ ] Metadata versioning

**Acceptance Criteria:**
- JSON schema valid and documented
- Support incremental analysis (skip unchanged ADRs)
- Reports include visualizations (charts, tables)

#### F6: CLI Interface

**User Stories:**
- As a DevOps engineer, I want to integrate ADR analysis into CI/CD pipelines
- As a researcher, I want batch processing for large datasets

**Requirements:**
- [ ] Unified `adrminer` command
- [ ] Subcommands for each service (classify, topics, check, analyze)
- [ ] Model management commands (train, list, info)
- [ ] Report generation command
- [ ] Configuration via environment variables and config files
- [ ] Progress bars and verbose output
- [ ] Error handling and validation

**Acceptance Criteria:**
- All CLI commands have `--help` documentation
- Support both single ADR and batch processing
- Exit codes for CI/CD integration

#### F7: Streamlit Web UI

**User Stories:**
- As a non-technical stakeholder, I want a simple interface to view ADR insights
- As a software architect, I want interactive visualizations of my ADR collection

**Requirements:**
- [ ] File/folder selection interface
- [ ] Service configuration (framework, model, examples)
- [ ] Results visualization (charts, tables, summaries)
- [ ] Individual ADR detail view
- [ ] Batch processing with progress indication
- [ ] Export/download functionality
- [ ] Responsive design

**Acceptance Criteria:**
- Load and analyze 50 ADRs in browser
- Interactive charts for topic distribution, classification balance
- Mobile-friendly interface

---

## 3. Product Roadmap

### Phase 1: MVP (4-6 weeks)

**Focus:** Core functionality with CLI and basic UI

#### Sprint 1-2: Foundation (Week 1-2)
- Service layer architecture
- Model packaging and loading
- JSON sidecar exporter
- Basic CLI structure

#### Sprint 3-4: Core Services (Week 3-4)
- Topic mining service (pre-trained model)
- Classification service (all 3 frameworks)
- Checking service (MADR template)
- Basic insights generation

#### Sprint 5-6: Interfaces (Week 5-6)
- Complete CLI with all commands
- Streamlit UI with basic features
- Documentation and examples

**MVP Deliverables:**
- ✅ CLI tool with all core services
- ✅ Streamlit UI for interactive use
- ✅ Pre-trained models packaged
- ✅ JSON sidecar export
- ✅ Basic insights and reports
- ✅ User documentation

---

### Phase 2: Enhanced Features (4-6 weeks)

**Focus:** Advanced insights and user experience

#### Sprint 7-8: Advanced Insights
- Pattern detection algorithms
- Anomaly identification
- Trend analysis over time
- Cross-project comparison
- Recommendation engine

#### Sprint 9-10: Enhanced UI
- Interactive visualizations (D3.js)
- ADR comparison view
- History and version tracking
- Dark mode and theming
- Export to PDF/HTML

#### Sprint 11-12: Model Management
- Custom model training UI
- Model performance metrics
- A/B testing models
- Model versioning and rollback

**Phase 2 Deliverables:**
- ✅ Advanced insights engine
- ✅ Interactive dashboards
- ✅ Model management CLI/UI
- ✅ Enhanced visualizations
- ✅ ADR comparison tools

---

### Phase 3: Enterprise Features (6-8 weeks)

**Focus:** Scalability, integration, and advanced features

#### Sprint 13-15: Integration & Automation
- FastAPI REST API
- CI/CD integration examples
- Webhook support
- Scheduled analysis
- Git integration (analyze on commit)

#### Sprint 16-17: Collaboration
- Multi-user support (basic auth)
- Comment and annotation system
- Review workflows
- Team insights (aggregate across teams)

#### Sprint 18-20: Advanced Analytics
- Natural language insights
- Decision impact tracking
- Cost/benefit analysis suggestions
- Architecture health score

**Phase 3 Deliverables:**
- ✅ REST API for programmatic access
- ✅ CI/CD integration guides
- ✅ Team collaboration features
- ✅ Advanced analytics
- ✅ Architecture health metrics

---

### Phase 4: Platform & Ecosystem (Ongoing)

**Focus:** Platform capabilities and community

- Cloud-hosted service (SaaS)
- Plugin system for custom analyzers
- Community model marketplace
- Integration with popular ADR tools (MADR, Nix)
- API for third-party integrations
- Mobile app for quick insights

---

## 4. Architecture Design

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interfaces                          │
├─────────────────────┬───────────────────┬──────────────────────┤
│      CLI (Click)    │  Streamlit UI     │   FastAPI (Future)   │
└──────────┬──────────┴─────────┬─────────┴──────────┬───────────┘
           │                    │                      │
           ▼                    ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
├──────────────┬──────────────┬──────────────┬──────────────────┤
│ Topic Service │ Class. Service│ Check Service│ Insights Service  │
└───────┬──────┴───────┬──────┴───────┬──────┴──────┬───────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Model Layer                                 │
├──────────────┬──────────────┬──────────────┬──────────────────┤
│ BERTopic      │ LLM Wrapper   │ MADR Checker  │ Analyzer Engine  │
│ (Sentence-    │ (LangChain)   │ (Pydantic)    │                 │
│ Transformers)  │              │              │                 │
└───────┬──────┴───────┬──────┴───────┬──────┴──────┬───────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Data & Storage Layer                           │
├──────────────┬──────────────┬──────────────┬──────────────────┤
│ Model Files   │ Examples DB   │ ADR Files    │ Metadata Files   │
│ ( packaged )  │ ( JSON )     │ ( Markdown )  │ ( JSON sidecar )│
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Detailed Component Architecture

#### 4.2.1 Service Layer

```python
# Core service interfaces
class TopicService:
    - load_model(model_path)
    - predict(text, metadata)
    - predict_batch(texts, metadata, parallel)
    - train_model(texts, output_path)
    - get_topic_distribution(results)

class ClassificationService:
    - configure_framework(framework, examples)
    - classify(text, metadata)
    - classify_batch(texts, metadata, parallel)
    - evaluate_with_ground_truth(ground_truth, predictions)

class CheckService:
    - check_madr_adherence(text, metadata)
    - check_sections(text, metadata)
    - check_batch(texts, metadata, parallel)
    - generate_completeness_report(results)

class InsightsService:
    - generate_quality_insights(check_results)
    - detect_patterns(all_results)
    - generate_recommendations(all_results)
    - create_statistical_summary(all_results)
    - cross_service_insights(topics, classification, checks)
```

#### 4.2.2 Model Layer

```python
# Model wrappers
class BERTopicModel:
    - __init__(embedding_model, representation_model)
    - load(path)
    - save(path)
    - fit(texts, topics)
    - transform(text)
    - transform_batch(texts)
    - get_topic_info()
    - get_topic_labels()

class LLMClassifier:
    - __init__(llm_provider, model_name, temperature)
    - set_framework(framework, examples)
    - classify(text)
    - classify_batch(texts, parallel)
    - configure_chain(framework)

class MADRChecker:
    - __init__(llm_provider, model_name)
    - check_global(text)
    - check_section_wise(text)
    - generate_score(sections)
```

#### 4.2.3 Data Flow

```
User ADRs (Markdown)
    ↓
Parser (extract text)
    ↓
┌─────────────────────────────────────┐
│         Service Layer                │
├──────────────┬──────────────┬──────┤
│ Topic Mining  │ Classification│ Check│
│              │              │      │
│ BERTopic      │ LLM (LangChain)│    │
└───────┬──────┴───────┬──────┴──────┘
        │              │              │
        ▼              ▼              ▼
  Topic Results  Classification  Check Results
    Data            Data            Data
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              ┌─────────────────┐
              │ Insights Engine  │
              └────────┬────────┘
                       ▼
            Actionable Insights
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
  JSON Sidecar    Reports    Visualizations
```

### 4.4 Directory Structure

```
adrminer/
├── adrminer/
│   ├── __init__.py
│   ├── config.py                    # Configuration management
│   ├── models/                      # Model management
│   │   ├── __init__.py
│   │   ├── topic_model.py          # BERTopic wrapper
│   │   ├── classification_model.py  # LLM wrapper
│   │   └── checker_model.py        # MADR checker
│   ├── services/                    # Business logic layer
│   │   ├── __init__.py
│   │   ├── topic_service.py
│   │   ├── classification_service.py
│   │   ├── check_service.py
│   │   └── insights_service.py     # Generates actionable insights
│   ├── exporters/                   # Output formats
│   │   ├── __init__.py
│   │   ├── json_exporter.py         # Sidecar JSON files
│   │   └── report_generator.py      # Human-readable reports
│   ├── examples/                     # Few-shot examples database
│   │   ├── __init__.py
│   │   ├── kruchten_examples.json
│   │   ├── qas_examples.json
│   │   └── zimmermann_examples.json
│   └── utils.py
├── cli/
│   ├── __init__.py
│   ├── main.py                      # CLI entry point
│   └── commands/                    # CLI commands
│       ├── __init__.py
│       ├── classify.py
│       ├── topics.py
│       ├── check.py
│       ├── analyze.py
│       └── train.py                 # Re-training commands
├── ui/
│   ├── __init__.py
│   ├── streamlit_app.py             # Streamlit interface
│   └── components/                  # UI components
│       ├── __init__.py
│       ├── upload.py
│       ├── results.py
│       └── insights.py
├── api/                              # Optional FastAPI layer
│   ├── __init__.py
│   ├── main.py
│   └── routes/
│       ├── __init__.py
│       ├── classification.py
│       ├── topics.py
│       └── check.py
├── models/                           # Pre-trained model storage
│   ├── topic_model/
│   │   ├── config.json
│   │   ├── topics.json
│   │   └── topics_dataframe.pickle
│   └── examples/
│       ├── kruchten_examples.json
│       ├── qas_examples.json
│       └── zimmermann_examples.json
├── tests/
│   ├── __init__.py
│   ├── test_services/
│   ├── test_models/
│   └── test_cli/
├── docs/
│   ├── SERVICE_ROADMAP.md            # This document
│   ├── API.md
│   └── USER_GUIDE.md
├── setup.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 5. Technology Stack

### 5.1 Core Technologies

| Component | Technology | Rationale |
|-----------|-------------|-----------|
| **Language** | Python 3.10+ | Existing codebase, ML ecosystem |
| **CLI Framework** | Click | Clean API, excellent documentation, composable |
| **Web UI** | Streamlit | Pure Python, rapid prototyping, built-in widgets |
| **Web Framework** | FastAPI (future) | Async, auto-docs, type hints, Pydantic integration |
| **LLM Integration** | LangChain | Multi-provider support, chains, structured output |
| **Topic Modeling** | BERTopic | Industry standard, flexible, good performance |
| **Embeddings** | Sentence-Transformers | State-of-the-art, multiple models available |
| **Data Models** | Pydantic | Validation, serialization, JSON schema |
| **CLI Progress** | tqdm, rich | Progress bars, colored output, tables |
| **Visualization** | Plotly, matplotlib | Interactive charts, publication quality |

### 5.2 LLM Providers (via LangChain)

- **Primary**: OpenAI (GPT-4o-mini, GPT-4o)
- **Alternative**: Anthropic (Claude 3 Haiku/Sonnet)
- **Local**: Ollama (Llama 3, Mistral)
- **Future**: Google Gemini, Azure OpenAI

### 5.3 Storage & Packaging

- **Model Storage**: Package with `pip` (safetensors format)
- **Examples Database**: JSON files in package
- **Configuration**: TOML + environment variables
- **Metadata**: JSON sidecar files
- **Package Manager**: pip + setuptools

### 5.4 Development Tools

- **Testing**: pytest, pytest-cov
- **Linting**: ruff (fast), mypy (type checking)
- **Documentation**: Sphinx, MkDocs
- **CI/CD**: GitHub Actions
- **Code Quality**: pre-commit hooks (black, isort)

---

## 6. Data Models

### 6.1 Metadata Schema

```json
{
  "version": "1.0.0",
  "adr_file": "adr-001.md",
  "analyzed_at": "2026-04-17T12:00:00Z",
  "model_versions": {
    "topic_model": "v1.0",
    "classification_llm": "gpt-4o-mini",
    "check_llm": "gpt-4o-mini"
  },
  "classification": {
    "kruchten": {
      "primary_category": "Existence",
      "confidence": 0.92,
      "alternatives": ["Property"],
      "explanation": "..."
    }
  },
  "topics": [
    {
      "id": 5,
      "label": "Database Migration",
      "probability": 0.85,
      "keywords": ["database", "migration", "schema"],
      "representation": "KeyBERT"
    }
  ],
  "check": {
    "template_adherence": 0.78,
    "missing_sections": ["alternatives"],
    "section_assessments": [
      {
        "section_name": "context",
        "presence": "Yes",
        "content_quality": "Yes",
        "purpose_consistency": "Yes",
        "justification": "..."
      }
    ]
  },
  "insights": {
    "quality": [
      "Add alternatives section for better completeness"
    ],
    "patterns": [
      "Similar to ADR-003, ADR-007"
    ],
    "recommendations": [
      "Consider Zimmermann framework for organizational decisions"
    ]
  }
}
```

### 6.2 Insights Schema

```json
{
  "collection_id": "my-project-adrs",
  "analyzed_at": "2026-04-17T12:00:00Z",
  "adr_count": 25,
  "summary": {
    "topics": {
      "total_topics": 8,
      "dominant_topic": "Database Migration",
      "topic_diversity": 0.75
    },
    "classification": {
      "framework": "kruchten",
      "category_distribution": {
        "Existence": 15,
        "Property": 6,
        "Ban": 2,
        "Executive": 2
      },
      "avg_confidence": 0.89
    },
    "checks": {
      "avg_adherence": 0.72,
      "common_missing_sections": ["alternatives"],
      "quality_score": 0.68
    }
  },
  "insights": [
    {
      "type": "quality",
      "priority": "high",
      "message": "40% of ADRs are missing the alternatives section",
      "affected_adrs": ["adr-003", "adr-007", "adr-012"]
    },
    {
      "type": "pattern",
      "priority": "medium",
      "message": "Recent ADRs show better context descriptions",
      "evidence": "Last 5 ADRs have avg. context length of 150 words vs 100 previously"
    },
    {
      "type": "recommendation",
      "priority": "medium",
      "message": "Consider Zimmermann framework for organizational decisions",
      "rationale": "4 ADRs classified as Executive might fit better in Zimmermann"
    }
  ]
}
```

---

## 7. Non-Functional Requirements

### Performance

- **Topic Mining**: < 2 seconds per ADR (batch mode)
- **Classification**: < 6 seconds per ADR (GPT-4o-mini)
- **Checking**: < 4 seconds per ADR
- **Batch Processing**: Support 100+ ADRs with parallel execution

### Scalability

- Handle projects with 500+ ADRs
- Support multiple concurrent analyses
- Incremental analysis (skip unchanged ADRs)

### Reliability

- 95% accuracy on classification (vs human ground truth)
- Graceful degradation when LLM API fails
- Retry logic for network failures

### Usability

- CLI completion and help for all commands
- Progress indication for long-running operations
- Clear error messages with actionable suggestions

### Extensibility

- Plugin system for custom analyzers (future)
- Support for additional classification frameworks
- Custom insight generators

### Security

- No ADR data sent to external services (local models option)
- API key management for LLM providers
- No telemetry or tracking (privacy-first)

---

## 8. Summary

This product transforms ADRminer into a practical tool that helps teams:

1. **Understand** their architectural decisions through analysis
2. **Improve** ADR quality with actionable insights
3. **Automate** tedious analysis tasks
4. **Scale** decision documentation across projects

The architecture is modular, extensible, and built on proven technologies. The roadmap progresses from MVP (core functionality) to enhanced features, then to enterprise capabilities, with clear milestones and deliverables.

### Next Steps

1. ✅ **Planning Complete** - Architecture and roadmap defined
2. 🔄 **Implementation Ready** - All requirements documented
3. 📋 **Start Development** - Begin Phase 1 (MVP)

---

**Document History:**
- v1.0 - Initial planning document (2026-04-17)