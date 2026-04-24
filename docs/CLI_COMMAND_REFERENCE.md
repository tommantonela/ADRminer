# ADRminer CLI Command Reference

Complete reference for all commands and options in both Interactive and Non-Interactive CLI modes.

## Table of Contents

- [CLI Modes Overview](#cli-modes-overview)
- [Interactive CLI Commands](#interactive-cli-commands)
  - [Navigation & Utility Commands](#navigation--utility-commands)
  - [Analysis Commands](#analysis-commands)
- [Non-Interactive CLI Commands](#non-interactive-cli-commands)
  - [Topics Commands](#topics-commands)
  - [Classify Commands](#classify-commands)
  - [Check Commands](#check-commands)
  - [Summary Commands](#summary-commands)
  - [Utility Commands](#utility-commands)

---

## CLI Modes Overview

ADRminer provides two CLI modes:

### Interactive Mode (`adrminer chat`)
- Session-based interface with `/` prefix commands
- Persistent services across commands
- Conversation-style workflow
- Ideal for iterative analysis
- **Start with:** `adrminer chat`

### Non-Interactive Mode (`adrminer <command>`)
- One-off commands with direct execution
- No `/` prefix required
- Suitable for automation and scripting
- Each command loads services independently
- **Usage:** `adrminer topics <subcommand> [options]`

---

## Interactive CLI Commands

### Navigation & Utility Commands

#### `/help`
Show help for commands.

**Usage:** `/help [command] [subcommand]`

**Arguments:**
- `command` (optional) - Command to show help for
- `subcommand` (optional) - Subcommand to show help for

**Examples:**
```bash
/help                    # Show all commands
/help topics              # Show topics command help
/help topics predict      # Show topics predict subcommand help
```

---

#### `/list`
List ADRs in current directory.

**Usage:** `/list [path]`

**Arguments:**
- `path` (optional) - Path to directory (defaults to current)

**Examples:**
```bash
/list                    # List ADRs in current directory
/list ./adrs            # List ADRs in specific directory
```

---

#### `/quit`
Exit interactive session.

**Usage:** `/quit`

**Note:** Can also use `exit` or Ctrl+C to quit.

---

### Analysis Commands

#### `/topics`
Topic mining commands.

**Usage:** `/topics <subcommand> [args] [options]`

##### Subcommands

###### `/topics predict`
Predict topics for ADRs.

**Usage:** `/topics predict <path> [options]`

**Arguments:**
- `path` (required) - Path to ADR file or directory

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--model` | Path to topic model | `None` (uses default) |
| `--output` | Output format (sidecar, consolidated) | `sidecar` |
| `--parallel` | Enable parallel processing | `True` |
| `--threshold` | Topic probability threshold | `0.0` |
| `--multiple` | Allow multiple topics per ADR | `False` |
| `--verbose` | Show detailed output | `False` |
| `--csv` | Export results to CSV file | `None` |

**Examples:**
```bash
/topics predict ./adrs
/topics predict ./adrs --csv topics.csv --verbose
/topics predict ./adrs --threshold 0.5 --multiple
```

---

###### `/topics info`
Show information about topics.

**Usage:** `/topics info [--topic-id <id>]`

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--topic-id` | Show specific topic ID | `None` (shows all) |

**Examples:**
```bash
/topics info                    # Show all topics
/topics info --topic-id 42     # Show specific topic
```

---

#### `/classify`
Classification commands using Kruchten, Quality Attributes, or Zimmermann frameworks.

**Usage:** `/classify <subcommand> [args] [options]`

##### Subcommands

###### `/classify predict`
Classify ADRs using specified framework.

**Usage:** `/classify predict <path> [options]`

**Arguments:**
- `path` (required) - Path to ADR file or directory

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--framework` | Classification framework (kruchten, quality_attributes, zimmermann) | `None` (uses config) |
| `--examples` | Path to custom examples JSON file | `None` (uses default) |
| `--no-examples` | Disable few-shot learning (zero-shot) | `False` |
| `--use-parser` | Use ADR parser for section extraction | `False` |
| `--strict` | Enable strict parsing (fail on errors) | `False` |
| `--no-language-detect` | Disable language detection in parser | `False` |
| `--output` | Output format (sidecar, consolidated) | `sidecar` |
| `--parallel` | Enable parallel processing | `True` |
| `--verbose` | Show detailed output | `False` |
| `--csv` | Export results to CSV file | `None` |

**Examples:**
```bash
/classify predict ./adrs
/classify predict ./adrs --framework kruchten --verbose
/classify predict ./adrs --no-examples --csv classifications.csv
/classify predict ./adrs --use-parser --strict
```

---

###### `/classify info`
Show information about classification frameworks.

**Usage:** `/classify info [--framework <name>]`

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--framework` | Framework name (kruchten, quality_attributes, zimmermann) | `None` (shows all) |

**Examples:**
```bash
/classify info                        # Show all frameworks
/classify info --framework kruchten     # Show specific framework
```

---

#### `/check`
Quality checking commands against MADR template.

**Usage:** `/check <subcommand> [args] [options]`

##### Subcommands

###### `/check predict`
Check ADR quality against MADR template.

**Usage:** `/check predict <path> [options]`

**Arguments:**
- `path` (required) - Path to ADR file or directory

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--mode` | Checking mode (adherence, sections, full) | `full` |
| `--parallel` | Enable parallel processing | `True` |
| `--use-parser` | Use ADR parser for section extraction | `False` |
| `--strict` | Enable strict parsing (fail on errors) | `False` |
| `--no-language-detect` | Disable language detection in parser | `False` |
| `--csv` | Export results to CSV file | `None` |

**Examples:**
```bash
/check predict ./adrs
/check predict ./adrs --mode adherence
/check predict ./adrs --use-parser --csv quality.csv
```

---

#### `/util`
Utility commands.

**Usage:** `/util <subcommand> [args] [options]`

##### Subcommands

###### `/util llm`
Test LLM configuration.

**Usage:** `/util llm [prompt]`

**Arguments:**
- `prompt` (optional) - Test prompt to send to LLM

**Examples:**
```bash
/util llm                     # Test with default prompt
/util llm "What is 2+2?"      # Test with custom prompt
```

---

###### `/util inspect`
Inspect and display an ADR with Rich Markdown rendering.

**Usage:** `/util inspect <path> [options]`

**Arguments:**
- `path` (required) - Path to ADR file

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--metadata` | Show metadata alongside ADR | `False` |
| `--raw` | Show raw content without Markdown formatting | `False` |
| `--width` | Set display width | `None` (auto) |

**Examples:**
```bash
/util inspect ./adrs/ADR001.md
/util inspect ./adrs/ADR001.md --metadata
/util inspect ./adrs/ADR001.md --raw --width 80
```

---

###### `/util list`
List ADRs with enhanced features.

**Usage:** `/util list [path] [options]`

**Arguments:**
- `path` (optional) - Path to ADR file or directory

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--has-metadata` | Show only ADRs that have metadata | `False` |
| `--details` | Show detailed information (title, status, topic, classifications) | `False` |
| `--compact` | Show compact list (filenames only) | `False` |

**Examples:**
```bash
/util list                    # List all ADRs
/util list --has-metadata     # List only ADRs with metadata
/util list --details          # Show detailed information
/util list --compact          # Compact list
```

---

#### `/summary`
Generate summaries and insights for ADRs.

**Usage:** `/summary <path> [options]`

**Arguments:**
- `path` (required) - Path to ADR file or directory

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--output-summary` | Export summary report to Markdown file | `None` |
| `--output-detailed` | Export detailed report with insights to Markdown file | `None` |
| `--verbose` | Show detailed output | `False` |
| `--force-rewrite` | Regenerate all summaries (ignore cached files) | `False` |

**Examples:**
```bash
/summary ./adrs
/summary ./adrs --output-summary summary.md
/summary ./adrs --output-detailed detailed.md --verbose
```

**Output includes:**
- Per-ADR content summaries
- Topic and classification information
- Quality scores
- Project-level insights:
  - Classification patterns
  - Quality trends
  - Architectural themes
  - Risk assessment
  - Recommendations

---

## Non-Interactive CLI Commands

### Topics Commands

#### `topics train`
Train a new topic model from ADRs.

**Usage:** `adrminer topics train <path> [options]`

**Arguments:**
- `path` (required) - Path to ADR files

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--output` | Path to save trained model | `~/.adrminer/models/topic_model` |
| `--embedding-model` | Embedding model name | `all-MiniLM-L6-v2` |
| `--n-topics` | Number of topics (None for auto) | `None` |
| `--reduce-topics` | Reduce number of topics after training | `False` |
| `--language` | Language for stop words | `english` |
| `--umap-n-neighbors` | UMAP n_neighbors parameter | `15` |
| `--umap-n-components` | UMAP n_components parameter | `5` |
| `--umap-min-dist` | UMAP min_dist parameter | `0.0` |
| `--umap-metric` | UMAP metric parameter | `cosine` |
| `--use-llm-names` | Use LLM to generate human-readable topic names | `False` |

**Examples:**
```bash
adrminer topics train ./adrs
adrminer topics train ./adrs --n-topics 20 --use-llm-names
adrminer topics train ./adrs --output ./my_model --embedding-model paraphrase-multilingual-MiniLM-L12-v2
```

---

#### `topics predict`
Predict topics for ADRs using a trained model.

**Usage:** `adrminer topics predict <path> [options]`

**Arguments:**
- `path` (required) - Path to ADR file or directory

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--model` | Path to topic model | `~/.adrminer/models/topic_model` |
| `--output` | Output format (sidecar, consolidated) | `sidecar` |
| `--parallel` | Enable parallel processing | `True` |
| `--threshold` | Topic probability threshold | `0.0` |
| `--multiple` | Allow multiple topics per ADR | `False` |

**Examples:**
```bash
adrminer topics predict ./adrs
adrminer topics predict ./adrs --model ./my_model --threshold 0.5
adrminer topics predict ./adrs --output consolidated --multiple
```

---

#### `topics info`
Show information about topics in a model.

**Usage:** `adrminer topics info [--topic-id <id>]`

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--model` | Path to topic model | `~/.adrminer/models/topic_model` |
| `--topic-id` | Show specific topic ID | `None` (shows all) |

**Examples:**
```bash
adrminer topics info
adrminer topics info --topic-id 42
adrminer topics info --model ./my_model
```

---

### Classify Commands

#### `classify predict`
Classify ADRs using specified framework.

**Usage:** `adrminer classify predict <path> [options]`

**Arguments:**
- `path` (required) - Path to ADR file or directory

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--framework` | Classification framework | `kruchten` |
| `--examples` | Path to examples JSON file | `~/.adrminer/examples/kruchten_examples.json` |
| `--no-examples` | Disable few-shot learning | `False` |
| `--use-parser` | Use ADR parser for section extraction | `False` |
| `--strict` | Enable strict parsing | `False` |
| `--no-language-detect` | Disable language detection | `False` |
| `--output` | Output format (sidecar, consolidated) | `sidecar` |
| `--parallel` | Enable parallel processing | `True` |

**Examples:**
```bash
adrminer classify predict ./adrs
adrminer classify predict ./adrs --framework zimmermann
adrminer classify predict ./adrs --no-examples --use-parser
```

---

#### `classify info`
Show information about classification frameworks.

**Usage:** `adrminer classify info [--framework <name>]`

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--framework` | Framework name | `None` (shows all) |

**Examples:**
```bash
adrminer classify info
adrminer classify info --framework quality_attributes
```

---

### Check Commands

#### `check predict`
Check ADR quality against MADR template.

**Usage:** `adrminer check predict <path> [options]`

**Arguments:**
- `path` (required) - Path to ADR file or directory

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--mode` | Checking mode (adherence, sections, full) | `full` |
| `--use-parser` | Use ADR parser for section extraction | `False` |
| `--strict` | Enable strict parsing | `False` |
| `--no-language-detect` | Disable language detection | `False` |
| `--output` | Output format (sidecar, consolidated) | `sidecar` |
| `--parallel` | Enable parallel processing | `True` |

**Examples:**
```bash
adrminer check predict ./adrs
adrminer check predict ./adrs --mode adherence
adrminer check predict ./adrs --use-parser --strict
```

---

### Summary Commands

#### `summary`
Generate summaries and insights for ADRs.

**Usage:** `adrminer summary <path> [options]`

**Arguments:**
- `path` (required) - Path to ADR file or directory

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--output-summary` | Export summary report to Markdown file | `None` |
| `--output-detailed` | Export detailed report with insights to Markdown file | `None` |
| `--verbose` | Show detailed output | `False` |
| `--force-rewrite` | Regenerate all summaries (ignore cached files) | `False` |

**Examples:**
```bash
adrminer summary ./adrs
adrminer summary ./adrs --output-summary summary.md
adrminer summary ./adrs --output-detailed detailed.md
```

**Output includes:**
- Per-ADR content summaries
- Project-level insights:
  - Classification patterns
  - Quality trends
  - Architectural themes
  - Risk assessment
  - Recommendations

---

### Utility Commands

#### `util llm`
Test LLM configuration.

**Usage:** `adrminer util llm [--prompt <text>]`

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--prompt` | Test prompt to send to LLM | `"How are you doing?"` |

**Examples:**
```bash
adrminer util llm
adrminer util llm --prompt "What is 2+2?"
```

---

#### `util inspect`
Inspect and display an ADR.

**Usage:** `adrminer util inspect <path> [options]`

**Arguments:**
- `path` (required) - Path to ADR file

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--metadata` | Show metadata alongside ADR | `False` |
| `--raw` | Show raw content without Markdown formatting | `False` |
| `--width` | Set display width | `None` (auto) |

**Examples:**
```bash
adrminer util inspect ./adrs/ADR001.md
adrminer util inspect ./adrs/ADR001.md --metadata
```

---

#### `util list`
List ADRs in a directory.

**Usage:** `adrminer util list <path> [options]`

**Arguments:**
- `path` (required) - Path to ADR file or directory

**Options:**
| Option | Description | Default |
|--------|-------------|----------|
| `--has-metadata` | Show only ADRs that have metadata | `False` |
| `--details` | Show detailed information | `False` |
| `--compact` | Show compact list | `False` |

**Examples:**
```bash
adrminer util list ./adrs
adrminer util list ./adrs --has-metadata --details
```

---

## Configuration

ADRminer reads configuration from multiple sources (in order of precedence):

1. **Command-line options** (highest priority)
2. **Environment variables** (prefixed with `ADRMINER_`)
3. **Project-local config** (`.adrminer.yaml` or `adrminer.yaml` in current directory)
4. **Global config** (`~/.adrminer.yaml`)

### Example Config File

```yaml
# .adrminer.yaml
llm:
  provider: openai
  model: gpt-4.1-mini
  temperature: 0.0
  max_tokens: 2000

topic_model:
  path: ~/.adrminer/models/topic_model
  use_llm_representation: true  # Use LLM for human-readable topic names
  embedding_model: all-MiniLM-L6-v2

classification:
  framework: kruchten
  use_examples: true

check:
  template: madr

output:
  format: json-sidecar
  parallel: true
  verbose: false
```

---

## Output Formats

### JSON Sidecar (Default)
- Creates `.metadata.json` file alongside each ADR
- Contains topics, classifications, checks, and insights
- Easy to parse programmatically

### Consolidated JSON
- Single JSON file with all results
- Includes metadata header
- Suitable for batch processing

### CSV Export
- Available for topics, classify, and check commands
- Easy to open in spreadsheet applications
- Specified with `--csv <filename>` option

### Markdown Reports
- Generated by `/summary` command
- Human-readable documentation
- Includes project-level insights

---

## Tips & Best Practices

### Interactive Mode
- Use `/list` to verify ADRs before analysis
- Start with `/topics info` to understand your model
- Use `/util inspect` to preview ADRs
- Leverage `--verbose` flag for detailed output during testing
- Use `--csv` export for easy data analysis

### Non-Interactive Mode
- Use `--parallel` flag for faster processing of multiple ADRs
- Set appropriate `--threshold` values to filter low-confidence results
- Use `--output consolidated` for batch processing
- Train custom models with `--use-llm-names` for better interpretability

### Performance
- Use parallel processing for directories with 10+ ADRs
- Cache topic model in local directory for faster loading
- Disable language detection if all ADRs are in English
- Use zero-shot classification (`--no-examples`) for faster but less accurate results

---

## Getting Help

### Interactive Mode
```bash
/help                    # Show all commands
/help topics              # Show topics command help
/help topics predict      # Show topics predict subcommand help
```

### Non-Interactive Mode
```bash
adrminer --help          # Show top-level help
adrminer topics --help   # Show topics command help
adrminer topics train --help  # Show train subcommand help
```

---

## See Also

- [CLI Guide](CLI_GUIDE.md) - Getting started guide
- [Interactive CLI Guide](INTERACTIVE_CLI_GUIDE.md) - Detailed interactive mode usage
- [Implementation Summary](FINAL_IMPLEMENTATION_SUMMARY.md) - Implementation details