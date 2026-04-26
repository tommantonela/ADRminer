# Commands and Tools Consistency Implementation Plan

## Overview

This document outlines the implementation plan to achieve consistency between CLI commands, chat handlers, and agent tools in ADRminer. The goal is to ensure that tools and handlers provide similar execution paths while maintaining appropriate UI differences for their respective interfaces.

## Problem Statement

### Current Issues

1. **Batch Processing Inconsistency**
   - CLI commands and chat handlers manually loop through ADR files calling `service.classify()` individually
   - Agent tools call `service.classify_batch()` for parallel processing
   - This leads to inconsistent behavior and performance

2. **Code Duplication**
   - Commands, handlers, and tools have duplicate logic for:
     - File loading and validation
     - Batch processing orchestration
     - Error handling
     - Result formatting

3. **Different Execution Paths**
   - CLI commands: Direct service instantiation → individual processing → Rich UI
   - Chat handlers: Session services → individual processing → Rich UI
   - Agent tools: Session services → batch processing → Structured data

### Architectural Concern

User can either:
- Trigger commands directly (CLI or interactive CLI)
- Chat with Langchain agent that executes tools

Tools and commands have analogous functionality but different implementations, leading to:
- Maintenance burden (bugs fixed in one place, not others)
- Inconsistent behavior
- Duplicate code

## Solution: Enhanced Handlers with Silent Mode

### Key Design Decision

**Extend chat handlers to support both interactive and programmatic modes:**

```python
def execute(
    self,
    args: List[str],
    options: Dict[str, Any],
    silent: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Execute handler with optional silent mode.
    
    Args:
        args: Command arguments
        options: Command options
        silent: If True, suppress console output and return structured data
    
    Returns:
        Structured result dict if silent=True, None otherwise
    """
```

### Architecture

```
┌─────────────────┐
│  Interactive CLI│
│  /classify cmd  │
└────────┬────────┘
         │ silent=False
         │
         ▼
┌─────────────────────────────────┐
│    ClassifyPredictHandler       │
│  execute(args, options, silent) │
│                                 │
│  - Load ADR files              │
│  - Call service.classify_batch │
│  - Store in session            │
│                                 │
│  if silent:                    │
│    return structured data      │
│  else:                         │
│    display Rich UI             │
│    export files               │
└────────────┬────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐      ┌─────────┐
│Session  │      │Services │
│State    │      │Layer    │
└─────────┘      └─────────┘
         │
         │ silent=True
         ▼
┌─────────────────┐
│  Agent Tool     │
│  classify_adrs │
└─────────────────┘
```

## Implementation Plan

### Phase 1: Extend Base Handler

**File:** `src/adrminer/chat/handlers/base.py`

**Changes:**
1. Update `BaseHandler` class to support silent mode
2. Modify `execute()` method signature
3. Add return type hint

```python
from typing import Optional, Dict, Any, List

class BaseHandler:
    """Base class for command handlers."""
    
    def __init__(self, session):
        self.session = session
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any],
        silent: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Execute handler with optional silent mode.
        
        Args:
            args: Command arguments
            options: Command options
            silent: If True, suppress console output and return structured data
        
        Returns:
            Structured result dict if silent=True, None otherwise
        """
        raise NotImplementedError
    
    # Helper methods remain unchanged
    def print_success(self, message: str) -> None: ...
    def print_error(self, message: str) -> None: ...
    def print_warning(self, message: str) -> None: ...
    def print_info(self, message: str) -> None: ...
    def confirm_batch_operation(self, operation: str, count: int) -> bool: ...
```

### Phase 2: Update ClassifyPredictHandler

**File:** `src/adrminer/chat/handlers/classify.py`

**Changes:**

1. **Update `execute()` signature** to accept `silent` parameter
2. **Replace manual loop** with `service.classify_batch(texts, parallel=True)`
3. **Add `_calculate_statistics()`** method for structured returns
4. **Conditionalize Rich UI output** on `not silent`
5. **Add conditional batch operation confirmation** (skip in silent mode)

```python
class ClassifyPredictHandler(BaseHandler):
    """Handler for /classify predict command."""
    
    def execute(
        self,
        args: List[str],
        options: Dict[str, Any],
        silent: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Classify ADRs with optional silent mode.
        
        Args:
            args: [path]
            options: framework, examples, use-parser, strict, output, verbose, csv
            silent: Suppress console output and return structured data
        
        Returns:
            Dict with results, statistics if silent=True, None otherwise
        """
        # ... implementation ...
```

**Key Implementation Details:**

#### File Loading
```python
path_str = args[0]
path = Path(path_str)

if not path.exists():
    if not silent:
        self.print_error(f"Path does not exist: {path}")
    return None if silent else None

adr_files = self.session.load_adr_files(path)

if not adr_files:
    if not silent:
        self.print_warning(f"No ADRs found in {path}")
    return None if silent else None
```

#### Batch Operation Confirmation
```python
# Confirm batch operation (skip in silent mode)
if not silent and not self.confirm_batch_operation("classify", len(adr_files)):
    self.print_info("Operation cancelled")
    return None
```

#### Framework Configuration
```python
framework = options.get("framework")
service = self.session.classification_service

if framework:
    service.framework = framework
```

#### Batch Processing (FIX)
```python
# FIX: Use batch service instead of looping
texts = []
for adr_file in adr_files:
    with open(adr_file, 'r') as f:
        texts.append(f.read())

# Use classify_batch for parallel processing
results = service.classify_batch(texts, parallel=True)

# Add file paths to results
for i, result in enumerate(results):
    result["adr_file"] = str(adr_files[i])
```

#### Conditional Progress Display
```python
if not silent:
    self.session.console.print(f"\nFound {len(adr_files)} ADR file(s) to analyze\n")
    self.session.console.print(f"[bold]Framework:[/bold] {service.framework}\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=self.session.console,
    ) as progress:
        task = progress.add_task("Classifying ADRs...", total=len(adr_files))
        progress.update(task, completed=len(adr_files))
```

#### Conditional Result Display
```python
if not silent:
    self._display_results(results, verbose=options.get("verbose", False))
    self._export_results(
        results, 
        options.get("output", "sidecar"),
        options.get("csv")
    )
```

#### Always Store in Session
```python
self.session.store_analysis_result("classification", results)
```

#### Structured Return
```python
if silent:
    return {
        "results": results,
        "framework": service.framework,
        "count": len(results),
        "statistics": self._calculate_statistics(results)
    }

return None
```

#### New Statistics Method
```python
def _calculate_statistics(self, results: List[Dict]) -> Dict:
    """Calculate statistics for structured return."""
    from collections import Counter
    
    categories = [r.get('primary_category', 'Unknown') for r in results]
    category_counts = Counter(categories)
    
    confidences = [r.get('confidence', 0.0) for r in results]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    high_conf = sum(1 for r in results if r.get('confidence', 0.0) > 0.8)
    
    return {
        "total_adrs": len(results),
        "average_confidence": avg_confidence,
        "high_confidence_count": high_conf,
        "high_confidence_percentage": high_conf / len(results) if results else 0.0,
        "category_distribution": dict(category_counts.most_common())
    }
```

### Phase 3: Update Agent Tools

**File:** `src/adrminer/agents/tools.py`

**Changes:**

1. **Modify `classify_adrs` tool** to call `ClassifyPredictHandler` with `silent=True`
2. **Remove duplicate logic** from tool (file loading, service calls)
3. **Convert handler's structured return** to `ToolResult`
4. **Apply same pattern** to other tools

```python
@tool(parse_docstring=True)
def classify_adrs(
    path: str,
    framework: str = "kruchten",
    use_examples: bool = True
) -> Dict[str, Any]:
    """Classify a batch of ADRs using a specified classification framework.
    
    This tool classifies a batch of ADRs according to architectural decision
    classification frameworks. Supports multiple frameworks with different
    classification schemes.
    
    Args:
        path: Directory path to load ADRs from
        framework: Classification framework (kruchten, quality_attributes, zimmermann)
        use_examples: Whether to use few-shot examples for better accuracy
    
    Returns:
        Dictionary with classification results for each ADR
    
    Example:
        >>> classify_adrs("adrs/", framework="kruchten")
        >>> classify_adrs(framework="zimmermann", use_examples=False)
    """
    session = get_session()
    if session is None:
        return ToolResult(
            success=False,
            message="Session not initialized",
            requires_approval=False
        ).model_dump()
    
    # Log tool invocation
    if hasattr(session, 'console'):
        session.console.print("\n[dim]→ Tool called: classify_adrs[/dim]")
        session.console.print(f"  [dim]framework: {framework}, use_examples: {use_examples}[/dim]")
    
    try:
        # Import handler
        from adrminer.chat.handlers.classify import ClassifyPredictHandler
        
        # Create handler instance
        handler = ClassifyPredictHandler(session)
        
        # Call handler in silent mode
        result_data = handler.execute(
            args=[path],
            options={
                "framework": framework,
                "use_examples": use_examples
            },
            silent=True  # Get structured return, no console output
        )
        
        if result_data is None:
            return ToolResult(
                success=False,
                message="Classification failed",
                requires_approval=False
            ).model_dump()
        
        # Convert to ToolResult
        result = ToolResult(
            success=True,
            message=f"Classified {result_data['count']} ADR(s) using {framework} framework",
            data=result_data,
            requires_approval=True,
            batch_operation=True,
            num_affected=result_data['count']
        ).model_dump()
        
        # Log completion
        if hasattr(session, 'console'):
            session.console.print(f"[green]✓[/green] {result['message']}")
        
        return result
        
    except Exception as e:
        result = ToolResult(
            success=False,
            message=f"Failed to classify ADRs: {str(e)}",
            requires_approval=False
        ).model_dump()
        
        # Log error
        if hasattr(session, 'console'):
            session.console.print(f"[red]✗[/red] {result['message']}")
        
        return result
```

**Apply similar pattern to other tools:**

- `check_quality` → `CheckHandler`
- `mine_topics` → `TopicsPredictHandler`
- `get_classification_info` → `ClassifyInfoHandler` (already simple)
- `get_topics_info` → `TopicsInfoHandler`
- `generate_insights` → `InsightsHandler`

### Phase 4: Update Other Handlers

Apply the same pattern to other handlers:

#### Topics Handler
**File:** `src/adrminer/chat/handlers/topics.py`

1. Update `TopicsPredictHandler.execute()` to support `silent` mode
2. Use `service.predict_batch()` instead of manual loop
3. Add `_calculate_statistics()` method
4. Conditionalize Rich UI output

#### Check Handler
**File:** `src/adrminer/chat/handlers/check.py`

1. Update `CheckQualityHandler.execute()` to support `silent` mode
2. Use `service.check_batch()` instead of manual loop
3. Add `_calculate_statistics()` method
4. Conditionalize Rich UI output

#### Summary Handler
**File:** `src/adrminer/chat/handlers/util.py`

1. Update `SummaryGenerateHandler.execute()` to support `silent` mode
2. Add structured return for results

#### Insights Handler
**File:** `src/adrminer/chat/handlers/base.py` or new file

1. Create `InsightsGenerateHandler` with `silent` mode support
2. Return structured insights data

### Phase 5: (Optional) Update CLI Commands

**File:** `src/adrminer/cli/commands/classify.py`

Optionally, refactor CLI commands to also use handlers for full consistency:

```python
@classify_app.command("predict")
def predict(
    path: Path = typer.Argument(...),
    framework: Literal["kruchten", "quality_attributes", "zimmermann"] = typer.Option(None),
    # ... other options ...
) -> None:
    """Classify ADRs using LLM models."""
    # ... setup service ...
    
    # Create minimal session for CLI
    from adrminer.chat.session import SessionManager
    session = SessionManager()
    session.classification_service = service
    
    # Import handler
    from adrminer.chat.handlers.classify import ClassifyPredictHandler
    
    # Call handler (interactive mode)
    handler = ClassifyPredictHandler(session)
    handler.execute(
        args=[str(path)],
        options={"framework": framework, ...},
        silent=False  # Interactive: show Rich output
    )
```

**Benefits:**
- Full consistency across all interfaces
- Single source of truth
- Reduced code duplication

**Trade-offs:**
- Requires session management in CLI (may not be necessary)
- More refactoring required

## Benefits of This Approach

### 1. Consistent Execution Path
- Both tools and handlers use identical logic
- Same service calls, same error handling, same session updates
- Only difference is UI output mode

### 2. Minimal Code Changes
- Extend existing handlers (no new modules)
- Tools become thin wrappers around handlers
- Single source of truth for each operation

### 3. Session Synchronization
- Handlers already manage session perfectly
- Tools leverage same session management
- No additional complexity

### 4. Fixes Batch Processing Issue
- Both paths now use `service.classify_batch()`
- Consistent parallel processing behavior
- No more manual looping

### 5. Backward Compatible
- Existing interactive CLI behavior unchanged (`silent=False` by default)
- CLI commands can optionally use handlers if desired
- No breaking changes to existing functionality

## Example: User Experience Comparison

### Interactive CLI Mode
```
User: /classify predict adrs/

→ Handler shows: [blue]Loading classification service...[/blue]
→ Handler shows: Found 25 ADR file(s) to analyze
→ Handler shows: [bold]Framework:[/bold] kruchten
→ Handler shows: Progress bar ████████ 100%
→ Handler shows: Rich table with classification results
→ Handler shows: Category Distribution table
→ Handler shows: Statistics
→ Handler shows: [green]✓ Exported 25 sidecar file(s)[/green]
→ Session updated with results
```

### Agent Chat Mode
```
User: Please classify the ADRs in adrs/

→ Agent calls: classify_adrs("adrs/", framework="kruchten")
→ Handler runs silently (no UI output)
→ ToolResult returned: 
  {
    "success": true,
    "message": "Classified 25 ADR(s) using kruchten framework",
    "data": {
      "results": [...],
      "framework": "kruchten",
      "count": 25,
      "statistics": {...}
    }
  }
→ Agent summarizes: "I've classified 25 ADRs using the Kruchten framework. 
   The average confidence is 0.85 with 22 high-confidence classifications 
   (88%). The most common category is Property (diacrisis) with 12 ADRs."
→ Agent can access detailed results from ToolResult.data if needed
→ Session updated with results (same as interactive CLI)
```

### Both Paths
- Use same `service.classify_batch()` logic
- Store results in `session.analysis_results["classification"]`
- Same error handling and recovery
- Same behavior, different presentation

## Potential Concerns and Mitigations

### 1. Handler Coupling to Agent Tools
**Concern:** Tools depend on handlers, creating dependency

**Mitigation:**
- Handlers are already the "interface layer" for CLI
- Natural place for reuse
- Clear separation: handlers orchestrate, services execute

### 2. Silent Mode Complexity
**Concern:** Adding `silent` parameter makes handlers more complex

**Mitigation:**
- Simple conditional (`if not silent:`)
- Clear separation of concerns
- Type hints make contract explicit

### 3. Return Value Handling
**Concern:** Handlers return `None` in normal mode, data in silent mode

**Mitigation:**
- Clear contract with `Optional[Dict[str, Any]]`
- Well-documented behavior
- Type safety through hints

### 4. Console Output in Silent Mode
**Concern:** What should be printed in silent mode?

**Decision:**
- Developer controls what's printed
- Current pattern: Use dim colored logs for tool invocation
- Progress and results are suppressed
- Only success/failure messages shown

Example from current tools:
```python
# Log tool invocation (always shown in dim)
session.console.print("\n[dim]→ Tool called: classify_adrs[/dim]")

# Progress/results only shown in non-silent mode
if not silent:
    session.console.print(f"[green]✓[/green] Classified {len(results)} ADRs")
```

## Testing Strategy

### Unit Tests

1. **Handler Tests**
   - Test `execute()` with `silent=True` returns structured data
   - Test `execute()` with `silent=False` displays UI and returns None
   - Test batch processing uses `service.classify_batch()`
   - Test statistics calculation
   - Test error handling

2. **Tool Tests**
   - Test tool calls handler with `silent=True`
   - Test tool converts handler result to `ToolResult`
   - Test tool logs invocation and completion
   - Test error handling

3. **Service Tests** (existing)
   - Ensure `classify_batch()` works correctly
   - Test parallel processing

### Integration Tests

1. **Interactive CLI Flow**
   - Test command → handler → service → UI
   - Verify results stored in session
   - Verify files exported

2. **Agent Tool Flow**
   - Test user chat → agent → tool → handler → service
   - Verify tool returns correct data
   - Verify results stored in session
   - Verify no console duplication

3. **Consistency Tests**
   - Verify same inputs produce same results (regardless of path)
   - Verify session state is identical after command vs tool execution

## Migration Timeline

### Week 1: Foundation
- [ ] Update `BaseHandler` with silent mode support
- [ ] Update `ClassifyPredictHandler` with silent mode
- [ ] Fix batch processing issue (use `classify_batch()`)
- [ ] Add unit tests for handler

### Week 2: Tools Integration
- [ ] Update `classify_adrs` tool to call handler
- [ ] Remove duplicate code from tool
- [ ] Add unit tests for tool
- [ ] Integration tests for tool flow

### Week 3: Other Handlers
- [ ] Update `TopicsPredictHandler` with silent mode
- [ ] Update `CheckQualityHandler` with silent mode
- [ ] Update other handlers as needed
- [ ] Add unit tests

### Week 4: Other Tools
- [ ] Update `check_quality` tool
- [ ] Update `mine_topics` tool
- [ ] Update other tools to use handlers
- [ ] Add integration tests

### Week 5: (Optional) CLI Commands
- [ ] Refactor CLI commands to use handlers
- [ ] Test CLI compatibility
- [ ] Update documentation

## Conclusion

This approach achieves the goal of consistent execution between commands and tools while maintaining appropriate UI differences for their respective interfaces. The key advantages are:

1. ✅ **Consistent execution**: Both paths use identical logic
2. ✅ **Fixes batch processing**: Both use `classify_batch()`
3. ✅ **Minimal refactoring**: Extend existing handlers
4. ✅ **Session management**: Handlers already handle it perfectly
5. ✅ **User experience**: Both paths work seamlessly in interactive CLI
6. ✅ **Maintainability**: Single source of truth for each operation

The implementation is straightforward and can be done incrementally, starting with the classification handler and tool as a proof of concept, then applying the pattern to other handlers and tools.