"""Simple standalone test for CLI command recommendation system metadata."""

import ast
import sys
from pathlib import Path

def parse_tools_metadata():
    """Parse tool metadata directly from source file."""
    print("=" * 60)
    print("STANDALONE TEST: Tool Metadata Parsing")
    print("=" * 60)
    
    # Read tools.py file
    tools_file = Path(__file__).parent.parent / "src" / "adrminer" / "agents" / "tools.py"
    
    with open(tools_file, 'r') as f:
        source = f.read()
    
    # Parse AST
    tree = ast.parse(source)
    
    # Find all function definitions
    tool_functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if it has @tool_metadata decorator
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if hasattr(decorator.func, 'id') and decorator.func.id == 'tool_metadata':
                        # Extract metadata
                        metadata = {}
                        for keyword in decorator.keywords:
                            if keyword.arg == 'related_commands':
                                # Parse list of strings
                                if isinstance(keyword.value, ast.List):
                                    metadata['related_commands'] = [
                                        elt.value for elt in keyword.value.elts
                                        if isinstance(elt, ast.Constant)
                                    ]
                            elif keyword.arg == 'description':
                                if isinstance(keyword.value, ast.Constant):
                                    metadata['description'] = keyword.value.value
                        
                        tool_functions.append({
                            'name': node.name,
                            'metadata': metadata
                        })
    
    print(f"\n✓ Found {len(tool_functions)} tools with @tool_metadata decorator:")
    print()
    
    all_have_commands = True
    for tool in tool_functions:
        name = tool['name']
        metadata = tool['metadata']
        commands = metadata.get('related_commands', [])
        description = metadata.get('description', 'N/A')
        
        has_commands = len(commands) > 0
        status = "✓" if has_commands else "✗"
        
        print(f"{status} {name}")
        print(f"   Description: {description}")
        print(f"   Related Commands ({len(commands)}):")
        for cmd in commands:
            print(f"     * {cmd}")
        print()
        
        all_have_commands = all_have_commands and has_commands
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total tools with metadata: {len(tool_functions)}")
    print(f"Tools with related commands: {sum(1 for t in tool_functions if len(t['metadata'].get('related_commands', [])) > 0)}")
    print()
    
    if all_have_commands:
        print("✓ All tools have related commands!")
        return True
    else:
        print("✗ Some tools are missing related commands")
        return False


def main():
    """Run standalone test."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "CLI Recommendation Metadata Test" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    success = parse_tools_metadata()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())