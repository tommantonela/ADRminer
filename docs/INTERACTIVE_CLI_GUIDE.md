# ADRminer Interactive CLI Guide

**Version:** 1.0  
**Date:** 2026-04-21  
**Status:** Phase 1 Complete (Command-Based)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Getting Started](#2-getting-started)
3. [Command Reference](#3-command-reference)
4. [Session Management](#4-session-management)
5. [Common Workflows](#5-common-workflows)
6. [Tips and Tricks](#6-tips-and-tricks)
7. [Future Enhancements](#7-future-enhancements)

---

## 1. Overview

The ADRminer interactive CLI provides a chat-like interface for analyzing Architecture Decision Records (ADRs). It allows you to run commands interactively, manage sessions, and perform analyses without repeatedly typing full command-line arguments.

### Features

- **Interactive Command Loop**: Enter commands using `/` prefix
- **Session State**: Maintain state across commands (working directory, loaded ADRs, analysis results)
- **Lazy Service Loading**: Services load only when needed
- **Command History**: Navigate previous commands with Up/Down arrows
- **Auto-completion**: Tab-complete commands and options
- **Progress Indicators**: Visual progress for batch operations
- **Confirmation Prompts**: Protect against accidental batch operations

### Current Status

**Phase 1 (Command-Based)**: ✅ Complete
- Full command support for topics, classification, and checking
- Session management and state persistence
- Command history and navigation

**Phase 2 (LLM-Powered)**: 🔜 Planned
- Natural language queries
- LLM interpretation of user intent
- Smart command suggestions

---

## 2. Getting Started

### 2.1 Launch Interactive Mode

```bash
adrminer chat
```

This starts the interactive CLI in your current working directory.

### 2.2 First-Time Experience

When you first launch the interactive CLI, you'll see:

```
╭──────────────────────────────────────────╮
│     ADRminer Interactive CLI v0.1.0      │
│     Analyze your ADRs interactively      │
╰──────────────────────────────────────────╯

Type /help for available commands
Type /quit to exit

ADRminer [/Users/user/project]> _
```

### 2.3 Basic Navigation

- **Type commands**: Start with `/` (e.g., `/help`)
- **Navigate history**: Use Up/Down arrow keys to browse previous commands
- **Search history**: Press `Ctrl+R` to search through command history
- **Auto-complete**: Press Tab to complete commands and options
- **Edit commands**: Use standard editing (Home/End, Ctrl+A/E, etc.)
- **Exit**: Type `/quit` or press `Ctrl+D`

---

## 3. Command Reference

### 3.1 Help Commands

#### `/help`
Display all available commands.

```
ADRminer [/Users/user/project]> /help
```

**Output:**
```
Available Commands:

  /help               Show this help message
  /cd [path]          Change working directory
  /pwd                Show current working directory
  /ls [path]          List ADR files
  
  /topics predict <path>    Predict topics for ADRs
  /topics info [options]    Show topic information
  
  /classify predict <path>  Classify ADRs
  /classify list            List frameworks
  
  /check predict <path>     Check ADR quality
  /check templates          List templates
  
  /util inspect <path>      Inspect ADR metadata
  
  /history [n]       Show command history
  /clear             Clear screen
  /quit              Exit interactive mode
```

#### `/help <command>`
Show detailed help for a specific command.

```
ADRminer [/Users/user/project]> /help topics predict
```

### 3.2 Navigation Commands

#### `/cd [path]`
Change working directory.

```
ADRminer [/Users/user/project]> /cd ./adrs
ADRminer [/Users/user/project/adrs]>
```

**Examples:**
```bash
# Change to directory
/cd ./docs/adrs

# Go up one level
/cd ..

# Use absolute path
/cd /Users/user/projects/my-project
```

#### `/pwd`
Show current working directory.

```
ADRminer [/Users/user/project]> /pwd
Current directory: /Users/user/project
```

#### `/ls [path]`
List ADR files in directory.

```
ADRminer [/Users/user/project]> /ls
```

**Output:**
```
ADR Files in /Users/user/project:
  • adr-001.md
  • adr-002.md
  • adr-003.md
  • adr-004.md
```

### 3.3 Topics Commands

#### `/topics predict <path> [options]`
Predict topics for ADRs.

```
ADRminer [/Users/user/project]> /topics predict ./adrs
```

**Options:**
- `--model <path>`: Use custom topic model
- `--output <format>`: Output format (sidecar, consolidated)
- `--threshold <value>`: Topic probability threshold (default: 0.0)
- `--multiple`: Allow multiple topics per ADR

**Examples:**
```bash
# Predict topics for directory
/topics predict ./adrs

# Predict with threshold
/topics predict ./adrs --threshold 0.5

# Export to consolidated JSON
/topics predict ./adrs --output consolidated

# Use custom model
/topics predict ./adrs --model ./models/custom
```

#### `/topics info [options]`
Show topic information.

```
ADRminer [/Users/user/project]> /topics info
```

**Output:**
```
Total Topics: 15
Model Path: ~/.adrminer/models/topic_model
Topic Names: LLM-generated

┌────┬──────────────────────────┬───────┐
│ ID │ Topic Name               │ Count │
├────┼──────────────────────────┼───────┤
│  0 │ Database Migration       │     8 │
│  1 │ API Design               │     6 │
│  2 │ Authentication           │     4 │
└────┴──────────────────────────┴───────┘
```

**Options:**
- `--topic-id <id>`: Show details for specific topic

**Examples:**
```bash
# Show all topics
/topics info

# Show specific topic
/topics info --topic-id 5
```

### 3.4 Classification Commands

#### `/classify predict <path> [options]`
Classify ADRs using specified framework.

```
ADRminer [/Users/user/project]> /classify predict ./adrs --framework kruchten
```

**Options:**
- `--framework <name>`: Classification framework (kruchten, quality_attributes, zimmermann)
- `--examples <path>`: Use custom examples file
- `--no-examples`: Zero-shot classification
- `--output <format>`: Output format (sidecar, consolidated)

**Examples:**
```bash
# Classify with Kruchten framework
/classify predict ./adrs --framework kruchten

# Classify with Quality Attributes
/classify predict ./adrs --framework quality_attributes

# Zero-shot classification
/classify predict ./adrs --framework kruchten --no-examples

# Custom examples
/classify predict ./adrs --examples ./custom/examples.json
```

#### `/classify list`
List supported classification frameworks.

```
ADRminer [/Users/user/project]> /classify list
```

**Output:**
```
Supported Classification Frameworks:

  • kruchten (default)
      - 4 categories: ontocrisis, diacrisis, pericrisis, anticrisis
      - Focus: Architectural decision crisis types

  • quality_attributes
      - 10 categories: performance, security, usability, etc.
      - Focus: Quality attribute impact

  • zimmermann
      - 9 categories: architecture, technology, integration, etc.
      - Focus: Architectural decision types
```

### 3.5 Check Commands

#### `/check predict <path> [options]`
Check ADR quality and template adherence.

```
ADRminer [/Users/user/project]> /check predict ./adrs
```

**Options:**
- `--template <name>`: Template to check against (default: madr)
- `--sections`: Run section-wise analysis
- `--output <format>`: Output format (sidecar, consolidated)

**Examples:**
```bash
# Check ADRs
/check predict ./adrs

# Section-wise analysis
/check predict ./adrs --sections

# Custom template
/check predict ./adrs --template custom_template.yaml
```

#### `/check templates`
List supported templates.

```
ADRminer [/Users/user/project]> /check templates
```

**Output:**
```
Supported Templates:

  • madr (default)
      - 7 sections: Status, Context, Decision, Consequences, etc.
      - Minimal but complete

  • adr-template
      - 9 sections: Title, Status, Context, Decision, etc.
      - More detailed
```

### 3.6 Utility Commands

#### `/util inspect <path>`
Inspect ADR metadata.

```
ADRminer [/Users/user/project]> /util inspect adr-001.md
```

**Output:**
```
ADR: adr-001.md

File: /Users/user/project/adr-001.md
Analyzed: 2026-04-21T10:00:00Z

Topics:
  • ID: 5, Name: Database Migration, Probability: 0.85
  • ID: 2, Name: API Design, Probability: 0.72

Classifications:
  • kruchten:
    - Primary: Existence (ontocrisis)
    - Confidence: 0.92
    - Alternatives: Property

  • zimmermann:
    - Primary: Architecture
    - Confidence: 0.95
    - Alternatives: Technology

Check:
  • Template Adherence: 0.78
  • Missing Sections: alternatives
```

### 3.7 Session Commands

#### `/history [n]`
Show command history.

```
ADRminer [/Users/user/project]> /history
```

**Output:**
```
Command History:

  1 /cd ./adrs
  2 /ls
  3 /topics predict . --threshold 0.5
  4 /topics info
  5 /help
```

#### `/clear`
Clear screen.

```
ADRminer [/Users/user/project]> /clear
```

#### `/quit`
Exit interactive mode.

```
ADRminer [/Users/user/project]> /quit
Goodbye!
```

---

## 4. Session Management

### 4.1 Session State

The interactive CLI maintains session state across commands:

- **Working Directory**: Current directory for file operations
- **Loaded ADRs**: List of ADR files loaded during session
- **Analysis Results**: Results from analyses (topics, classification, check)
- **Command History**: Commands executed during session

### 4.2 Working Directory

The working directory affects file path resolution:

```bash
# Start in project root
ADRminer [/Users/user/project]> /pwd
Current directory: /Users/user/project

# Change to ADR directory
ADRminer [/Users/user/project]> /cd ./adrs
ADRminer [/Users/user/project/adrs]> /pwd
Current directory: /Users/user/project/adrs

# Use relative paths
ADRminer [/Users/user/project/adrs]> /topics predict .
```

### 4.3 Command History

Navigate command history with arrow keys:

- **Up Arrow**: Previous command
- **Down Arrow**: Next command
- **Home**: Start of line
- **End**: End of line

### 4.4 Auto-completion

Press Tab to auto-complete:

```bash
# Auto-complete command
ADRminer [/Users/user/project]> /top[TAB]
/topics

# Auto-complete options
ADRminer [/Users/user/project]> /topics info --t[TAB]
--topic-id
```

---

## 5. Common Workflows

### 5.1 Quick Analysis

Analyze ADRs quickly with default settings:

```bash
# Start interactive CLI
$ adrminer chat

# Navigate to ADR directory
ADRminer [/Users/user/project]> /cd ./adrs

# List ADRs
ADRminer [/Users/user/project/adrs]> /ls

# Predict topics
ADRminer [/Users/user/project/adrs]> /topics predict .

# Classify with Kruchten
ADRminer [/Users/user/project/adrs]> /classify predict . --framework kruchten

# Check quality
ADRminer [/Users/user/project/adrs]> /check predict .

# Inspect specific ADR
ADRminer [/Users/user/project/adrs]> /util inspect adr-001.md
```

### 5.2 Multi-Framework Classification

Classify ADRs using multiple frameworks:

```bash
# Classify with Kruchten
ADRminer [/Users/user/project]> /classify predict ./adrs --framework kruchten

# Add Quality Attributes classification
ADRminer [/Users/user/project]> /classify predict ./adrs --framework quality_attributes

# Add Zimmermann classification
ADRminer [/Users/user/project]> /classify predict ./adrs --framework zimmermann

# Inspect combined results
ADRminer [/Users/user/project]> /util inspect adr-001.md
```

### 5.3 Batch Processing with Thresholds

Filter results by probability thresholds:

```bash
# Predict topics with high threshold
ADRminer [/Users/user/project]> /topics predict ./adrs --threshold 0.7

# Classify with confidence threshold
ADRminer [/Users/user/project]> /classify predict ./adrs --framework kruchten
# (Results are filtered by confidence in the service)
```

### 5.4 Export Results

Export results in different formats:

```bash
# Export to sidecar files
ADRminer [/Users/user/project]> /topics predict ./adrs --output sidecar

# Export to consolidated JSON
ADRminer [/Users/user/project]> /topics predict ./adrs --output consolidated

# Results saved to ./topics_results.json
```

---

## 6. Tips and Tricks

### 6.1 Efficient Workflows

**Use relative paths from current directory:**
```bash
# Good
ADRminer [/Users/user/project/adrs]> /topics predict .

# Less efficient
ADRminer [/Users/user/project]> /topics predict /Users/user/project/adrs
```

**Combine operations:**
```bash
# Navigate once, use relative paths
ADRminer [/Users/user/project]> /cd ./adrs
ADRminer [/Users/user/project/adrs]> /topics predict .
ADRminer [/Users/user/project/adrs]> /classify predict .
ADRminer [/Users/user/project/adrs]> /check predict .
```

### 6.2 Batch Operation Confirmations

Large operations require confirmation:

```
ADRminer [/Users/user/project]> /topics predict ./adrs

Found 50 ADR file(s) to analyze
Proceed with analysis? [y/N]: y
```

### 6.3 Service Loading

Services load lazily when first used:

```
ADRminer [/Users/user/project]> /topics predict .
[blue]Loading topic model...[/blue]
[green]✓ Topic model loaded[/green]

Processing ADRs...
```

Services stay loaded for the session:
```bash
# First call loads service
ADRminer [/Users/user/project]> /topics predict .
[blue]Loading topic model...[/blue]

# Second call uses cached service
ADRminer [/Users/user/project]> /topics info
(No loading message)
```

### 6.4 Error Handling

Commands show helpful error messages:

```bash
# File not found
ADRminer [/Users/user/project]> /topics predict ./nonexistent
Error: Path does not exist: /Users/user/project/nonexistent

# No ADRs found
ADRminer [/Users/user/project]> /topics predict ./empty
Warning: No ADRs found in /Users/user/project/empty

# Invalid topic ID
ADRminer [/Users/user/project]> /topics info --topic-id 999
Error: Topic 999 not found
```

### 6.5 Keyboard Shortcuts

- `Ctrl+C`: Cancel current command
- `Ctrl+D`: Exit interactive mode
- `Up/Down`: Navigate history
- `Tab`: Auto-complete
- `Home/End`: Navigate to start/end of line

---

## 7. Future Enhancements

### Phase 2: LLM-Powered Commands (Planned)

**Natural Language Queries:**
```bash
# Instead of:
ADRminer [/Users/user/project]> /topics predict ./adrs --threshold 0.7

# You'll be able to say:
ADRminer [/Users/user/project]> Which ADRs are about database migration?
```

**Smart Suggestions:**
```bash
ADRminer [/Users/user/project]> I want to analyze my ADRs
AI: Would you like to:
  1. Predict topics for all ADRs?
  2. Classify ADRs using a specific framework?
  3. Check ADR quality?
```

**Context-Aware Commands:**
```bash
ADRminer [/Users/user/project]> /topics predict .
# Analyzes 25 ADRs...

ADRminer [/Users/user/project]> Show me the top topic
AI: The most common topic is "Database Migration" (8 ADRs, 32%)
```

**Multi-Turn Conversations:**
```bash
ADRminer [/Users/user/project]> What decisions affect performance?
AI: Based on topic analysis, these ADRs are relevant:
  • adr-012 - Caching Strategy
  • adr-023 - Database Indexing
  • adr-045 - API Optimization

Would you like me to classify these ADRs by quality attributes?
```

### Integration Roadmap

1. **Q2 2026**: Phase 2 Design & Specification
2. **Q3 2026**: LLM Integration & Command Interpretation
3. **Q4 2026**: Beta Testing & Refinement
4. **Q1 2027**: Stable Release

---

## Appendix

### A. Exit Codes

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Input file not found
- `4`: Model load error
- `5`: API error

### B. Configuration Files

Interactive CLI respects standard ADRminer configuration:

- `.env`: API keys and environment variables
- `.adrminer.yaml`: Service configuration
- `~/.adrminer.yaml`: Global configuration

### C. Keyboard Sequences

| Sequence | Action |
|----------|--------|
| `Ctrl+C` | Cancel current command |
| `Ctrl+D` | Exit interactive mode |
| `Ctrl+L` | Clear screen (same as `/clear`) |
| `Ctrl+R` | Search through command history |
| `Up Arrow` | Previous command |
| `Down Arrow` | Next command |
| `Tab` | Auto-complete |
| `Home` | Start of line |
| `End` | End of line |
| `Ctrl+A` | Start of line |
| `Ctrl+E` | End of line |
| `Ctrl+U` | Delete to start of line |
| `Ctrl+K` | Delete to end of line |

---

**Document History:**
- v1.0 - Initial interactive CLI guide (2026-04-21)