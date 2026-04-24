"""Command registry for interactive chat CLI."""

from typing import Dict, List, Optional, Callable, Any

# Command metadata structure:
# {
#   "/command": {
#       "handler": function_name,
#       "description": "Brief description",
#       "help": "Usage syntax",
#       "subcommands": {
#           "subcommand": {
#               "handler": function_name,
#               "description": "Description",
#               "args": [
#                   {"name": "arg_name", "help": "help text", "required": True}
#               ],
#               "options": [
#                   {"name": "option_name", "help": "help text", "required": False, "default": None}
#               ]
#           }
#       }
#   }
# }

COMMAND_REGISTRY: Dict[str, Dict[str, Any]] = {
    "/help": {
        "handler": "handle_help",
        "description": "Show help for commands",
        "help": "/help [command] [subcommand]  - Show help for all commands or specific command/subcommand",
        "args": [
            {"name": "command", "help": "Command to show help for (optional)", "required": False},
            {"name": "subcommand", "help": "Subcommand to show help for (optional)", "required": False}
        ]
    },
    "/list": {
        "handler": "handle_list",
        "description": "List ADRs in current directory",
        "help": "/list [path]  - List ADRs in current or specified path",
        "args": [
            {"name": "path", "help": "Path to directory (optional, defaults to current)", "required": False}
        ]
    },
    "/quit": {
        "handler": "handle_quit",
        "description": "Exit the interactive session",
        "help": "/quit  - Exit the interactive session"
    },
    "/topics": {
        "handler": "handle_topics",
        "description": "Topic mining commands",
        "help": "/topics <subcommand> [args] [options]  - Topic mining",
        "subcommands": {
            "predict": {
                "handler": "handle_topics_predict",
                "description": "Predict topics for ADRs",
                "help": "/topics predict <path> [options]",
                "args": [
                    {"name": "path", "help": "Path to ADR file or directory", "required": True}
                ],
                "options": [
                    {"name": "model", "help": "Path to topic model", "required": False, "default": None},
                    {"name": "output", "help": "Output format (sidecar, consolidated)", "required": False, "default": "sidecar"},
                    {"name": "parallel", "help": "Enable parallel processing", "required": False, "default": True},
                    {"name": "threshold", "help": "Topic probability threshold (default: 0.0)", "required": False, "default": 0.0},
                    {"name": "multiple", "help": "Allow multiple topics per ADR", "required": False, "default": False},
                    {"name": "verbose", "help": "Show detailed output (default: auto based on result count)", "required": False, "default": False},
                    {"name": "csv", "help": "Export results to CSV file", "required": False, "default": None}
                ]
            },
            "info": {
                "handler": "handle_topics_info",
                "description": "Show information about topics",
                "help": "/topics info [--topic-id <id>]  - Show topic information",
                "options": [
                    {"name": "topic-id", "help": "Show specific topic ID", "required": False, "default": None}
                ]
            }
        }
    },
    "/classify": {
        "handler": "handle_classify",
        "description": "Classification commands",
        "help": "/classify <subcommand> [args] [options]  - Classify ADRs",
        "subcommands": {
            "predict": {
                "handler": "handle_classify_predict",
                "description": "Classify ADRs using specified framework",
                "help": "/classify predict <path> [options]",
                "args": [
                    {"name": "path", "help": "Path to ADR file or directory", "required": True}
                ],
                "options": [
                    {"name": "framework", "help": "Classification framework (kruchten, quality_attributes, zimmermann)", "required": False, "default": None},
                    {"name": "examples", "help": "Path to custom examples JSON file", "required": False, "default": None},
                    {"name": "no-examples", "help": "Disable few-shot learning (zero-shot)", "required": False, "default": False},
                    {"name": "use-parser", "help": "Use ADR parser for section extraction", "required": False, "default": False},
                    {"name": "strict", "help": "Enable strict parsing (fail on errors)", "required": False, "default": False},
                    {"name": "no-language-detect", "help": "Disable language detection in parser", "required": False, "default": False},
                    {"name": "output", "help": "Output format (sidecar, consolidated)", "required": False, "default": "sidecar"},
                    {"name": "parallel", "help": "Enable parallel processing", "required": False, "default": True},
                    {"name": "verbose", "help": "Show detailed output (default: auto based on result count)", "required": False, "default": False},
                    {"name": "csv", "help": "Export results to CSV file", "required": False, "default": None}
                ]
            },
            "info": {
                "handler": "handle_classify_info",
                "description": "Show information about classification frameworks",
                "help": "/classify info [--framework <name>]  - Show framework information",
                "options": [
                    {"name": "framework", "help": "Framework name (kruchten, quality_attributes, zimmermann)", "required": False, "default": None}
                ]
            }
        }
    },
    "/check": {
        "handler": "handle_check",
        "description": "Quality checking commands",
        "help": "/check <subcommand> [args] [options]  - Check ADR quality",
        "subcommands": {
            "predict": {
                "handler": "handle_check_predict",
                "description": "Check ADR quality against MADR template",
                "help": "/check predict <path> [options]",
                "args": [
                    {"name": "path", "help": "Path to ADR file or directory", "required": True}
                ],
                "options": [
                    {"name": "mode", "help": "Checking mode (adherence, sections, full)", "required": False, "default": "full"},
                    {"name": "parallel", "help": "Enable parallel processing", "required": False, "default": True},
                    {"name": "use-parser", "help": "Use ADR parser for section extraction", "required": False, "default": False},
                    {"name": "strict", "help": "Enable strict parsing (fail on errors)", "required": False, "default": False},
                    {"name": "no-language-detect", "help": "Disable language detection in parser", "required": False, "default": False},
                    {"name": "csv", "help": "Export results to CSV file", "required": False, "default": None}
                ]
            }
        }
    },
    "/util": {
        "handler": "handle_util",
        "description": "Utility commands",
        "help": "/util <subcommand> [args] [options]  - Utility commands",
        "subcommands": {
            "llm": {
                "handler": "handle_util_llm",
                "description": "Test LLM configuration",
                "help": "/util llm [prompt]  - Test LLM with optional prompt",
                "args": [
                    {"name": "prompt", "help": "Test prompt to send to LLM (optional)", "required": False}
                ]
            },
            "inspect": {
                "handler": "handle_util_inspect",
                "description": "Inspect and display an ADR",
                "help": "/util inspect <path> [options]  - View ADR with formatting",
                "args": [
                    {"name": "path", "help": "Path to ADR file", "required": True}
                ],
                "options": [
                    {"name": "metadata", "help": "Show metadata alongside ADR", "required": False, "default": False},
                    {"name": "raw", "help": "Show raw content without Markdown formatting", "required": False, "default": False},
                    {"name": "width", "help": "Set display width", "required": False, "default": None}
                ]
            },
            "list": {
                "handler": "handle_util_list",
                "description": "List ADRs with enhanced features",
                "help": "/util list [path] [options]  - List ADRs with filtering and details",
                "args": [
                    {"name": "path", "help": "Path to ADR file or directory (optional)", "required": False}
                ],
                "options": [
                    {"name": "has-metadata", "help": "Show only ADRs that have metadata", "required": False, "default": False},
                    {"name": "details", "help": "Show detailed information (title, status, topic, classifications)", "required": False, "default": False},
                    {"name": "compact", "help": "Show compact list (filenames only)", "required": False, "default": False}
                ]
            }
        }
    },
    "/summary": {
        "handler": "handle_summary",
        "description": "Generate summaries and insights",
        "help": "/summary <path> [options]  - Generate ADR summaries and insights",
        "args": [
            {"name": "path", "help": "Path to ADR file or directory", "required": True}
        ],
        "options": [
            {"name": "output-summary", "help": "Export summary report to Markdown file", "required": False, "default": None},
            {"name": "output-detailed", "help": "Export detailed report with insights to Markdown file", "required": False, "default": None},
            {"name": "verbose", "help": "Show detailed output", "required": False, "default": False},
            {"name": "force-rewrite", "help": "Regenerate all summaries (ignore cached files)", "required": False, "default": False}
        ]
    }
}


def get_command_info(command: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a command.
    
    Args:
        command: Command name (e.g., "/topics")
        
    Returns:
        Command metadata or None if not found
    """
    return COMMAND_REGISTRY.get(command)


def get_subcommand_info(command: str, subcommand: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a subcommand.
    
    Args:
        command: Command name (e.g., "/topics")
        subcommand: Subcommand name (e.g., "predict")
        
    Returns:
        Subcommand metadata or None if not found
    """
    cmd_info = COMMAND_REGISTRY.get(command)
    if not cmd_info:
        return None
    
    subcommands = cmd_info.get("subcommands", {})
    return subcommands.get(subcommand)


def list_commands() -> List[str]:
    """Get list of all available commands."""
    return list(COMMAND_REGISTRY.keys())


def list_subcommands(command: str) -> List[str]:
    """
    Get list of subcommands for a command.
    
    Args:
        command: Command name
        
    Returns:
        List of subcommand names
    """
    cmd_info = COMMAND_REGISTRY.get(command)
    if not cmd_info:
        return []
    
    subcommands = cmd_info.get("subcommands", {})
    return list(subcommands.keys())