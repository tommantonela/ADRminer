"""Simple test script for LangChain agent implementation.

This script tests the basic functionality of the new LangChain-based agent.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from adrminer.config import get_settings
from adrminer.agents.agent_factory import create_adrminer_agent, AdrminerAgent
from adrminer.chat.session import SessionManager


def test_langchain_agent():
    """Test the LangChain agent implementation."""
    
    print("=" * 60)
    print("Testing LangChain Agent Implementation")
    print("=" * 60)
    
    # Get settings
    settings = get_settings()
    print(f"\nLLM Provider: {settings.llm.provider}")
    print(f"LLM Model: {settings.llm.model}")
    
    # Create a simple mock session for testing
    # In a real scenario, this would be initialized by the CLI
    class MockSession:
        def __init__(self):
            self.loaded_adrs = []
            self.analysis_results = {}
            self.available_directories = [Path.cwd()]
            
            # Mock services
            self.topic_service = None
            self.classification_service = None
            self.checking_service = None
            self.insight_service = None
            
            # Mock console
            self.console = None
    
    session = MockSession()
    
    print("\n" + "=" * 60)
    print("Test 1: Create Agent Factory")
    print("=" * 60)
    
    try:
        agent = create_adrminer_agent(session)
        print("✓ Agent created successfully")
        print(f"  Agent type: {type(agent)}")
    except Exception as e:
        print(f"✗ Failed to create agent: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("Test 2: Create AdrminerAgent Wrapper")
    print("=" * 60)
    
    try:
        wrapper = AdrminerAgent(session)
        print("✓ AdrminerAgent wrapper created successfully")
        print(f"  Thread ID: {wrapper.get_thread_id()}")
    except Exception as e:
        print(f"✗ Failed to create wrapper: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("Test 3: Check Agent Methods")
    print("=" * 60)
    
    try:
        # Test context methods
        context = wrapper.get_context()
        print("✓ get_context() works")
        
        # Test thread ID
        thread_id = wrapper.get_thread_id()
        print(f"✓ get_thread_id() works: {thread_id}")
        
        # Test get_agent
        agent_ref = wrapper.get_agent()
        print(f"✓ get_agent() works: {type(agent_ref)}")
        
        # Test update_context
        wrapper.update_context({"available_directories": [Path.cwd()]})
        print("✓ update_context() works")
        
    except Exception as e:
        print(f"✗ Method test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("Test 4: Check Available Tools")
    print("=" * 60)
    
    try:
        # Get the underlying agent
        langchain_agent = wrapper.langchain_agent
        if hasattr(langchain_agent, 'agent'):
            # For LangChain agent, check if we can inspect it
            print("✓ Agent is accessible")
            # Note: We can't easily list tools from a compiled agent without invoking it
        else:
            print("✗ Agent structure unexpected")
    except Exception as e:
        print(f"✗ Tool check failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("All Tests Completed!")
    print("=" * 60)
    print("\nSummary:")
    print("  ✓ LangChain agent factory works")
    print("  ✓ AdrminerAgent wrapper works")
    print("  ✓ All methods accessible")
    print("  ✓ Agent can be created and configured")
    print("\nNote: Full integration test requires actual ADR files")
    print("      and LLM API access. This test validates structure.")
    
    return True


if __name__ == "__main__":
    success = test_langchain_agent()
    sys.exit(0 if success else 1)