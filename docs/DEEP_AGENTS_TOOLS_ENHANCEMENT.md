# Deep Agents Tools Enhancement Summary

**Date:** April 25, 2026  
**Task:** Add missing CLI tools to Deep Agents and enhance existing tools

---

## Overview

This document summarizes the enhancements made to the Deep Agents tools to improve parity with CLI commands.

---

## Changes Made

### 1. New Tools Added

#### 1.1 `get_topic_info`
**Purpose:** Display information about topics in the BERTopic model  
**Equivalent CLI Command:** `adrminer topics info`  

**Parameters:**
- `topic_id` (Optional[int]): Specific topic ID to show details for
- `model` (Optional[str]): Custom model path

**Features:**
- Show all topics with ID, name, count, and top keywords
- Show detailed information for a specific topic
- Accesses TopicService through session

**Usage Examples:**
```python
# Show all topics
get_topic_info()

# Show specific topic
get_topic_info(topic_id=5)
```

---

#### 1.2 `get_classification_info`
**Purpose:** Display information about classification frameworks  
**Equivalent CLI Command:** `adrminer classify info`

**Parameters:**
- `framework` (Optional[str]): Specific framework to show (kruchten, quality_attributes, zimmermann)

**Features:**
- Show all available frameworks with description and category counts
- Show detailed framework information including:
  - Framework name and description
  - All categories
  - Category descriptions

**Usage Examples:**
```python
# Show all frameworks
get_classification_info()

# Show specific framework
get_classification_info(framework="kruchten")
```

---

#### 1.3 `list_adr_files`
**Purpose:** Discover and list ADR files in directories  
**Equivalent CLI Command:** Utility functionality

**Parameters:**
- `path` (str): Directory path to search (absolute or relative)

**Features:**
- Recursive search for `.md` and `.MD` files
- Filters out common non-ADR directories (node_modules, .git, __pycache__)
- Returns file count and list of paths
- Useful for filesystem exploration before loading

**Usage Examples:**
```python
# List ADRs in directory
list_adr_files("adrs/")

# List ADRs with absolute path
list_adr_files("/path/to/adrs")
```

---

### 2. Agent Factory Updates

#### 2.1 Tool Import Updates
Added imports for new tools:
```python
from adrminer.agents.tools import (
    # ... existing imports ...
    get_topic_info,
    get_classification_info,
    list_adr_files,
)
```

#### 2.2 Tools List Enhancement
Updated tools list to include new tools:
```python
tools = [
    load_adrs,
    list_adr_files,           # NEW
    mine_topics,
    get_topic_info,            # NEW
    classify_adrs,
    get_classification_info,     # NEW
    check_quality,
    generate_insights,
    export_metadata
]
```

#### 2.3 System Prompt Enhancement
Updated SYSTEM_PROMPT to document new capabilities:
```
- Discovering ADR files in directories (tool: list_adr_files)
- Viewing topic model information (tool: get_topic_info)
- Viewing classification framework information (tool: get_classification_info)
```

---

## Tool Inventory

### Complete Tool List (9 tools)

| Tool | Purpose | CLI Equivalent | Status |
|-------|-----------|----------------|----------|
| `load_adrs` | Load ADR files | None (CLI auto-loads) | ✅ Existing |
| `list_adr_files` | Discover ADR files | Utility | ✅ **NEW** |
| `mine_topics` | Extract topics | `topics predict` | ✅ Existing |
| `get_topic_info` | View topic info | `topics info` | ✅ **NEW** |
| `classify_adrs` | Classify ADRs | `classify predict` | ✅ Existing |
| `get_classification_info` | View framework info | `classify info` | ✅ **NEW** |
| `check_quality` | Check quality | `check` | ✅ Existing |
| `generate_insights` | Generate insights | `summary` | ✅ Existing |
| `export_metadata` | Export results | Various export | ✅ Existing |

---

## Files Modified

1. **src/adrminer/agents/tools.py**
   - Added `get_topic_info` function (lines ~127-227)
   - Added `get_classification_info` function (lines ~229-327)
   - Added `list_adr_files` function (lines ~329-402)

2. **src/adrminer/agents/agent_factory.py**
   - Updated imports to include new tools
   - Updated tools list to register new tools
   - Updated SYSTEM_PROMPT to document new capabilities

---

## Tool Coverage Analysis

### Before Enhancement
- Total CLI commands: 20+ subcommands across 5 command groups
- Total Deep Agent tools: 6
- Coverage: ~30%

### After Enhancement
- Total Deep Agent tools: 9
- New tools added: 3 (50% increase)
- Coverage: ~50% (improved from 30%)

### Remaining Gaps

The following CLI features still lack Deep Agent equivalents:

1. **Training topic models** (`topics train`)
   - Complexity: High (training BERTopic models)
   - Recommendation: Add as advanced tool

2. **Initializing configuration** (`init`)
   - Complexity: Low (file creation)
   - Recommendation: Add as utility tool

3. **Advanced classification options** (`classify predict` options)
   - Parser integration (--use-parser, --strict, --no-language-detect)
   - Custom examples path
   - CSV export

4. **Advanced quality check options** (`check` options)
   - Parser integration (--use-parser, --strict, --no-language-detect)
   - CSV export
   - Mode-specific output

5. **Enhanced insights** (`summary` options)
   - Summary report generation (Markdown)
   - Detailed report generation with project insights
   - Per-ADR insights
   - Caching/force-rewrite control

---

## Future Enhancement Recommendations

### Priority 1: Parser Integration
Add `--use-parser` support to existing tools:
- `classify_adrs`: Add `use_parser`, `strict`, `no_language_detect` parameters
- `check_quality`: Add `use_parser`, `strict`, `no_language_detect` parameters

**Rationale:** Parser integration is a core CLI feature that improves accuracy

### Priority 2: CSV Export
Add `--csv` export to tools:
- `mine_topics`: Add `csv_output` parameter
- `classify_adrs`: Add `csv_output` parameter
- `check_quality`: Add `csv_output` parameter

**Rationale:** CSV export is frequently requested for data analysis

### Priority 3: Enhanced Insights
Expand `generate_insights` to match `summary` command:
- Generate Markdown reports
- Project-level insights
- Per-ADR insights
- Caching support

**Rationale:** Insights are more useful when properly formatted

### Priority 4: Topic Training
Add `train_topic_model` tool
- Train BERTopic models
- All CLI training options
- Save models to custom paths

**Rationale:** Enables custom topic modeling workflows

---

## Testing Recommendations

### Unit Tests
Create test file: `tests/test_agents/test_new_tools.py`

Test cases for each new tool:
```python
def test_get_topic_info_all():
    """Test getting all topics."""
    
def test_get_topic_info_specific():
    """Test getting specific topic."""
    
def test_get_classification_info_all():
    """Test getting all frameworks."""
    
def test_get_classification_info_specific():
    """Test getting specific framework."""
    
def test_list_adr_files():
    """Test listing ADR files."""
```

### Integration Tests
1. Test agent with natural language queries:
   - "Show me all topics"
   - "What classification frameworks are available?"
   - "List ADRs in the adrs directory"

2. Test context management:
   - Load ADRs, get topic info, list ADRs
   - Verify session state is maintained

3. Test error handling:
   - Invalid topic IDs
   - Invalid framework names
   - Non-existent directories

---

## Backward Compatibility

All changes are **backward compatible**:
- Existing tools unchanged
- New tools are optional additions
- No breaking changes to API
- System prompt enhanced without breaking existing functionality

---

## Documentation Updates Needed

1. **User Guide** (docs/INTERACTIVE_CLI_GUIDE.md)
   - Add examples of new tools
   - Update tool reference section

2. **API Reference** (docs/CLI_COMMAND_REFERENCE.md)
   - Document new tool parameters
   - Add usage examples

3. **Architecture Docs** (docs/ARCHITECTURE.md)
   - Update tool inventory
   - Document new tool responsibilities

---

## Summary

**Achievements:**
- ✅ Added 3 new tools (50% increase in tool count)
- ✅ Improved CLI command coverage from 30% to 50%
- ✅ Added filesystem discovery capability
- ✅ Added information retrieval for topics and frameworks
- ✅ Updated agent configuration and prompts
- ✅ Maintained backward compatibility

**Impact:**
- Users can now discover and explore ADR files through natural language
- Users can inspect topic models without running predictions
- Users can learn about classification frameworks
- Enhanced agent capabilities for more interactive workflows

**Next Steps:**
1. Add parser integration to existing tools (Priority 1)
2. Add CSV export capabilities (Priority 2)
3. Expand insights generation (Priority 3)
4. Add topic training tool (Priority 4)
5. Comprehensive testing of all tools

---

## Contact & Support

For questions or issues:
- GitHub Repository: https://github.com/tommantonela/ADRminer
- Documentation: docs/
- Test Suite: tests/test_agents/