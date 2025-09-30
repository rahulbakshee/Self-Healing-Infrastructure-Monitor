"""
Metrics Resource Provider for MCP Server.

Exposes infrastructure metrics from various sources (Prometheus, CloudWatch, etc.)
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from mcp.types import Resource

logger = logging.getLogger(__name__)


class MetricsResourceProvider:
    """
    Provides access to infrastructure metrics as MCP resources.
    
    Supports multiple metric sources:
    - Prometheus
    - AWS CloudWatch
    - Custom metrics
    """
    
    def __init__(self, config: Any):
        """Initialize metrics provider with configuration."""
        self.config = config
        self.cache: Dict[str, Any] = {}
        self.cache_timestamp: Dict[str, datetime] = {}
        
        logger.info(f"Initialized MetricsResourceProvider with providers: {config.providers}")
    
    async def list_resources(self) -> List[Resource]:
        """
        List all available metric resources.
        
        Returns:
            List of Resource objects representing available metrics.
        """
        resources = []
        
        # CPU Metrics
        resources.append(Resource(
            uri="metrics://cpu/usage",
            name="CPU Usage Metrics",
            description="Current and historical CPU usage across all instances",
            mimeType="application/json"
        ))
        
        # Memory Metrics
        resources.append(Resource(
            uri="metrics://memory/usage",
            name="Memory Usage Metrics",
            description="Current and historical memory usage across all instances",
            mimeType="application/json"
        ))
        
        # Disk Metrics
        resources.append(Resource(
            uri="metrics://disk/usage",
            name="Disk Usage Metrics",
            description="Current and historical disk usage across all instances",
            mimeType="application/json"
        ))
        
        # Network Metrics
        resources.append(Resource(
            uri="metrics://network/throughput",
            name="Network Throughput Metrics",
            description="Network I/O metrics across all instances",
            mimeType="application/json"
        ))
        
        # Application Metrics
        resources.append(Resource(
            uri="metrics://application/requests",
            name="Application Request Metrics",
            description="Request rate, latency, and error rate metrics",
            mimeType="application/json"
        ))
        
        # Service Health
        resources.append(Resource(
            uri="metrics://health/services",
            name="Service Health Status",
            description="Overall health status of all monitored services",
            mimeType="application/json"
        ))
        
        return resources
    
    async def read_resource(self, uri: str) -> str:
        """
        Read metrics data for a specific resource URI.
        
        Args:
            uri: Resource URI (e.g., "metrics://cpu/usage")
        
        Returns:
            JSON string containing metric data.
        """
        # Check cache
        if self._is_cached(uri):
            logger.debug(f"Returning cached metrics for {uri}")
            return self.cache[uri]
        
        # Parse URI
        parts = uri.replace("metrics://", "").split("/")
        metric_type = parts[0] if parts else "unknown"
        metric_name = parts[1] if len(parts) > 1 else "all"
        
        # Fetch metrics based on type
        if metric_type == "cpu":
            data = await self._get_cpu_metrics(metric_name)
        elif metric_type == "memory":
            data = await self._get_memory_metrics(metric_name)
        elif metric_type == "disk":
            data = await self._get_disk_metrics(metric_name)
        elif metric_type == "network":
            data = await self._get_network_metrics(metric_name)
        elif metric_type == "application":
            data = await self._get_application_metrics(metric_name)
        elif metric_type == "health":
            data = await self._get_health_metrics(metric_name)
        else:
            data = {"error": f"Unknown metric type: {metric_type}"}
        
        # Cache the result
        result = json.dumps(data, indent=2)
        self._cache_result(uri, result)
        
        return result
    
    async def _get_cpu_metrics(self, name: str) -> Dict[str, Any]:
        """Fetch CPU metrics."""
        # TODO: Integrate with actual metric sources (Prometheus, CloudWatch)
        # For now, return mock data
        return {
            "metric": "cpu_usage",
            "type": name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": [
                {
                    "instance": "i-1234567890abcdef0",
                    "current": 45.2,
                    "average_1h": 42.8,
                    "average_24h": 38.5,
                    "peak_24h": 78.3,
                    "status": "healthy"
                },
                {
                    "instance": "i-0987654321fedcba0",
                    "current": 82.1,
                    "average_1h": 79.5,
                    "average_24h": 65.2,
                    "peak_24h": 95.7,
                    "status": "warning"
                }
            ],
            "thresholds": {
                "warning": 70,
                "critical": 85
            }
        }
    
    async def _get_memory_metrics(self, name: str) -> Dict[str, Any]:
        """Fetch memory metrics."""
        return {
            "metric": "memory_usage",
            "type": name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": [
                {
                    "instance": "i-1234567890abcdef0",
                    "current": 68.5,
                    "average_1h": 65.2,
                    "average_24h": 62.1,
                    "peak_24h": 85.3,
                    "status": "healthy"
                },
                {
                    "instance": "i-0987654321fedcba0",
                    "current": 88.7,
                    "average_1h": 86.4,
                    "average_24h": 82.9,
                    "peak_24h": 94.2,
                    "status": "critical"
                }
            ],
            "thresholds": {
                "warning": 75,
                "critical": 90
            }
        }
    
    async def _get_disk_metrics(self, name: str) -> Dict[str, Any]:
        """Fetch disk metrics."""
        return {
            "metric": "disk_usage",
            "type": name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": [
                {
                    "instance": "i-1234567890abcdef0",
                    "volume": "/dev/sda1",
                    "current": 72.3,
                    "capacity_gb": 100,
                    "used_gb": 72.3,
                    "status": "healthy"
                },
                {
                    "instance": "i-0987654321fedcba0",
                    "volume": "/dev/sda1",
                    "current": 91.8,
                    "capacity_gb": 100,
                    "used_gb": 91.8,
                    "status": "critical"
                }
            ],
            "thresholds": {
                "warning": 80,
                "critical": 95
            }
        }
    
    async def _get_network_metrics(self, name: str) -> Dict[str, Any]:
        """Fetch network metrics."""
        return {
            "metric": "network_throughput",
            "type": name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": [
                {
                    "instance": "i-1234567890abcdef0",
                    "in_mbps": 125.3,
                    "out_mbps": 87.6,
                    "errors": 0,
                    "dropped": 0,
                    "status": "healthy"
                }
            ]
        }
    
    async def _get_application_metrics(self, name: str) -> Dict[str, Any]:
        """Fetch application metrics."""
        return {
            "metric": "application_requests",
            "type": name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "request_rate": 1250.5,  # requests per second
                "avg_latency_ms": 125.3,
                "p95_latency_ms": 287.6,
                "p99_latency_ms": 456.2,
                "error_rate": 0.012,  # 1.2%
                "success_rate": 0.988,  # 98.8%
                "status": "healthy"
            },
            "thresholds": {
                "latency_warning": 200,
                "latency_critical": 500,
                "error_rate_warning": 0.05,
                "error_rate_critical": 0.10
            }
        }
    
    async def _get_health_metrics(self, name: str) -> Dict[str, Any]:
        """Fetch overall health metrics."""
        return {
            "metric": "service_health",
            "type": name,
            "timestamp": datetime.utcnow().isoformat(),
            "services": [
                {
                    "name": "web-service",
                    "status": "healthy",
                    "uptime": "99.98%",
                    "last_check": datetime.utcnow().isoformat()
                },
                {
                    "name": "api-service",
                    "status": "degraded",
                    "uptime": "98.52%",
                    "last_check": datetime.utcnow().isoformat(),
                    "issues": ["High memory usage"]
                },
                {
                    "name": "database",
                    "status": "healthy",
                    "uptime": "99.99%",
                    "last_check": datetime.utcnow().isoformat()
                }
            ],
            "overall_status": "degraded"
        }
    
    def _is_cached(self, uri: str) -> bool:
        """Check if resource is in cache and still valid."""
        if uri not in self.cache:
            return False
        
        cache_age = (datetime.utcnow() - self.cache_timestamp[uri]).total_seconds()
        return cache_age < self.config.cache_ttl
    
    def _cache_result(self, uri: str, result: str) -> None:
        """Cache resource result."""
        self.cache[uri] = result
        self.cache_timestamp[uri] = datetime.utcnow()