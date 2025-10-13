"""
Agent Factory for ADK Integration.

Creates and manages AI agents for infrastructure monitoring and remediation.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import google.genai as genai

from .diagnostic_agent import DiagnosticAgent
from .remediation_agent import RemediationAgent
from .analysis_agent import AnalysisAgent

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating and managing ADK agents.
    
    Manages the lifecycle of:
    - Diagnostic Agent: Analyzes infrastructure issues
    - Remediation Agent: Suggests and validates fixes
    - Analysis Agent: Performs root cause analysis
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the agent factory.
        
        Args:
            config: ADK configuration including API keys and agent settings
        """
        self.config = config
        
        # Initialize Google GenAI client
        api_key = config.get("api", {}).get("key")
        if not api_key:
            raise ValueError("ADK API key is required. Set SHIM_ADK_API_KEY environment variable.")
        
        genai.configure(api_key=api_key)
        
        # Agent instances
        self._diagnostic_agent: Optional[DiagnosticAgent] = None
        self._remediation_agent: Optional[RemediationAgent] = None
        self._analysis_agent: Optional[AnalysisAgent] = None
        
        logger.info("Initialized AgentFactory")
    
    def get_diagnostic_agent(self) -> DiagnosticAgent:
        """
        Get or create the diagnostic agent.
        
        Returns:
            DiagnosticAgent instance
        """
        if self._diagnostic_agent is None:
            agent_config = self.config.get("agents", {}).get("diagnostic", {})
            self._diagnostic_agent = DiagnosticAgent(agent_config)
            logger.info("Created DiagnosticAgent")
        
        return self._diagnostic_agent
    
    def get_remediation_agent(self) -> RemediationAgent:
        """
        Get or create the remediation agent.
        
        Returns:
            RemediationAgent instance
        """
        if self._remediation_agent is None:
            agent_config = self.config.get("agents", {}).get("remediation", {})
            self._remediation_agent = RemediationAgent(agent_config)
            logger.info("Created RemediationAgent")
        
        return self._remediation_agent
    
    def get_analysis_agent(self) -> AnalysisAgent:
        """
        Get or create the analysis agent.
        
        Returns:
            AnalysisAgent instance
        """
        if self._analysis_agent is None:
            agent_config = self.config.get("agents", {}).get("analysis", {})
            self._analysis_agent = AnalysisAgent(agent_config)
            logger.info("Created AnalysisAgent")
        
        return self._analysis_agent
    
    async def diagnose_issue(
        self, 
        symptoms: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Use diagnostic agent to analyze an issue.
        
        Args:
            symptoms: Observed symptoms and metrics
            context: Additional context (logs, metrics, etc.)
        
        Returns:
            Diagnostic results with findings and recommendations
        """
        agent = self.get_diagnostic_agent()
        return await agent.diagnose(symptoms, context)
    
    async def suggest_remediation(
        self,
        diagnosis: Dict[str, Any],
        available_actions: list
    ) -> Dict[str, Any]:
        """
        Use remediation agent to suggest fixes.
        
        Args:
            diagnosis: Diagnostic results
            available_actions: List of available remediation actions
        
        Returns:
            Remediation suggestions with risk assessment
        """
        agent = self.get_remediation_agent()
        return await agent.suggest_remediation(diagnosis, available_actions)
    
    async def analyze_root_cause(
        self,
        incident: Dict[str, Any],
        historical_data: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Use analysis agent for root cause analysis.
        
        Args:
            incident: Incident details
            historical_data: Historical incidents for pattern matching
        
        Returns:
            Root cause analysis with confidence scores
        """
        agent = self.get_analysis_agent()
        return await agent.analyze(incident, historical_data)
    
    async def multi_agent_analysis(
        self,
        issue: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordinate multiple agents for comprehensive analysis.
        
        Args:
            issue: Issue to analyze
        
        Returns:
            Comprehensive analysis from all agents
        """
        logger.info("Starting multi-agent analysis")
        
        # Step 1: Diagnostic agent analyzes the issue
        diagnostic_result = await self.diagnose_issue(
            symptoms=issue.get("symptoms", {}),
            context=issue.get("context", {})
        )
        
        # Step 2: Analysis agent performs root cause analysis
        analysis_result = await self.analyze_root_cause(
            incident=issue,
            historical_data=issue.get("historical_data")
        )
        
        # Step 3: Remediation agent suggests fixes
        remediation_result = await self.suggest_remediation(
            diagnosis={
                "diagnostic": diagnostic_result,
                "analysis": analysis_result
            },
            available_actions=issue.get("available_actions", [])
        )
        
        return {
            "diagnostic": diagnostic_result,
            "root_cause_analysis": analysis_result,
            "remediation": remediation_result,
            "timestamp": diagnostic_result.get("timestamp"),
            "confidence": self._calculate_overall_confidence(
                diagnostic_result,
                analysis_result,
                remediation_result
            )
        }
    
    def _calculate_overall_confidence(
        self,
        diagnostic: Dict[str, Any],
        analysis: Dict[str, Any],
        remediation: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence score from all agents."""
        diagnostic_conf = diagnostic.get("confidence", 0.5)
        analysis_conf = analysis.get("confidence", 0.5)
        remediation_conf = remediation.get("confidence", 0.5)
        
        # Weighted average (analysis gets more weight)
        return (diagnostic_conf * 0.3 + analysis_conf * 0.4 + remediation_conf * 0.3)
    
    def shutdown(self) -> None:
        """Cleanup and shutdown all agents."""
        logger.info("Shutting down AgentFactory")
        self._diagnostic_agent = None
        self._remediation_agent = None
        self._analysis_agent = None


def load_adk_config(config_path: str = "config/adk_config.yaml") -> Dict[str, Any]:
    """
    Load ADK configuration from file.
    
    Args:
        config_path: Path to ADK config file
    
    Returns:
        Configuration dictionary
    """
    import yaml
    import os
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.warning(f"ADK config file not found: {config_path}, using defaults")
        return {
            "agents": {
                "diagnostic": {
                    "model": "gemini-2.0-flash-exp",
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                "remediation": {
                    "model": "gemini-2.0-flash-exp",
                    "temperature": 0.1,
                    "max_tokens": 1500
                },
                "analysis": {
                    "model": "gemini-2.0-flash-exp",
                    "temperature": 0.5,
                    "max_tokens": 3000
                }
            },
            "api": {
                "key": os.getenv("SHIM_ADK_API_KEY"),
                "timeout": 60
            }
        }
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables
    if "api" not in config:
        config["api"] = {}
    
    if "key" not in config["api"]:
        config["api"]["key"] = os.getenv("SHIM_ADK_API_KEY")
    
    return config