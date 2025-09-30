"""ADK Agent factory

Create agent instances by type. Minimal stub for diagnostics, remediation, analysis agents.
"""
from typing import Any, Optional

from .diagnostic_agent import DiagnosticAgent
from .remediation_agent import RemediationAgent
from .analysis_agent import AnalysisAgent


def create_agent(agent_type: str, config: Optional[dict] = None, client: Optional[Any] = None):
    """Return an agent instance for the requested agent_type.

    Args:
        agent_type: one of "diagnostic", "remediation", "analysis".
        config: optional dict of configuration values.
        client: optional ADK/LLM client wrapper.
    """
    mapping = {
        "diagnostic": DiagnosticAgent,
        "remediation": RemediationAgent,
        "analysis": AnalysisAgent,
    }

    cls = mapping.get(agent_type.lower())
    if cls is None:
        raise ValueError(f"Unknown agent_type: {agent_type}")

    return cls(config=config or {}, client=client)
