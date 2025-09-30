"""
Logs Resource Provider for MCP Server.

Exposes infrastructure logs from various sources (CloudWatch, Kubernetes, etc.)
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from mcp.types import Resource

logger = logging.getLogger(__name__)


class LogsResourceProvider:
    """
    Provides access to infrastructure logs as MCP resources.
    
    Supports multiple log sources:
    - AWS CloudWatch Logs
    - Kubernetes Pod Logs
    - Application Logs
    """
    
    def __init__(self, config: Any):
        """Initialize logs provider with configuration."""
        self.config = config
        self.cache: Dict[str, Any] = {}
        
        logger.info(f"Initialized LogsResourceProvider with sources: {config.sources}")
    
    async def list_resources(self) -> List[Resource]:
        """
        List all available log resources.
        
        Returns:
            List of Resource objects representing available logs.
        """
        resources = []
        
        # Application Logs
        resources.append(Resource(
            uri="logs://application/errors",
            name="Application Error Logs",
            description="Recent error logs from all application instances",
            mimeType="application/json"
        ))
        
        resources.append(Resource(
            uri="logs://application/access",
            name="Application Access Logs",
            description="HTTP access logs from all application instances",
            mimeType="application/json"
        ))
        
        # System Logs
        resources.append(Resource(
            uri="logs://system/syslog",
            name="System Logs",
            description="System-level logs from all infrastructure",
            mimeType="application/json"
        ))
        
        # Kubernetes Logs
        if "kubernetes" in self.config.sources:
            resources.append(Resource(
                uri="logs://kubernetes/pods",
                name="Kubernetes Pod Logs",
                description="Logs from all Kubernetes pods",
                mimeType="application/json"
            ))
        
        # CloudWatch Logs
        if "cloudwatch" in self.config.sources:
            resources.append(Resource(
                uri="logs://cloudwatch/groups",
                name="CloudWatch Log Groups",
                description="AWS CloudWatch log groups and streams",
                mimeType="application/json"
            ))
        
        # Audit Logs
        resources.append(Resource(
            uri="logs://audit/changes",
            name="Infrastructure Audit Logs",
            description="Audit trail of all infrastructure changes",
            mimeType="application/json"
        ))
        
        return resources
    
    async def read_resource(self, uri: str) -> str:
        """
        Read logs for a specific resource URI.
        
        Args:
            uri: Resource URI (e.g., "logs://application/errors")
        
        Returns:
            JSON string containing log data.
        """
        # Parse URI
        parts = uri.replace("logs://", "").split("/")
        log_source = parts[0] if parts else "unknown"
        log_type = parts[1] if len(parts) > 1 else "all"
        
        # Fetch logs based on source
        if log_source == "application":
            data = await self._get_application_logs(log_type)
        elif log_source == "system":
            data = await self._get_system_logs(log_type)
        elif log_source == "kubernetes":
            data = await self._get_kubernetes_logs(log_type)
        elif log_source == "cloudwatch":
            data = await self._get_cloudwatch_logs(log_type)
        elif log_source == "audit":
            data = await self._get_audit_logs(log_type)
        else:
            data = {"error": f"Unknown log source: {log_source}"}
        
        return json.dumps(data, indent=2)
    
    async def _get_application_logs(self, log_type: str) -> Dict[str, Any]:
        """Fetch application logs."""
        # TODO: Integrate with actual log sources
        # For now, return mock data
        
        if log_type == "errors":
            return {
                "source": "application",
                "type": "errors",
                "timestamp": datetime.utcnow().isoformat(),
                "count": 15,
                "logs": [
                    {
                        "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                        "level": "ERROR",
                        "service": "api-service",
                        "instance": "i-1234567890abcdef0",
                        "message": "Database connection timeout",
                        "stack_trace": "at db.connect() line 45",
                        "request_id": "req-abc123"
                    },
                    {
                        "timestamp": (datetime.utcnow() - timedelta(minutes=12)).isoformat(),
                        "level": "ERROR",
                        "service": "api-service",
                        "instance": "i-0987654321fedcba0",
                        "message": "Memory allocation failed",
                        "stack_trace": "at handler.process() line 128",
                        "request_id": "req-xyz789"
                    },
                    {
                        "timestamp": (datetime.utcnow() - timedelta(minutes=18)).isoformat(),
                        "level": "CRITICAL",
                        "service": "worker-service",
                        "instance": "i-1111222233334444",
                        "message": "Out of memory error",
                        "stack_trace": "at process.run() line 67",
                        "request_id": "req-def456"
                    }
                ],
                "filters": {
                    "time_range": "1h",
                    "min_level": "ERROR"
                }
            }
        elif log_type == "access":
            return {
                "source": "application",
                "type": "access",
                "timestamp": datetime.utcnow().isoformat(),
                "count": 1250,
                "sample_logs": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "method": "GET",
                        "path": "/api/users",
                        "status": 200,
                        "response_time_ms": 45,
                        "ip": "192.168.1.100"
                    },
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "method": "POST",
                        "path": "/api/orders",
                        "status": 500,
                        "response_time_ms": 2500,
                        "ip": "192.168.1.105",
                        "error": "Internal Server Error"
                    }
                ]
            }
        else:
            return {"error": f"Unknown application log type: {log_type}"}
    
    async def _get_system_logs(self, log_type: str) -> Dict[str, Any]:
        """Fetch system logs."""
        return {
            "source": "system",
            "type": log_type,
            "timestamp": datetime.utcnow().isoformat(),
            "logs": [
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=3)).isoformat(),
                    "host": "server-01",
                    "facility": "kern",
                    "level": "warning",
                    "message": "High CPU temperature detected"
                },
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=8)).isoformat(),
                    "host": "server-02",
                    "facility": "daemon",
                    "level": "error",
                    "message": "Service restart failed"
                }
            ]
        }
    
    async def _get_kubernetes_logs(self, log_type: str) -> Dict[str, Any]:
        """Fetch Kubernetes logs."""
        return {
            "source": "kubernetes",
            "type": log_type,
            "timestamp": datetime.utcnow().isoformat(),
            "namespace": self.config.k8s_namespace if hasattr(self.config, 'k8s_namespace') else "default",
            "pods": [
                {
                    "pod_name": "api-deployment-abc123",
                    "container": "api",
                    "status": "Running",
                    "restart_count": 0,
                    "recent_logs": [
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            "level": "INFO",
                            "message": "Server started on port 8080"
                        },
                        {
                            "timestamp": (datetime.utcnow() - timedelta(seconds=30)).isoformat(),
                            "level": "WARN",
                            "message": "Connection pool size approaching limit"
                        }
                    ]
                },
                {
                    "pod_name": "worker-deployment-xyz789",
                    "container": "worker",
                    "status": "CrashLoopBackOff",
                    "restart_count": 5,
                    "recent_logs": [
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            "level": "ERROR",
                            "message": "Fatal: Unable to connect to message queue"
                        }
                    ]
                }
            ]
        }
    
    async def _get_cloudwatch_logs(self, log_type: str) -> Dict[str, Any]:
        """Fetch CloudWatch logs."""
        return {
            "source": "cloudwatch",
            "type": log_type,
            "timestamp": datetime.utcnow().isoformat(),
            "region": "us-east-1",
            "log_groups": [
                {
                    "name": "/aws/lambda/api-function",
                    "stored_bytes": 1024000,
                    "metric_filter_count": 2,
                    "recent_streams": [
                        {
                            "name": "2025/01/15/[$LATEST]abc123",
                            "last_event_time": datetime.utcnow().isoformat(),
                            "events_count": 150
                        }
                    ]
                },
                {
                    "name": "/aws/ecs/api-cluster",
                    "stored_bytes": 2048000,
                    "metric_filter_count": 3,
                    "recent_streams": [
                        {
                            "name": "ecs/api-task/abc123",
                            "last_event_time": datetime.utcnow().isoformat(),
                            "events_count": 320
                        }
                    ]
                }
            ]
        }
    
    async def _get_audit_logs(self, log_type: str) -> Dict[str, Any]:
        """Fetch audit logs."""
        return {
            "source": "audit",
            "type": log_type,
            "timestamp": datetime.utcnow().isoformat(),
            "changes": [
                {
                    "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    "action": "instance_restart",
                    "resource": "i-1234567890abcdef0",
                    "user": "system",
                    "status": "success",
                    "details": "Auto-remediation: High memory usage"
                },
                {
                    "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "action": "scale_up",
                    "resource": "api-autoscaling-group",
                    "user": "admin@example.com",
                    "status": "success",
                    "details": "Manual scaling operation"
                },
                {
                    "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                    "action": "config_change",
                    "resource": "load-balancer-01",
                    "user": "terraform",
                    "status": "success",
                    "details": "Updated health check configuration"
                }
            ]
        }