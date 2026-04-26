# Command Recommendation Feature Design

## Executive Summary

This document outlines the design for a command recommendation feature that bridges the gap between agent tools and CLI commands in ADRminer. When the agent executes one or more tools, it will suggest relevant CLI commands that the user can run to achieve similar or related functionality.

### Goal

Improve user experience by:
- **Discoverability**: Help users learn about available CLI commands
- **Workflow guidance**: Suggest logical next steps after tool execution
- **Bridging interfaces**: Connect the conversational agent experience to the powerful CLI
- **Context-awareness**: Provide suggestions based on what tools were just executed

### Example User Experience

```
User: Please classify the ADRs in adrs/

Agent: I've classified 25 ADRs using the Kruchten framework. 
       The average confidence is 0.85 with 22 high-confidence classifications (88%).
       
[dim]→ Related commands you might want to run:[/dim]
  /classify info  # See more details about classification frameworks
  /topics predict adrs/  # Mine topics from these classified ADRs  
  /check predict adrs/  # Check quality of classified ADRs
  /summary adrs/  # Generate insights from analysis results
```

---

## Tools vs Commands Analysis

### Comparison Table

| Tool Name | Direct Command Mapping | Similarities | Differences | Gaps/Notes |
|------------|----------------------|--------------|-------------|------------|
| **load_adrs** | `/list` | Both discover ADR files | Tool loads into session memory; Command just lists | Tool stores in `session.loaded_adrs`; Command only displays |
| **get_topics_info** | `/topics info` | Both show topic information | Tool returns structured data; Command displays formatted | Exact functional match |
| **get_classification_info** | `/classify info` | Both show framework info | Tool returns structured data; Command displays formatted | Exact functional match |
| **list_adr_files** | `/list` | Both list ADR files | Tool returns paths; Command displays with metadata | Redundant with `/list` |
| **mine_topics** | `/topics predict` | Both predict topics on ADRs | Tool uses loaded ADRs; Command takes path param | Tool requires `load_adrs` first; Command handles loading internally |
| **classify_adrs** | `/classify predict` | Both classify ADRs | Tool uses loaded ADRs; Command takes path param | Tool requires `load_adrs` first; Command handles loading internally |
| **check_quality** | `/check predict` | Both check quality | Tool uses loaded ADRs; Command takes path param | Tool requires `load_adrs` first; Command handles loading internally |
| **generate_insights** | `/summary` | Both generate insights | Tool uses stored results; Command generates from scratch | Tool depends on previous analyses; Command is standalone |
| **reset_memory** | `/reset_memory` | Both clear session state | Exact match | Exact functional match |

### Commands Without Tool Equivalents

| Command | Purpose | Why No Tool? |
|---------|---------|--------------|
| `/help` | Show command help | UI/UX command, not analysis |
| `/quit` | Exit session | UI/UX command, not analysis |
| `/util llm` | Test LLM configuration | Utility/debug command |
| `/util inspect` | View ADR with formatting | Utility/display command |
| `/util list` | Enhanced list with filtering | Utility/display command |

### Tools Without Command Equivalents

| Tool | Purpose | Why No Command? |
|------|---------|----------------|
| `load_adrs` | Load ADRs into session | Session management, implicit in commands |
| `list_adr_files` | List ADR files | Redundant with `/list` |

---

## Architectural Differences

### 1. Parameter Passing

**Tools (Session-Based):**
```python
classify_adrs(path=None, framework="kruchten", use_examples=True)
# - Optional: uses session.loaded_adrs if path not provided
```

**Commands (Standalone):**
```bash
/classify predict <path> --framework kruchten
# - Required: always needs path parameter
```

### 2. Data Flow

**Tools (Session-Based):**
```
User: "Classify these ADRs"
  → Tool checks session.loaded_adrs
  → If empty, asks user to load_adrs first
  → Uses loaded ADRs
  → Stores results in session.analysis_results
```

**Commands (Standalone):**
```
User: "/classify predict adrs/"
  → Handler loads ADRs from path
  → Processes immediately
  → Displays results
  → Stores in session.analysis_results
```

### 3. Result Handling

**Tools:**
- Return structured `ToolResult` objects
- Success/failure flags
- Data in `result['data']`
- Agent interprets and summarizes

**Commands:**
- Display formatted output to console
- Use Rich tables/panels
- Progress bars for batch operations
- Export to files (JSON, CSV, sidecar)

---

## Gaps and Opportunities

### 1. Missing Tool for `/summary`

The `generate_insights` tool exists but differs:
- **Tool**: Uses stored analysis results from session
- **Command**: Generates summaries from ADRs directly

**Recommendation**: Create a new tool or enhance `generate_insights` to match command functionality.

### 2. Tool Redundancy

- `load_adrs` + `list_adr_files` both overlap with `/list`
- Consider consolidating or making one clearly distinct

### 3. Tool-Command Flow Mismatch

Tools require explicit `load_adrs` call, while commands handle loading internally. This creates friction when transitioning between agent and CLI.

**Recommendation**: Either:
- Make tools auto-load if path provided (like commands)
- Create tool wrappers that handle loading

### 4. Missing Utility Tools

Commands have utility subcommands (`llm`, `inspect`, `list`) with no tool equivalents. These could be valuable for agents to:
- Test LLM connectivity
- Inspect individual ADRs
- List with filters

---

## Recommendation Service Design

### Architecture

The recommendation service will be implemented as a standalone service that can be integrated with the agent through middleware or direct call.

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Execution                        │
│  User: "Classify ADRs in adrs/"                          │
│  Agent: Executes classify_adrs tool                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           CommandRecommendationService                       │
│  1. Receives: tool_name, tool_result                     │
│  2. Looks up: direct mappings                            │
│  3. Generates: context-aware suggestions                  │
│  4. Returns: formatted recommendations                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Response                          │
│  "I've classified 25 ADRs..."                           │
│                                                          │
│  [dim]Related commands:[/dim]                            │
│    /classify info                                         │
│    /topics predict adrs/                                  │
│    /check predict adrs/                                   │
└─────────────────────────────────────────────────────────────┘
```

### Service Interface

```python
# src/adrminer/chat/command_recommendations.py

from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Recommendation:
    """A single command recommendation."""
    command: str
    description: str
    priority: int = 0  # Higher = more important
    context: str = ""  # Optional context explanation

class CommandRecommendationService:
    """Maps agent tools to CLI commands and provides recommendations."""
    
    def get_recommendations(
        self,
        tools_used: List[str],
        results: List[Dict[str, Any]]
    ) -> List[Recommendation]:
        """Get CLI command recommendations based on tools executed.
        
        Args:
            tools_used: List of tool function names executed
            results: List of tool results from execution
            
        Returns:
            List of recommendations sorted by priority
        """
        pass
    
    def get_direct_mapping(self, tool_name: str) -> str:
        """Get direct command mapping for a tool."""
        pass
    
    def get_context_suggestions(
        self,
        tool_name: str,
        result: Dict[str, Any]
    ) -> List[Recommendation]:
        """Get context-aware suggestions based on tool execution."""
        pass
```

---

## Tool-to-Command Mappings

### Direct Mappings

```python
DIRECT_MAPPINGS = {
    # Exact functional matches
    "get_topics_info": "/topics info",
    "get_classification_info": "/classify info",
    "reset_memory": "/reset_memory",
    
    # Functional equivalents (with path conversion)
    "mine_topics": "/topics predict {path}",
    "classify_adrs": "/classify predict {path}",
    "check_quality": "/check predict {path}",
    
    # Related but different semantics
    "generate_insights": "/summary {path}",  # Note: different semantics
    "load_adrs": "/list {path}",  # Similar: file discovery
    "list_adr_files": "/list {path}",  # Similar: file discovery
}
```

### Context-Aware Suggestions

```python
CONTEXT_SUGGESTIONS = {
    "classify_adrs": [
        {
            "command": "/classify info",
            "description": "See more details about classification frameworks",
            "priority": 1,
            "context": "Explore other classification frameworks"
        },
        {
            "command": "/topics predict {path}",
            "description": "Mine topics from these classified ADRs",
            "priority": 2,
            "context": "Complementary analysis"
        },
        {
            "command": "/check predict {path}",
            "description": "Check quality of classified ADRs",
            "priority": 2,
            "context": "Quality validation"
        },
        {
            "command": "/summary {path}",
            "description": "Generate insights from classification results",
            "priority": 3,
            "context": "Post-analysis insights"
        },
    ],
    
    "mine_topics": [
        {
            "command": "/topics info",
            "description": "See details about topics found",
            "priority": 1,
            "context": "Explore topic details"
        },
        {
            "command": "/classify predict {path}",
            "description": "Classify by topic",
            "priority": 2,
            "context": "Combine with classification"
        },
        {
            "command": "/summary {path}",
            "description": "Generate insights from topics",
            "priority": 3,
            "context": "Post-analysis insights"
        },
    ],
    
    "check_quality": [
        {
            "command": "/util inspect {file}",
            "description": "Review low-quality ADRs in detail",
            "priority": 1,
            "context": "Quality improvement workflow"
        },
        {
            "command": "/classify predict {path}",
            "description": "Classify checked ADRs",
            "priority": 2,
            "context": "Complementary analysis"
        },
    ],
    
    "generate_insights": [
        {
            "command": "/topics predict {path}",
            "description": "Mine topics for deeper analysis",
            "priority": 2,
            "context": "Expand analysis"
        },
        {
            "command": "/classify predict {path}",
            "description": "Classify to get more insights",
            "priority": 2,
            "context": "Expand analysis"
        },
    ],
}
```

### Multi-Tool Combinations

```python
MULTI_TOOL_SUGGESTIONS = {
    frozenset(["classify_adrs", "mine_topics"]): [
        {
            "command": "/summary {path}",
            "description": "Generate comprehensive insights from classification and topics",
            "priority": 1,
            "context": "Combine analyses"
        },
    ],
    
    frozenset(["classify_adrs", "check_quality"]): [
        {
            "command": "/summary {path}",
            "description": "Generate insights considering classification and quality",
            "priority": 1,
            "context": "Combine analyses"
        },
    ],
    
    frozenset(["classify_adrs", "mine_topics", "check_quality"]): [
        {
            "command": "/summary {path}",
            "description": "Generate comprehensive insights from all analyses",
            "priority": 1,
            "context": "Full analysis summary"
        },
    ],
}
```

---

## Integration Strategy

### Option 1: Agent Middleware (Recommended)

Add a post-processing middleware that injects recommendations into agent responses.

```python
# src/adrminer/agents/command_recommendation_middleware.py

class CommandRecommendationMiddleware:
    """Middleware that adds command recommendations to agent responses."""
    
    def __init__(self, recommendation_service: CommandRecommendationService):
        self.recommendation_service = recommendation_service
        self.last_tools_used = []
        self.last_results = []
    
    def on_tool_start(self, tool_name: str, tool_args: Dict):
        """Track when a tool is called."""
        self.last_tools_used.append(tool_name)
    
    def on_tool_end(self, tool_name: str, result: Dict):
        """Track tool results."""
        self.last_results.append(result)
    
    def process_response(self, response: str) -> str:
        """Add recommendations to agent response."""
        if not self.last_tools_used:
            return response
        
        recommendations = self.recommendation_service.get_recommendations(
            self.last_tools_used,
            self.last_results
        )
        
        if recommendations:
            response += "\n\n" + self._format_recommendations(recommendations)
        
        # Clear for next round
        self.last_tools_used = []
        self.last_results = []
        
        return response
    
    def _format_recommendations(self, recommendations: List[Recommendation]) -> str:
        """Format recommendations for display."""
        lines = ["[dim]→ Related commands you might want to run:[/dim]"]
        for rec in recommendations[:5]:  # Limit to top 5
            line = f"  {rec.command}"
            if rec.description:
                line += f"  # {rec.description}"
            lines.append(line)
        return "\n".join(lines)
```

**Integration with LangChain Agent:**

```python
# In agent initialization
recommendation_service = CommandRecommendationService()
recommendation_middleware = CommandRecommendationMiddleware(recommendation_service)

agent = create_react_agent(
    model=llm,
    tools=tools,
    callbacks=[recommendation_middleware]
)
```

**Integration with Deep Agent:**

```python
# In deep_agent.py
class DeepAgent:
    def __init__(self, ...):
        self.recommendation_service = CommandRecommendationService()
    
    def invoke(self, messages):
        # ... existing agent invocation ...
        
        # Add recommendations
        if self.last_tools_used:
            recommendations = self.recommendation_service.get_recommendations(
                self.last_tools_used,
                self.last_results
            )
            response += self._format_recommendations(recommendations)
        
        return response
```

### Option 2: Direct Agent Integration

Modify agent response generation to include recommendations.

```python
# In agent's response method
def _generate_response(self, intermediate_steps):
    """Generate response with recommendations."""
    # Get tools used
    tools_used = [step[0].name for step in intermediate_steps]
    results = [step[1] for step in intermediate_steps]
    
    # Generate standard response
    response = self.llm.invoke(...)
    
    # Add recommendations
    recommendations = self.recommendation_service.get_recommendations(
        tools_used,
        results
    )
    
    if recommendations:
        response += "\n\n" + self._format_recommendations(recommendations)
    
    return response
```

### Option 3: Post-Processing Wrapper

Wrap agent invocation to add recommendations.

```python
def invoke_agent_with_recommendations(agent, query):
    """Invoke agent and add recommendations to response."""
    
    # Track tools used during execution
    tools_used = []
    results = []
    
    # Callback to track tool execution
    def on_tool_call(tool, result):
        tools_used.append(tool.name)
        results.append(result)
    
    # Invoke agent with callback
    response = agent.invoke(query, callbacks=[on_tool_call])
    
    # Add recommendations
    recommendations = recommendation_service.get_recommendations(
        tools_used,
        results
    )
    
    if recommendations:
        response += "\n\n" + self._format_recommendations(recommendations)
    
    return response
```

---

## User Experience Examples

### Example 1: Single Tool Execution

```
User: Classify the ADRs in the adrs/ directory

Agent: I've classified 25 ADRs using the Kruchten framework.
       Results:
       - Total ADRs: 25
       - Average confidence: 0.85
       - High confidence (>0.8): 22 (88%)
       Most common categories:
       • Integration (8 ADRs)
       • Data (6 ADRs)
       • Interface (5 ADRs)
       
[dim]→ Related commands you might want to run:[/dim]
  /classify info  # See more details about classification frameworks
  /topics predict adrs/  # Mine topics from these classified ADRs
  /check predict adrs/  # Check quality of classified ADRs
  /summary adrs/  # Generate insights from analysis results
```

### Example 2: Multiple Tools Execution

```
User: Analyze the ADRs in adrs/ for topics and classification

Agent: I've completed the analysis of 25 ADRs:
       
       Topic Mining:
       - Found 8 topics
       - Average probability: 0.72
       Top topics:
       • API Design (7 ADRs)
       • Database Schema (5 ADRs)
       
       Classification:
       - Framework: Kruchten
       - Average confidence: 0.85
       Most common:
       • Integration (8 ADRs)
       
[dim]→ Related commands you might want to run:[/dim]
  /summary adrs/  # Generate comprehensive insights from all analyses
  /classify info  # Explore other classification frameworks
  /check predict adrs/  # Validate quality of analyzed ADRs
```

### Example 3: Quality Check Follow-up

```
User: Check the quality of ADRs in adrs/

Agent: I've checked 25 ADRs for quality:
       - Average score: 0.82
       - Low quality ADRs (<0.5): 3
       - Issues found:
       • Missing context section: 5 ADRs
       • Missing decision section: 2 ADRs
       
[dim]→ Related commands you might want to run:[/dim]
  /util inspect adrs/0005-missing-context.md  # Review low-quality ADR in detail
  /util list adrs/ --details  # List ADRs with quality metadata
  /classify predict adrs/  # Classify checked ADRs
```

---

## Implementation Plan

### Phase 1: Core Service (Priority: High)

1. **Create CommandRecommendationService**
   - File: `src/adrminer/chat/command_recommendations.py`
   - Implement `get_recommendations()` method
   - Define direct mappings
   - Define context-aware suggestions

2. **Define Mappings**
   - Create `DIRECT_MAPPINGS` dictionary
   - Create `CONTEXT_SUGGESTIONS` dictionary
   - Create `MULTI_TOOL_SUGGESTIONS` dictionary

3. **Unit Tests**
   - File: `tests/test_chat/test_command_recommendations.py`
   - Test direct mappings
   - Test context suggestions
   - Test multi-tool combinations
   - Test priority sorting

### Phase 2: Agent Integration (Priority: High)

4. **Choose Integration Approach**
   - Implement Option 1 (Middleware) - Recommended
   - Or implement Option 2 (Direct Integration)
   - Or implement Option 3 (Post-Processing Wrapper)

5. **Integrate with Agent**
   - Modify `src/adrminer/agents/langchain_agent.py`
   - Modify `src/adrminer/agents/deep_agent.py`
   - Add recommendation service initialization
   - Add recommendation formatting

6. **Integration Tests**
   - Test agent with single tool execution
   - Test agent with multiple tools
   - Test agent with no tools (no recommendations)
   - Test recommendation formatting

### Phase 3: User Experience (Priority: Medium)

7. **Format Recommendations**
   - Implement Rich formatting
   - Add icons/emojis for visual appeal
   - Truncate long descriptions
   - Limit to top N recommendations

8. **Configuration**
   - Add setting to enable/disable recommendations
   - Add setting to control max recommendations
   - Add setting to customize format

9. **Documentation**
   - Update user guide
   - Add examples to documentation
   - Create troubleshooting guide

### Phase 4: Enhancement (Priority: Low)

10. **Path Resolution**
    - Automatically infer path from session
    - Handle path placeholders in mappings
    - Support multiple path sources

11. **Learning from Usage**
    - Track which recommendations are followed
    - Improve priority based on usage
    - Add personalized suggestions

12. **Advanced Context**
    - Analyze tool results for smart suggestions
    - Suggest based on result quality
    - Suggest based on result patterns

---

## Configuration

### Settings

```python
# src/adrminer/config/settings.py

class RecommendationSettings(BaseSettings):
    """Settings for command recommendation feature."""
    
    enabled: bool = True
    """Enable/disable command recommendations."""
    
    max_recommendations: int = 5
    """Maximum number of recommendations to show."""
    
    show_descriptions: bool = True
    """Show descriptions in recommendations."""
    
    show_context: bool = False
    """Show context explanations in recommendations."""
    
    min_confidence: float = 0.5
    """Minimum confidence threshold for showing recommendations."""
    
    model_config = SettingsConfigDict(env_prefix="ADRMINER_RECOMMENDATION_")
```

### Configuration File

```yaml
# .adrminer.yaml

recommendation:
  enabled: true
  max_recommendations: 5
  show_descriptions: true
  show_context: false
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_chat/test_command_recommendations.py

def test_direct_mapping():
    """Test direct tool-to-command mappings."""
    service = CommandRecommendationService()
    
    assert service.get_direct_mapping("classify_adrs") == "/classify predict {path}"
    assert service.get_direct_mapping("reset_memory") == "/reset_memory"
    assert service.get_direct_mapping("unknown_tool") is None

def test_context_suggestions():
    """Test context-aware suggestions."""
    service = CommandRecommendationService()
    
    result = {"success": True, "num_affected": 10}
    suggestions = service.get_context_suggestions("classify_adrs", result)
    
    assert len(suggestions) > 0
    assert any("/classify info" in s.command for s in suggestions)
    assert s.priority > 0

def test_multi_tool_combinations():
    """Test multi-tool suggestions."""
    service = CommandRecommendationService()
    
    tools_used = ["classify_adrs", "mine_topics"]
    results = [
        {"success": True, "num_affected": 10},
        {"success": True, "num_affected": 10}
    ]
    
    recommendations = service.get_recommendations(tools_used, results)
    
    assert len(recommendations) > 0
    # Should prioritize summary command for combined analysis
    assert any("/summary" in r.command for r in recommendations)
```

### Integration Tests

```python
# tests/test_agents/test_command_recommendations_integration.py

def test_agent_with_recommendations():
    """Test agent adds recommendations to responses."""
    agent = create_test_agent_with_recommendations()
    
    response = agent.invoke("Classify ADRs in adrs/")
    
    assert "Related commands you might want to run" in response
    assert "/classify info" in response or "/topics predict" in response

def test_agent_without_tools():
    """Test agent doesn't show recommendations for no tools."""
    agent = create_test_agent_with_recommendations()
    
    response = agent.invoke("What is ADR?")
    
    assert "Related commands you might want to run" not in response
```

---

## Future Enhancements

### 1. Adaptive Recommendations

Learn from user behavior to improve recommendations:
- Track which recommendations users follow
- Adjust priority based on usage patterns
- Remember user preferences

### 2. Result-Based Suggestions

Analyze tool results to provide smarter suggestions:
- Suggest fixing issues if quality check fails
- Suggest re-classifying if confidence is low
- Suggest investigating outliers in topic distribution

### 3. Workflow Suggestions

Suggest complete workflows:
- "Full analysis workflow: classify → topics → check → summary"
- "Quality improvement workflow: check → inspect → fix → re-check"

### 4. Personalized Recommendations

Customize based on user role:
- Developers: Suggest classification and topics
- Architects: Suggest insights and summaries
- Reviewers: Suggest quality checks

### 5. Command Examples

Include example usage in recommendations:
```
/classify predict adrs/ --framework zimmermann --csv results.csv
```

---

## Conclusion

The command recommendation feature will significantly improve the user experience by:

1. **Bridging the gap** between agent and CLI interfaces
2. **Improving discoverability** of CLI commands
3. **Guiding workflows** with context-aware suggestions
4. **Providing seamless transition** from conversational to command-line interaction

The implementation follows a clean architecture with:
- Separated recommendation service
- Multiple integration options
- Comprehensive testing strategy
- Extensible design for future enhancements

This feature will help users leverage the full power of ADRminer's CLI while enjoying the convenience of the conversational agent interface.