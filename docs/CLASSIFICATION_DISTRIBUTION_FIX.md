# Classification Distribution Table Fix

## Problem

The Category Distribution table in the `adrminer classify predict` command was not showing all categories. Some categories that appeared in the results (e.g., "Compatibility", "Portability" for quality_attributes framework) were missing from the distribution table.

## Root Cause

The `FRAMEWORKS` dictionary in `src/adrminer/services/classification_service.py` had outdated category lists that didn't match the actual enum values defined in `src/adrminer/models/classification_schemas.py`.

When the LLM returned categories like "Compatibility" or "Portability", they weren't in the framework's category list, so they weren't counted in the distribution statistics.

## Solution

Updated the `FRAMEWORKS` dictionary to match the actual enum values from `classification_schemas.py`:

### Quality Attributes Framework

**Before (10 categories, missing some):**
```python
"categories": [
    "Performance",
    "Security",
    "Availability",      # Not in enum
    "Scalability",
    "Maintainability",
    "Usability",
    "Interoperability",  # Not in enum
    "Modifiability",      # Not in enum
    "Testability",
    "Reliability",
]
```

**After (11 categories, matching enum):**
```python
"categories": [
    "Performance",
    "Reliability",
    "Security",
    "Maintainability",
    "Scalability",
    "Usability",
    "Portability",       # Added
    "Compatibility",     # Added
    "Observability",     # Added
    "Testability",
    "Other/Only Functional Concern",  # Added
]
```

### Zimmermann Framework

**Before (6 categories, incorrect):**
```python
"categories": [
    "Technology",
    "Organization",
    "Information",
    "Architecture",
    "Process",
    "Tools",
]
```

**After (9 categories, matching enum):**
```python
"categories": [
    "Design",                     # Added
    "Technology",
    "Infrastructure",             # Added
    "Organizational/Process",     # Updated
    "Constraint",                # Added
    "Quality Attribute",          # Added
    "Crosscutting Concerns",     # Added
    "Implementation",            # Added
    "Other",                     # Updated from "Tools"
]
```

## Impact

- ✅ Category Distribution table now shows all framework categories
- ✅ Categories returned by LLM are correctly counted in statistics
- ✅ All tests pass (35/35)
- ✅ Consistency between schema enums and framework definitions
- ✅ Better user experience with complete distribution information

## Testing

### Manual Testing
```bash
cd examples/pharmacy-food
adrminer classify predict -f quality_attributes ./adrs
```

**Result:** Category Distribution table now shows all 11 categories:
- Performance (1 ADR, 16.7%)
- Reliability (0 ADRs, 0.0%)
- Security (0 ADRs, 0.0%)
- Maintainability (2 ADRs, 33.3%)
- Scalability (0 ADRs, 0.0%)
- Usability (0 ADRs, 0.0%)
- Portability (2 ADRs, 33.3%)  ← Now shows correctly
- Compatibility (1 ADR, 16.7%)  ← Now shows correctly
- Observability (0 ADRs, 0.0%)
- Testability (0 ADRs, 0.0%)
- Other/Only Functional Concern (0 ADRs, 0.0%)

### Automated Testing
```bash
cd /Users/adiazpace/Documents/GitHub/ADRminer
python -m pytest tests/ -v
```

**Result:** All 35 tests passed (100% success rate)

## Files Modified

- `src/adrminer/services/classification_service.py`:
  - Updated `quality_attributes` framework categories to match `QualityAttributesEnum`
  - Updated `zimmermann` framework categories to match `ZimmermannEnum`
  - Added updated category descriptions for new categories

## References

- Schema definitions: `src/adrminer/models/classification_schemas.py`
- Framework definitions: `src/adrminer/services/classification_service.py`