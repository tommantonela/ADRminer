"""Deep Agents integration for ADRminer.

This module provides natural language-based exploration of ADRs
through a Deep Agent that interprets user queries and invokes
appropriate ADRminer services.
"""

from adrminer.agents.agent_factory import create_adrminer_agent, AdrminerAgent
from adrminer.agents.context import AgentContext
from adrminer.agents.tools import (
    load_adrs,
    mine_topics,
    classify_adrs,
    check_quality,
    generate_insights,
    # export_metadata
)

__all__ = [
    "create_adrminer_agent",
    "AdrminerAgent",
    "AgentContext",
    "load_adrs",
    "mine_topics",
    "classify_adrs",
    "check_quality",
    "generate_insights",
    # "export_metadata"
]
