"""
Remediation Agent using Google ADK.

AI agent specialized in suggesting and validating infrastructure
remediation actions with safety assessment.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import google.genai as genai

logger = logging.getLogger(__name__)


class RemediationAgent:
    """
    AI agent for infrastructure remediation.
    
    Capabilities:
    - Suggest remediation actions based on diagnosis
    - Assess risk and impact of actions
    - Prioritize remediation steps
    - Validate remediation plans
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize remediation agent.
        
        Args:
            config: Agent configuration (model, temperature, etc.)
        """
        self.config = config
        self.model_name = config.get("model", "gemini-2.0-flash-exp")
        self.temperature = config.get("temperature", 0.1)  # Lower for safety
        self.max_tokens = config.get("max_tokens", 1500)
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        logger.info(f"Initialized RemediationAgent with model {self.model_name}")
    
    def _load_system_prompt(self) -> str:
        """Load the remediation agent system prompt."""
        prompt_file = Path(__file__).parent / "prompts" / "remediation.txt"
        
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                return f.read()
        
        # Default prompt if file doesn't exist
        return """You are an expert infrastructure remediation agent. Your role is to:

1. Suggest safe and effective remediation actions
2. Assess risk and impact of proposed actions
3. Prioritize remediation steps
4. Consider rollback strategies
5. Ensure minimal disruption to services

When suggesting remediations:
- Always prioritize safety and service availability
- Consider blast radius and potential side effects
- Suggest gradual approaches over aggressive changes
- Include rollback plans
- Validate against best practices

Respond in JSON format with:
{
    "recommended_actions": [
        {
            "action": "action_name",
            "priority": "immediate|high|medium|low",
            "risk_level": "low|medium|high|critical",
            "expected_impact": "description",
            "steps": [list of steps],
            "rollback_plan": "description",
            "estimated_duration": "duration string"
        }
    ],
    "confidence": 0.0-1.0,
    "safety_checks": [list of checks to perform],
    "precautions": [list of precautions]
}
"""
    
    async def suggest_remediation(
        self,
        diagnosis: Dict[str, Any],
        available_actions: List[str]
    ) -> Dict[str, Any]:
        """
        Suggest remediation actions based on diagnosis.
        
        Args:
            diagnosis: Diagnostic results
            available_actions: List of available remediation tools
        
        Returns:
            Remediation suggestions with risk assessment
        """
        logger.info("RemediationAgent generating remediation plan")
        
        # Prepare the remediation request
        prompt = self._build_remediation_prompt(diagnosis, available_actions)
        
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
            result["agent"] = "remediation"
            
            logger.info(f"Remediation plan generated: {len(result.get('recommended_actions', []))} actions")
            
            return result
            
        except Exception as e:
            logger.error(f"Remediation agent error: {str(e)}")
            return {
                "error": str(e),
                "recommended_actions": [],
                "confidence": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "remediation"
            }
    
    def _build_remediation_prompt(
        self,
        diagnosis: Dict[str, Any],
        available_actions: List[str]
    ) -> str:
        """Build the remediation prompt for the AI agent."""
        prompt_parts = ["# Infrastructure Remediation Request\n"]
        
        # Add diagnosis
        prompt_parts.append("## Diagnostic Results:")
        prompt_parts.append(json.dumps(diagnosis, indent=2))
        
        # Add available actions
        prompt_parts.append("\n## Available Remediation Actions:")
        for action in available_actions:
            prompt_parts.append(f"- {action}")
        
        prompt_parts.append("\n## Task:")
        prompt_parts.append("Based on the diagnostic results, suggest appropriate remediation actions.")
        prompt_parts.append("Prioritize safety and service availability. Include risk assessment and rollback plans.")
        
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
            if "recommended_actions" not in result:
                result["recommended_actions"] = []
            if "confidence" not in result:
                result["confidence"] = 0.5
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent response: {e}")
            logger.debug(f"Response text: {response_text}")
            
            return {
                "recommended_actions": [],
                "confidence": 0.3,
                "raw_response": response_text,
                "parse_error": str(e)
            }
    
    async def validate_action(
        self,
        action: Dict[str, Any],
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a proposed remediation action.
        
        Args:
            action: Proposed remediation action
            current_state: Current infrastructure state
        
        Returns:
            Validation results with safety assessment
        """
        logger.info(f"Validating action: {action.get('action')}")
        
        prompt = f"""# Remediation Action Validation

## Proposed Action:
{json.dumps(action, indent=2)}

## Current Infrastructure State:
{json.dumps(current_state, indent=2)}

## Task:
Validate this remediation action for safety and effectiveness.
Assess risks, potential side effects, and provide recommendations.

Respond in JSON format with:
{{
    "validation_result": "approved|rejected|needs_review",
    "risk_assessment": {{
        "risk_level": "low|medium|high|critical",
        "blast_radius": "description",
        "potential_side_effects": [list]
    }},
    "safety_concerns": [list],
    "recommendations": [list],
    "confidence": 0.0-1.0
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
            result["validated_action"] = action.get("action")
            
            return result
            
        except Exception as e:
            logger.error(f"Action validation error: {str(e)}")
            return {
                "validation_result": "rejected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def prioritize_actions(
        self,
        actions: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Prioritize multiple remediation actions.
        
        Args:
            actions: List of proposed actions
            constraints: Operational constraints (maintenance windows, etc.)
        
        Returns:
            Prioritized and ordered list of actions
        """
        logger.info(f"Prioritizing {len(actions)} remediation actions")
        
        prompt = f"""# Remediation Action Prioritization

## Proposed Actions:
{json.dumps(actions, indent=2)}

## Constraints:
{json.dumps(constraints or {}, indent=2)}

## Task:
Prioritize these remediation actions considering:
- Severity and impact
- Dependencies between actions
- Risk levels
- Resource requirements
- Operational constraints

Respond in JSON format with:
{{
    "prioritized_actions": [
        {{
            "action": "action_name",
            "priority_rank": 1,
            "rationale": "explanation",
            "dependencies": [list],
            "recommended_sequence": "description"
        }}
    ],
    "execution_plan": "overall strategy"
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
            return result.get("prioritized_actions", actions)
            
        except Exception as e:
            logger.error(f"Action prioritization error: {str(e)}")
            return actions  # Return original order on error