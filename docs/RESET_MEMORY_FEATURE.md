# Reset Memory Feature Documentation

## Overview

The Reset Memory feature allows users to clear session state and analysis results in ADRminer's interactive CLI. This feature provides two ways to reset memory:

1. **Tool-based reset**: Use the `reset_memory` tool via natural language interaction with the AI agent
2. **Command-based reset**: Use the `/reset_memory` command directly in the CLI

## Use Cases

- Starting fresh with a new set of ADRs
- Clearing accumulated analysis results to free memory
- Resetting command history for a clean session
- Testing different analysis workflows without restarting the CLI

## What Gets Cleared

The reset_memory function clears:

- **Analysis Results**: All stored analysis results (topics, classifications, quality checks, etc.)
- **Loaded ADRs**: List of ADR files currently loaded in the session
- **Command History**: History of commands executed in the current session

**Note**: Agent conversation history (stored in the LangGraph checkpointer) is **NOT** cleared. This allows users to continue natural language conversations with the agent after resetting data.

## Implementation Details

### 1. Tool-based Reset (Natural Language)

Users can ask the AI agent to reset memory:

```
User: Reset my memory
User: Clear all analysis results
User: Start fresh with new data
```

The agent will use the `reset_memory` tool to clear session state.

**Tool Definition** (in `src/adrminer/agents/tools.py`):

```python
reset_memory = StructuredTool.from_function(
    name="reset_memory",
    description="Reset session memory and clear all analysis results",
    func=_reset_memory_impl
)
```

**Tool Response Format**:

```json
{
  "success": true,
  "message": "Memory reset complete",
  "data": {
    "analysis_results_cleared": 3,
    "loaded_adrs_cleared": 10,
    "has_conversation_history": true
  },
  "requires_approval": false,
  "batch_operation": false,
  "num_affected": 0
}
```

### 2. Command-based Reset (/reset_memory)

Users can execute the command directly:

```bash
/reset_memory
```

**Command Handler**: `ResetMemoryHandler` (in `src/adrminer/chat/handlers/util.py`)

The handler displays a formatted summary of what was cleared:

```
✓ Memory reset complete
  Analysis results cleared: 3
  Loaded ADRs cleared: 10
  Command history cleared: Yes
  Note: Agent conversation history preserved
```

## Architecture

### Components

1. **`SessionManager.reset_memory()`** (in `src/adrminer/chat/session.py`)
   - Core implementation that clears session state
   - Returns summary of what was cleared

2. **`reset_memory` tool** (in `src/adrminer/agents/tools.py`)
   - LangChain StructuredTool for agent interaction
   - Wraps SessionManager.reset_memory()
   - Returns structured response for agent

3. **`ResetMemoryHandler`** (in `src/adrminer/chat/handlers/util.py`)
   - CLI command handler for `/reset_memory`
   - Displays formatted output using Rich console

4. **Integration Points**:
   - Added to tool list in `LangChainAdrminerAgent`
   - Registered in command registry (`src/adrminer/chat/commands.py`)
   - Mapped in dispatcher (`src/adrminer/chat/dispatcher.py`)

### SessionManager Implementation

```python
def reset_memory(self) -> Dict[str, Any]:
    """
    Reset session memory and clear all analysis results.
    
    Clears:
    - analysis_results: All stored analysis results
    - loaded_adrs: List of loaded ADR files
    - command_history: History of executed commands
    
    Note: Agent conversation history is NOT cleared.
    
    Returns:
        Summary of what was cleared
    """
    summary = {
        "analysis_results": list(self.analysis_results.keys()),
        "loaded_adrs_count": len(self.loaded_adrs),
        "has_agent": self.agent is not None
    }
    
    # Clear session state
    self.analysis_results.clear()
    self.loaded_adrs.clear()
    self.command_history.clear()
    
    return summary
```

## Usage Examples

### Example 1: Natural Language Reset

```
User> Load ADRs from ./examples/adrs
[Loads 10 ADRs...]

User> Analyze topics
[Performs topic analysis...]

User> Reset my memory
AI: I'll reset your session memory. This will clear all analysis results and loaded ADRs.
    ✓ Memory reset complete
      Analysis results cleared: 1
      Loaded ADRs cleared: 10
      Command history cleared: Yes

User> Load ADRs from ./different/adrs
[Loads new set of ADRs...]
```

### Example 2: Command-based Reset

```
User> /topics predict ./examples/adrs
[Performs topic analysis...]

User> /classify predict ./examples/adrs --framework kruchten
[Performs classification...]

User> /reset_memory
✓ Memory reset complete
  Analysis results cleared: 2 (topics, classification)
  Loaded ADRs cleared: 10
  Command history cleared: Yes
  Note: Agent conversation history preserved

User> /topics predict ./new/adrs
[Starts fresh with new analysis...]
```

### Example 3: Mixed Usage

```
User> Load ADRs and analyze them
[AI uses tools to load and analyze...]

User> Clear everything and start over
AI: I'll reset your memory for a fresh start.
    ✓ Memory reset complete
      Analysis results cleared: 2
      Loaded ADRs cleared: 5
      Command history cleared: Yes

User> Now analyze this different project
[AI continues with fresh state...]
```

## Design Decisions

### Why Not Clear Conversation History?

The agent's conversation history is stored in the LangGraph checkpointer and is **not** cleared by `reset_memory`. This design choice allows:

1. **Continuity**: Users can maintain context and conversation flow while resetting data
2. **Flexibility**: Start fresh with new data but keep the conversation going
3. **Efficiency**: No need to rebuild conversation context after reset

If users want to completely reset everything (including conversation history), they can restart the CLI session.

### Dual Interface (Tool + Command)

Providing both tool and command interfaces:

1. **Tool**: Enables natural language interaction ("Reset my memory")
2. **Command**: Provides direct, explicit control (`/reset_memory`)
3. **Flexibility**: Users can choose their preferred interaction style
4. **Discovery**: Users might discover the tool through natural language, then use the command for efficiency

### Structured Tool Response

The tool returns a structured response that:

1. **Indicates success/failure**: `success` boolean
2. **Provides details**: Count of items cleared
3. **Follows convention**: Consistent with other tools in ADRminer
4. **Enables automation**: Programmatic access to reset results

## Error Handling

The reset_memory function handles edge cases:

### No Data to Clear

```json
{
  "success": true,
  "message": "Nothing to clear - session is already empty",
  "data": {
    "analysis_results_cleared": 0,
    "loaded_adrs_cleared": 0,
    "has_conversation_history": false
  }
}
```

### Session Not Initialized (Tool Only)

If the tool is called without session initialization:

```json
{
  "success": false,
  "message": "Session not initialized. Reset cannot be performed.",
  "data": None
}
```

The command handler (`/reset_memory`) doesn't have this issue as it directly accesses the SessionManager.

## Testing

Run the test suite to verify functionality:

```bash
python test_reset_memory.py
```

Tests cover:

1. Tool invocation and response format
2. Command handler execution
3. SessionManager.reset_memory() method
4. Edge cases (no data, no agent)

## Future Enhancements

Potential improvements for the reset_memory feature:

1. **Selective Reset**: Allow clearing specific types of data (e.g., only analysis results, keep loaded ADRs)
2. **Confirmation Prompt**: Add optional confirmation before clearing data
3. **Reset History**: Maintain a log of reset operations for auditing
4. **Batch Operations**: Support resetting multiple sessions in batch mode
5. **Undo Functionality**: Allow undoing the last reset operation (with limits)

## Related Features

- **Session Management**: `SessionManager` class handles all session state
- **Agent Context**: `AgentContext` class tracks agent-specific state
- **Command History**: Maintained by `SessionManager.command_history`
- **Analysis Results**: Stored in `SessionManager.analysis_results`

## Files Modified

1. `src/adrminer/agents/tools.py` - Added `reset_memory` tool
2. `src/adrminer/chat/session.py` - Added `reset_memory()` method
3. `src/adrminer/chat/handlers/util.py` - Added `ResetMemoryHandler`
4. `src/adrminer/chat/handlers/__init__.py` - Exported handler
5. `src/adrminer/chat/commands.py` - Registered `/reset_memory` command
6. `src/adrminer/chat/dispatcher.py` - Added command mapping
7. `src/adrminer/agents/langchain_agent.py` - Added tool to agent
8. `test_reset_memory.py` - Comprehensive test suite

## Support

For issues or questions about the reset_memory feature:

1. Check the test suite: `python test_reset_memory.py`
2. Review this documentation
3. Examine the implementation files listed above
4. Check the ADRminer documentation index