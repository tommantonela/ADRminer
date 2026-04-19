# ADRminer CLI - Complete Testing Guide

**Version:** 1.0  
**Date:** 2026-04-18  
**Status:** Production Ready

---

## Table of Contents

1. [Quick Test Commands](#quick-test-commands)
2. [Command List & Testing](#command-list--testing)
3. [Smoke Test (5 Minutes)](#smoke-test-5-minutes)
4. [Full Integration Test (15 Minutes)](#full-integration-test-15-minutes)
5. [Expected Results Summary](#expected-results-summary)
6. [Common Issues & Solutions](#common-issues--solutions)

---

## Quick Test Commands

```bash
# Test all commands with sample data
cd /Users/adiazpace/Documents/GitHub/ADRminer
```

---

## Command List & Testing

### 1. Initialize Configuration

```bash
adrminer init config
```

**What it does:** Creates `~/.adrminer.yaml` with default configuration

**How to test:**

```bash
# Remove existing config to test fresh initialization
rm ~/.adrminer.yaml
adrminer init config

# Verify config was created
cat ~/.adrminer.yaml
```

**Expected output:**
```
✓ Configuration initialized at ~/.adrminer.yaml
✓ You can customize settings in configuration file
```

---

### 2. Topic Mining Commands

#### 2.1 Show Topic Information

```bash
adrminer topics info [OPTIONS]
```

**Options:**
- `--topic-id, -t`: Show specific topic details
- `--model, -m`: Path to topic model (overrides config)

**How to test:**

**Test A: Show all topics (KeyBERT mode)**

```bash
# Ensure KeyBERT mode is active
sed -i '' 's/use_llm_representation: true/use_llm_representation: false/' ~/.adrminer.yaml

# Show all topics
adrminer topics info
```

**Expected:** Table with 73 topics, "Topic Names: KeyBERT" in header

**Test B: Show all topics (LLM mode)**

```bash
# Enable LLM mode
sed -i '' 's/use_llm_representation: false/use_llm_representation: true/' ~/.adrminer.yaml

# Show all topics (takes longer, generates LLM names)
adrminer topics info
```

**Expected:** Table with 73 topics, "Topic Names: LLM-generated" in header, human-readable names like "API-Driven Data Publishing Architecture", "React Styling and Framework Integration", etc.

**Test C: Show specific topic**

```bash
# Show topic 0 details
adrminer topics info --topic-id 0

# Show topic 1 details
adrminer topics info --topic-id 1
```

**Expected:** Topic details with top keywords and probabilities

---

#### 2.2 Predict Topics

```bash
adrminer topics predict PATH [OPTIONS]
```

**Options:**
- `--output, -o`: Output format (sidecar, consolidated)
- `--verbose, -v`: Show detailed output
- `--model, -m`: Path to topic model

**How to test:**

**Test A: Single ADR file**

```bash
# Find a sample ADR file
ls sample/*.md 2>/dev/null || echo "No markdown files in sample/"

# If no markdown files, create a test ADR
cat > test_adr.md << 'EOF'
# ADR-001: Test Decision

## Context
We need to decide on a database for our application.

## Decision
Use PostgreSQL as the primary database.

## Consequences
- Better for complex queries
- Requires more resources
EOF

# Predict topic
adrminer topics predict test_adr.md --verbose
```

**Expected:** Topic prediction with probability and keywords

**Test B: Multiple ADRs**

```bash
# Create multiple test ADRs
mkdir -p test_adrs
cat > test_adrs/adr1.md << 'EOF'
# ADR-001: API Design

Design REST API for user authentication.
EOF

cat > test_adrs/adr2.md << 'EOF'
# ADR-002: Docker Deployment

Use Docker for containerization.
EOF

# Predict topics
adrminer topics predict test_adrs --verbose
```

**Expected:** Progress bar, results for both ADRs, topic distribution summary

**Test C: Export sidecar files**

```bash
adrminer topics predict test_adrs --output sidecar

# Check for sidecar files
ls test_adrs/*.metadata.json
cat test_adrs/adr1.metadata.json
```

**Expected:** `.metadata.json` files created alongside each ADR

**Test D: Export consolidated JSON**

```bash
adrminer topics predict test_adrs --output consolidated

# Check consolidated output
cat test_adrs/topics_results.json
```

**Expected:** Single JSON file with all predictions

---

### 3. Classification Commands

#### 3.1 Show Framework Information

```bash
adrminer classify info [OPTIONS]
```

**Options:**
- `--framework, -f`: Framework to display (kruchten, quality_attributes, zimmermann)

**How to test:**

**Test A: Kruchten framework**

```bash
adrminer classify info --framework kruchten
```

**Expected:** 4 categories with detailed descriptions:

| Category | Description |
|----------|-------------|
| **Existence (ontocrisis)** | Decisions about whether something exists or not, fundamental structural choices |
| **Property (diacrisis)** | Decisions about qualities, characteristics, or properties of the system |
| **Executive (pericrisis)** | Organizational, process, or policy decisions that affect the project |
| **Ban (anticrisis)** | Decisions to explicitly avoid or prohibit certain technologies or approaches |

**Test B: Quality Attributes framework**

```bash
adrminer classify info --framework quality_attributes
```

**Expected:** 10 categories (Performance, Security, Availability, Scalability, etc.) with detailed descriptions

**Test C: Zimmermann framework**

```bash
adrminer classify info --framework zimmermann
```

**Expected:** 6 categories (Technology, Organization, Information, Interface, Structure, Process) with detailed descriptions

**Test D: All frameworks**

```bash
adrminer classify info
```

**Expected:** All three frameworks displayed sequentially

---

#### 3.2 Classify ADRs

```bash
adrminer classify predict PATH [OPTIONS]
```

**Options:**
- `--framework, -f`: Classification framework
- `--examples, -e`: Use few-shot examples
- `--output, -o`: Output format (sidecar, consolidated)
- `--verbose, -v`: Show detailed output

**How to test:**

**Test A: Single ADR with Kruchten**

```bash
# Set Kruchten framework
sed -i '' 's/framework: .*/framework: kruchten/' ~/.adrminer.yaml

# Classify
adrminer classify predict test_adr.md --verbose
```

**Expected:** Classification with primary category, confidence, and alternatives

**Test B: Multiple ADRs with Quality Attributes**

```bash
# Set Quality Attributes framework
sed -i '' 's/framework: .*/framework: quality_attributes/' ~/.adrminer.yaml

# Classify multiple ADRs
adrminer classify predict test_adrs --verbose
```

**Expected:** Progress bar, classifications for all ADRs

**Test C: Different framework**

```bash
# Set Zimmermann framework
sed -i '' 's/framework: .*/framework: zimmermann/' ~/.adrminer.yaml

# Classify
adrminer classify predict test_adr.md --verbose
```

**Expected:** Classification using Zimmermann categories

**Test D: With examples (few-shot)**

```bash
# Ensure examples are enabled
sed -i '' 's/use_examples: .*/use_examples: true/' ~/.adrminer.yaml

# Classify with examples
adrminer classify predict test_adr.md --verbose
```

**Expected:** Classification using few-shot examples from configuration

**Test E: Without examples (zero-shot)**

```bash
# Disable examples
sed -i '' 's/use_examples: .*/use_examples: false/' ~/.adrminer.yaml

# Classify without examples
adrminer classify predict test_adr.md --verbose
```

**Expected:** Classification using zero-shot approach (no examples provided to LLM)

**Test F: Export results**

```bash
# Export sidecar files
adrminer classify predict test_adrs --output sidecar

# Check for metadata files
ls test_adrs/*.metadata.json

# Export consolidated
adrminer classify predict test_adrs --output consolidated
cat test_adrs/classification_results.json
```

**Expected:** Sidecar `.metadata.json` files or consolidated JSON with all classifications

---

### 4. Checking Commands

#### 4.1 Check ADR Quality

```bash
adrminer check ADR_PATH [OPTIONS]
```

**Options:**
- `--mode`: Checking mode (adherence, sections, full)
- `--verbose, -v`: Show detailed output

**How to test:**

**Test A: Adherence mode (single ADR)**

```bash
# Check adherence to MADR template
adrminer check test_adr.md --mode adherence --verbose
```

**Expected:** Overall MADR template adherence score (0.0-1.0) with detailed section assessments

**Test B: Sections mode (single ADR)**

```bash
# Check individual sections
adrminer check test_adr.md --mode sections --verbose
```

**Expected:** Detailed assessment of each MADR core section (Title, Context, Decision Drivers, Decision, Consequences, Alternatives, Status)

**Test C: Full mode (single ADR)**

```bash
# Check both adherence and sections
adrminer check test_adr.md --mode full --verbose
```

**Expected:** Combined results with adherence score and detailed section assessments

**Test D: Batch checking - Adherence mode**

```bash
# Check multiple ADRs for adherence
adrminer check test_adrs --mode adherence
```

**Expected:** Progress bar, consolidated table showing adherence scores for all ADRs

**Test E: Batch checking - Sections mode**

```bash
# Check multiple ADRs for section consistency
adrminer check test_adrs --mode sections
```

**Expected:** Progress bar, consolidated table showing section presence, quality, and consistency for all ADRs

**Test F: Batch checking - Full mode**

```bash
# Check multiple ADRs with full analysis
adrminer check test_adrs --mode full
```

**Expected:** Progress bar, consolidated table with all metrics (adherence score, section presence, quality, consistency)

**Expected Output Format:**

**Individual ADR (Adherence mode):**
```
Evaluates overall MADR template adherence with a score (0.0-1.0)

     ADR Template Adherence Results
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ ADR                          ┃ Score ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ test_adr.md                  │ 0.90  │
└──────────────────────────────┴───────┘

                                                    MADR Core Sections
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Section          ┃ Assessment                                         ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Title            │ Present and correctly reflects the ADR content.       │
│ Context          │ Present at the beginning...                            │
│ Decision Drivers │ Not explicitly titled as 'Decision Drivers'...        │
...
```

**Batch (Full mode):**
```
Combines adherence to MADR template and section consistency assessment (presence, quality, purpose)

                                             ADR Quality Assessment
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ ADR                                   ┃ Adherence score ┃ Section presence ┃ Section quality ┃ Section consistency ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ adr1.md                              │ 0.90            │ 6/7              │ 5/7             │ 5/7                 │
│ adr2.md                              │ 0.85            │ 6/7              │ 5/7             │ 6/7                 │
│ adr3.md                              │ 0.95            │ 7/7              │ 7/7             │ 7/7                 │
└───────────────────────────────────────┴─────────────────┴──────────────────┴──────────────────┴─────────────────────┘
```

---

### 5. Utility Commands

#### 5.1 List Sidecar Files

```bash
adrminer util list PATH [OPTIONS]
```

**Options:**
- `--size/--no-size`: Show/hide file sizes (default: show)
- `--modified, -m`: Show modification dates

**How to test:**

**Test A: List all sidecar files**

```bash
# List sidecar files in directory
adrminer util list test_adrs
```

**Expected:** Table showing all `.metadata.json` files with sizes

**Test B: List with modification dates**

```bash
# List with modification timestamps
adrminer util list test_adrs --modified
```

**Expected:** Table showing files with sizes and modification dates

**Test C: List without sizes**

```bash
# List without file sizes
adrminer util list test_adrs --no-size
```

**Expected:** Table showing only file names

**Test D: Check specific ADR's sidecar**

```bash
# Check if specific ADR has sidecar
adrminer util list test_adr.md
```

**Expected:** Shows sidecar file if it exists

---

#### 5.2 Delete Metadata Files

```bash
adrminer util delete-metadata PATH [OPTIONS]
```

**Options:**
- `--dry-run, -d`: Preview what would be deleted without actually deleting
- `--verbose, -v`: Show detailed output including each file

**How to test:**

**Test A: Dry run (preview deletion)**

```bash
# Preview what would be deleted
adrminer util delete-metadata test_adrs --dry-run
```

**Expected:** Shows table of files that would be deleted, but doesn't delete them

**Test B: Delete single ADR's sidecar**

```bash
# Delete sidecar for single ADR
echo "yes" | adrminer util delete-metadata test_adr.md --verbose
```

**Expected:** Confirmation prompt, progress bar, success message, list of deleted files

**Test C: Delete all sidecars in directory**

```bash
# Delete all sidecar files
echo "yes" | adrminer util delete-metadata test_adrs --verbose
```

**Expected:** Confirmation prompt, progress bar with percentage, success message showing count

**Test D: Verify deletion**

```bash
# Verify files were deleted
adrminer util list test_adrs
```

**Expected:** "No sidecar metadata files found"

**Test E: Cancel deletion**

```bash
# Test canceling the deletion
echo "no" | adrminer util delete-metadata test_adrs
```

**Expected:** "Operation cancelled" message, no files deleted

**Expected Output:**

**List command:**
```
Found 3 sidecar file(s)

┏━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ # ┃ Sidecar File                           ┃   Size ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 1 │ adr1.metadata.json                     │ 1.3 KB │
│ 2 │ adr2.metadata.json                     │ 1.3 KB │
│ 3 │ adr3.metadata.json                     │ 1.4 KB │
└───┴────────────────────────────────────────┴────────┘
```

**Delete command (verbose):**
```
Found 3 sidecar file(s)

┏━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ # ┃ Sidecar File                           ┃   Size ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 1 │ adr1.metadata.json                     │ 1.3 KB │
│ 2 │ adr2.metadata.json                     │ 1.3 KB │
│ 3 │ adr3.metadata.json                     │ 1.4 KB │
└───┴────────────────────────────────────────┴────────┘

This will delete all sidecar metadata files!
Are you sure you want to continue? [y/N]: y
⠋ Deleting sidecar files... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   0%
  Deleting sidecar files... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

✓ Successfully deleted 3 sidecar file(s)

Deleted files:
  • adr1.metadata.json
  • adr2.metadata.json
  • adr3.metadata.json
```

---

## Smoke Test (5 Minutes)

A quick verification script to test all core functionality:

```bash
#!/bin/bash

echo "=== ADRminer CLI Smoke Test ==="
echo ""

# 1. Test init
echo "1. Testing init..."
rm -f ~/.adrminer.yaml
adrminer init config
if [ -f ~/.adrminer.yaml ]; then
    echo "✓ Init works"
else
    echo "✗ Init failed"
fi
echo ""

# 2. Test topics info
echo "2. Testing topics info..."
adrminer topics info | head -5
echo ""

# 3. Test classify info
echo "3. Testing classify info..."
adrminer classify info --framework kruchten | head -5
echo ""

# 4. Test topic prediction
echo "4. Testing topics predict..."
mkdir -p test_adrs
echo "# Test ADR" > test_adrs/test.md
adrminer topics predict test_adrs/test.md --verbose
echo ""

# 5. Test classification
echo "5. Testing classify predict..."
adrminer classify predict test_adrs/test.md --verbose
echo ""

echo "=== Smoke Test Complete ==="
```

**How to run:**

```bash
cd /Users/adiazpace/Documents/GitHub/ADRminer
bash -c "$(cat << 'SCRIPT'
#!/bin/bash

echo "=== ADRminer CLI Smoke Test ==="
echo ""

# 1. Test init
echo "1. Testing init..."
rm -f ~/.adrminer.yaml
adrminer init config
if [ -f ~/.adrminer.yaml ]; then
    echo "✓ Init works"
else
    echo "✗ Init failed"
fi
echo ""

# 2. Test topics info
echo "2. Testing topics info..."
adrminer topics info | head -5
echo ""

# 3. Test classify info
echo "3. Testing classify info..."
adrminer classify info --framework kruchten | head -5
echo ""

# 4. Test topic prediction
echo "4. Testing topics predict..."
mkdir -p test_adrs
echo "# Test ADR" > test_adrs/test.md
adrminer topics predict test_adrs/test.md --verbose
echo ""

# 5. Test classification
echo "5. Testing classify predict..."
adrminer classify predict test_adrs/test.md --verbose
echo ""

echo "=== Smoke Test Complete ==="
SCRIPT
)"
```

---

## Full Integration Test (15 Minutes)

Comprehensive test suite covering all features:

```bash
#!/bin/bash

echo "=== ADRminer Full Integration Test ==="
echo ""

# Setup
rm -rf test_integration
mkdir -p test_integration
cd test_integration

# Create test ADRs
cat > adr1.md << 'EOF'
# ADR-001: Database Migration

Migrate from MySQL to PostgreSQL.

## Context
Current MySQL performance is poor for complex queries.

## Decision
Use PostgreSQL for better performance and features.

## Consequences
- Improved query performance
- Better JSON support
- Migration effort required
- Team training needed
EOF

cat > adr2.md << 'EOF'
# ADR-002: REST API Design

Implement RESTful API for authentication.

## Context
Need authentication for mobile app and web interface.

## Decision
Use OAuth2 with JWT tokens for authentication.

## Consequences
- Secure authentication flow
- Token refresh mechanism required
- Integration with OAuth providers
EOF

cat > adr3.md << 'EOF'
# ADR-003: Docker Deployment

Deploy application using Docker containers.

## Context
Need consistent deployment across development, staging, and production.

## Decision
Use Docker Compose for orchestration and deployment.

## Consequences
- Reproducible deployments
- Easier local development
- Learning curve for team
- Requires Docker infrastructure
EOF

echo "Created 3 test ADRs"
echo ""

# Test 1: Topic mining (KeyBERT)
echo "=== Test 1: Topic Mining (KeyBERT) ==="
sed -i '' 's/use_llm_representation: true/use_llm_representation: false/' ~/.adrminer.yaml
adrminer topics info | head -5
adrminer topics predict . --output sidecar --verbose
echo "✓ Topic mining (KeyBERT) complete"
echo ""

# Test 2: Topic mining (LLM)
echo "=== Test 2: Topic Mining (LLM) ==="
sed -i '' 's/use_llm_representation: false/use_llm_representation: true/' ~/.adrminer.yaml
adrminer topics info --topic-id 0
echo "✓ Topic mining (LLM) complete"
echo ""

# Test 3: Classification (Kruchten)
echo "=== Test 3: Classification (Kruchten) ==="
sed -i '' 's/framework: .*/framework: kruchten/' ~/.adrminer.yaml
adrminer classify info --framework kruchten | head -10
adrminer classify predict . --output sidecar --verbose
echo "✓ Classification (Kruchten) complete"
echo ""

# Test 4: Classification (Quality Attributes)
echo "=== Test 4: Classification (Quality Attributes) ==="
sed -i '' 's/framework: .*/framework: quality_attributes/' ~/.adrminer.yaml
adrminer classify predict . --output consolidated
cat classification_results.json | jq '.[].classification.primary_category'
echo "✓ Classification (Quality Attributes) complete"
echo ""

# Test 5: Classification (Zimmermann)
echo "=== Test 5: Classification (Zimmermann) ==="
sed -i '' 's/framework: .*/framework: zimmermann/' ~/.adrminer.yaml
adrminer classify predict . --verbose
echo "✓ Classification (Zimmermann) complete"
echo ""

# Verify outputs
echo "=== Verification ==="
echo "Sidecar files created:"
ls *.metadata.json
echo ""
echo "Metadata content sample:"
cat adr1.metadata.json | jq .
echo ""

# Cleanup
cd ..
rm -rf test_integration

echo "=== Full Integration Test Complete ==="
```

**How to run:**

```bash
cd /Users/adiazpace/Documents/GitHub/ADRminer
bash -c "$(cat << 'SCRIPT'
#!/bin/bash

echo "=== ADRminer Full Integration Test ==="
echo ""

# Setup
rm -rf test_integration
mkdir -p test_integration
cd test_integration

# Create test ADRs
cat > adr1.md << 'EOF'
# ADR-001: Database Migration

Migrate from MySQL to PostgreSQL.

## Context
Current MySQL performance is poor for complex queries.

## Decision
Use PostgreSQL for better performance and features.

## Consequences
- Improved query performance
- Better JSON support
- Migration effort required
- Team training needed
EOF

cat > adr2.md << 'EOF'
# ADR-002: REST API Design

Implement RESTful API for authentication.

## Context
Need authentication for mobile app and web interface.

## Decision
Use OAuth2 with JWT tokens for authentication.

## Consequences
- Secure authentication flow
- Token refresh mechanism required
- Integration with OAuth providers
EOF

cat > adr3.md << 'EOF'
# ADR-003: Docker Deployment

Deploy application using Docker containers.

## Context
Need consistent deployment across development, staging, and production.

## Decision
Use Docker Compose for orchestration and deployment.

## Consequences
- Reproducible deployments
- Easier local development
- Learning curve for team
- Requires Docker infrastructure
EOF

echo "Created 3 test ADRs"
echo ""

# Test 1: Topic mining (KeyBERT)
echo "=== Test 1: Topic Mining (KeyBERT) ==="
sed -i '' 's/use_llm_representation: true/use_llm_representation: false/' ~/.adrminer.yaml
adrminer topics info | head -5
adrminer topics predict . --output sidecar --verbose
echo "✓ Topic mining (KeyBERT) complete"
echo ""

# Test 2: Topic mining (LLM)
echo "=== Test 2: Topic Mining (LLM) ==="
sed -i '' 's/use_llm_representation: false/use_llm_representation: true/' ~/.adrminer.yaml
adrminer topics info --topic-id 0
echo "✓ Topic mining (LLM) complete"
echo ""

# Test 3: Classification (Kruchten)
echo "=== Test 3: Classification (Kruchten) ==="
sed -i '' 's/framework: .*/framework: kruchten/' ~/.adrminer.yaml
adrminer classify info --framework kruchten | head -10
adrminer classify predict . --output sidecar --verbose
echo "✓ Classification (Kruchten) complete"
echo ""

# Test 4: Classification (Quality Attributes)
echo "=== Test 4: Classification (Quality Attributes) ==="
sed -i '' 's/framework: .*/framework: quality_attributes/' ~/.adrminer.yaml
adrminer classify predict . --output consolidated
cat classification_results.json | jq '.[].classification.primary_category'
echo "✓ Classification (Quality Attributes) complete"
echo ""

# Test 5: Classification (Zimmermann)
echo "=== Test 5: Classification (Zimmermann) ==="
sed -i '' 's/framework: .*/framework: zimmermann/' ~/.adrminer.yaml
adrminer classify predict . --verbose
echo "✓ Classification (Zimmermann) complete"
echo ""

# Verify outputs
echo "=== Verification ==="
echo "Sidecar files created:"
ls *.metadata.json
echo ""
echo "Metadata content sample:"
cat adr1.metadata.json | jq .
echo ""

# Cleanup
cd ..
rm -rf test_integration

echo "=== Full Integration Test Complete ==="
SCRIPT
)"
```

---

## Expected Results Summary

| Command | Success Indicators |
|----------|-------------------|
| `init config` | ✅ Config file created at `~/.adrminer.yaml` |
| `topics info` | ✅ Table with 73 topics, no warnings |
| `topics info --topic-id X` | ✅ Topic details with keywords shown |
| `topics predict` | ✅ Progress bar, results displayed, sidecar files created |
| `classify info` | ✅ Framework categories with descriptions shown |
| `classify predict` | ✅ Classification with confidence, alternatives shown |
| LLM mode | ✅ Human-readable topic names (e.g., "Database Migration Strategy", "API-Driven Data Publishing Architecture") |
| KeyBERT mode | ✅ Keyword-based names (e.g., "0_publishing_database_metadata_api", "1_fxa_jsx_framework_styles") |

### Sample Outputs

**Topic Info (KeyBERT mode):**
```
╭────────────────────────── Topic Model Information ───────────────────────────╮
│ Total Topics: 73                                                             │
│ Model Path: notebooks/saved_topicmodel                                       │
│ Topic Names: KeyBERT                                                         │
╰──────────────────────────────────────────────────────────────────────────────╯
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ ID ┃ Name                                                            ┃ Count ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ -1 │ -1_aws_deployment_cloud_services                                │  1514 │
│  0 │ 0_publishing_database_metadata_api                              │   407 │
│  1 │ 1_fxa_jsx_framework_styles                                      │   257 │
...
```

**Topic Info (LLM mode):**
```
╭────────────────────────── Topic Model Information ───────────────────────────╮
│ Total Topics: 73                                                             │
│ Model Path: notebooks/saved_topicmodel                                       │
│ Topic Names: LLM-generated                                                   │
╰──────────────────────────────────────────────────────────────────────────────╯
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ ID ┃ Name                                             ┃ Count ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ -1 │ -1_aws_deployment_cloud_services                 │  1514 │
│  0 │ API-Driven Data Publishing Architecture          │   407 │
│  1 │ React Styling and Framework Integration          │   257 │
│  2 │ Architectural Decision Documentation Practices   │   213 │
...
```

**Classification (Kruchten):**
```
╭───────────────────────────── Classification Results ─────────────────────────────╮
│                                                                         │
│  📄 ADR: test_adr.md                                               │
│  🎯 Framework: Kruchten                                               │
│                                                                         │
│  Primary Category: Existence (ontocrisis)                                │
│  Confidence: 0.92                                                      │
│                                                                         │
│  Alternatives:                                                          │
│    • Property (diacrisis) - 0.05                                    │
│    • Executive (pericrisis) - 0.03                                   │
│                                                                         │
│  Explanation: This ADR describes a fundamental structural...               │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Classification Info (Kruchten):**
```
╭───────────────────── Kruchten Classification Framework ─────────────────────╮
│                                                                         │
│  Framework: Kruchten                                                    │
│  Categories: 4                                                          │
│  Focus: Decision types based on crisis (ontocrisis, diacrisis, etc.)    │
│                                                                         │
│  Categories:                                                          │
│                                                                         │
│  📌 Existence (ontocrisis)                                             │
│     Decisions about whether something exists or not, fundamental            │
│     structural choices such as adopting a technology, creating a          │
│     component, or establishing a pattern. These decisions determine        │
│     the core architecture of the system.                                │
│                                                                         │
│  📌 Property (diacrisis)                                              │
│     Decisions about qualities, characteristics, or properties of            │
│     the system. These decisions affect non-functional requirements        │
│     such as performance, security, scalability, etc.                      │
│...
```

---

## Common Issues & Solutions

### Issue 1: "Model not found"

**Error:**
```
RuntimeError: Failed to load topic model from /path/to/model
```

**Solution:**
```bash
# Check model path in config
cat ~/.adrminer.yaml | grep "topic_model:"

# Update path if needed (use actual path to saved model)
sed -i '' 's|path:.*|path: ./notebooks/saved_topicmodel|' ~/.adrminer.yaml

# Verify model exists
ls -la ./notebooks/saved_topicmodel/
```

---

### Issue 2: "LLM API error"

**Error:**
```
Error: Failed to initialize LLM: Invalid API key
```

**Solution:**
```bash
# Check LLM configuration
cat ~/.adrminer.yaml | grep -A 3 "llm:"

# Set API key for your provider
export OPENAI_API_KEY="your-openai-key-here"
# OR
export ANTHROPIC_API_KEY="your-anthropic-key-here"

# Test API key
echo $OPENAI_API_KEY
```

---

### Issue 3: "No ADR files found"

**Error:**
```
Warning: No ADR files found at /path/to/adrs
```

**Solution:**
```bash
# Check file extension
ls -la sample/*.md

# Create test ADRs if needed
mkdir -p test_adrs
cat > test_adrs/test.md << 'EOF'
# Test ADR

## Context
This is a test decision.

## Decision
Test decision here.

## Consequences
Test consequences.
EOF

# Verify files exist
ls -la test_adrs/
```

---

### Issue 4: "BERTopic warning: loading without embedding model"

**Error:**
```
WARNING: You are loading a BERTopic model without explicitly defining an embedding model.
```

**Solution:**

This should **not** occur with the current implementation, as we explicitly load the embedding model. If you see this:

```bash
# Check embedding model is configured
cat ~/.adrminer.yaml | grep "embedding_model:"

# Verify default is set correctly
# Should show: embedding_model: all-MiniLM-L6-v2

# If not, update it:
sed -i '' 's|embedding_model:.*|embedding_model: all-MiniLM-L6-v2|' ~/.adrminer.yaml
```

---

### Issue 5: "LLM topic naming takes too long"

**Issue:** Generating LLM names for all topics is slow

**Solution:**

```bash
# Switch to KeyBERT mode for faster results
sed -i '' 's/use_llm_representation: true/use_llm_representation: false/' ~/.adrminer.yaml

# Use LLM mode only when you need human-readable names
sed -i '' 's/use_llm_representation: false/use_llm_representation: true/' ~/.adrminer.yaml
```

**Note:** LLM mode calls the LLM for each topic, which can be slow for large topic sets. Use KeyBERT mode for quick exploration, LLM mode for final presentations.

---

### Issue 6: "Permission denied writing to config"

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/Users/username/.adrminer.yaml'
```

**Solution:**

```bash
# Remove existing config and re-create
rm -f ~/.adrminer.yaml
adrminer init config

# Or manually create with proper permissions
touch ~/.adrminer.yaml
chmod 644 ~/.adrminer.yaml
```

---

## Testing Checklist

Use this checklist to verify all functionality:

- [ ] Configuration initializes correctly
- [ ] Topics info displays all 73 topics (KeyBERT mode)
- [ ] Topics info displays LLM-generated names when enabled
- [ ] Topic prediction works for single ADR
- [ ] Topic prediction works for multiple ADRs
- [ ] Sidecar files are created with topic metadata
- [ ] Consolidated JSON export works
- [ ] All three frameworks display correctly with descriptions
  - [ ] Kruchten (4 categories)
  - [ ] Quality Attributes (10 categories)
  - [ ] Zimmermann (6 categories)
- [ ] Classification works for single ADR
- [ ] Classification works for multiple ADRs
- [ ] Few-shot classification works (with examples)
- [ ] Zero-shot classification works (without examples)
- [ ] All frameworks work correctly
  - [ ] Kruchten
  - [ ] Quality Attributes
  - [ ] Zimmermann
- [ ] Checking service works for single ADR
  - [ ] Adherence mode displays score (0.0-1.0)
  - [ ] Sections mode shows detailed section assessments
  - [ ] Full mode combines adherence and sections
- [ ] Checking service works for batch operations
  - [ ] Batch adherence shows consolidated table
  - [ ] Batch sections shows consolidated table
  - [ ] Batch full shows consolidated table with all metrics
- [ ] Checking service sidecar files are created correctly
- [ ] Utility commands work correctly
  - [ ] List sidecar files displays table with sizes
  - [ ] List with modification dates works
  - [ ] Delete metadata dry-run previews without deleting
  - [ ] Delete metadata with verbose shows deleted files
  - [ ] Delete metadata confirmation prompt works
  - [ ] Delete metadata cancellation works
  - [ ] Progress bars display correctly for deletion
- [ ] No warnings or errors in output
- [ ] Progress bars display correctly for all commands
- [ ] Rich output formatting looks good
- [ ] Help documentation is complete

---

## Additional Testing Resources

### Sample ADR Files

The project includes sample ADRs in the `sample/` directory. Use these for testing:

```bash
# List sample ADRs
ls sample/*.md

# Test with sample files
adrminer topics predict sample/
adrminer classify predict sample/
```

### Test Data

For more comprehensive testing, use the provided test data:

```bash
# Use existing results for comparison
ls results/*.json

# Use sample processed data
ls sample/*.csv
```

---

## Performance Testing

To test performance with larger datasets:

```bash
# Create large test set
mkdir -p large_test
for i in {1..100}; do
    cat > large_test/adr$i.md << EOF
# ADR-$i: Test Decision $i

## Context
Test context for decision $i.

## Decision
Test decision $i.

## Consequences
Test consequences for decision $i.
EOF
done

# Test with large set (expect progress bar and reasonable time)
time adrminer topics predict large_test --verbose
time adrminer classify predict large_test --verbose
```

**Expected performance:**
- Topic prediction: ~2-3 seconds per 100 ADRs
- Classification: ~5-10 seconds per 100 ADRs (with GPT-4.1-mini)
- LLM topic naming: ~1-2 seconds per topic (73 topics = ~2 minutes)

---

## CI/CD Integration Testing

For CI/CD pipeline testing:

```bash
#!/bin/bash

# CI/CD Test Script
set -e  # Exit on error

echo "Running ADRminer CI/CD Tests..."

# Initialize config
rm -f ~/.adrminer.yaml
adrminer init config

# Test topics info
adrminer topics info > /dev/null
echo "✓ Topics info works"

# Test classification info
adrminer classify info --framework kruchten > /dev/null
echo "✓ Classification info works"

# Test with sample data
adrminer topics predict sample/ --output consolidated > /dev/null
echo "✓ Topics predict works"

adrminer classify predict sample/ --output consolidated > /dev/null
echo "✓ Classification predict works"

echo "All CI/CD tests passed!"
```

---

## Summary

This testing guide provides comprehensive coverage of all ADRminer CLI features:

✅ **Configuration Management** - Initialize and customize settings  
✅ **Topic Mining** - Info display, prediction, LLM/KeyBERT modes  
✅ **Classification** - Three frameworks, few-shot/zero-shot modes  
✅ **Export Options** - Sidecar files and consolidated JSON  
✅ **Error Handling** - Graceful failures and clear messages  
✅ **Rich Output** - Progress bars, tables, and formatted results  

Run the **Smoke Test** (5 minutes) for quick verification, or the **Full Integration Test** (15 minutes) for comprehensive coverage.

---

**Document History:**
- v1.0 - Initial testing guide (2026-04-18)