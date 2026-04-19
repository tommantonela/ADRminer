# Topic Model Loading Fix

## Problem

The `adrminer topics predict` command was failing with the error:
```
Failed to load topic model: 'NoneType' object has no attribute 'topic_model'
```

## Root Cause Analysis

Two issues were identified in `src/adrminer/services/topic_service.py`:

### Issue 1: Wrong Embedding Model Type
The code was using `SentenceTransformer` directly from `sentence_transformers` instead of `SentenceTransformerBackend` from BERTopic's backend module. This caused compatibility issues when loading the saved model.

### Issue 2: Incorrect Settings Reference
In the `__init__` method, the code was using the `settings` parameter directly instead of `self.settings` after base class initialization. This caused an `AttributeError` when accessing `settings.topic_model.path`.

## Solution

### Change 1: Use Correct Embedding Model Backend

**Before:**
```python
from sentence_transformers import SentenceTransformer
embedding_model = SentenceTransformer(embedding_model_name)
self.model = BERTopic.load(self.model_path, embedding_model=embedding_model)
```

**After:**
```python
from bertopic.backend._sentencetransformers import SentenceTransformerBackend
embedding_model = SentenceTransformerBackend(embedding_model_name)
self.model = BERTopic.load(self.model_path, embedding_model=embedding_model)
```

This matches the approach used in `notebooks/adr_topic_mining.py`.

### Change 2: Use `self.settings` After Initialization

**Before:**
```python
super().__init__(settings)
self.model_path = Path(model_path) if model_path else Path(settings.topic_model.path)
self.use_llm_representation = settings.topic_model.use_llm_representation
```

**After:**
```python
super().__init__(settings)
self.model_path = Path(model_path) if model_path else Path(self.settings.topic_model.path)
self.use_llm_representation = self.settings.topic_model.use_llm_representation
```

### Change 3: Enhanced Error Handling

The `_load_model` method now includes:
- Better error messages with fallback details
- Verification that model is not `None` after loading
- Fallback to loading without embedding model if the primary approach fails
- Informative logging for debugging

## Testing

### Manual Testing
```bash
cd examples/pharmacy-food
adrminer topics predict ./adrs
```

**Result:** Successfully predicted topics for 6 ADRs:
- 3 ADRs classified as "Service-Oriented Architecture Platform"
- 3 ADRs classified as "Microservices Deployment on Cloud"

### Automated Testing
```bash
cd /Users/adiazpace/Documents/GitHub/ADRminer
python -m pytest tests/ -v
```

**Result:** All 35 tests passed (100% success rate)

## Impact

- ✅ Topic prediction now works correctly with saved models
- ✅ Better error handling and debugging information
- ✅ Consistency with notebook implementation
- ✅ No regressions in existing functionality
- ✅ All tests pass

## Files Modified

- `src/adrminer/services/topic_service.py`:
  - Fixed `_load_model()` method to use `SentenceTransformerBackend`
  - Fixed `__init__()` method to use `self.settings`
  - Added enhanced error handling and validation

## References

- Original notebook: `notebooks/adr_topic_mining.py`
- BERTopic documentation: https://maartengr.github.io/BERTopic/