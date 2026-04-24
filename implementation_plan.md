# Implementation Plan

Integrate Deep Agents into ADRminer's interactive CLI to enable natural language-based exploration of ADRs while maintaining existing command-based functionality.

This implementation will transform the interactive CLI from a pure command interface to a hybrid system supporting both direct commands (e.g., `/topics predict .`) and natural language queries (e.g., "Analyze all ADRs for topics"). The Deep Agent will intelligently route user requests to appropriate tools, maintain context across sessions, and request human approval for large or computationally expensive operations.

The implementation follows the architecture defined in `docs/DEEP_AGENTS_CLI_DESIGN.md` and integrates with the existing Phase 1 interactive CLI (`src/adrminer/chat/`). Key features include: natural language understanding, hybrid command interface, context awareness, human-in-the-loop approvals, persistent memory, and extensible skills support.

## Types

Core data structures and interfaces for the Deep Agents integration.

### Configuration Types

```python
# Agent Configuration
class AgentConfig(BaseModel):
    """Configuration for Deep Agent."""
    memory_enabled: bool = True  # Enable persistent memory across sessions
    hitl_enabled: bool = True  # Enable human-in-the-loop approvals
    skills_dir: Optional[Path] = None  # Path to skills directory
    default_session_prefix: str = "adrminer-"  # Prefix for session IDs
    
    # Middleware configuration
    middleware: MiddlewareConfig = Field(default_factory=MiddlewareConfig)

class MiddlewareConfig(BaseModel):
    """Middleware configuration for Deep Agent."""
    todo_list_enabled: bool = True  # Enable task planning
    filesystem_enabled: bool = True  # Enable filesystem access
    virtual_filesystem: bool = True  # Use virtual filesystem mode
    memory_backend: Literal["memory", "store"] = "store"  # Memory backend type
    
    # Human-in-the-loop configuration
    hitl_auto_approve_threshold: int = 5  # Auto-approve if <= this many ADRs
    hitl_require_commands: List[str] = [  # Commands requiring approval
        "classify_adrs",
        "check_quality"
    ]
```

### Tool Types

```python
# Tool Result Types
class ToolResult(BaseModel):
    """Standard result from tool execution."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    requires_approval: bool = False  # If True, agent should request approval

# Context Types
class AgentContext(BaseModel):
    """Context maintained by agent."""
    current_directory: Path
    loaded_adrs: List[Path]
    analysis_results: Dict[str, Any]  # topics, classification, check, insights
    command_history: List[str]
    session_id: str
```

### Command Types

```python
# Command Registry Entry
class CommandEntry(BaseModel):
    """Entry in command registry for agent awareness."""
    name: str  # e.g., "/topics predict"
    description: str
    handler: str  # Handler function name
    natural_language_patterns: List[str]  # Patterns agent can recognize
    batch_operation: bool  # Whether this is a batch operation
    computationally_expensive: bool  # Whether this requires approval
```

## Files

### New Files to Create

1. **`src/adrminer/agents/__init__.py`**
   - Package initialization
   - Exports main classes: `create_adrminer_agent`, `AdrminerAgent`

2. **`src/adrminer/agents/agent_factory.py`** (~200 lines)
   - `create_adrminer_agent()` factory function
   - Configure Deep Agent with middleware
   - Set up system prompt
   - Configure interrupt rules for HITL
   - Register all tools

3. **`src/adrminer/agents/tools.py`** (~350 lines)
   - LangChain tool wrappers for all services
   - Tools: `load_adrs`, `mine_topics`, `classify_adrs`, `check_quality`, `generate_insights`, `export_metadata`
   - Each tool returns standardized `ToolResult`
   - Tool descriptions include batch/expensive flags

4. **`src/adrminer/agents/context.py`** (~150 lines)
   - `AgentContext` class for state management
   - Synchronization with SessionManager
   - Context serialization for persistence

5. **`src/adrminer/agents/skills/`** (directory)
   - `__init__.py`
   - `madr_template/` - MADR template validation skill
   - `architectural_patterns/` - Pattern recognition skill
   - Example SKILL.md files

### Modified Files

1. **`src/adrminer/chat/session.py`** (+50 lines)
   - Add `agent` property (lazy-loaded)
   - Add `agent_context` for agent state
   - Add method `initialize_agent()` for agent setup
   - Integrate agent with session state

2. **`src/adrminer/chat/dispatcher.py`** (+80 lines)
   - Add `_is_natural_language()` method
   - Add `_route_to_agent()` method
   - Modify `dispatch()` to handle natural language
   - Add agent response formatting

3. **`src/adrminer/chat/__init__.py`** (+30 lines)
   - Update welcome banner to mention natural language
   - Add agent initialization feedback
   - Handle agent-specific errors

4. **`src/adrminer/config/settings.py`** (+40 lines)
   - Add `AgentConfig` class
   - Add `agent` field to `Settings`
   - Add validators for agent configuration
   - Support `.adrminer.yaml` agent section

5. **`requirements.txt`** (+2 lines)
   - Add `deepagents>=0.1.0`
   - Add `langgraph>=0.2.0`

6. **`docs/CLI_COMMAND_REFERENCE.md`** (+100 lines)
   - Document natural language examples
   - Explain agent capabilities
   - Add agent troubleshooting section

7. **`docs/INTERACTIVE_CLI_GUIDE.md`** (+150 lines)
   - Add "Natural Language Queries" section
   - Document agent context awareness
   - Explain human-in-the-loop behavior
   - Add agent troubleshooting tips

### Configuration Files

8. **`.adrminer.yaml`** (example update)
   ```yaml
   agent:
     memory_enabled: true
     hitl_enabled: true
     skills_dir: "./skills"
     default_session_prefix: "adrminer-"
     middleware:
       todo_list_enabled: true
       filesystem_enabled: true
       memory_backend: "store"
       hitl_auto_approve_threshold: 5
   ```

9. **`skills/madr_template/SKILL.md`** (new)
   - MADR template validation skill
   - Checks ADR adherence to template

10. **`skills/architectural_patterns/SKILL.md`** (new)
    - Architectural pattern recognition
    - Identifies patterns in ADRs

## Functions

### New Functions

#### `create_adrminer_agent()`
- **File**: `src/adrminer/agents/agent_factory.py`
- **Signature**: 
  ```python
  def create_adrminer_agent(
      session: SessionManager,
      config: Optional[AgentConfig] = None
  ) -> CompiledGraph
  ```
- **Purpose**: Factory function to create configured Deep Agent instance
- **Behavior**:
  - Load all tools from `tools.py`
  - Configure middleware (TodoList, Filesystem, HITL, Memory)
  - Set up system prompt with ADRminer context
  - Configure interrupt rules based on batch/expensive flags
  - Return compiled graph for execution

#### `load_adrs` (tool)
- **File**: `src/adrminer/agents/tools.py`
- **Signature**:
  ```python
  @tool
  def load_adrs(path: str) -> ToolResult:
      """Load ADR files from a directory."""
  ```
- **Purpose**: LangChain tool for loading ADR files
- **Behavior**:
  - Parse path (relative to agent context)
  - Load ADR files from directory
  - Return list of loaded files
  - Update agent context
  - Return standardized `ToolResult`

#### `mine_topics` (tool)
- **File**: `src/adrminer/agents/tools.py`
- **Signature**:
  ```python
  @tool
  def mine_topics(
      adr_paths: List[str],
      model: Optional[str] = None,
      threshold: float = 0.0
  ) -> ToolResult:
      """Extract topics from ADRs using BERTopic."""
  ```
- **Purpose**: LangChain tool for topic mining
- **Behavior**:
  - Use SessionManager's TopicService
  - Predict topics for ADRs
  - Return results with probabilities
  - Store in agent context
  - Mark as batch operation (may require approval)

#### `classify_adrs` (tool)
- **File**: `src/adrminer/agents/tools.py`
- **Signature**:
  ```python
  @tool
  def classify_adrs(
      adr_paths: List[str],
      framework: str = "kruchten",
      use_examples: bool = True
  ) -> ToolResult:
      """Classify ADRs using specified framework."""
  ```
- **Purpose**: LangChain tool for classification
- **Behavior**:
  - Use SessionManager's ClassificationService
  - Classify ADRs with specified framework
  - Return classifications with confidence
  - Store in agent context
  - Mark as batch operation requiring approval

#### `check_quality` (tool)
- **File**: `src/adrminer/agents/tools.py`
- **Signature**:
  ```python
  @tool
  def check_quality(
      adr_paths: List[str],
      mode: str = "full"
  ) -> ToolResult:
      """Check ADR quality against MADR template."""
  ```
- **Purpose**: LangChain tool for quality checking
- **Behavior**:
  - Use SessionManager's CheckingService
  - Check ADR quality and adherence
  - Return quality scores and issues
  - Store in agent context
  - Mark as batch operation requiring approval

#### `generate_insights` (tool)
- **File**: `src/adrminer/agents/tools.py`
- **Signature**:
  ```python
  @tool
  def generate_insights(
      include_topics: bool = True,
      include_classification: bool = True,
      include_check: bool = True
  ) -> ToolResult:
      """Generate actionable insights from analysis results."""
  ```
- **Purpose**: LangChain tool for insights generation
- **Behavior**:
  - Use SessionManager's InsightService
  - Generate insights from stored results
  - Return patterns, issues, recommendations
  - Format for user-friendly display

#### `export_metadata` (tool)
- **File**: `src/adrminer/agents/tools.py`
- **Signature**:
  ```python
  @tool
  def export_metadata(
      format: str = "sidecar"
  ) -> ToolResult:
      """Export analysis results to files."""
  ```
- **Purpose**: LangChain tool for exporting results
- **Behavior**:
  - Export stored analysis results
  - Support sidecar or consolidated format
  - Return exported file paths

#### `_is_natural_language()`
- **File**: `src/adrminer/chat/dispatcher.py`
- **Signature**:
  ```python
  def _is_natural_language(self, user_input: str) -> bool:
      """Determine if input is natural language or command."""
  ```
- **Purpose**: Distinguish between commands and natural language
- **Behavior**:
  - Check for `/` prefix (command)
  - Use simple heuristics for NL detection
  - Return True if no command pattern found

#### `_route_to_agent()`
- **File**: `src/adrminer/chat/dispatcher.py`
- **Signature**:
  ```python
  def _route_to_agent(self, user_input: str) -> Optional[bool]:
      """Route natural language input to Deep Agent."""
  ```
- **Purpose**: Route natural language to agent and handle response
- **Behavior**:
  - Get agent from session
  - Invoke agent with user input
  - Handle interrupts (HITL approvals)
  - Format and display agent response
  - Return False if quit, True otherwise

### Modified Functions

#### `CommandDispatcher.dispatch()`
- **File**: `src/adrminer/chat/dispatcher.py`
- **Current**: Only handles commands starting with `/`
- **Changes**:
  - Add check for natural language input
  - Route to agent if not a command
  - Handle agent responses and errors
  - Maintain backward compatibility with commands

#### `SessionManager.__init__()`
- **File**: `src/adrminer/chat/session.py`
- **Current**: Initializes services and session state
- **Changes**:
  - Add `self._agent = None` for lazy loading
  - Add `self.agent_context` for agent state
  - Add `self.agent_config` from settings

#### `SessionManager.agent` (property)
- **File**: `src/adrminer/chat/session.py`
- **New**: Lazy-loaded property for Deep Agent
- **Behavior**:
  - Create agent on first access
  - Configure with middleware and tools
  - Cache for session duration

#### `run_chat()`
- **File**: `src/adrminer/chat/__init__.py`
- **Current**: Runs command loop
- **Changes**:
  - Add agent initialization status
  - Display natural language capabilities in welcome
  - Handle agent-specific errors gracefully

## Classes

### New Classes

#### `AdrminerAgent`
- **File**: `src/adrminer/agents/agent_factory.py`
- **Purpose**: Wrapper around Deep Agent with ADRminer-specific functionality
- **Key Methods**:
  - `__init__(session, config)` - Initialize agent
  - `process_natural_language(input)` - Process NL query
  - `handle_interrupt(interrupt_data)` - Handle HITL interrupts
  - `get_context()` - Get current agent context
  - `update_context(updates)` - Update agent context
- **Inheritance**: None (wraps Deep Agent)

#### `AgentContext`
- **File**: `src/adrminer/agents/context.py`
- **Purpose**: Manages agent state and context
- **Key Methods**:
  - `load_from_session(session)` - Load state from SessionManager
  - `sync_to_session(session)` - Sync state to SessionManager
  - `to_dict()` - Serialize for persistence
  - `from_dict(data)` - Deserialize from persistence
- **Attributes**:
  - `current_directory` (Path)
  - `loaded_adrs` (List[Path])
  - `analysis_results` (Dict)
  - `session_id` (str)
  - `timestamp` (datetime)

### Modified Classes

#### `SessionManager`
- **File**: `src/adrminer/chat/session.py`
- **Current**: Manages services and session state
- **Modifications**:
  - Add `agent` property (lazy-loaded)
  - Add `agent_context: AgentContext`
  - Add `agent_config: AgentConfig`
  - Add `initialize_agent()` method
  - Modify service properties to work with agent tools

#### `CommandDispatcher`
- **File**: `src/adrminer/chat/dispatcher.py`
- **Current**: Dispatches commands to handlers
- **Modifications**:
  - Add `_is_natural_language()` method
  - Add `_route_to_agent()` method
  - Modify `dispatch()` to handle NL input
  - Add agent response formatting

#### `Settings`
- **File**: `src/adrminer/config/settings.py`
- **Current**: Application settings
- **Modifications**:
  - Add `agent: AgentConfig` field
  - Add validator for agent configuration
  - Support `.adrminer.yaml` agent section

## Dependencies

### New Packages

1. **`deepagents>=0.1.0`**
   - Core Deep Agents framework
   - Provides `create_deep_agent()` function
   - Includes middleware: TodoList, Filesystem, HITL, Memory
   - Required for agent orchestration

2. **`langgraph>=0.2.0`**
   - Stateful workflow engine
   - Provides StateGraph and checkpointer
   - Required for persistent memory
   - Enables session management

### Version Changes

No version changes for existing packages.

### Integration Requirements

- Deep Agents uses LangChain tools (already have `langchain-core`)
- LangGraph integrates with LangChain (compatible with existing setup)
- Both packages use OpenAI API (already configured)
- No conflicts with existing dependencies

## Testing

### Test Files to Create

1. **`tests/test_agents/test_agent_factory.py`**
   - Test agent creation
   - Test middleware configuration
   - Test tool registration
   - Test system prompt setup

2. **`tests/test_agents/test_tools.py`**
   - Test each tool independently
   - Mock SessionManager services
   - Verify ToolResult format
   - Test batch/expensive flags

3. **`tests/test_agents/test_context.py`**
   - Test context serialization
   - Test context synchronization
   - Test persistence operations

4. **`tests/test_chat/test_agent_integration.py`**
   - Test natural language routing
   - Test agent invocation
   - Test HITL interrupt handling
   - Test context updates

### Test Modifications

1. **`tests/test_chat/test_dispatcher.py`**
   - Add tests for natural language detection
   - Add tests for agent routing
   - Test error handling

2. **`tests/test_chat/test_session.py`**
   - Add tests for agent lazy loading
   - Test agent context management
   - Test session integration

### Test Scenarios

1. **Natural Language Queries**
   - Simple queries: "List all ADRs"
   - Complex queries: "Analyze ADRs for topics and classify them"
   - Ambiguous queries: "Check the files"

2. **Hybrid Interface**
   - Command after NL: "List ADRs" → `/topics predict .`
   - NL after command: `/list` → "Which ADRs are about security?"
   - Mixed input: "Use /topics to analyze, then classify"

3. **Context Awareness**
   - Agent remembers current directory
   - Agent remembers loaded ADRs
   - Agent remembers previous results
   - Cross-reference context in queries

4. **Human-in-the-Loop**
   - Approval for batch operations
   - Skip approval for small operations
   - Cancel operations
   - Approval history

5. **Error Handling**
   - Agent doesn't understand query
   - Tool execution fails
   - Service loading fails
   - Network errors (LLM)

## Implementation Order

### Phase 1: Foundation (Week 1)

1. Add dependencies to `requirements.txt`
2. Create `src/adrminer/agents/` package structure
3. Implement `AgentConfig` in `settings.py`
4. Implement `AgentContext` class
5. Implement tool wrappers in `tools.py`
6. Write tests for tools

### Phase 2: Agent Creation (Week 2)

7. Implement `create_adrminer_agent()` factory
8. Configure middleware
9. Set up system prompt
10. Configure interrupt rules
11. Write tests for agent factory

### Phase 3: Session Integration (Week 2-3)

12. Modify `SessionManager` to support agent
13. Implement agent lazy loading
14. Integrate agent context
15. Write tests for session integration

### Phase 4: Dispatcher Integration (Week 3)

16. Modify `CommandDispatcher` for NL detection
17. Implement `_route_to_agent()` method
18. Handle agent responses
19. Handle interrupts (HITL)
20. Write tests for dispatcher integration

### Phase 5: Documentation & Examples (Week 4)

21. Update CLI guide with NL examples
22. Update command reference
23. Create example skills
24. Write troubleshooting guide

### Phase 6: Polish & Testing (Week 4-5)

25. End-to-end testing
26. Performance optimization
27. Error message refinement
28. User acceptance testing