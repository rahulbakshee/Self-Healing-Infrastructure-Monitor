"""
Remediation Tool for MCP Server.

Provides tools for automatically remediating infrastructure issues
with safety guardrails and approval workflows.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from mcp.types import Tool
import asyncio

logger = logging.getLogger(__name__)


class RemediationTool:
    """
    Remediation tools for infrastructure self-healing.
    
    Provides automatic remediation capabilities with:
    - Safety checks
    - Approval workflows
    - Rollback support
    - Audit logging
    """
    
    def __init__(self, config: Any):
        """Initialize remediation tool with configuration."""
        self.config = config
        self.require_approval = config.require_approval if hasattr(config, 'require_approval') else True
        self.max_retries = config.max_retries if hasattr(config, 'max_retries') else 3
        self.rollback_on_failure = config.rollback_on_failure if hasattr(config, 'rollback_on_failure') else True
        self.allowed_actions = config.allowed_actions if hasattr(config, 'allowed_actions') else []
        
        # Track remediation history
        self.remediation_history: List[Dict[str, Any]] = []
        
        logger.info("Initialized RemediationTool")
    
    async def list_tools(self) -> List[Tool]:
        """
        List all available remediation tools.
        
        Returns:
            List of Tool objects representing remediation capabilities.
        """
        tools = [
            Tool(
                name="remediate_restart_service",
                description="Restart a service or application instance",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "resource_uri": {
                            "type": "string",
                            "description": "Resource to restart (e.g., 'infra://aws/ec2/i-12345')"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force restart without graceful shutdown",
                            "default": False
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for restart"
                        }
                    },
                    "required": ["resource_uri", "reason"]
                }
            ),
            Tool(
                name="remediate_scale_up",
                description="Scale up resources (add instances, increase capacity)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "resource_uri": {
                            "type": "string",
                            "description": "Resource to scale"
                        },
                        "target_capacity": {
                            "type": "integer",
                            "description": "Target number of instances or capacity units",
                            "minimum": 1
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for scaling"
                        }
                    },
                    "required": ["resource_uri", "target_capacity", "reason"]
                }
            ),
            Tool(
                name="remediate_scale_down",
                description="Scale down resources (remove instances, decrease capacity)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "resource_uri": {
                            "type": "string",
                            "description": "Resource to scale down"
                        },
                        "target_capacity": {
                            "type": "integer",
                            "description": "Target number of instances",
                            "minimum": 0
                        },
                        "drain_timeout": {
                            "type": "integer",
                            "description": "Timeout for draining connections (seconds)",
                            "default": 300
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for scaling down"
                        }
                    },
                    "required": ["resource_uri", "target_capacity", "reason"]
                }
            ),
            Tool(
                name="remediate_clear_cache",
                description="Clear cache to resolve stale data issues",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cache_uri": {
                            "type": "string",
                            "description": "Cache resource URI"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Key pattern to clear (supports wildcards)",
                            "default": "*"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for clearing cache"
                        }
                    },
                    "required": ["cache_uri", "reason"]
                }
            ),
            Tool(
                name="remediate_update_config",
                description="Update configuration to resolve issues",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "resource_uri": {
                            "type": "string",
                            "description": "Resource to update"
                        },
                        "config_changes": {
                            "type": "object",
                            "description": "Configuration changes to apply"
                        },
                        "restart_required": {
                            "type": "boolean",
                            "description": "Whether restart is needed after config change",
                            "default": True
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for configuration update"
                        }
                    },
                    "required": ["resource_uri", "config_changes", "reason"]
                }
            ),
            Tool(
                name="remediate_restart_pod",
                description="Restart a Kubernetes pod",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pod_name": {
                            "type": "string",
                            "description": "Name of the pod to restart"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for restart"
                        }
                    },
                    "required": ["pod_name", "reason"]
                }
            ),
            Tool(
                name="remediate_kill_process",
                description="Kill a problematic process",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "resource_uri": {
                            "type": "string",
                            "description": "Resource where process is running"
                        },
                        "process_id": {
                            "type": "integer",
                            "description": "Process ID to kill"
                        },
                        "signal": {
                            "type": "string",
                            "enum": ["SIGTERM", "SIGKILL"],
                            "description": "Signal to send",
                            "default": "SIGTERM"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for killing process"
                        }
                    },
                    "required": ["resource_uri", "process_id", "reason"]
                }
            )
        ]
        
        return tools
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a remediation action with safety checks.
        
        Args:
            tool_name: Name of the remediation tool
            arguments: Tool arguments
        
        Returns:
            Remediation result with status and details
        """
        logger.info(f"Executing remediation: {tool_name}")
        
        # Check if action is allowed
        action_type = tool_name.replace("remediate_", "")
        if self.allowed_actions and action_type not in self.allowed_actions:
            return {
                "status": "rejected",
                "reason": f"Action '{action_type}' not in allowed actions list",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Create remediation record
        remediation_id = f"REM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        remediation_record = {
            "remediation_id": remediation_id,
            "tool": tool_name,
            "arguments": arguments,
            "status": "pending",
            "timestamp": datetime.utcnow().isoformat(),
            "require_approval": self.require_approval
        }
        
        # Check if approval is required
        if self.require_approval:
            remediation_record["status"] = "awaiting_approval"
            self.remediation_history.append(remediation_record)
            
            return {
                "status": "awaiting_approval",
                "remediation_id": remediation_id,
                "message": "Remediation action requires approval before execution",
                "action": tool_name,
                "details": arguments,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Execute the remediation
        try:
            if tool_name == "remediate_restart_service":
                result = await self._restart_service(arguments)
            elif tool_name == "remediate_scale_up":
                result = await self._scale_up(arguments)
            elif tool_name == "remediate_scale_down":
                result = await self._scale_down(arguments)
            elif tool_name == "remediate_clear_cache":
                result = await self._clear_cache(arguments)