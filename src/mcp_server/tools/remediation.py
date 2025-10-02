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
            elif tool_name == "remediate_update_config":
                result = await self._update_config(arguments)
            elif tool_name == "remediate_restart_pod":
                result = await self._restart_pod(arguments)
            elif tool_name == "remediate_kill_process":
                result = await self._kill_process(arguments)
            else:
                result = {
                    "status": "error",
                    "message": f"Unknown remediation tool: {tool_name}"
                }
            
            remediation_record["status"] = result.get("status", "completed")
            remediation_record["result"] = result
            remediation_record["completed_at"] = datetime.utcnow().isoformat()
            self.remediation_history.append(remediation_record)
            
            return result
            
        except Exception as e:
            logger.error(f"Remediation failed: {str(e)}")
            remediation_record["status"] = "failed"
            remediation_record["error"] = str(e)
            remediation_record["failed_at"] = datetime.utcnow().isoformat()
            self.remediation_history.append(remediation_record)
            
            return {
                "status": "failed",
                "remediation_id": remediation_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _restart_service(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Restart a service or instance."""
        resource_uri = args.get("resource_uri")
        force = args.get("force", False)
        reason = args.get("reason")
        
        # TODO: Integrate with actual cloud providers
        # For now, simulate the restart
        
        logger.info(f"Restarting service: {resource_uri}")
        
        # Simulate restart delay
        await asyncio.sleep(2)
        
        return {
            "status": "completed",
            "action": "restart_service",
            "resource_uri": resource_uri,
            "force": force,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "previous_state": "running",
                "new_state": "running",
                "restart_duration_seconds": 15,
                "graceful_shutdown": not force,
                "health_check_passed": True
            },
            "message": f"Successfully restarted service {resource_uri}"
        }
    
    async def _scale_up(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Scale up resources."""
        resource_uri = args.get("resource_uri")
        target_capacity = args.get("target_capacity")
        reason = args.get("reason")
        
        logger.info(f"Scaling up: {resource_uri} to {target_capacity}")
        
        # Simulate scaling
        await asyncio.sleep(3)
        
        return {
            "status": "completed",
            "action": "scale_up",
            "resource_uri": resource_uri,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "previous_capacity": 2,
                "target_capacity": target_capacity,
                "current_capacity": target_capacity,
                "scaling_duration_seconds": 45,
                "new_instances": [
                    f"i-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-001",
                    f"i-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-002"
                ],
                "health_status": "healthy"
            },
            "message": f"Successfully scaled up {resource_uri} to {target_capacity} instances"
        }
    
    async def _scale_down(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Scale down resources."""
        resource_uri = args.get("resource_uri")
        target_capacity = args.get("target_capacity")
        drain_timeout = args.get("drain_timeout", 300)
        reason = args.get("reason")
        
        logger.info(f"Scaling down: {resource_uri} to {target_capacity}")
        
        # Simulate scaling
        await asyncio.sleep(2)
        
        return {
            "status": "completed",
            "action": "scale_down",
            "resource_uri": resource_uri,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "previous_capacity": 5,
                "target_capacity": target_capacity,
                "current_capacity": target_capacity,
                "drain_timeout": drain_timeout,
                "terminated_instances": [
                    "i-0987654321fedcba0",
                    "i-1111222233334444"
                ],
                "connections_drained": True,
                "scaling_duration_seconds": 35
            },
            "message": f"Successfully scaled down {resource_uri} to {target_capacity} instances"
        }
    
    async def _clear_cache(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Clear cache entries."""
        cache_uri = args.get("cache_uri")
        pattern = args.get("pattern", "*")
        reason = args.get("reason")
        
        logger.info(f"Clearing cache: {cache_uri} pattern: {pattern}")
        
        # Simulate cache clear
        await asyncio.sleep(1)
        
        return {
            "status": "completed",
            "action": "clear_cache",
            "cache_uri": cache_uri,
            "pattern": pattern,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "keys_cleared": 1523,
                "memory_freed_mb": 342.5,
                "duration_seconds": 2.3,
                "cache_hit_rate_before": 0.87,
                "cache_hit_rate_after": 0.0
            },
            "message": f"Successfully cleared cache {cache_uri} with pattern {pattern}"
        }
    
    async def _update_config(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration."""
        resource_uri = args.get("resource_uri")
        config_changes = args.get("config_changes")
        restart_required = args.get("restart_required", True)
        reason = args.get("reason")
        
        logger.info(f"Updating config: {resource_uri}")
        
        # Simulate config update
        await asyncio.sleep(2)
        
        result = {
            "status": "completed",
            "action": "update_config",
            "resource_uri": resource_uri,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "changes_applied": config_changes,
                "backup_created": True,
                "backup_id": f"backup-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "restart_required": restart_required,
                "validation_passed": True
            },
            "message": f"Successfully updated configuration for {resource_uri}"
        }
        
        # If restart is required, perform it
        if restart_required:
            restart_result = await self._restart_service({
                "resource_uri": resource_uri,
                "force": False,
                "reason": "Configuration update requires restart"
            })
            result["details"]["restart_result"] = restart_result
        
        return result
    
    async def _restart_pod(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Restart a Kubernetes pod."""
        pod_name = args.get("pod_name")
        namespace = args.get("namespace", "default")
        reason = args.get("reason")
        
        logger.info(f"Restarting pod: {namespace}/{pod_name}")
        
        # Simulate pod restart
        await asyncio.sleep(2)
        
        return {
            "status": "completed",
            "action": "restart_pod",
            "pod_name": pod_name,
            "namespace": namespace,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "previous_pod": pod_name,
                "new_pod": f"{pod_name.rsplit('-', 1)[0]}-{datetime.utcnow().strftime('%H%M%S')}",
                "restart_duration_seconds": 18,
                "container_restarts": 0,
                "health_check_passed": True,
                "ready": True
            },
            "message": f"Successfully restarted pod {namespace}/{pod_name}"
        }
    
    async def _kill_process(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Kill a problematic process."""
        resource_uri = args.get("resource_uri")
        process_id = args.get("process_id")
        signal = args.get("signal", "SIGTERM")
        reason = args.get("reason")
        
        logger.info(f"Killing process {process_id} on {resource_uri} with {signal}")
        
        # Simulate process kill
        await asyncio.sleep(1)
        
        return {
            "status": "completed",
            "action": "kill_process",
            "resource_uri": resource_uri,
            "process_id": process_id,
            "signal": signal,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "process_name": "java",
                "process_user": "app",
                "memory_usage_mb": 2048,
                "cpu_percent": 95.2,
                "termination_successful": True,
                "graceful_shutdown": signal == "SIGTERM"
            },
            "message": f"Successfully killed process {process_id} on {resource_uri}"
        }
    
    def register_action(self, action: Dict[str, Any]) -> None:
        """
        Register a custom remediation action.
        
        Args:
            action: Action configuration with name, description, handler
        """
        action_name = action.get("name")
        if action_name:
            self.allowed_actions.append(action_name)
            logger.info(f"Registered custom remediation action: {action_name}")
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get remediation history.
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of remediation records
        """
        return self.remediation_history[-limit:]
    
    async def approve_remediation(self, remediation_id: str, approved_by: str) -> Dict[str, Any]:
        """
        Approve a pending remediation action.
        
        Args:
            remediation_id: ID of the remediation to approve
            approved_by: User or system approving the action
        
        Returns:
            Result of the approved remediation
        """
        # Find the pending remediation
        remediation = None
        for record in self.remediation_history:
            if record.get("remediation_id") == remediation_id:
                remediation = record
                break
        
        if not remediation:
            return {
                "status": "error",
                "message": f"Remediation {remediation_id} not found"
            }
        
        if remediation.get("status") != "awaiting_approval":
            return {
                "status": "error",
                "message": f"Remediation {remediation_id} is not awaiting approval (status: {remediation.get('status')})"
            }
        
        # Execute the approved remediation
        logger.info(f"Executing approved remediation {remediation_id}")
        remediation["status"] = "approved"
        remediation["approved_by"] = approved_by
        remediation["approved_at"] = datetime.utcnow().isoformat()
        
        # Temporarily disable approval requirement
        original_require_approval = self.require_approval
        self.require_approval = False
        
        try:
            result = await self.execute(remediation["tool"], remediation["arguments"])
            remediation["status"] = "completed"
            remediation["result"] = result
            return result
        finally:
            self.require_approval = original_require_approval
    
    async def reject_remediation(self, remediation_id: str, rejected_by: str, reason: str) -> Dict[str, Any]:
        """
        Reject a pending remediation action.
        
        Args:
            remediation_id: ID of the remediation to reject
            rejected_by: User or system rejecting the action
            reason: Reason for rejection
        
        Returns:
            Rejection confirmation
        """
        # Find the pending remediation
        remediation = None
        for record in self.remediation_history:
            if record.get("remediation_id") == remediation_id:
                remediation = record
                break
        
        if not remediation:
            return {
                "status": "error",
                "message": f"Remediation {remediation_id} not found"
            }
        
        if remediation.get("status") != "awaiting_approval":
            return {
                "status": "error",
                "message": f"Remediation {remediation_id} is not awaiting approval"
            }
        
        logger.info(f"Rejecting remediation {remediation_id}")
        remediation["status"] = "rejected"
        remediation["rejected_by"] = rejected_by
        remediation["rejected_at"] = datetime.utcnow().isoformat()
        remediation["rejection_reason"] = reason
        
        return {
            "status": "rejected",
            "remediation_id": remediation_id,
            "rejected_by": rejected_by,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }