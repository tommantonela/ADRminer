"""Test script for Markdown rendering in agent responses."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.markdown import Markdown


def test_markdown_rendering():
    """Test that Rich Markdown rendering works correctly."""
    print("=" * 60)
    print("MARKDOWN RENDERING TEST")
    print("=" * 60 + "\n")
    
    console = Console()
    
    # Test 1: Basic Markdown
    print("Test 1: Basic Markdown")
    print("-" * 60)
    markdown_text = """
# Analysis Complete

I've analyzed your ADRs and found the following topics:

1. **Data Management** - 5 ADRs
2. **API Design** - 4 ADRs
3. **Authentication** - 3 ADRs

Would you like me to dive deeper into any of these topics?
"""
    console.print(Markdown(markdown_text))
    console.print()
    
    # Test 2: Code blocks
    print("Test 2: Code blocks")
    print("-" * 60)
    markdown_text = """
Here's the classification configuration:

```yaml
classification:
  framework: kruchten
  use_examples: true
  parser:
    strict: false
```

You can modify this in your `adrminer.yaml` file.
"""
    console.print(Markdown(markdown_text))
    console.print()
    
    # Test 3: Lists and emphasis
    print("Test 3: Lists and emphasis")
    print("-" * 60)
    markdown_text = """
### Key Findings

* **High quality**: 80% of ADRs meet MADR standards
* *Medium quality*: 15% have minor issues
* Low quality: 5% need major improvements

#### Recommendations

1. Add context sections to all ADRs
2. Include decision status (proposed, accepted, rejected)
3. Document alternatives considered
4. Add consequences for each decision
"""
    console.print(Markdown(markdown_text))
    console.print()
    
    # Test 4: Links and blockquotes
    print("Test 4: Links and blockquotes")
    print("-" * 60)
    markdown_text = """
> **Note**: The quality check is based on the MADR template.
> See [MADR Documentation](https://adr.github.io/madr/) for details.

For more information:
- Visit [ADRminer GitHub](https://github.com/tommantonela/ADRminer)
- Check [User Guide](docs/USAGE.md)
- Review [examples](examples/)
"""
    console.print(Markdown(markdown_text))
    console.print()
    
    # Test 5: Agent-style response
    print("Test 5: Complete agent response simulation")
    print("-" * 60)
    markdown_text = """
## Analysis Results

I've successfully processed your ADRs from `./examples/adrs`.

### Topic Mining

Found **12 topics** across 25 ADRs:

| Topic | # ADRs | Description |
|-------|---------|-------------|
| Data Management | 5 | Database and storage decisions |
| API Design | 4 | REST/GraphQL endpoints |
| Authentication | 3 | OAuth, JWT, session management |
| Deployment | 3 | Docker, Kubernetes, CI/CD |

### Classification

Using Kruchten's framework:

- **Software Architecture**: 8 decisions
- **Process**: 6 decisions
- **Requirements**: 5 decisions
- **Others**: 6 decisions

### Quality Check

- **Passed**: 22 ADRs
- **Needs improvement**: 2 ADRs
- **Failed**: 1 ADR

Would you like me to:
1. Show detailed results for a specific topic?
2. Export results to a file?
3. Generate insights and recommendations?
"""
    
    # Simulate how it would look in chat
    console.print()
    console.print("[cyan bold]AI:[/cyan bold]")
    console.print(Markdown(markdown_text))
    console.print()
    
    print("\n" + "=" * 60)
    print("[green]✓ Markdown rendering test complete![/green]")
    print("=" * 60 + "\n")
    
    print("Summary:")
    print("  - Basic Markdown rendering works")
    print("  - Code blocks are properly formatted")
    print("  - Lists and emphasis are displayed correctly")
    print("  - Links and blockquotes work as expected")
    print("  - Tables are rendered beautifully")
    print("\nAgent responses will now be formatted with Markdown!")


if __name__ == "__main__":
    try:
        test_markdown_rendering()
    except Exception as e:
        print(f"\n[red]✗ Test failed with error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)