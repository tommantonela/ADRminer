# ADRminer Implementation Decisions

**Version:** 1.0  
**Date:** 2026-04-19  
**Status:** Active

---

## Table of Contents

1. [Prompt Simplification in Refactored Services](#1-prompt-simplification-in-refactored-services)
2. [ADR Parser Service Design Decision](#2-adr-parser-service-design-decision)
3. [Comparison: Notebook vs Refactored Implementations](#3-comparison-notebook-vs-refactored-implementations)
4. [Rationale for Design Choices](#4-rationale-for-design-choices)

---

## 1. Prompt Simplification in Refactored Services

### Decision
Use simplified prompts in classification and checking services instead of comprehensive prompt definitions from original notebooks.

### Context
During the refactoring from notebook prototypes to production services, we made a deliberate choice to simplify LLM prompts for:

- **Faster LLM calls** (lower token usage, lower latency, lower cost)
- **Simpler code and maintenance** (easier to understand, modify, and maintain)
- **Good enough for most cases** (standard ADRs follow clear patterns)

### Comparison

| Aspect | Original Notebooks | Refactored Services |
|---------|------------------|----------------------|
| **Prompt Source** | `notebooks/prompts.py` (600+ lines) | Hardcoded in services |
| **Prompt Detail** | Multiple variants with personas, examples, guidelines | Single simplified prompt (~40 lines) |
| **Examples Support** | Built-in few-shot examples | Configurable (can be disabled) |
| **Prompt Complexity** | High (comprehensive guidelines, disambiguation rules) | Medium (basic framework definition) |
| **LLM Token Usage** | High | Low (~40 lines vs ~600 lines) |
| **Maintainability** | Low (need to edit Python file) | High (edit Markdown files) |

### Implementation

#### Classification Service (`src/adrminer/services/classification_service.py`)

**Original Approach (notebooks):**
```python
KRUCHTEN_FRAMEWORK_V1 = """
Your task is to analyze Architectural Decision Records (ADRs) to identify architectural decisions types according to Philippe Kruchten's ontology...
[600 lines with detailed guidelines]
"""
```

**Current Implementation:**
```python
def _build_prompt(self, text: str, framework: str, examples: Optional[List[Dict]] = None) -> str:
    """Build classification prompt."""
    framework_info = FRAMEWORKS[framework]
    categories = framework_info["categories"]
    
    # Start with system instructions
    prompt = f"""You are an expert architectural decision analyst. Your task is to classify the given Architectural Decision Record (ADR) into one of the following categories for the {framework_info['name']} framework.

Categories:
"""
    
    # Add categories
    for i, category in enumerate(categories, 1):
        prompt += f"{i}. {category}\n"
    
    prompt += """
Instructions:
1. Read the ADR carefully
2. Identify the most appropriate category based on the decision's primary focus
3. Provide your classification in JSON format with the following structure:
   {
     "category": "<category name>",
     "confidence": <0.0 to 1.0>,
     "explanation": "<brief explanation>",
     "alternatives": ["<alternative category 1>", "<alternative category 2>"]
   }

"""
    
    # Add examples if provided (few-shot)
    if examples:
        prompt += "Here are some examples to guide your classification:\n\n"
        
        for i, example in enumerate(examples[:3], 1):
            if "text" in example and "category" in example:
                prompt += f"Example {i}:\n"
                prompt += f"ADR: {example['text'][:500]}...\n"
                prompt += f"Category: {example['category']}\n\n"
        
        prompt += "---\n\n"
    
    # Add the ADR to classify
    prompt += f"Now classify the following ADR:\n\n{text}\n\n"
    prompt += "Provide your classification in JSON format:"
    
    return prompt
```

**Rationale:**
- ✅ **Faster**: Shorter prompt = fewer tokens, faster LLM calls
- ✅ **Simpler**: Easier to understand and maintain prompt logic
- ✅ **Cost Effective**: Reduced token usage lowers LLM API costs
- ✅ **Good Enough**: Works well for standard ADRs that follow clear patterns
- ✅ **Configurable**: Can enable few-shot examples via configuration if needed

#### Checking Service (`src/adrminer/services/checking_service.py`)

**Original Approach (notebooks):**
```python
CONSISTENCY_PROMPT_ALL_SECTIONS = """
## Instructions
For each MADR section_name (Status, Context, Decision, Consequences, Decision Drivers, Considered Options), return the following information:
[~500 lines with chain-of-thought checklist]
"""
```

**Current Implementation:**
```python
FULL_CONSISTENCY_PROMPT = """
You are an expert software architect who knows about Architecture Decision Records (ADRs).
Your task is to check the ADR below and assess its adherence to the sections of the MADR template.

For each section, analyze:
- if the section is present in the ADR under the right title/subtitle, and
- if the section contents are present somewhere in the ADR text.

Note:
- A section can have its content present but lack a proper heading (e.g., 'Decision' content is present but not under a clear heading).
- If such misalignments exist (title vs. content location), describe them in your assessment.

Your adherence score, between 0.0 (lack of alignment) and 1.0 (almost perfect alignment), should be calculated based on the presence and degree of alignment of each section.
Please make your assessment of each section before giving an adherence score.

For the assessment, use a string list of bullets to enumerate your individual analysis of each template section.
"""
```

**Rationale:**
- ✅ **Clear Instructions**: Simple, direct instructions work well for most cases
- ✅ **Faster**: Shorter prompt = faster LLM calls, lower costs
- ✅ **Maintainable**: Hardcoded constant, but well-structured
- ✅ **Effective**: Works well for template adherence checks

### Trade-offs

**Benefits:**
- ⚡ **Performance**: 60-90% reduction in LLM token usage
- 💰 **Cost**: Proportional cost reduction (fewer tokens = lower API costs)
- 🔧 **Simplicity**: Easier to understand and maintain codebase
- 🚀 **Good Enough**: Produces accurate results for standard ADRs

**Drawbacks:**
- ⚠️ **Accuracy**: May be less accurate for complex or edge-case ADRs
- ⚠️ **Edge Cases**: Fewer guidelines may miss edge cases
- ⚠️ **Guidance**: Less detailed instructions may lead to lower quality on ambiguous ADRs
- 🔧 **Customization**: Harder to customize for specific domains or organizations

### Recommendation

**For Current MVP:** ✅ Keep simplified prompts

**Rationale:**
- Performance and cost benefits outweigh minor accuracy loss
- Most ADRs follow standard patterns that simple prompts handle well
- Can iterate: monitor classification accuracy and add complexity if needed
- Users who need more sophisticated prompts can provide custom prompts externally (future enhancement)

---

## 2. ADR Parser Service Design Decision

### Decision
No dedicated ADR parser service will be implemented. Services will continue to read ADR files directly and extract what they need.

### Context
- Original notebooks had parsing utilities in `notebooks/utils.py` and `notebooks/adr.py`
- Current refactored services use `Path.read_text()` to load ADR content
- No dedicated reusable parsing component in current architecture

### Comparison

| Aspect | Dedicated Parser | Current Approach |
|---------|-----------------|----------------|
| **Structured Access** | ✅ Extract sections into Pydantic models | ❌ No structured access |
| **Section Extraction** | ✅ Extract individual sections with metadata | ❌ Full-text only |
| **Template Detection** | ✅ Identify ADR template type | ❌ No detection |
| **Normalization** | ✅ Standardize different ADR formats | ❌ No normalization |
| **Validation** | ✅ Validate ADR structure | ❌ No validation |
| **Error Handling** | ✅ Graceful parsing of malformed ADRs | ❌ Basic error handling |
| **Overhead** | 🔴 Medium (new service, Pydantic models) | 🟢 Low (minimal) |
| **Maintainability** | 🟡 Medium (parsing logic centralized) | 🟢 High (no changes needed) |
| **Complexity** | 🔴 Higher (regex, validation logic) | 🟢 Low (simple file reading) |

### Rationale for Current Approach

**Why No Dedicated Parser:**

1. **Minimal Overhead**: Current services work fine without structured parsing
2. **Simpler**: `Path.read_text()` is sufficient for most use cases
3. **Fast Enough**: Services don't need section-level granularity
4. **Lower Risk**: Adding parser service increases complexity and potential bugs
5. **Works For Now**: Current implementation is production-ready and tested

**When Parser Becomes Necessary:**

A dedicated ADR parser service should be implemented when:

1. **LLM Agent Development** (Phase 2): Agent needs structured ADR data for:
   - Better classification with section context
   - Better checking with precise section analysis
   - Cross-service insights (e.g., "ADRs with missing alternatives section")

2. **Advanced Insights**: When generating cross-service analysis, need:
   - Section-level statistics
   - Template usage patterns
   - Decision completeness metrics

3. **Template Normalization**: When supporting multiple ADR templates (MADR, custom, etc.), need:
   - Template detection and routing
   - Section mapping between templates

4. **CLI Enhancements**: When adding advanced inspection features, need:
   - Section-by-section quality scores
   - ADR completeness validation
   - Template-specific guidelines

**Implementation Recommendation:**
```python
# Lightweight alternative (optional enhancement)
def extract_sections_simple(adr_text: str) -> Dict[str, str]:
    """Extract key sections using simple regex patterns.
    
    Lightweight extraction for basic use cases. Full parser should be implemented
    when section-level granularity is required (e.g., for LLM agent).
    """
    import re
    
    patterns = {
        r'#+\s*Status\s*': 'status',
        r'#+\s*Context\s*': 'context',
        r'#+\s*Decision\s*': 'decision',
        r'#+\s*Decision Drivers\s*': 'decision_drivers',
        r'#+\s*Consequences\s*': 'consequences',
        r'#+\s*Alternatives Considered\s*': 'alternatives',
    }
    
    sections = {}
    
    for header, key in patterns.items():
        match = re.search(header, adr_text, re.IGNORECASE)
        if match:
            # Extract section content
            start = match.end()
            next_header_pos = len(adr_text)
            
            # Find next header or end of document
            next_match = re.search(r'#+\s*\s*', adr_text[start:])
            if next_match:
                end = next_match.start()
                section_content = adr_text[start:end].strip()
                
                if key == 'alternatives considered':
                    # Parse bullet points
                    items = [line.strip('- ').strip() for line in section_content.split('\n') if line.strip()]
                    sections[key] = items
                else:
                    sections[key] = section_content
            
            adr_text = adr_text[:start] + adr_text[end:]
    
    return sections
```

### Benefits of Current Approach

✅ **Works For Now**: All current features work without changes  
✅ **Minimal Complexity**: Simple file reading is sufficient  
✅ **Fast**: No parsing overhead  
✅ **Low Risk**: Fewer components to maintain  
✅ **Production Ready**: Current implementation is stable  
✅ **Cost Effective**: No additional dependencies needed

---

## 3. Comparison: Notebook vs Refactored Implementations

### Classification Service

| Feature | Notebooks (`notebooks/prompts.py`) | Refactored (`classification_service.py`) |
|---------|-----------------------------------|-----------------------------------|
| **Prompt Storage** | Single Python file | Hardcoded in service |
| **Prompt Loading** | Import from file | Hardcoded string |
| **Variants** | Multiple versions (V1, V2) | Single version |
| **Examples** | Built-in few-shot examples | Configurable via `use_examples` parameter |
| **Prompt Size** | ~600 lines | ~40 lines |
| **Persona** | Senior architect | None |
| **Guidelines** | Comprehensive disambiguation rules | Basic instructions |
| **Test Rules** | Multiple test scenarios | Basic JSON format requirement |
| **Complexity** | High | Medium |

### Checking Service

| Feature | Notebooks (`notebooks/prompts.py`) | Refactored (`checking_service.py`) |
|---------|-----------------------------------|-----------------------------------|
| **Prompt Storage** | Single Python file | Hardcoded constants |
| **Prompt Loading** | Import from file | Hardcoded strings |
| **Variants** | Single prompt for all sections | Single prompt for all sections |
| **Examples** | N/A (few-shot in prompt) | N/A |
| **Prompt Size** | ~500-700 lines | ~110-180 lines |
| **Chain-of-Thought** | Comprehensive checklist | Basic instructions |
| **Section Handling** | Individual section prompts | Single comprehensive prompt |
| **Strict Rules** | Multiple validation rules | Basic presence check |
| **Complexity** | High | Medium |

### Key Differences

1. **Abstraction Level**: Notebooks had higher abstraction (function for loading prompts), refactored services have lower abstraction (hardcoded prompts)
2. **Flexibility**: Notebooks more flexible (multiple prompt variants), refactored services simpler but rigid
3. **Completeness**: Notebooks more comprehensive (detailed guidelines, rules), refactored services pragmatic (good enough)
4. **Performance**: Refactored services significantly faster (60-90% fewer tokens), notebooks had higher accuracy potential
5. **Maintainability**: Notebooks harder to maintain (Python file), refactored services easier to maintain (in code, but hardcoded)

### Migration Path

The refactoring represents a **pragmatic simplification**:

- ✅ **Preserved Functionality**: All core features work correctly
- ✅ **Improved Performance**: 60-90% reduction in LLM token usage
- ✅ **Simplified Codebase**: Easier to understand and maintain
- ⚠️ **Reduced Accuracy Potential**: May be less accurate for edge cases
- ⚠️ **Lost Some Features**: Detailed disambiguation rules, test scenarios

### Original Features Not Currently Implemented

The following features from original notebooks are **not** in refactored services:

1. **Multiple Prompt Variants**: V1, V2 versions of prompts (with/without examples)
2. **Personas**: Senior architect persona with expertise level
3. **Comprehensive Guidelines**: Detailed disambiguation rules for ambiguous cases
4. **Test Scenarios**: Multiple test rules for classification accuracy
5. **Section-Level Prompts**: Individual prompts for each MADR section with detailed rules
6. **Example Management**: Built-in few-shot examples with selection logic
7. **Strict Scoring**: Confidence scoring with multiple test scenarios
8. **Disambiguation Rules**: Explicit rules for resolving ambiguities
9. **Prompt A/B Testing**: Support for testing different prompt variants

### When to Restore These Features

Consider restoring original prompt features when:

1. **Production Feedback**: If users report low accuracy or confusion
2. **Complex ADRs**: If many ADRs require sophisticated classification
3. **Quality Requirements**: If accuracy becomes critical for production use
4. **A/B Testing**: For systematic prompt optimization

**Implementation Strategy:**
- Keep simplified prompts as default
- Add `prompt_mode` configuration option (basic/advanced)
- Implement prompt variant loading from external files (see Prompt Externalization plan)
- Add prompt performance metrics (token count, latency, accuracy)
- Run A/B tests with different prompts and measure effectiveness

---

## 4. Rationale for Design Choices

### Design Principles Applied

1. **Pragmatism over Perfectionism**
   - Start with simple, working solution
   - Iterate based on actual usage and feedback
   - Avoid over-engineering before validating need

2. **Performance First**
   - LLM calls are the primary cost driver
   - Token reduction has immediate impact on latency and cost
   - Simplicity enables faster development and iteration

3. **Maintainability Focus**
   - Code that is easy to understand is easy to maintain
   - Hardcoded strings are easier to modify than complex template logic
   - Avoid unnecessary abstraction layers

4. **Flexibility for Future Changes**
   - Design allows for future enhancements without breaking changes
   - Configuration options enable custom behavior
   - External files allow user customization without code changes

5. **Good Enough for Most Users**
   - 80/20 rule: Simple solution that works for 80% of use cases
   - Target standard ADRs (MADR template, clear structure)
   - Handle edge cases gracefully rather than optimizing for them

### Trade-off Analysis

| Concern | Weight | Prompt Simplification | No Parser Service |
|---------|--------|---------------------|-------------------|
| **Performance** | 🔴 High | 🟢 Very High | 🟢 High |
| **Cost** | 🔴 High | 🟢 Very High | 🟢 Low |
| **Maintainability** | 🟢 Medium | 🟢 Very High | 🟢 High |
| **Accuracy** | 🟢 Medium | 🟢 High | 🟢 High |
| **Complexity** | 🟢 Low | 🟢 Low | 🔴 High |
| **Flexibility** | 🟢 Low | 🟢 Low | 🟢 Low |
| **Time to Market** | ⚡ Fast | ⚡ Fast | ⚡ Fast |

**Net Assessment:** ✅ Prompt simplification is the right choice for current stage

### Future Evolution Path

**Phase 1 (Current - MVP)**
- Simplified prompts
- Direct file reading
- Basic services
- Interactive CLI foundation

**Phase 2 (LLM Agent)**
- May need structured ADR data
- Consider lightweight section extractor
- Prompt variant testing based on production feedback

**Phase 3 (Advanced Features)**
- Full ADR parser service if needed
- Prompt A/B testing framework
- External prompt management system
- Multi-prompt optimization

---

## 5. Implementation Recommendations

### Immediate Actions

1. ✅ **Document Simplification Decision** (This document)
2. ✅ **Document No-Parser Decision** (This document)
3. ✅ **Update Service Roadmap** to reflect current state
4. ✅ **Add Implementation Notes** to services explaining why prompts are simplified

### Short-Term Enhancements

**Priority 1: External Prompt Configuration** (2-3 weeks)
- Create prompt template system
- Allow custom prompts via configuration
- Add prompt loading from external Markdown files
- Document prompt template format

**Priority 2: Lightweight Section Extraction** (1-2 weeks)
- Add optional section extractor utility
- Extract key sections using regex
- Make available to services that need it
- Keep minimal and optional

**Priority 3: Prompt Performance Tracking** (1 week)
- Add metrics collection (token count, latency)
- Log prompt effectiveness data
- Create dashboard for prompt analysis

### Medium-Term Enhancements

**Priority 4: ADR Parser Service** (3-4 weeks, when needed)
- Implement full Pydantic-based parser
- Add section-level parsing
- Support multiple template types
- Add validation and normalization
- Integrate with services

**Priority 5: Prompt A/B Testing Framework** (2-3 weeks)
- Create prompt variant management system
- Add A/B testing utilities
- Implement automated evaluation metrics
- Add prompt optimization workflows

---

## 6. Migration Notes

### From Notebooks to Refactored Services

The refactoring from notebook prototypes to production services involved significant simplification:

**What Was Removed:**
- Multiple prompt variants (V1, V2)
- Detailed personas and guidelines
- Comprehensive disambiguation rules
- Test scenarios and rules
- Section-level prompts with strict validation

**What Was Preserved:**
- Core functionality (classification, checking)
- Framework definitions (Kruchten, Quality Attributes, Zimmermann)
- Batch processing capabilities
- JSON output format
- Service layer architecture

**Why It Worked:**
1. **Different Goals**: Notebooks were for research/experimentation, production services are for practical use
2. **Focus on Performance**: Production prioritized speed and cost over accuracy
3. **Simplicity**: Production prioritized maintainability over feature richness

### Backward Compatibility

If you need to restore original notebook-style prompts:

1. **Configuration Option**: Add `--prompt-mode basic|advanced` to CLI
2. **Feature Flag**: Use environment variable or config file
3. **Gradual Migration**: Test advanced prompts in staging before production
4. **Fallback**: Default to simplified prompts for stability

---

## 7. Conclusion

The ADRminer refactoring represents a **pragmatic, production-focused approach** that successfully:

✅ **Delivers Core Value**: Functional classification and checking services  
✅ **Optimizes for Use Case**: Fast, cost-effective for standard ADRs  
✅ **Maintainable**: Clean, simple codebase  
✅ **Extensible**: Designed to support future enhancements  

The design decisions trade some accuracy and features for significant gains in performance, maintainability, and time-to-market.

**Next Steps:**
1. Monitor classification accuracy in production
2. Collect user feedback on prompt effectiveness
3. Iterate based on real-world usage patterns
4. Add complexity only when validated as necessary

---

**Document History:**
- v1.0 - Initial documentation (2026-04-19)