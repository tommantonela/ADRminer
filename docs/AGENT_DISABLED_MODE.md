# Agent-Disabled Mode Documentation

## Overview

The Agent-Disabled mode allows you to run ADRminer's interactive CLI without the AI assistant enabled. This provides a pure command-based interface with no agent layer, which is useful for:

- **Faster startup**: No agent initialization overhead
- **Reduced dependencies**: No need for LLM API keys or models
- **Simpler debugging**: Test commands without agent interference
- **Resource efficiency**: No memory usage for the agent
- **Production use**: Run ADRminer as a pure CLI tool

## Usage

### 1. Disable via CLI Flag

The simplest way to disable the agent is to use the `--no-agent` flag:

```bash
# Start chat without AI assistant
adrminer chat --no-agent

# Start chat in a specific directory without agent
adrminer chat examples/pharmacy-food --no-agent
```

### 2. Disable via Configuration File

Add the following to your `adrminer.yaml` or `.adrminer.yaml` file:

```yaml
agent:
  agent_enabled: false
```

Example:

```yaml
# adrminer.yaml
llm:
  provider: openai
  model: gpt-4.1-mini

topic_model:
  path: ~/.adrminer/models/topic_model

agent:
  agent_enabled: false  # Disable AI assistant
```

### 3. Disable via Environment Variable

Set the environment variable before running the CLI:

```bash
# Unix/Linux/macOS
export ADRMINER_AGENT__AGENT_ENABLED=false
adrminer chat

# Windows (PowerShell)
$env:ADRMINER_AGENT__AGENT_ENABLED="false"
adrminer chat

# Windows (CMD)
set ADRMINER_AGENT__AGENT_ENABLED=false
adrminer chat
```

## Behavior Differences

### With Agent Enabled (Default)

```
╔══════════════════════════════════════════════════════╗
║          ✨ ADRminer Interactive CLI ✨               ║
╚══════════════════════════════════════════════════════╝

Initializing AI assistant...
✓ AI assistant ready

ADRminer > Analyze my ADRs
[AI processes request and uses tools]

ADRminer > What topics are covered?
[AI processes request and provides insights]
```

### With Agent Disabled

```
╔══════════════════════════════════════════════════════╗
║          ✨ ADRminer Interactive CLI ✨               ║
╚══════════════════════════════════════════════════════╝

AI assistant disabled - commands only mode

ADRminer > /topics predict ./examples/adrs
[Direct command execution]

ADRminer > /classify predict ./examples/adrs --framework kruchten
[Direct command execution]
```

## What Still Works

When the agent is disabled, all commands continue to work normally:

- `/cd <path>` - Change working directory
- `/topics predict <path>` - Analyze topics
- `/topics info` - View topic information
- `/classify predict <path>` - Classify ADRs
- `/classify info` - View classification framework info
- `/check predict <path>` - Check ADR quality
- `/reset_memory` - Reset session memory
- `/help` - Show available commands
- `/quit` - Exit the CLI

## What Doesn't Work

With the agent disabled, you cannot:

- Use natural language queries (e.g., "Analyze my ADRs")
- Ask questions to the AI assistant
- Use AI-powered features that require the agent
- Get AI-generated insights or recommendations

You must use explicit commands (starting with `/`) instead.

## Technical Details

### Configuration Hierarchy

The agent-enabled setting follows this priority order (highest to lowest):

1. **CLI flag**: `--no-agent` (overrides everything)
2. **Config file**: `agent.agent_enabled = false`
3. **Environment variable**: `ADRMINER_AGENT__AGENT_ENABLED=false`
4. **Default**: `true` (agent enabled by default)

### Implementation

The agent-disabled mode is implemented through:

1. **AgentConfig field** (`src/adrminer/config/settings.py`):
   ```python
   class AgentConfig(BaseModel):
       agent_enabled: bool = Field(
           default=True,
           description="Enable AI assistant in chat mode"
       )
   ```

2. **SessionManager** (`src/adrminer/chat/session.py`):
   ```python
   def __init__(self, console, initial_dir=None, agent_enabled=True):
       self.agent_enabled = agent_enabled
       if not agent_enabled:
           self._agent = False
           self.console.print("AI assistant disabled - commands only mode")
   ```

3. **CLI command** (`src/adrminer/cli/main.py`):
   ```python
   def chat(directory=None, no_agent=False):
       run_chat(initial_dir=initial_dir, agent_enabled=not no_agent)
   ```

4. **Chat entry point** (`src/adrminer/chat/__init__.py`):
   ```python
   def run_chat(initial_dir=None, agent_enabled=None):
       if agent_enabled is None:
           agent_enabled = settings.agent.agent_enabled
       session = SessionManager(console, initial_dir=initial_dir, 
                             agent_enabled=agent_enabled)
   ```

## Use Cases

### 1. Development and Testing

```bash
# Test commands without waiting for agent to load
adrminer chat --no-agent

# Run quick checks during development
ADRminer > /topics predict ./test-data
ADRminer > /classify predict ./test-data --framework kruchten
```

### 2. CI/CD Pipelines

```bash
# Use in automated scripts without LLM dependencies
#!/bin/bash
export ADRMINER_AGENT__AGENT_ENABLED=false
adrminer chat --no-agent <<EOF
/cd ./project-adrs
/topics predict . --output results/topics.json
/check predict . --output results/checks.json
/quit
EOF
```

### 3. Production Scripts

```python
# Use as a library without agent
from adrminer.chat import SessionManager
from rich.console import Console

console = Console()
session = SessionManager(console, agent_enabled=False)

# Use services directly
topics = session.topic_service.predict(adr_files)
```

### 4. Resource-Constrained Environments

```bash
# Run on systems with limited resources
# No need for LLM models or API keys
adrminer chat --no-agent
```

## Performance Comparison

### Startup Time

- **Agent Enabled**: ~2-5 seconds (agent initialization)
- **Agent Disabled**: <1 second (no agent overhead)

### Memory Usage

- **Agent Enabled**: ~500MB - 2GB (depends on model)
- **Agent Disabled**: ~100-200MB (services only)

### Dependencies

- **Agent Enabled**: Requires LLM provider (OpenAI, Anthropic, etc.)
- **Agent Disabled**: Only requires core ADRminer dependencies

## Troubleshooting

### Agent Still Loading

If the agent still loads despite disabling it:

1. Check CLI flag syntax: `adrminer chat --no-agent`
2. Verify config file: `agent.agent_enabled: false`
3. Check environment variable: `echo $ADRMINER_AGENT__AGENT_ENABLED`
4. Priority: CLI flag > config file > environment variable > default

### Commands Not Working

If commands don't work in agent-disabled mode:

1. Ensure you're using `/` prefix (e.g., `/help` not `help`)
2. Check that the command exists with `/help`
3. Verify you're in the correct directory with `/cd <path>`

### Want to Enable Agent Mid-Session

Currently, you cannot enable the agent after starting the CLI. You must restart with the agent enabled:

```bash
# Exit current session
/quit

# Start new session with agent
adrminer chat
```

## Examples

### Example 1: Analyze Project with Commands Only

```bash
$ adrminer chat --no-agent
AI assistant disabled - commands only mode

ADRminer > /cd ./my-project/adrs
Current directory: ./my-project/adrs

ADRminer > /topics predict .
Loading topic model...
✓ Topic model loaded
Predicting topics for 25 ADRs...
✓ Topics saved to topics_results.json

ADRminer > /topics info
Topics: 15
Top topics:
  1. Data Management (5 ADRs)
  2. API Design (4 ADRs)
  3. Authentication (3 ADRs)

ADRminer > /quit
Goodbye!
```

### Example 2: Batch Processing

```bash
$ adrminer chat --no-agent <<EOF
/cd ./projects/project1
/topics predict . --output results/project1-topics.json
/classify predict . --framework kruchten --output results/project1-classification.json
/cd ../project2
/topics predict . --output results/project2-topics.json
/check predict . --output results/project2-checks.json
/quit
EOF
```

### Example 3: Config File Setup

```yaml
# adrminer.yaml
agent:
  agent_enabled: false

llm:
  provider: openai
  model: gpt-4.1-mini

topic_model:
  path: ~/.adrminer/models/topic_model
  n_topics: 15

classification:
  framework: kruchten
  use_examples: true
```

```bash
$ adrminer chat  # Uses config file
AI assistant disabled - commands only mode
```

## Migration Guide

### From Agent-Enabled to Agent-Disabled

1. **Natural language → Commands**

   Before:
   ```
   ADRminer > Analyze topics in my ADRs
   ```

   After:
   ```
   ADRminer > /topics predict .
   ```

2. **Questions → Info commands**

   Before:
   ```
   ADRminer > What topics did you find?
   ```

   After:
   ```
   ADRminer > /topics info
   ```

3. **Complex requests → Multiple commands**

   Before:
   ```
   ADRminer > Load ADRs from ./adrs, classify them, and check quality
   ```

   After:
   ```
   ADRminer > /cd ./adrs
   ADRminer > /classify predict .
   ADRminer > /check predict .
   ```

## Best Practices

1. **Use for automation**: Agent-disabled mode is ideal for scripts and CI/CD
2. **Document workflows**: Create command sequences for common tasks
3. **Use aliases**: Create shell aliases for common command sequences
4. **Batch operations**: Process multiple projects in one session
5. **Combine with config**: Use config files for consistent settings

## Related Features

- **Reset Memory**: `/reset_memory` command to clear session state
- **Session Management**: Persistent state across commands
- **Lazy Loading**: Services load only when needed
- **Command History**: Navigate with ↑/↓ arrows

## Files Modified

1. `src/adrminer/config/settings.py` - Added `agent_enabled` field
2. `src/adrminer/chat/session.py` - Added `agent_enabled` parameter
3. `src/adrminer/chat/__init__.py` - Added `agent_enabled` parameter to `run_chat`
4. `src/adrminer/cli/main.py` - Added `--no-agent` flag

## Support

For issues or questions about agent-disabled mode:

1. Check this documentation
2. Run `adrminer chat --no-agent --help`
3. Review the test suite: `python test_agent_disabled.py`
4. Check ADRminer documentation index