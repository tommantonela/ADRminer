"""Command parser for interactive chat CLI."""

from typing import Tuple, Dict, List, Optional, Any
from pathlib import Path

from adrminer.chat.commands import (
    get_command_info,
    get_subcommand_info,
    COMMAND_REGISTRY
)


class CommandParseError(Exception):
    """Exception raised when command parsing fails."""
    pass


class CommandParser:
    """Parse user input into command components."""
    
    def __init__(self):
        """Initialize command parser."""
        pass
    
    def parse(self, user_input: str) -> Dict[str, Any]:
        """
        Parse user input into command components.
        
        Args:
            user_input: Raw user input string
            
        Returns:
            Dictionary with parsed components:
            {
                "command": str,  # e.g., "/topics"
                "subcommand": Optional[str],  # e.g., "predict"
                "args": List[str],  # Positional arguments
                "options": Dict[str, Any],  # Key-value options
                "raw": str  # Original input
            }
            
        Raises:
            CommandParseError: If parsing fails
        """
        user_input = user_input.strip()
        
        if not user_input:
            raise CommandParseError("Empty input")
        
        # Split into tokens
        tokens = self._tokenize(user_input)
        
        if not tokens:
            raise CommandParseError("Empty input")
        
        # Check if it's a command (starts with /)
        if not tokens[0].startswith("/"):
            raise CommandParseError("Commands must start with /")
        
        # Extract command
        command = tokens[0].lower()
        
        # Validate command exists
        if command not in COMMAND_REGISTRY:
            available = ", ".join(sorted(COMMAND_REGISTRY.keys()))
            raise CommandParseError(
                f"Unknown command: {command}\n"
                f"Available commands: {available}"
            )
        
        # Parse remaining tokens
        remaining_tokens = tokens[1:]
        
        # Check if command has subcommands
        cmd_info = get_command_info(command)
        has_subcommands = "subcommands" in cmd_info and cmd_info["subcommands"]
        
        subcommand = None
        args = []
        options = {}
        
        if has_subcommands:
            # First token should be subcommand
            if remaining_tokens and not remaining_tokens[0].startswith("-"):
                subcommand = remaining_tokens[0].lower()
                remaining_tokens = remaining_tokens[1:]
                
                # Validate subcommand
                if subcommand not in cmd_info["subcommands"]:
                    available = ", ".join(sorted(cmd_info["subcommands"].keys()))
                    raise CommandParseError(
                        f"Unknown subcommand: {subcommand}\n"
                        f"Available subcommands for {command}: {available}"
                    )
            else:
                # No subcommand provided
                available = ", ".join(sorted(cmd_info["subcommands"].keys()))
                raise CommandParseError(
                    f"{command} requires a subcommand\n"
                    f"Available subcommands: {available}"
                )
        else:
            # No subcommands, all remaining tokens are args/options
            pass
        
        # Parse args and options
        subcmd_info = get_subcommand_info(command, subcommand) if subcommand else cmd_info
        
        if subcmd_info:
            # Get expected args and options
            expected_args = subcmd_info.get("args", [])
            expected_options = subcmd_info.get("options", [])
            
            # Parse remaining tokens
            args, options = self._parse_args_options(
                remaining_tokens,
                expected_args,
                expected_options
            )
        else:
            # No specific args/options defined, parse generically
            args, options = self._parse_generic(remaining_tokens)
        
        return {
            "command": command,
            "subcommand": subcommand,
            "args": args,
            "options": options,
            "raw": user_input
        }
    
    def _tokenize(self, input_str: str) -> List[str]:
        """
        Tokenize input string, respecting quotes.
        
        Args:
            input_str: Input string to tokenize
            
        Returns:
            List of tokens
        """
        tokens = []
        current_token = []
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(input_str):
            char = input_str[i]
            
            if char in ('"', "'"):
                if not in_quotes:
                    # Start quoted string
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    # End quoted string
                    in_quotes = False
                    quote_char = None
                else:
                    # Different quote char, include it
                    current_token.append(char)
            elif char in (' ', '\t'):
                if in_quotes:
                    # Space in quotes, include it
                    current_token.append(char)
                elif current_token:
                    # End of token
                    tokens.append(''.join(current_token))
                    current_token = []
            else:
                # Regular character
                current_token.append(char)
            
            i += 1
        
        # Add last token
        if current_token:
            tokens.append(''.join(current_token))
        
        return tokens
    
    def _parse_args_options(
        self,
        tokens: List[str],
        expected_args: List[Dict[str, Any]],
        expected_options: List[Dict[str, Any]]
    ) -> Tuple[List[str], Dict[str, Any]]:
        """
        Parse tokens into args and options based on expected structure.
        
        Args:
            tokens: Remaining tokens after command/subcommand
            expected_args: Expected positional arguments
            expected_options: Expected options
            
        Returns:
            Tuple of (args, options)
        """
        args = []
        options = {}
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token.startswith("--"):
                # Long option
                option_name = token[2:]
                
                # Check if valid option
                if not any(opt["name"] == option_name for opt in expected_options):
                    raise CommandParseError(f"Unknown option: --{option_name}")
                
                # Get option value
                option_def = next(opt for opt in expected_options if opt["name"] == option_name)
                
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    # Option has value
                    option_value = tokens[i + 1]
                    # Convert type if needed
                    option_value = self._convert_option_value(
                        option_name,
                        option_value,
                        option_def.get("default")
                    )
                    options[option_name] = option_value
                    i += 2
                else:
                    # Boolean flag
                    options[option_name] = True
                    i += 1
            
            elif token.startswith("-"):
                # Short option (not fully implemented for now)
                # For now, treat as unknown option
                raise CommandParseError(
                    f"Short options not supported yet: {token}\n"
                    f"Use long options: --{token[1:]}"
                )
            
            else:
                # Positional argument
                if len(args) < len(expected_args):
                    args.append(token)
                    i += 1
                else:
                    # Too many arguments
                    raise CommandParseError(
                        f"Unexpected argument: {token}\n"
                        f"Expected {len(expected_args)} argument(s), got more"
                    )
        
        # Check for missing required args
        for i, arg_def in enumerate(expected_args):
            if i >= len(args) and arg_def.get("required", True):
                raise CommandParseError(
                    f"Missing required argument: {arg_def['name']}\n"
                    f"Usage: {self._get_usage(arg_def)}"
                )
        
        return args, options
    
    def _parse_generic(self, tokens: List[str]) -> Tuple[List[str], Dict[str, Any]]:
        """
        Parse tokens without expected structure.
        
        Args:
            tokens: Tokens to parse
            
        Returns:
            Tuple of (args, options)
        """
        args = []
        options = {}
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token.startswith("--"):
                # Option
                option_name = token[2:]
                
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    options[option_name] = tokens[i + 1]
                    i += 2
                else:
                    options[option_name] = True
                    i += 1
            else:
                # Argument
                args.append(token)
                i += 1
        
        return args, options
    
    def _convert_option_value(
        self,
        option_name: str,
        value: str,
        default: Any
    ) -> Any:
        """
        Convert option value to appropriate type.
        
        Args:
            option_name: Name of the option
            value: String value to convert
            default: Default value to infer type from
            
        Returns:
            Converted value
        """
        # Try to infer type from default
        if default is not None:
            if isinstance(default, bool):
                return value.lower() in ('true', '1', 'yes', 'y')
            elif isinstance(default, int):
                try:
                    return int(value)
                except ValueError:
                    raise CommandParseError(
                        f"Invalid integer value for --{option_name}: {value}"
                    )
            elif isinstance(default, float):
                try:
                    return float(value)
                except ValueError:
                    raise CommandParseError(
                        f"Invalid float value for --{option_name}: {value}"
                    )
        
        # Default to string
        return value
    
    def _get_usage(self, arg_def: Dict[str, Any]) -> str:
        """
        Get usage string for an argument.
        
        Args:
            arg_def: Argument definition
            
        Returns:
            Usage string
        """
        return f"<{arg_def['name']}>  - {arg_def['help']}"