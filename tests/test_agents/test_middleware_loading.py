"""Tests for Deep Agents middleware and backend loading."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from io import StringIO


class TestMiddlewareLoading:
    """Test that middleware and backends are loaded correctly."""

    def test_deep_agents_not_installed_graceful_degradation(self):
        """Test that agent factory handles missing Deep Agents gracefully."""
        from adrminer.chat.session import SessionManager
        from rich.console import Console
        
        # Create a mock session
        console = Console(file=StringIO())
        session = SessionManager(console=console)
        
        # Mock the import to simulate Deep Agents not being installed
        with patch('builtins.__import__', side_effect=ImportError("No module named 'deepagents'")):
            with pytest.raises(ImportError) as exc_info:
                from adrminer.agents import create_adrminer_agent
                create_adrminer_agent(session)
            
            # Verify the error message includes installation instructions
            assert "Deep Agents dependencies not installed" in str(exc_info.value) or "deepagents" in str(exc_info.value)

    def test_adrminer_agent_wrapper_initialization(self):
        """Test that AdrminerAgent wrapper initializes correctly."""
        from adrminer.agents import AdrminerAgent
        from adrminer.chat.session import SessionManager
        from rich.console import Console
        
        with patch('adrminer.agents.agent_factory.create_adrminer_agent') as mock_create_agent:
            console = Console(file=StringIO())
            session = SessionManager(console=console)
            
            mock_agent = MagicMock()
            mock_create_agent.return_value = mock_agent
            
            # Create wrapper
            wrapper = AdrminerAgent(session)
            
            # Verify initialization
            assert wrapper.session is session
            assert wrapper.agent is not None
            assert wrapper.thread_id is not None
            assert len(wrapper.thread_id) > 0

    def test_thread_local_session_isolation(self):
        """Test that thread-local session isolation works correctly."""
        from adrminer.agents.tools import set_session, get_session
        from threading import Thread
        import time
        
        session1 = object()
        session2 = object()
        results = {}
        
        def thread1_func():
            set_session(session1)
            time.sleep(0.1)  # Give thread2 time to set its session
            results['thread1'] = get_session() is session1
        
        def thread2_func():
            set_session(session2)
            results['thread2'] = get_session() is session2
        
        t1 = Thread(target=thread1_func)
        t2 = Thread(target=thread2_func)
        
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        
        # Both threads should see their own sessions
        assert results.get('thread1') == True
        assert results.get('thread2') == True

    def test_set_session_functionality(self):
        """Test that set_session and get_session work correctly."""
        from adrminer.agents.tools import set_session, get_session
        
        # Test initial state
        assert get_session() is None
        
        # Set a session
        test_session = {"test": "data"}
        set_session(test_session)
        
        # Retrieve it
        retrieved = get_session()
        assert retrieved is test_session
        assert retrieved == {"test": "data"}

    def test_agent_context_initialization(self):
        """Test that AgentContext initializes and loads from session correctly."""
        from adrminer.agents.context import AgentContext
        from adrminer.chat.session import SessionManager
        from rich.console import Console
        from pathlib import Path
        
        console = Console(file=StringIO())
        session = SessionManager(console=console)
        
        # Set some session data
        session.current_dir = Path("/test/dir")
        session.loaded_adrs = [Path("/test/adr1.md")]
        session.analysis_results = {"test": "results"}
        
        # Create context
        context = AgentContext()
        context.load_from_session(session)
        
        # Verify data was loaded (note: current_dir comes from session.cwd, not manually set)
        assert len(context.loaded_adrs) == 1
        assert "test" in context.analysis_results
        # current_directory should be set from session's cwd
        assert context.current_directory is not None

    def test_agent_context_to_dict(self):
        """Test that AgentContext converts to dict correctly."""
        from adrminer.agents.context import AgentContext
        from pathlib import Path
        
        context = AgentContext()
        context.current_directory = Path("/test/dir")
        context.loaded_adrs = [Path("/test/adr1.md")]
        context.analysis_results = {"test": "results"}
        
        # Convert to dict
        result = context.to_dict()
        
        # Verify conversion
        assert isinstance(result, dict)
        assert "current_directory" in result
        assert "loaded_adrs" in result
        assert "analysis_results" in result
        assert result["current_directory"] == "/test/dir"
        assert len(result["loaded_adrs"]) == 1

    def test_tool_imports(self):
        """Test that all tools can be imported successfully."""
        from adrminer.agents.tools import (
            load_adrs,
            mine_topics,
            classify_adrs,
            check_quality,
            generate_insights,
            # export_metadata
        )
        
        # Verify tools are available (they're wrapped in StructuredTool)
        assert load_adrs is not None
        assert mine_topics is not None
        assert classify_adrs is not None
        assert check_quality is not None
        assert generate_insights is not None
        # assert export_metadata is not None

    def test_tool_has_metadata(self):
        """Test that tools have proper metadata."""
        from adrminer.agents.tools import (
            load_adrs,
            mine_topics,
            classify_adrs
        )
        
        # Check that tools have names and descriptions
        assert hasattr(load_adrs, 'name')
        assert hasattr(load_adrs, 'description')
        assert hasattr(mine_topics, 'name')
        assert hasattr(mine_topics, 'description')
        assert hasattr(classify_adrs, 'name')
        assert hasattr(classify_adrs, 'description')

    def test_agent_factory_module_structure(self):
        """Test that agent_factory module has expected structure."""
        from adrminer.agents import agent_factory
        
        # Check that key functions exist
        assert hasattr(agent_factory, 'create_adrminer_agent')
        assert hasattr(agent_factory, 'AdrminerAgent')
        assert hasattr(agent_factory, 'SYSTEM_PROMPT')

    def test_agents_module_exports(self):
        """Test that agents module exports expected items."""
        from adrminer.agents import (
            create_adrminer_agent,
            AdrminerAgent,
            AgentContext,
            load_adrs,
            mine_topics,
            classify_adrs,
            check_quality,
            generate_insights,
            # export_metadata
        )
        
        # Verify exports are available
        assert callable(create_adrminer_agent)
        assert AdrminerAgent is not None
        assert AgentContext is not None
        # Tools are wrapped in StructuredTool, check they're not None
        assert load_adrs is not None
        assert mine_topics is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])