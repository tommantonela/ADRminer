# CLI Command Recommendation System - Implementation Summary

## Overview

Implemented a CLI command recommendation system that suggests equivalent CLI commands to users after they interact with the LangChain agent. This helps users discover CLI commands that provide similar functionality to the tools they just used.

## Architecture

### 1. Tool Metadata Decorator (`@tool_metadata`)

**Location:** `src/adrminer/agents/tools.py`

A decorator that attaches CLI command metadata to tool functions:

```python
@tool_metadata(
    related_commands=["/list", "/summary {path}"],
    description="For loading and listing ADR files"
)
@tool(parse_docstring=True)
def load_adrs(path: str) -> Dict[str, Any]:
    ...
```

**Properties:**
- `related_commands`: List of CLI commands that provide similar functionality
- `description`: Human-readable description of the command group

### 2. Recommendation Service

**Location:** `src/adrminer/chat/recommendation_service.py`

Service that reads tool metadata and generates CLI command recommendations:

**Key Methods:**
- `_build_metadata_cache()`: Scans tools and builds metadata cache (handles both raw functions and LangChain StructuredTool objects)
- `get_recommendations(tool_names)`: Returns recommendations for used tools
- `show_recommendations(tool_names)`: Displays formatted recommendations to user
- `get_all_tools_metadata()`: Returns all tool metadata (for debugging)

**Output Format:**
```
💡 Tip: You can also execute these commands directly:

For loading and listing ADR files:
  /list, /summary {path}

For topic mining and analysis:
  /topics predict {path}, /topics info, /summary {path}

Type any command to execute it, or use /help for more information.
```

The recommendations are displayed in a compact, integrated format without bounding boxes or background colors, blending seamlessly with the rest of the CLI interface.

### 3. Agent Integration

**Locations:** 
- `src/adrminer/agents/langchain_agent.py` (LangChainAdrminerAgent)
- `src/adrminer/agents/agent_factory.py` (AdrminerAgent wrapper)

Added method to extract tool calls from agent results in both classes:

```python
# In LangChainAdrminerAgent
def extract_tool_calls(self, result: Dict[str, Any]) -> List[str]:
    """Extract names of tools used in the agent result."""
    tool_names = []
    messages = result.get("data", {}).get("messages", [])
    
    for message in messages:
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.get('name', '')
                if tool_name:
                    tool_names.append(tool_name)
    
    return tool_names

# In AdrminerAgent wrapper (delegates to LangChain agent)
def extract_tool_calls(self, result: Dict[str, Any]) -> list:
    """Extract names of tools used in the agent result."""
    return self.langchain_agent.extract_tool_calls(result)
```

### 4. Dispatcher Integration

**Location:** `src/adrminer/chat/dispatcher.py`

Integrated recommendation service into command dispatcher:

```python
# In __init__:
self.recommendation_service = RecommendationService(session.console)

# In _route_to_agent() after successful agent processing:
tool_calls = agent.extract_tool_calls(result)
if tool_calls:
    self.recommendation_service.show_recommendations(tool_calls)
```

## Tools with Metadata

All 9 ADRminer tools now have metadata:

| Tool | Description | Related Commands |
|------|-------------|------------------|
| `load_adrs` | For loading and listing ADR files | `/list`, `/summary {path}` |
| `list_adr_files` | For discovering and listing ADR files | `/list`, `/summary {path}` |
| `mine_topics` | For topic mining and analysis | `/topics predict {path}`, `/topics info`, `/summary {path}` |
| `classify_adrs` | For ADR classification using various frameworks | `/classify predict {path} --framework {framework}`, `/classify info`, `/summary {path}` |
| `check_quality` | For ADR quality checking against templates | `/check predict {path}`, `/summary {path}` |
| `generate_insights` | For generating insights from analysis results | `/summary {path}`, `/summary {path} --output-detailed` |
| `get_topics_info` | For viewing topic model information | `/topics info`, `/topics predict {path}` |
| `get_classification_info` | For viewing classification framework information | `/classify info`, `/classify predict {path}` |
| `reset_memory` | For resetting agent memory and analysis results | `/reset_memory` |

## User Experience

When a user interacts with the agent:

1. User types natural language query (e.g., "Analyze my ADRs for topics")
2. Agent uses tools (e.g., `load_adrs`, `mine_topics`)
3. Agent displays results
4. **NEW:** System shows CLI command recommendations in a compact format
5. User can copy/paste commands for direct execution

Example:

```
User: Analyze my ADRs for topics

AI: I've analyzed your ADRs and found 5 topics...
[Topic analysis results]

💡 Tip: You can also execute these commands directly:

For loading and listing ADR files:
  /list, /summary {path}

For topic mining and analysis:
  /topics predict {path}, /topics info, /summary {path}

Type any command to execute it, or use /help for more information.

User: /topics predict adrs/
[Direct CLI execution]
```

## Benefits

1. **Discoverability**: Users discover CLI commands they might not know about
2. **Learning**: Natural language interaction teaches users about CLI capabilities
3. **Flexibility**: Users can switch between agent and CLI as needed
4. **Documentation**: CLI commands are documented in tool metadata
5. **No Duplication**: No need to implement the same functionality in both tools and commands

## Technical Details

### Decorator Implementation

The `@tool_metadata` decorator uses function attributes to store metadata:

```python
def tool_metadata(**metadata):
    def decorator(func):
        func._tool_metadata = metadata  # Function attribute
        return func
    return decorator
```

This metadata is accessible at runtime:

```python
metadata = load_adrs._tool_metadata
# => {'related_commands': [...], 'description': '...'}
```

### StructuredTool Compatibility

The recommendation service handles both raw Python functions and LangChain `StructuredTool` objects:

**Key insight:** When using decorator order:
```python
@tool_metadata(...)  # Applied first
@tool(...)          # Wraps function into StructuredTool
def load_adrs(...):
```

The `@tool_metadata` decorator receives the StructuredTool object and attaches metadata to it directly. This works because StructuredTool objects are Python objects that can have custom attributes.

**Implementation:**
- Detects `hasattr(tool, 'name')` to identify StructuredTool objects
- Checks for `_tool_metadata` directly on the tool object (not on `tool.func`)
- Uses `tool.name` for StructuredTool name, or `func.__name__` for raw functions

This approach is simpler than unwrapping StructuredTools to access underlying functions.

### Tool Call Extraction

LangChain agents store tool calls in message objects. The implementation navigates the result structure to extract tool names from AI messages with tool calls.

### De-duplication

The recommendation service de-duplicates commands across multiple tools:
- Uses a `Set` to track seen commands
- Only shows each unique command once
- Groups commands by description for better organization

## Files Modified

1. **src/adrminer/agents/tools.py**
   - Added `tool_metadata` decorator function
   - Applied decorator to all 9 tools (before `@tool` decorator)

2. **src/adrminer/agents/langchain_agent.py**
   - Added `extract_tool_calls()` method
   - Added `List` to imports

3. **src/adrminer/agents/agent_factory.py**
   - Added `extract_tool_calls()` method to `AdrminerAgent` wrapper class
   - Method delegates to underlying `LangChainAdrminerAgent`

4. **src/adrminer/chat/recommendation_service.py** (NEW)
   - Complete recommendation service implementation
   - Handles both raw functions and LangChain StructuredTool objects
   - Checks for `_tool_metadata` attribute directly on tool objects

5. **src/adrminer/chat/dispatcher.py**
   - Added `RecommendationService` import
   - Initialized service in `__init__()`
   - Added recommendation display after agent processing

6. **src/adrminer/prompts/agent_system_prompt.md**
   - Removed `export_metadata` tool reference
   - Added file management tools section

## Testing

Created test scripts in the `tests/` directory:

1. **tests/test_recommendation_system.py**: Full integration test (requires LangChain dependencies)
2. **tests/test_recommendation_simple.py**: Standalone metadata parser test

## Future Enhancements

Potential improvements:

1. **Parameter Mapping**: Add parameter mapping from tool args to CLI command options
2. **Command Help**: Add `/help <command>` integration
3. **Context-aware Recommendations**: Consider user's current state/context
4. **Favorite Commands**: Allow users to mark frequently-used commands
5. **Command History**: Track which CLI commands user actually executes after recommendations

## Conclusion

The CLI command recommendation system successfully bridges the gap between the conversational agent interface and the direct CLI interface. Users can now discover CLI commands naturally through agent interaction, making the system more user-friendly while maintaining the power and efficiency of direct CLI commands.

This implementation follows the decorator pattern (Option 1 from the design document), providing a clean, maintainable solution that doesn't require changes to tool implementations beyond adding metadata decorators.