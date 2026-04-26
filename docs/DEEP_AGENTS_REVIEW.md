# Deep Agents Implementation Review

**Date:** 2026-04-24  
**Reviewer:** Deep Agents Core Skill  
**Status:** Implementation Complete - Requires Critical Fixes

---

## Executive Summary

The Deep Agents integration for ADRminer's interactive CLI provides a solid foundation for natural language-based ADR exploration. The architecture follows the overall design pattern with lazy loading, context management, and hybrid command/natural language interfaces.

However, **several critical issues** must be addressed to ensure the implementation works correctly with the Deep Agents framework:

1. **Critical**: Interrupt rules implementation is incorrect
2. **Critical**: Checkpointer handling is fragile
3. **High**: Memory backend implementation is incomplete
4. **High**: Agent invoke pattern is non-standard
5. **Medium**: Filesystem middleware lacks proper backend
6. **Medium**: Global session state in tools is anti-pattern
7. **Low**: Skills integration is missing

---

## Detailed Findings

### 1. Interrupt Rules Implementation ❌ CRITICAL

**File:** `src/adrminer/agents/agent_factory.py` (lines 186-233)

**Issue:**
The interrupt rules defined in `_create_interrupt_rules()` use lambda functions with incorrect parameters and format. The Deep Agents `HumanInTheLoopMiddleware` expects interrupt rules in a specific format, but the current implementation doesn't match.

**Current Code:**
```python
rules.append({
    "tool_name": "classify_adrs",
    "condition": lambda num_affected: num_affected > agent_config.middleware.hitl_auto_approve_threshold,
    "message": "This will classify {num} ADRs using {framework}. Continue?",
    "requires_approval": True
})
```

**Problems:**
- Lambda receives `num_affected` but this parameter isn't passed by Deep Agents
- Interrupt rule format doesn't match Deep Agents expectations
- Condition function signature is incorrect
- Message formatting with `{framework}` won't work as intended

**Recommended Fix:**
According to Deep Agents best practices, interrupt rules should be defined differently. The `interrupt_on` parameter in `create_deep_agent()` should be used:

```python
agent = create_deep_agent(
    model=settings.llm.model,
    tools=tools,
    system_prompt=customized_prompt,
    middleware=middleware,
    interrupt_on={
        "classify_adrs": True,  # Always require approval
        "check_quality": True,
        "mine_topics": True
    },
    checkpointer=checkpointer
)
```

Or use `HumanInTheLoopMiddleware` with proper interrupt rules based on the actual Deep Agents API.

---

### 2. Checkpointer Handling ❌ CRITICAL

**File:** `src/adrminer/agents/agent_factory.py` (lines 172-178)

**Issue:**
The checkpointer is extracted from `middleware[-1].checkpointer`, which assumes MemoryMiddleware is always the last middleware. This is fragile and will break if middleware order changes.

**Current Code:**
```python
agent = create_deep_agent(
    model=settings.llm.model,
    tools=tools,
    system_prompt=customized_prompt,
    middleware=middleware,
    checkpointer=middleware[-1].checkpointer if agent_config.memory_enabled else None
)
```

**Problems:**
- Assumes MemoryMiddleware is always last in the list
- Will break if middleware order changes or if MemoryMiddleware is not present
- Dependencies between middleware creation and checkpointer extraction

**Recommended Fix:**
Create checkpointer separately and pass it explicitly:

```python
# Create checkpointer once
checkpointer = MemorySaver() if agent_config.memory_enabled else None

# Create middleware
middleware = []

# ... create middleware without creating checkpointer inside MemoryMiddleware ...

# Pass checkpointer to both MemoryMiddleware and create_deep_agent
if agent_config.memory_enabled:
    memory_middleware = MemoryMiddleware(
        backend=memory_backend,
        checkpointer=checkpointer
    )
    middleware.append(memory_middleware)

agent = create_deep_agent(
    model=settings.llm.model,
    tools=tools,
    system_prompt=customized_prompt,
    middleware=middleware,
    checkpointer=checkpointer
)
```

---

### 3. Memory Backend Implementation ❌ HIGH

**File:** `src/adrminer/agents/agent_factory.py` (lines 134-149)

**Issue:**
The memory backend configuration has both branches creating `InMemoryStore()`, which doesn't differentiate between ephemeral and persistent memory backends.

**Current Code:**
```python
if agent_config.middleware.memory_backend == "store":
    # Use persistent store backend
    memory_backend = InMemoryStore()
else:
    # Use ephemeral memory backend
    memory_backend = InMemoryStore()
```

**Problems:**
- Both branches create the same `InMemoryStore()`
- No actual difference between "store" and "memory" backends
- StoreBackend pattern is not used for persistent memory

**Recommended Fix:**
According to Deep Agents best practices, use proper backend patterns:

```python
from deepagents.backends import StoreBackend

if agent_config.middleware.memory_backend == "store":
    # Use persistent Store backend
    memory_backend = lambda rt: StoreBackend(rt)
    store = InMemoryStore()
else:
    # Use ephemeral memory (no backend)
    memory_backend = None
    store = None

# ... pass store to create_deep_agent if using StoreBackend
```

---

### 4. Agent Invoke Pattern ❌ HIGH

**File:** `src/adrminer/agents/agent_factory.py` (lines 288-295)

**Issue:**
The agent is invoked using `Command(resume=user_input)` which is not the standard way to invoke a Deep Agent. This pattern is typically used for resuming after interrupts, not for initial queries.

**Current Code:**
```python
from langgraph.types import Command
result = self.agent.invoke(
    Command(resume=user_input),
    config={
        "configurable": {
            "thread_id": self.thread_id
        }
    }
)
```

**Problems:**
- `Command(resume=...)` is for resuming after interrupts, not standard invocation
- Standard Deep Agent invoke uses message format
- May cause issues with conversation flow

**Recommended Fix:**
Use standard message format:

```python
result = self.agent.invoke(
    {
        "messages": [
            {"role": "user", "content": user_input}
        ]
    },
    config={
        "configurable": {
            "thread_id": self.thread_id
        }
    }
)
```

---

### 5. Filesystem Middleware Backend ⚠️ MEDIUM

**File:** `src/adrminer/agents/agent_factory.py` (lines 127-130)

**Issue:**
FilesystemMiddleware is created without specifying a backend, which may not work as expected.

**Current Code:**
```python
fs_middleware = FilesystemMiddleware(
    virtual_mode=agent_config.middleware.virtual_filesystem
)
```

**Problems:**
- No backend specified for filesystem operations
- Virtual filesystem mode may not be configured correctly
- Should use CompositeBackend or specify backend explicitly

**Recommended Fix:**
```python
from deepagents.backends import FilesystemBackend, CompositeBackend

# Create backend
fs_backend = FilesystemBackend(
    root_dir=str(Path.cwd()),
    virtual_mode=agent_config.middleware.virtual_filesystem
)

fs_middleware = FilesystemMiddleware(backend=fs_backend)
```

---

### 6. Global Session State in Tools ⚠️ MEDIUM

**File:** `src/adrminer/agents/tools.py` (lines 49-70)

**Issue:**
Tools use a global `_session` variable set by `set_session()`, which is an anti-pattern and makes testing difficult.

**Current Code:**
```python
_session = None

def set_session(session):
    global _session
    _session = session

@tool
def load_adrs(path: str) -> Dict[str, Any]:
    session = get_session()
    if session is None:
        return ToolResult(...)
```

**Problems:**
- Global state makes testing difficult
- Not thread-safe
- Breaks functional programming principles
- Limits ability to have multiple agents with different sessions

**Recommended Fix:**
Pass session through tool invocation context or use a session manager pattern. However, since LangChain tools don't support custom context injection, one approach is:

1. Create a tool factory that returns tools with session bound
2. Or use a session-aware tool wrapper
3. Or store session in a thread-local variable for thread safety

Example approach:
```python
from threading import local

_session_local = local()

def set_session(session):
    _session_local.value = session

def get_session():
    return getattr(_session_local, 'value', None)
```

---

### 7. Missing Skills Integration ℹ️ LOW

**File:** `src/adrminer/agents/agent_factory.py`

**Issue:**
The `skills_dir` configuration is defined in settings but never used in the `create_deep_agent()` call.

**Current Code:**
```python
agent = create_deep_agent(
    model=settings.llm.model,
    tools=tools,
    system_prompt=customized_prompt,
    middleware=middleware,
    checkpointer=middleware[-1].checkpointer if agent_config.memory_enabled else None
)
```

**Recommended Fix:**
Add skills parameter if skills directory is configured:

```python
skills = None
if agent_config.skills_dir:
    skills = [agent_config.skills_dir]

agent = create_deep_agent(
    model=settings.llm.model,
    tools=tools,
    system_prompt=customized_prompt,
    middleware=middleware,
    skills=skills,
    checkpointer=checkpointer
)
```

---

### 8. Thread ID Management ℹ️ LOW

**File:** `src/adrminer/agents/agent_factory.py` (lines 262-267, 291-294)

**Issue:**
Thread ID is generated but there's no mechanism to use it for persistent conversation history across sessions.

**Current Code:**
```python
def _generate_thread_id(self) -> str:
    import uuid
    settings = get_settings()
    prefix = settings.agent.default_session_prefix
    return f"{prefix}{uuid.uuid4().hex[:8]}"
```

**Observation:**
- Thread ID is used correctly in invoke calls
- However, without proper Store backend and persistent storage, conversation history won't persist across CLI sessions
- This is acceptable for single-session use but limits long-term memory

**Note:**
If persistent memory across CLI sessions is desired, the thread ID should be stored and reused, or a user-specific thread ID should be generated based on user identity.

---

## Positive Aspects ✅

The implementation has several strengths:

1. **Lazy Loading Pattern** ✅
   - Services and agent are loaded only when needed
   - Reduces startup time and resource usage
   - Implemented correctly in SessionManager

2. **Context Management** ✅
   - AgentContext provides clean synchronization between agent and session
   - `load_from_session()` and `sync_to_session()` methods are well-designed
   - Maintains state consistency across the application

3. **Tool Design** ✅
   - Tools are well-documented with clear descriptions
   - Use Pydantic for structured results
   - Return consistent ToolResult format
   - Include metadata (batch_operation, num_affected, requires_approval)

4. **System Prompt** ✅
   - Clear, comprehensive instructions for the agent
   - Includes context information (current_directory, loaded_adr_count, etc.)
   - Provides examples of natural language queries

5. **Error Handling** ✅
   - Graceful degradation when Deep Agents is not installed
   - Clear error messages to users
   - Try-except blocks prevent crashes

6. **Hybrid Interface** ✅
   - Seamless integration of command-based and natural language interfaces
   - Simple detection logic (`_is_natural_language()`)
   - Dispatcher correctly routes to appropriate handler

7. **Configuration** ✅
   - Comprehensive AgentConfig and MiddlewareConfig
   - Environment variable support through Pydantic Settings
   - Sensible defaults provided

---

## Recommended Action Plan

### Phase 1: Critical Fixes (Required for Basic Functionality)

1. **Fix interrupt rules implementation**
   - Replace custom interrupt rules with Deep Agents `interrupt_on` parameter
   - Or implement correct `HumanInTheLoopMiddleware` usage
   - Test HITL workflow end-to-end

2. **Fix checkpointer handling**
   - Create checkpointer separately from middleware list
   - Pass explicitly to `create_deep_agent()`
   - Ensure proper initialization order

3. **Fix agent invoke pattern**
   - Replace `Command(resume=...)` with standard message format
   - Test conversation flow
   - Verify context persistence across multiple queries

### Phase 2: High Priority Improvements

4. **Implement proper memory backend**
   - Use `StoreBackend` pattern for persistent memory
   - Differentiate between ephemeral and persistent backends
   - Pass Store instance to `create_deep_agent()`

5. **Configure filesystem backend**
   - Create proper `FilesystemBackend` instance
   - Use `CompositeBackend` if combining multiple backends
   - Test filesystem operations

6. **Refactor tool session management**
   - Replace global session with thread-local storage
   - Improve testability
   - Consider tool factory pattern

### Phase 3: Low Priority Enhancements

7. **Add skills integration**
   - Pass skills directory to `create_deep_agent()`
   - Create example skills if needed
   - Document skills usage

8. **Improve thread ID management**
   - Consider user-specific thread IDs for persistence
   - Add configuration for thread ID generation strategy
   - Document thread ID lifecycle

---

## Testing Recommendations

### Unit Tests

1. Test middleware initialization with different configurations
2. Test tool invocation with various inputs
3. Test context synchronization between agent and session
4. Test error handling paths

### Integration Tests

1. End-to-end natural language queries
2. Multi-turn conversations
3. Interrupt/approval workflows
4. Context persistence across queries
5. Hybrid command/natural language routing

### Manual Testing

1. Test CLI with Deep Agents installed and not installed
2. Test natural language queries for each tool
3. Test approval workflows for batch operations
4. Test context awareness (e.g., "What topics did we find?")
5. Test error recovery and graceful degradation

---

## Conclusion

The Deep Agents integration provides a strong foundation but requires critical fixes to work correctly with the Deep Agents framework. The architecture and design patterns are sound, but the implementation details around middleware configuration, interrupt rules, and agent invocation need to align with Deep Agents best practices.

**Overall Assessment:**
- **Architecture:** ⭐⭐⭐⭐☆ (4/5) - Well-designed with good separation of concerns
- **Implementation:** ⭐⭐☆☆☆ (2/5) - Several critical issues that prevent proper functionality
- **Code Quality:** ⭐⭐⭐☆☆ (3/5) - Good structure but some anti-patterns
- **Documentation:** ⭐⭐⭐⭐☆ (4/5) - Well-documented with clear intent

**Priority:** High - Address critical fixes before production use

---

## Appendix: Deep Agents Best Practices Reference

### Correct Middleware Configuration
```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, StoreBackend
from deepagents.middleware import TodoListMiddleware, FilesystemMiddleware, MemoryMiddleware
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

# Create checkpointer and store
checkpointer = MemorySaver()
store = InMemoryStore()

# Configure backends
fs_backend = FilesystemBackend(root_dir=".", virtual_mode=True)
memory_backend = lambda rt: StoreBackend(rt)

# Create middleware
middleware = [
    TodoListMiddleware(),
    FilesystemMiddleware(backend=fs_backend),
    MemoryMiddleware(backend=memory_backend, checkpointer=checkpointer)
]

# Create agent
agent = create_deep_agent(
    model="gpt-4o-mini",
    tools=[tool1, tool2],
    system_prompt="You are a helpful assistant",
    middleware=middleware,
    interrupt_on={"tool_name": True},  # For HITL
    checkpointer=checkpointer,
    store=store
)
```

### Correct Agent Invocation
```python
# Standard invocation
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Hello"}]},
    config={"configurable": {"thread_id": "session-123"}}
)

# Streaming
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Hello"}]},
    config={"configurable": {"thread_id": "session-123"}}
):
    print(chunk)

# Resume after interrupt (if using Command)
result = agent.invoke(
    Command(resume=True),
    config={"configurable": {"thread_id": "session-123"}}
)
```

### Thread ID Best Practices
- Use consistent thread_id for conversation continuity
- Use user-specific thread IDs for persistent history
- Use session-specific thread IDs for ephemeral sessions
- Document thread ID lifecycle and persistence strategy