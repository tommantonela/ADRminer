# Usage Guide

Complete workflow and API documentation for ADRMiner.

## Notebook Workflow

### 1. Topic Modeling (`adrs_bertopic.ipynb`)

Discover topics in your ADR corpus using BERTopic.

```python
from adr_topic_mining import ADRTopicModel

# Initialize and prepare corpus
model = ADRTopicModel()
model.prepare_corpus(docs=your_adr_dict)

# Build topic model
topics_df = model.build(n_topics=50, use_openai=True)

# Save for later use
model.persist("./saved_topicmodel")
```

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `prepare_corpus(docs)` | Extract and clean ADR texts |
| `build(n_topics, use_openai)` | Train BERTopic model |
| `load(folder)` | Load previously saved model |
| `persist(folder)` | Save model and corpus |
| `get_topk_topics(k)` | Get top-K topics by frequency |
| `predict(adr_text, multiple_topics)` | Classify new ADR into topics |
| `compute_topic_coherence()` | Measure topic quality |
| `compute_topic_diversity()` | Measure topic uniqueness |

**Parameters:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `n_topics` | Target number of topics (None = auto-detect) | None |
| `use_openai` | Use GPT-4 for topic labeling (requires API key) | False |
| `language` | Stop words language for vectorization | 'english' |
| `predefined_embedding_model` | Sentence transformer model | 'all-MiniLM-L6-v2' |

**Output:**

Topics dataframe with columns:
- `Topic`: Topic ID
- `Count`: Number of documents assigned
- `Main`: KeyBERT-based topic label
- `OpenAI` (if enabled): GPT-generated topic label

---

### 2. Classification (`adr_llm_classification.ipynb`)

Classify ADRs using LLM across multiple frameworks.

```python
from adr_classification import ADRClassifier, ClassificationFramework
from langchain_openai import ChatOpenAI

# Initialize LLM
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.0)

# Create classifier
classifier = ADRClassifier(llm)

# Set framework (zero-shot)
classifier.set_framework(
    ClassificationFramework.QUALITY_ATTRIBUTES,
    include_examples=False
)

# Classify single ADR
result = classifier.classify(adr_text)

# Classify batch
results = classifier.classify_batch(
    adr_texts_dict,
    organization="org-name",
    project="project-name",
    parallel=True,
    json_file="results.json"
)
```

**Classification Frameworks:**

#### Kruchten (4 categories)
- Existence (ontocrisis): Adding new capabilities
- Ban/Non-Existence (anticrisis)**: Removing/avoiding options
- Property (diacrisis): Modifying quality properties
- Executive (pericrisis): Managing organizational aspects

#### Quality Attributes (10 categories)
- Performance, Reliability, Security, Maintainability, Scalability
- Usability, Portability, Compatibility, Observability, Testability
- Other/Functional Concern

#### Zimmermann (9 categories)  
- Design, Technology, Infrastructure, Organizational/Process
- Constraint, Quality Attribute, Crosscutting Concerns, Implementation, Other

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `set_framework(framework, include_examples, examples, k)` | Configure classification strategy |
| `classify(adr_text, as_dict, metadata)` | Single ADR classification |
| `classify_batch(adr_texts, parallel, json_file)` | Batch classification |
| `evaluate_on_ground_truth(ground_truth, llm_results)` | Compute metrics vs. human labels |
| `predict_and_evaluate_on_ground_truth(gt_df, parallel)` | End-to-end prediction + evaluation |

**Few-shot Strategies:**

```python
# Zero-shot (no examples)
classifier.set_framework(framework, include_examples=False)

# Static few-shot (pre-defined examples)
classifier.set_framework(framework, include_examples=True)

# Dynamic few-shot (select similar examples)
classifier.set_framework(
    framework,
    include_examples=True,
    examples=ground_truth_examples,
    k=5  # 5 most similar examples per prediction
)
```

---

### 3. Analysis (`classification_analysis.ipynb`)

Evaluate classification results and generate insights.

```python
from adr_classification import ADRClassifier

# Evaluate results
eval_results = classifier.predict_and_evaluate_on_ground_truth(
    ground_truth_df,
    parallel=True
)

# Access metrics
print(f"Matthews Correlation: {eval_results['matthews']}")
print(f"Accuracy: {eval_results['similarities']:.2f}%")

# Examine differences
differences = eval_results['differences']  # (index, true_label, pred_label, adr_key)

# Confusion matrix
cm = eval_results['confusion_matrix']
```

---

## Python API Reference

### `adr.py` – ADR Parsing

Parse and extract structure from markdown ADR documents.

```python
from adr import adr

# Load and parse a markdown ADR
doc = adr(path="path/to/adr-001.md")

# Or parse from string
doc = adr(path=None, content=markdown_content)

# Extract components
title = doc.get_title()                    # Main title
content = doc.get_content_no_code_str()    # Text without code
decision = doc.get_decision()              # Decision section only
hierarchy = doc.get_hierarchy()            # Nested structure
properties = doc.get_properties()          # Metadata (key: value pairs)

# Access full content
full = doc.get_full_content()              # Reconstructed markdown
raw = doc.get_full_raw_content()           # Original input

# Get code blocks only
code = doc.get_code()
```

**Methods:**

| Method | Returns |
|--------|---------|
| `get_title()` | str: Main document title |
| `get_content(title=None)` | str or dict: Paragraphs under section |
| `get_content_no_code_str(title=None)` | str: Content excluding code blocks |
| `get_decision()` | str: Extracted decision section |
| `get_hierarchy()` | dict: Section structure |
| `get_properties(key=None)` | dict or str: Metadata fields |
| `get_code(title=None)` | list or dict: Code blocks |
| `get_full_content()` | str: Reconstructed markdown |
| `get_titles(level=None)` | list: All titles or by level (h1-h4, p) |

---

### `adr_topic_mining.py` – Topic Modeling

Complete BERTopic integration with representation methods.

```python
from adr_topic_mining import ADRTopicModel

model = ADRTopicModel()
model.prepare_corpus(docs=adr_dict)
model.build(n_topics=50, use_openai=True)

# Get topic insights
top20 = model.get_topk_topics(k=20)
labels = model.get_topic_labels(representation='Main')
keywords = model.get_topic_words(topic_id=5, threshold=0.3)

# Predict on new texts
result = model.predict("New ADR text...", multiple_topics=True)
# result: {
#   'text': str,
#   'topics': [int],
#   'keywords': [[str]],
#   'keybert_representation': [str],
#   'openai_representation': [str],
#   'probabilities': [float]
# }

# Batch prediction
results = model.predict_batch(
    adr_texts_dict,
    organization="org",
    project="project",
    multiple_topics=True
)

# Quality metrics
coherence = model.compute_topic_coherence(top_n=20)
diversity = model.compute_topic_diversity(top_n=20)
```

---

### `adr_classification.py` – Classification

Complete LLM-based classification pipeline.

```python
from adr_classification import ADRClassifier, ClassificationFramework

classifier = ADRClassifier(llm)

# Configure framework
classifier.set_framework(
    ClassificationFramework.QUALITY_ATTRIBUTES,
    include_examples=True,      # Few-shot
    examples=None,              # Static examples
    k=7                         # 7 examples per prediction
)

# Classify
result = classifier.classify(adr_text)
# result: {
#   'framework': str,
#   'primary_category': str,
#   'explanation': str,
#   'primary_score': float (0-1),
#   'alternative_categories': [str],
#   'alternative_confidence_scores': [float]
# }

# Batch with metadata
results = classifier.classify_batch(
    adr_texts,
    organization="acme",
    project="backend",
    parallel=True,
    json_file="output.json"
)

# Evaluation
eval_dict = classifier.evaluate_on_ground_truth(
    ground_truth_df,
    llm_results,
    adr_key_column='ADR',
    adr_text_column='raw_text',
    true_label_column='human'
)
# eval_dict: {
#   'report': sklearn classification_report,
#   'confusion_matrix': pd.DataFrame,
#   'matthews': float,
#   'similarities': float (% match),
#   'differences': list (mismatch tuples),
#   'labels': list (all unique labels)
# }
```

---

## Configuration

### Environment Variables (`.env`)

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL_NAME=gpt-4o-mini
```

### Notebook Parameters

Key parameters to adjust in notebooks:

| Parameter | Effect | Suggested Range |
|-----------|--------|-----------------|
| `n_topics` | Number of BERTopic clusters | 20-100 |
| `use_openai` | GPT-4 topic labeling | True/False |
| `include_examples` | Few-shot learning | True/False |
| `temperature` | LLM creativity (0=deterministic) | 0.0-1.0 |
| `parallel` | Batch processing | True/False |
| `embedding_model` | Sentence transformer | 'all-MiniLM-L6-v2', 'all-mpnet-base-v2' |
| `metric` | Distance metric for UMAP | 'cosine', 'euclidean' |

---

## Tips & Best Practices

### Topic Modeling
- **Corpus size**: Minimum 50 ADRs for stable topic modeling
- **Embeddings**: `all-MiniLM-L6-v2` is fast; `all-mpnet-base-v2` is more accurate
- **Topics**: Auto-detection usually finds 30-60 topics; adjust manually if needed
- **OpenAI**: Requires API key for computing text embeddings (one-time cost)

### Classification
- **LLM choice**: `gpt-4o-mini` is cost-effective; `gpt-4o` is more accurate
- **Temperature**: Use 0.0 for consistent results; increase only if variation is desired
- **Few-shot**: 5-7 examples usually optimal; more examples can confuse the model

### Ground Truth Evaluation
- **Sample size**: Annotate at least 100 ADRs for reliable metrics
- **Stratification**: Ensure ground truth covers all decision categories evenly, if possible

---

## Examples

### Complete Topic + Classification Pipeline

```python
import json
from adr_topic_mining import ADRTopicModel
from adr_classification import ADRClassifier, ClassificationFramework
from langchain_openai import ChatOpenAI

# Step 1: Load ADRs and extract texts
adrs_dict = load_adrs_from_repos(...)  # Your data loading
adr_texts = {adr_key: adr.get_content_no_code_str() 
             for repo, adrs in adrs_dict.items() for adr_key, adr in adrs.items()}

# Step 2: Topic modeling
topic_model = ADRTopicModel()
topic_model.prepare_corpus(docs=adr_texts)
topics_df = topic_model.build(n_topics=50, use_openai=True)
topic_model.persist("./saved_topicmodel")

# Step 3: Get topic predictions
topic_results = topic_model.predict_batch(adr_texts, json_file="topics.json")

# Step 4: Classify ADRs
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.0)
classifier = ADRClassifier(llm)
classifier.set_framework(ClassificationFramework.QUALITY_ATTRIBUTES, include_examples=True)

classifications = classifier.classify_batch(
    adr_texts,
    parallel=True,
    json_file="classifications.json"
)

# Step 5: Evaluate (if you have ground truth)
gt_df = pd.read_csv("ground_truth.csv")
eval_results = classifier.evaluate_on_ground_truth(gt_df, classifications)

print(f"Matthews: {eval_results['matthews']:.3f}")

# Save results
with open("evaluation_results.json", "w") as f:
    json.dump({k: v.to_dict() if hasattr(v, 'to_dict') else str(v) 
               for k, v in eval_results.items()}, f, indent=2)
```

---

**See [Input Format](INPUT_FORMAT.md) for data structure requirements.**
