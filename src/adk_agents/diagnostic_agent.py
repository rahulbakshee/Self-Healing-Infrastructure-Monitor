"""
Diagnostic Agent using Google ADK.

AI agent specialized in diagnosing infrastructure issues,
analyzing metrics, and identifying anomalies.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import google.genai as genai

logger = logging.getLogger(__name__)


class DiagnosticAgent:
    """
    AI agent for infrastructure diagnostics.
    
    Capabilities:
    - Analyze metrics and identify anomalies
    - Detect performance issues
    - Identify resource bottlenecks
    - Assess system health
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize diagnostic agent.
        
        Args:
            config: Agent configuration (model, temperature, etc.)
        """
        self.config = config
        self.model_name = config.get("model", "gemini-2.0-flash-exp")
        self.temperature = config.get("temperature", 0.3)
        self.max_tokens = config.get("max_tokens", 2000)
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        logger.info(f"Initialized DiagnosticAgent with model {self.model_name}")
    
    def _load_system_prompt(self) -> str:
        """Load the diagnostic agent system prompt."""
        prompt_file = Path(__file__).parent / "prompts" / "diagnostic.txt"
        
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                return f.read()
        
        # Default prompt if file doesn't exist
        return """You are an expert infrastructure diagnostic agent. Your role is to:

1. Analyze infrastructure metrics, logs, and system state
2. Identify anomalies, performance issues, and potential failures
3. Assess the severity and impact of issues
4. Provide clear, actionable diagnostic findings

When analyzing issues:
- Consider baseline metrics vs current metrics
- Look for patterns and correlations
- Assess impact on users and business
- Prioritize based on severity
- Be specific and provide evidence

Respond in JSON format with:
{
    "severity": "critical|high|medium|low",
    "confidence": 0.0-1.0,
    "findings": [list of specific findings],
    "affected_resources": [list of resources],
    "impact_assessment": "description of impact",
    "recommendations": [list of next steps]
}
"""
    
    async def diagnose(
        self,
        symptoms: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Diagnose infrastructure issues based on symptoms.
        
        Args:
            symptoms: Observed symptoms (metrics, errors, etc.)
            context: Additional context (logs, historical data, etc.)
        
        Returns:
            Diagnostic results with findings and recommendations
        """
        logger.info("DiagnosticAgent analyzing issue")
        
        # Prepare the diagnostic request
        prompt = self._build_diagnostic_prompt(symptoms, context)
        
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
            result["agent"] = "diagnostic"
            
            logger.info(f"Diagnosis complete: severity={result.get('severity')}, confidence={result.get('confidence')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Diagnostic agent error: {str(e)}")
            return {
                "error": str(e),
                "severity": "unknown",
                "confidence": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "diagnostic"
            }
    
    def _build_diagnostic_prompt(
        self,
        symptoms: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the diagnostic prompt for the AI agent."""
        prompt_parts = ["# Infrastructure Diagnostic Request\n"]
        
        # Add symptoms
        prompt_parts.append("## Observed Symptoms:")
        prompt_parts.append(json.dumps(symptoms, indent=2))
        
        # Add context if available
        if context:
            prompt_parts.append("\n## Additional Context:")
            
            if "metrics" in context:
                prompt_parts.append("\n### Metrics:")
                prompt_parts.append(json.dumps(context["metrics"], indent=2))
            
            if "logs" in context:
                prompt_parts.append("\n### Recent Logs:")
                prompt_parts.append(json.dumps(context["logs"], indent=2))
            
            if "infrastructure" in context:
                prompt_parts.append("\n### Infrastructure State:")
                prompt_parts.append(json.dumps(context["infrastructure"], indent=2))
            
            if "thresholds" in context:
                prompt_parts.append("\n### Alert Thresholds:")
                prompt_parts.append(json.dumps(context["thresholds"], indent=2))
        
        prompt_parts.append("\n## Task:")
        prompt_parts.append("Analyze the above information and provide a comprehensive diagnostic assessment.")
        prompt_parts.append("Focus on identifying the root cause and assessing the impact.")
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the agent's JSON response."""
        try:
            # Try to extract JSON from response
            # Handle cases where model adds markdown code blocks
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
            if "severity" not in result:
                result["severity"] = "medium"
            if "confidence" not in result:
                result["confidence"] = 0.5
            if "findings" not in result:
                result["findings"] = []
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent response: {e}")
            logger.debug(f"Response text: {response_text}")
            
            # Return a structured response even if parsing fails
            return {
                "severity": "medium",
                "confidence": 0.3,
                "findings": ["Error parsing agent response"],
                "raw_response": response_text,
                "parse_error": str(e)
            }
    
    async def analyze_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze specific metrics for anomalies.
        
        Args:
            metrics: Metrics data to analyze
        
        Returns:
            Analysis results
        """
        symptoms = {
            "type": "metrics_analysis",
            "data": metrics
        }
        
        return await self.diagnose(symptoms, {"metrics": metrics})
    
    async def analyze_errors(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze error patterns.
        
        Args:
            errors: List of error records
        
        Returns:
            Error pattern analysis
        """
        symptoms = {
            "type": "error_analysis",
            "error_count": len(errors),
            "sample_errors": errors[:10]  # Send first 10 errors
        }
        
        return await self.diagnose(symptoms, {"logs": {"errors": errors}})
    
    async def assess_health(
        self,
        health_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess overall infrastructure health.
        
        Args:
            health_data: Health metrics and status
        
        Returns:
            Health assessment
        """
        symptoms = {
            "type": "health_assessment",
            "data": health_data
        }
        
        context = {
            "metrics": health_data.get("metrics", {}),
            "infrastructure": health_data.get("infrastructure", {})
        }
        
        return await self.diagnose(symptoms, context)