# Input Data Format

Specifications for ADR documents and dataset organization.

## ADR Markdown Structure

ADRs should follow a standard markdown format compatible with [MADR](https://adr.github.io/madr/) (Markdown Architecture Decision Records):

### Minimal ADR

```markdown
# Title of Decision

**Status:** Accepted | Pending | Rejected

## Context

Background information and problem statement.

## Decision

The chosen solution or approach.

## Consequences

Positive and negative impacts of this decision.
```

### Complete ADR Template

```markdown
# Title of Architectural Decision

**Status:** Accepted | Pending | Rejected | Superseded
**Date:** 2024-01-15
**Decision makers:** Team/Person names (optional)

## Context

Describe the background, constraints, and forces that led to this decision.
Include problem statement and relevant requirements.

## Decision drivers

List the key requirements or constraints:
- Scalability requirement: Handle 1M concurrent users
- Performance constraint: Response time < 100ms
- Compliance: GDPR compliance required

## Considered Options

### Option A: Solution 1
Description of approach A.
Pros and cons:
- Pro: Better performance
- Con: Higher complexity

### Option B: Solution 2
Description of approach B.
- Pro: Simpler implementation
- Con: Doesn't scale well

## Decision

We choose Option A because it better satisfies the scalability requirement.

## Consequences

### Positive
- Improved system scalability
- Meets performance SLA

### Negative
- Increased development time
- Additional operational complexity
```

### Supported Markdown Elements

ADRMiner can parse:

| Element | Example |
|---------|---------|
| **Headings** | `# Title`, `## Section`, `### Subsection` (h1-h4) |
| **Paragraphs** | Plain text and line breaks |
| **Lists** | `- Item` (bulleted) or `1. Item` (numbered) |
| **Code blocks** | `` ```code``` `` or triple-quoted text |
| **Inline formatting** | `**bold**`, `_italic_`, `[link](url)` |
| **Metadata** | `Key: value` pairs (YAML-style) |
| **Line breaks** | Horizontal rules `---` |


---

## Dataset Organization

It is recommended to organize your ADR files in a hierarchical structure:

```
data/
├── organization1/
│   ├── project-a/
│   │   ├── adr-001.md
│   │   ├── adr-002.md
│   │   ├── adr-003.md
│   │   └── architecture-decisions.md
│   ├── project-b/
│   │   ├── decisions-001.md
│   │   └── decisions-002.md
│   └── project-c/
│       └── adr-001.md
├── organization2/
│   ├── framework-x/
│   │   ├── adr-001.md
│   │   ├── adr-002.md
│   │   └── adr-003.md
│   └── tool-y/
│       └── adr-001.md
└── open-source-repos/
    ├── kubernetes/
    │   └── architecture-decisions/
    │       ├── adr-001.md
    │       └── ...
    └── docker/
        ├── adr-001.md
        └── ...
```

### Naming Conventions

- **File names**: `adr-NNN.md` or `decision-NNN.md` (helps identify order)
- **Directory names**: Use underscores for spaces (e.g., `my_organization`)
- **Consistency**: Maintain consistent naming across projects

### Metadata from Structure

ADRMiner automatically extracts:
```
data/organization1/project-a/adr-001.md
       └─────┬──────┘ └───┬───┘ └────┬─────┘
             org        project      adr_key
```

Accessible in results:
```python
result['metadata'] = {
    'organization': 'organization1',
    'project': 'project-a',
    'adr_key': 'adr-001.md'
}
```

---

## Dataset Filtering

ADRMiner provides filtering utilities:

```python
from utils import process_projects

# Filter out small projects and short ADRs
valid_projects = process_projects(
    dict_adrs,
    min_adrs_per_project=5,      # At least 5 ADRs
    min_adr_length=500           # At least 500 characters
)

# Extract documents from valid projects only
from utils import get_documents

adr_texts = get_documents(
    org_projects=valid_projects,
    adrs_dict=dict_adrs,
    field='both'  # 'title', 'content', 'decision', 'both', 'raw'
)
```

---

## Loading ADRs into Python

### From Local Files

```python
from adr import adr
import os

# Load single ADR
adr_doc = adr(path="data/org/project/adr-001.md")

# Load all ADRs from directory
adrs_dict = {}
for org in os.listdir("data/"):
    adrs_dict[org] = {}
    for project in os.listdir(f"data/{org}/"):
        adrs_dict[org][project] = {}
        adr_dir = f"data/{org}/{project}/"
        for adr_file in os.listdir(adr_dir):
            if adr_file.endswith('.md'):
                adr_path = os.path.join(adr_dir, adr_file)
                adrs_dict[org][project][adr_file] = adr(path=adr_path)
```

### From String Content

```python
from adr import adr

markdown_content = """
# My Decision
...
"""

adr_doc = adr(path=None, content=markdown_content)
```

---

## Extracting Content for Analysis

### Field Options

```python
from utils import get_documents

# Different extraction modes
docs = get_documents(
    org_projects=[('org', 'project')],
    adrs_dict=adrs_dict,
    field='both'  # Choose one:
)

# field='title'       → Only document titles
# field='content'     → Text content (excluding code)
# field='both'        → Title + content
# field='raw'         → Full original markdown
# field='decision'    → Decision section only
```

Output:
```python
docs = {
    ('org', 'project', 'adr-001.md'): 'Full text...',
    ('org', 'project', 'adr-002.md'): 'Full text...',
    ...
}
```

### Ground Truth Annotation

For evaluation, prepare a CSV with labeled ADRs:

```csv
ADR,raw_text,human,framework
adr-001.md,"Text of ADR...",Maintainability,quality_attributes
adr-002.md,"Text of ADR...",Technology,zimmermann
adr-003.md,"Text of ADR...",Design Decision,kruchten
```

Load into pandas:
```python
import pandas as pd

gt_df = pd.read_csv('ground_truth.csv')

# Pass to classifier
results = classifier.predict_and_evaluate_on_ground_truth(
    ground_truth_df=gt_df,
    adr_key_column='ADR',
    adr_text_column='raw_text',
    true_label_column='human'
)
```

---

## Data Validation

Check data quality before running analysis:

```python
from utils import process_projects

# Validate projects
all_projects, valid_projects, filtered = process_projects(
    dict_adrs,
    min_adrs_per_project=5,
    min_adr_length=500
)

print(f"Total projects: {len(all_projects)}")
print(f"Valid projects: {len(valid_projects)}")
print(f"Filtered out: {len(filtered)}")

# Check individual ADR
from adr import adr

doc = adr(path="sample.md")
print(f"Title: {doc.get_title()}")
print(f"Content length: {len(doc.get_content_no_code_str())}")
print(f"Has decision section: {len(doc.get_decision()) > 0}")
print(f"Properties: {doc.get_properties()}")
```

---

