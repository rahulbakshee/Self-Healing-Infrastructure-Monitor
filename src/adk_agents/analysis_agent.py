"""
Analysis Agent using Google ADK.

AI agent specialized in root cause analysis, pattern detection,
and learning from historical incidents.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import google.genai as genai

logger = logging.getLogger(__name__)


class AnalysisAgent:
    """
    AI agent for infrastructure analysis and root cause determination.
    
    Capabilities:
    - Perform root cause analysis
    - Detect patterns in incidents
    - Learn from historical data
    - Predict potential issues
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize analysis agent.
        
        Args:
            config: Agent configuration (model, temperature, etc.)
        """
        self.config = config
        self.model_name = config.get("model", "gemini-2.0-flash-exp")
        self.temperature = config.get("temperature", 0.5)
        self.max_tokens = config.get("max_tokens", 3000)
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        logger.info(f"Initialized AnalysisAgent with model {self.model_name}")
    
    def _load_system_prompt(self) -> str:
        """Load the analysis agent system prompt."""
        prompt_file = Path(__file__).parent / "prompts" / "analysis.txt"
        
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                return f.read()
        
        # Default prompt if file doesn't exist
        return """You are an expert infrastructure analysis agent specializing in root cause analysis. Your role is to:

1. Perform deep root cause analysis of infrastructure incidents
2. Identify patterns and correlations across events
3. Learn from historical incidents
4. Predict potential future issues
5. Provide actionable insights

When analyzing incidents:
- Use the "5 Whys" technique to dig deep
- Consider multiple potential root causes
- Look for cascading failures
- Identify contributing factors
- Learn from similar past incidents
- Be thorough and evidence-based

Respond in JSON format with:
{
    "root_cause": {
        "primary": "primary cause description",
        "contributing_factors": [list],
        "confidence": 0.0-1.0
    },
    "timeline": [ordered events leading to incident],
    "impact_analysis": {
        "severity": "critical|high|medium|low",
        "affected_systems": [list],
        "user_impact": "description"
    },
    "patterns": [similar patterns from history],
    "preventive_measures": [list],
    "lessons_learned": [list]
}
"""
    
    async def analyze(
        self,
        incident: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive root cause analysis.
        
        Args:
            incident: Incident details to analyze
            historical_data: Historical incidents for pattern matching
        
        Returns:
            Analysis results with root cause and recommendations
        """
        logger.info("AnalysisAgent performing root cause analysis")
        
        # Prepare the analysis request
        prompt = self._build_analysis_prompt(incident, historical_data)
        
        try:
            # Call Gemini API
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt
            )
            
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
            )
            
            # Parse response
            result = self._parse_response(response.text)
            result["timestamp"] = datetime.utcnow().isoformat()
            result["agent"] = "analysis"
            
            logger.info(f"Analysis complete: confidence={result.get('root_cause', {}).get('confidence', 0)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis agent error: {str(e)}")
            return {
                "error": str(e),
                "root_cause": {"primary": "Unknown", "confidence": 0.0},
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "analysis"
            }
    
    def _build_analysis_prompt(
        self,
        incident: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Build the analysis prompt for the AI agent."""
        prompt_parts = ["# Root Cause Analysis Request\n"]
        
        # Add incident details
        prompt_parts.append("## Current Incident:")
        prompt_parts.append(json.dumps(incident, indent=2))
        
        # Add historical context if available
        if historical_data:
            prompt_parts.append("\n## Historical Incidents (for pattern matching):")
            # Limit to recent relevant incidents
            recent_incidents = historical_data[-5:] if len(historical_data) > 5 else historical_data
            prompt_parts.append(json.dumps(recent_incidents, indent=2))
        
        prompt_parts.append("\n## Task:")
        prompt_parts.append("Perform a thorough root cause analysis of this incident.")
        prompt_parts.append("Consider the timeline, symptoms, and any patterns from historical data.")
        prompt_parts.append("Provide specific, evidence-based conclusions.")
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the agent's JSON response."""
        try:
            # Try to extract JSON from response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            result = json.loads(response_text)
            
            # Ensure required fields
            if "root_cause" not in result:
                result["root_cause"] = {
                    "primary": "Unknown",
                    "contributing_factors": [],
                    "confidence": 0.5
                }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent response: {e}")
            logger.debug(f"Response text: {response_text}")
            
            return {
                "root_cause": {
                    "primary": "Parse error",
                    "confidence": 0.0
                },
                "raw_response": response_text,
                "parse_error": str(e)
            }
    
    async def detect_patterns(
        self,
        incidents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect patterns across multiple incidents.
        
        Args:
            incidents: List of incidents to analyze
        
        Returns:
            Pattern analysis results
        """
        logger.info(f"Detecting patterns across {len(incidents)} incidents")
        
        prompt = f"""# Pattern Detection Analysis

## Incidents to Analyze:
{json.dumps(incidents, indent=2)}

## Task:
Identify patterns, correlations, and common themes across these incidents.
Look for:
- Common root causes
- Temporal patterns
- Resource patterns
- Error patterns
- Environmental factors

Respond in JSON format with:
{{
    "patterns": [
        {{
            "pattern_type": "type",
            "description": "description",
            "frequency": "how often",
            "incidents_affected": [incident_ids],
            "confidence": 0.0-1.0
        }}
    ],
    "trends": [list of identified trends],
    "recommendations": [preventive recommendations]
}}
"""
        
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt
            )
            
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
            )
            
            result = self._parse_response(response.text)
            result["timestamp"] = datetime.utcnow().isoformat()
            result["incidents_analyzed"] = len(incidents)
            
            return result
            
        except Exception as e:
            logger.error(f"Pattern detection error: {str(e)}")
            return {
                "error": str(e),
                "patterns": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def predict_issues(
        self,
        current_state: Dict[str, Any],
        historical_patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Predict potential future issues based on current state and patterns.
        
        Args:
            current_state: Current infrastructure state
            historical_patterns: Known patterns from past incidents
        
        Returns:
            Predictions with confidence scores
        """
        logger.info("Predicting potential issues")
        
        prompt = f"""# Issue Prediction Analysis

## Current Infrastructure State:
{json.dumps(current_state, indent=2)}

## Historical Patterns:
{json.dumps(historical_patterns, indent=2)}

## Task:
Based on the current state and historical patterns, predict potential issues that might occur.
Consider:
- Current metrics trends
- Known failure patterns
- Resource utilization trajectories
- Environmental factors

Respond in JSON format with:
{{
    "predictions": [
        {{
            "issue_type": "type",
            "description": "what might happen",
            "probability": 0.0-1.0,
            "timeframe": "when it might occur",
            "indicators": [early warning signs],
            "preventive_actions": [what to do]
        }}
    ],
    "confidence": 0.0-1.0,
    "monitoring_recommendations": [what to watch]
}}
"""
        
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt
            )
            
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
            )
            
            result = self._parse_response(response.text)
            result["timestamp"] = datetime.utcnow().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Issue prediction error: {str(e)}")
            return {
                "error": str(e),
                "predictions": [],
                "confidence": 0.0,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def generate_report(
        self,
        incident: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> str:
        """
        Generate a comprehensive incident analysis report.
        
        Args:
            incident: Incident details
            analysis_results: Analysis results from various agents
        
        Returns:
            Formatted report as markdown string
        """
        logger.info("Generating incident analysis report")
        
        prompt = f"""# Generate Incident Report

## Incident Details:
{json.dumps(incident, indent=2)}

## Analysis Results:
{json.dumps(analysis_results, indent=2)}

## Task:
Generate a comprehensive, executive-friendly incident report in markdown format.
Include:
- Executive summary
- Timeline of events
- Root cause analysis
- Impact assessment
- Remediation actions taken
- Preventive measures
- Lessons learned

Format the report professionally and clearly.
"""
        
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt
            )
            
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,  # Lower temperature for consistent formatting
                    max_output_tokens=self.max_tokens
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Report generation error: {str(e)}")
            return f"# Incident Report\n\nError generating report: {str(e)}"