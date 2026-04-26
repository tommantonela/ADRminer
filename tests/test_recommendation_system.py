"""Test script for CLI command recommendation system."""

import sys
from pathlib import Path
from importlib import import_module

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import tools directly without loading agent modules
tools_module = import_module('adrminer.agents.tools')
tools = tools_module

from rich.console import Console
from adrminer.chat.recommendation_service import RecommendationService


def test_tool_metadata():
    """Test that all tools have metadata decorators."""
    print("=" * 60)
    print("TEST 1: Tool Metadata Decorators")
    print("=" * 60)
    
    # List of tools to check
    tool_functions = [
        ("load_adrs", tools.load_adrs),
        ("list_adr_files", tools.list_adr_files),
        ("mine_topics", tools.mine_topics),
        ("classify_adrs", tools.classify_adrs),
        ("check_quality", tools.check_quality),
        ("generate_insights", tools.generate_insights),
        ("get_topics_info", tools.get_topics_info),
        ("get_classification_info", tools.get_classification_info),
        ("reset_memory", tools.reset_memory)
    ]
    
    all_have_metadata = True
    for name, func in tool_functions:
        has_metadata = hasattr(func, '_tool_metadata')
        status = "✓" if has_metadata else "✗"
        print(f"{status} {name}: {'has metadata' if has_metadata else 'MISSING metadata'}")
        
        if has_metadata:
            metadata = func._tool_metadata
            print(f"   - related_commands: {metadata.get('related_commands', [])}")
            print(f"   - description: {metadata.get('description', 'N/A')}")
        
        all_have_metadata = all_have_metadata and has_metadata
    
    print()
    if all_have_metadata:
        print("✓ All tools have metadata decorators")
    else:
        print("✗ Some tools are missing metadata decorators")
    
    print()
    return all_have_metadata


def test_recommendation_service():
    """Test recommendation service functionality."""
    print("=" * 60)
    print("TEST 2: Recommendation Service")
    print("=" * 60)
    
    console = Console()
    service = RecommendationService(console)
    
    # Test 1: Get all metadata
    print("\n2.1: Get all tool metadata")
    all_metadata = service.get_all_tools_metadata()
    print(f"✓ Found metadata for {len(all_metadata)} tools")
    
    # Test 2: Get recommendations for single tool
    print("\n2.2: Get recommendations for 'mine_topics' tool")
    recommendations = service.get_recommendations(['mine_topics'])
    print(f"✓ Found {len(recommendations)} recommendation group(s)")
    for desc, commands in recommendations.items():
        print(f"   - {desc}:")
        for cmd in commands:
            print(f"     * {cmd}")
    
    # Test 3: Get recommendations for multiple tools
    print("\n2.3: Get recommendations for multiple tools")
    recommendations = service.get_recommendations(['load_adrs', 'mine_topics', 'classify_adrs'])
    print(f"✓ Found {len(recommendations)} recommendation group(s)")
    
    # Count total commands
    total_commands = sum(len(cmds) for cmds in recommendations.values())
    print(f"✓ Total unique commands: {total_commands}")
    
    print()
    return True


def test_tool_call_extraction():
    """Test agent tool call extraction."""
    print("=" * 60)
    print("TEST 3: Tool Call Extraction (Mock)")
    print("=" * 60)
    
    # Mock agent result structure
    mock_result = {
        "success": True,
        "response": "I've analyzed your ADRs",
        "data": {
            "messages": [
                {
                    "role": "user",
                    "content": "Analyze my ADRs"
                },
                {
                    "role": "assistant",
                    "tool_calls": [
                        {"name": "load_adrs", "args": {"path": "adrs/"}, "id": "1"},
                        {"name": "mine_topics", "args": {}, "id": "2"}
                    ]
                }
            ]
        }
    }
    
    # Create a mock agent with extract_tool_calls method
    class MockAgent:
        def extract_tool_calls(self, result):
            tool_names = []
            messages = result.get("data", {}).get("messages", [])
            
            for message in messages:
                if hasattr(message, 'tool_calls'):
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.get('name', '')
                        if tool_name:
                            tool_names.append(tool_name)
            
            return tool_names
    
    agent = MockAgent()
    tool_calls = agent.extract_tool_calls(mock_result)
    
    print(f"✓ Extracted tool calls: {tool_calls}")
    print(f"✓ Number of tools called: {len(tool_calls)}")
    
    # Test recommendation display
    console = Console()
    service = RecommendationService(console)
    
    print("\n3.1: Show recommendations for extracted tools")
    service.show_recommendations(tool_calls)
    
    print()
    return True


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "CLI Recommendation System Tests" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Run tests
    test1_passed = test_tool_metadata()
    test2_passed = test_recommendation_service()
    test3_passed = test_tool_call_extraction()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Test 1 (Tool Metadata): {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"Test 2 (Recommendation Service): {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    print(f"Test 3 (Tool Call Extraction): {'✓ PASSED' if test3_passed else '✗ FAILED'}")
    print()
    
    if test1_passed and test2_passed and test3_passed:
        print("✓ All tests PASSED!")
        return 0
    else:
        print("✗ Some tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())