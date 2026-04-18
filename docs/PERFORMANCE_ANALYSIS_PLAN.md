# Performance ADR Analysis: Comprehensive Plan

## Overview

This document outlines the complete analysis plan for exploring Architecture Decision Records (ADRs) classified as Performance-related. The analysis will combine topic modeling (both new and existing models), LLM-based extraction of pros/cons using Chain-of-Thought prompting, and construction of a knowledge graph to identify common patterns, contexts, and drivers for performance decisions.

## Analysis Objectives

1. **Filter Performance ADRs**: Extract all ADRs classified as Performance from the quality attributes classification results
2. **Dual Topic Modeling Approach**: 
   - Train a new topic model specifically on Performance ADRs
   - Reuse the existing general topic model and compare results
3. **Pros/Cons Extraction**: Use OpenAI GPT with CoT prompting to extract main decisions, pros, cons, and contexts from each Performance ADR
4. **Knowledge Graph Construction**: Build a comprehensive graph connecting ADRs, topics, pros/cons, organizations, projects, and decision drivers
5. **Pattern Discovery**: Identify common themes, trade-offs, and decision patterns in performance-related architecture decisions

---

## Phase 1: Setup and Data Preparation

### 1.1 Load Classification Results
- Import necessary libraries (pandas, json, os, pickle)
- Load `results/all_projects-qas_classification_results.json`
- Filter entries where `primary_category == "Performance"`
- Group Performance ADRs by organization and project
- Display statistics: count of Performance ADRs per org/project
- Export filtered ADRs to `results/performance_adrs_filtered.json`

### 1.2 Load ADR Content
- Load `data/LLM4ADR-adrs__adrs_english.pickle`
- Extract full ADR content for Performance entries using metadata (organization, project, adr_key)
- Validate data completeness and handle missing ADRs
- Create a clean dataset with: ADR content + full metadata

---

## Phase 2: Topic Modeling - Dual Approach

### 2.1 Approach A: Build New Performance-Specific Model
- Extract clean content from Performance ADRs using `utils.get_documents()`
- Create new `ADRTopicModel` instance
- Configure embeddings (SentenceTransformer: 'all-MiniLM-L6-v2')
- Configure UMAP parameters for topic dimensionality reduction
- Configure representation models:
  - KeyBERTInspired for keyword-based labels
  - OpenAI GPT for semantic labels (if API key available)
- Train BERTopic model ONLY on Performance corpus
  - Use `nr_topics='auto'` for automatic topic reduction
  - Optionally reduce to specific topic count
- Generate topic labels (KeyBERT + OpenAI)
- Save model to `saved_topicmodel/performance_specific/`
- Extract topics and topic distribution for Performance ADRs
- Export to `results/performance_topics_new_model.json`

### 2.2 Approach B: Reuse Existing General Model
- Load existing topic model from `saved_topicmodel/`
- Apply to Performance ADRs using `predict_batch()` method
- Extract topic predictions and probabilities for each Performance ADR
- Compare topic distributions between new and existing models
- Identify which topics are Performance-specific vs general architecture topics
- Export results to `results/performance_topics_existing_model.json`

### 2.3 Topic Analysis and Comparison
- Display top 20 topics for both approaches
- Show word clouds for key Performance topics using `show_wordcloud()`
- Visualize topic distributions across organizations/projects
- Compute and compare:
  - Topic coherence scores (`compute_topic_coherence()`)
  - Topic diversity scores (`compute_topic_diversity()`)
- Visualize topic hierarchies and similarities
- Generate comparative analysis between new vs existing models

---

## Phase 3: Pros/Cons Extraction via LLM

### 3.1 Design CoT Prompt for Pros/Cons Extraction
Create structured prompt with the following components:

```python
"""
You are analyzing Architecture Decision Records (ADRs) related to software performance.

Analyze the following ADR:

{ADR_CONTENT}

Provide a structured analysis with the following information:

1. Main Decision: Brief summary (2-3 sentences) of the main architectural decision
2. Performance Context: What specific performance concern drives this decision? (e.g., latency, throughput, resource usage, scalability)
3. Pros (Benefits/Advantages): List each advantage with brief explanation
4. Cons (Drawbacks/Risks): List each drawback or risk with brief explanation
5. Related Topics: What performance-related topics does this decision address? (e.g., caching, load balancing, database optimization)

Return your response as valid JSON with the following structure:
{
  "main_decision": "string",
  "performance_context": "string",
  "pros": [
    {"pro": "string", "explanation": "string"}
  ],
  "cons": [
    {"con": "string", "explanation": "string"}
  ],
  "related_topics": ["string", "string", ...]
}

Think step by step before providing the JSON output.
"""
```

### 3.2 Batch Processing with OpenAI
- Configure OpenAI client using existing setup from `adr_topic_mining.py`
- Process each Performance ADR individually to ensure quality
- Use `client.chat.completions.create()` with:
  - Model: from `os.environ["OPENAI_MODEL_NAME"]`
  - Temperature: 0.3 (for more focused responses)
  - Response format: JSON
- Implement retry logic for API failures
- Save raw LLM responses for verification and debugging
- Progress tracking with tqdm
- Estimate API costs based on token usage

### 3.3 Structured Output Processing
- Parse JSON responses from LLM
- Validate required fields are present
- Handle parsing errors gracefully
- Store structured data with ADR metadata
- Export to `results/performance_pros_cons_llm.json`

---

## Phase 4: Knowledge Graph Construction

### 4.1 Define Graph Schema

**Node Types:**
1. **ADR**: Represents individual Architecture Decision Records
   - Attributes: id, title, organization, project, file_path
2. **Topic**: Represents topics from topic modeling
   - Attributes: id, label, approach (new/existing), keywords[], probability
3. **Pro**: Represents a benefit/advantage
   - Attributes: id, text, explanation, embedding_vector
4. **Con**: Represents a drawback/risk
   - Attributes: id, text, explanation, embedding_vector
5. **Organization**: Represents software organizations
   - Attributes: id, name, adr_count
6. **Project**: Represents software projects
   - Attributes: id, name, organization, adr_count
7. **Context/Driver**: Represents performance concerns or decision drivers
   - Attributes: id, label, frequency

**Edge Types:**
1. **has_topic**: ADR → Topic (weight = topic_probability)
2. **has_pro**: ADR → Pro
3. **has_con**: ADR → Con
4. **contains**: Organization → Project
5. **belongs_to**: Project → Organization
6. **appears_in**: Topic → Organization (weight = frequency)
7. **appears_in**: Topic → Project (weight = frequency)
8. **drives**: Context/Driver → ADR
9. **relates_to**: Pro/Con → Topic (weight = similarity_score)
10. **similar_to**: Pro/Con → Pro/Con (weight = embedding_similarity)

### 4.2 Build Comprehensive Knowledge Graph

```python
import networkx as nx
import numpy as np
from sentence_transformers import SentenceTransformer

# Initialize graph
G = nx.DiGraph()

# Initialize embedding model for pros/cons similarity
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
```

**Step 1: Add Organization and Project Nodes**
- Iterate through unique organizations from metadata
- Create organization nodes with adr_count
- For each organization, add its projects as nodes
- Create "contains" edges

**Step 2: Add ADR Nodes**
- Add each Performance ADR as a node
- Include metadata: title, org, project, file_path
- Create "belongs_to" edges to projects

**Step 3: Add Topic Nodes and Edges**
- For each ADR, add all assigned topics (from both new and existing models)
- Include topic probability as edge weight
- Aggregate topic frequencies per organization/project
- Create "appears_in" edges with frequency weights

**Step 4: Add Pros and Cons Nodes**
- Extract pros and cons from LLM outputs
- Generate embeddings for each pro/con text
- Create nodes with embedding vectors
- Create "has_pro" and "has_con" edges from ADRs

**Step 5: Add Context/Driver Nodes**
- Extract performance contexts from LLM outputs
- Create unique context nodes
- Create "drives" edges from contexts to ADRs

**Step 6: Create Similarity Edges**
- Compute pairwise similarities between all pros
- Create "similar_to" edges above threshold (default: 0.8)
- Repeat for cons
- Compute similarities between pros/cons and topics
- Create "relates_to" edges above threshold (default: 0.7)

**Step 7: Export Graph**
- Save graph structure to `results/performance_knowledge_graph.json`
- Include:
  - All nodes with attributes
  - All edges with weights and relationship types
  - Graph metadata (creation date, thresholds used)

### 4.3 Graph Analysis

**Centrality Analysis:**
- Compute PageRank centrality for all nodes
- Identify most influential topics, pros, cons, and ADRs
- Analyze centrality by organization/project

**Community Detection:**
- Use Louvain or Leiden algorithm to detect communities
- Identify clusters of related concepts
- Analyze community composition (what types of nodes cluster together)

**Path Analysis:**
- Find common paths: Context → ADR → Topic → Pro/Con
- Analyze most frequent decision patterns
- Identify typical performance decision flows

---

## Phase 5: Synthesis and Knowledge Extraction

### 5.1 Common Performance Themes
- Identify dominant topics across all Performance ADRs
  - By frequency
  - By centrality
  - By both approaches (new vs existing model)
- Most frequent pros and cons
  - Aggregate by topic
  - Map to organizations/projects
- Performance decision patterns by organization/project type
  - Are there organization-specific patterns?
  - Do certain project types favor certain decisions?

### 5.2 Context and Driver Analysis
- Extract all unique contexts/drivers from LLM outputs
- Cluster contexts using embeddings
- Identify major context categories:
  - Latency concerns
  - Throughput optimization
  - Resource efficiency
  - Scalability requirements
  - Cost constraints
- Map contexts to specific performance topics
- Identify trade-offs: which contexts often lead to conflicting pros/cons?

### 5.3 Visualizations

**Note:** Visualizations will be determined during implementation based on findings.

**Planned Visualizations:**
1. **Interactive Knowledge Graph**: Using pyvis or networkx + matplotlib
   - Color nodes by type
   - Size nodes by centrality
   - Hover tooltips with details
   - Filterable by organization/project

2. **Topic Analysis**:
   - Word clouds for top Performance topics
   - Heatmap: topic frequency vs organization
   - Bar charts: top pros/cons per topic
   - Sankey diagrams: context → decision → topic flow

3. **Comparative Analysis**:
   - Side-by-side comparison: new vs existing model topics
   - Radar charts: topic distribution by organization
   - Network diagrams: topic co-occurrence patterns

4. **Pros/Cons Clusters**:
   - t-SNE/UMAP visualization of clustered pros and cons
   - Dendrograms: hierarchy of similar pros/cons
   - Scatter plots: pro/con similarity vs topic relevance

### 5.4 Export Results

**JSON Exports:**
1. `results/performance_adrs_filtered.json` - Filtered Performance ADRs with metadata
2. `results/performance_topics_new_model.json` - Topics from new Performance-specific model
3. `results/performance_topics_existing_model.json` - Topics from existing general model
4. `results/performance_pros_cons_llm.json` - LLM-extracted pros/cons with full responses
5. `results/performance_knowledge_graph.json` - Complete graph structure (nodes + edges)
6. `results/performance_analysis_metadata.json` - Analysis metadata (thresholds, parameters, dates)

**CSV Exports:**
1. `results/performance_adrs_summary.csv` - Each ADR with:
   - organization, project, file_path
   - topics (new model): [list with probabilities]
   - topics (existing model): [list with probabilities]
   - main_decision
   - performance_context
   - pros: [list]
   - cons: [list]

2. `results/performance_topics_frequency.csv` - Each topic with:
   - topic_id, label (both approaches)
   - total_frequency
   - frequency_by_organization
   - frequency_by_project
   - avg_probability
   - coherence_score
   - diversity_score

3. `results/performance_pros_cons_aggregated.csv` - Each pro/con with:
   - text
   - type (pro/con)
   - frequency
   - related_topics: [list]
   - related_contexts: [list]
  - similar_items: [list of similar pro/con IDs]

4. `results/performance_contexts_drivers.csv` - Each context/driver with:
   - label
   - frequency
  - associated_adrs: [list]
  - common_topics: [list]
  - avg_topic_probability

---

## Technical Implementation Details

### Configuration and Thresholds (Parameterizable)

All thresholds will be defined as variables at the top of the analysis notebook:

```python
# Topic Modeling Thresholds
TOPIC_PROBABILITY_THRESHOLD = 0.1  # Minimum probability to include topic
N_TOPICS_TO_DISPLAY = 20
N_TOP_WORDS_PER_TOPIC = 10

# LLM Processing
LLM_MODEL = "gpt-4o-mini"  # Configurable via environment variable
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 4096
LLM_REQUEST_DELAY = 2  # Seconds between requests

# Knowledge Graph
PRO_CON_SIMILARITY_THRESHOLD = 0.8  # For creating "similar_to" edges
PRO_CON_TOPIC_SIMILARITY_THRESHOLD = 0.7  # For creating "relates_to" edges
MIN_PRO_CON_FREQUENCY = 2  # Minimum frequency to include in aggregated analysis

# Embeddings
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# File Paths
CLASSIFICATION_RESULTS_PATH = 'results/all_projects-qas_classification_results.json'
ADR_DATA_PATH = 'data/LLM4ADR-adrs__adrs_english.pickle'
TOPIC_MODEL_FOLDER = 'saved_topicmodel'
PERFORMANCE_MODEL_FOLDER = 'saved_topicmodel/performance_specific'
RESULTS_FOLDER = 'results/'
```

### Dependencies

Required libraries (add to requirements.txt if not present):
```txt
networkx>=3.1
pyvis>=0.3.0
sentence-transformers>=2.2.0
openai>=1.0.0
python-dotenv>=1.0.0
```

### File Organization

```
results/
├── performance_adrs_filtered.json              # Filtered Performance ADRs
├── performance_topics_new_model.json          # New model topics
├── performance_topics_existing_model.json      # Existing model topics
├── performance_pros_cons_llm.json             # LLM outputs
├── performance_knowledge_graph.json            # Graph structure
├── performance_analysis_metadata.json        # Analysis metadata
├── performance_adrs_summary.csv              # ADRs with topics & pros/cons
├── performance_topics_frequency.csv            # Topic frequencies
├── performance_pros_cons_aggregated.csv       # Aggregated pros/cons
└── performance_contexts_drivers.csv          # Contexts and drivers

notebooks/
└── performance_analysis.ipynb                 # Main analysis notebook

docs/
└── PERFORMANCE_ANALYSIS_PLAN.md               # This document
```

---

## Implementation Strategy

### Approach
The analysis will be implemented as a combination of:
1. **Python utility functions** in `notebooks/` for reusable components
2. **Jupyter notebooks** for the main analysis workflow
   - Main notebook: `performance_analysis.ipynb`
   - May use separate notebooks for different phases if needed

### Modular Design
- Each phase will be self-contained with clear cell boundaries
- Utility functions for graph operations, LLM calls, etc.
- Intermediate results saved to enable re-running from any phase

### Error Handling
- Graceful handling of missing ADRs
- Retry logic for LLM API failures
- Validation of LLM JSON outputs
- Logging of all operations for debugging

---

## Questions and Decisions Addressed

### Addressed During Planning:
1. **CoT Reasoning Storage**: Only final structured JSON will be saved; full CoT reasoning is not required
2. **Graph Construction**: Build comprehensive graph first with all relationships; filtering can be done later with different criteria
3. **Pros/Cons Clustering**: Use semantic embeddings (SentenceTransformer) for similarity-based clustering
4. **Visualizations**: Too early to determine specific types; will be decided during implementation based on findings
5. **Thresholds**: All thresholds will be parameterizable variables for easy adjustment

---

## Expected Outcomes

### Knowledge Graph Insights
1. **Most Common Performance Topics**: Which topics appear most frequently across organizations?
2. **Decision Patterns**: Typical flows from context → decision → pros/cons
3. **Trade-off Identification**: Which topics frequently have conflicting pros/cons?
4. **Organizational Patterns**: Do certain organizations favor specific performance approaches?

### Actionable Insights
1. **Common Pros/Cons**: Most frequently cited benefits and risks for performance decisions
2. **Context-Decision Mapping**: What performance contexts typically lead to what types of decisions?
3. **Topic-Pro/Con Relationships**: Which topics are associated with specific pros/cons?
4. **Cross-Project Patterns**: Universal vs project-specific performance strategies

---

## Timeline Estimation

- **Phase 1**: 30 minutes (data loading and preparation)
- **Phase 2A**: 1-2 hours (training new topic model)
- **Phase 2B**: 30 minutes (applying existing model)
- **Phase 2C**: 1 hour (comparative analysis)
- **Phase 3**: 2-4 hours (LLM extraction, depends on ADR count and API rate limits)
- **Phase 4**: 1-2 hours (graph construction and analysis)
- **Phase 5**: 2-3 hours (synthesis, visualizations, exports)
- **Total**: ~7-13 hours (highly dependent on ADR count and API rate limits)

---

## Notes

1. This plan prioritizes **reproducibility**: All intermediate results are saved for re-running
2. **Cost Awareness**: LLM usage will be tracked and estimated beforehand
3. **Flexibility**: Parameterizable thresholds allow for different analysis scenarios
4. **Comprehensiveness**: Both new and existing topic models provide complementary perspectives
5. **Knowledge Extraction**: The graph enables discovering patterns beyond simple aggregations

---

*Document Version: 1.0*
*Last Updated: During planning phase*
*Status: Ready for implementation*