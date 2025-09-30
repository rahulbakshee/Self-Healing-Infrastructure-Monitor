"""
Infrastructure Resource Provider for MCP Server.

Exposes infrastructure state from various platforms (AWS, Kubernetes, etc.)
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from mcp.types import Resource

logger = logging.getLogger(__name__)


class InfrastructureResourceProvider:
    """
    Provides access to infrastructure state as MCP resources.
    
    Supports multiple platforms:
    - AWS (EC2, ECS, Lambda, RDS)
    - Kubernetes (Pods, Deployments, Services)
    - Load Balancers
    - Databases
    """
    
    def __init__(self, config: Any):
        """Initialize infrastructure provider with configuration."""
        self.config = config
        self.cache: Dict[str, Any] = {}
        self.cache_timestamp: Dict[str, datetime] = {}
        
        logger.info(f"Initialized InfrastructureResourceProvider with platforms: {config.platforms}")
    
    async def list_resources(self) -> List[Resource]:
        """
        List all available infrastructure resources.
        
        Returns:
            List of Resource objects representing infrastructure components.
        """
        resources = []
        
        # AWS Resources
        if "aws" in self.config.platforms:
            resources.extend([
                Resource(
                    uri="infra://aws/ec2/instances",
                    name="AWS EC2 Instances",
                    description="All EC2 instances and their current state",
                    mimeType="application/json"
                ),
                Resource(
                    uri="infra://aws/ecs/clusters",
                    name="AWS ECS Clusters",
                    description="ECS clusters, services, and tasks",
                    mimeType="application/json"
                ),
                Resource(
                    uri="infra://aws/lambda/functions",
                    name="AWS Lambda Functions",
                    description="Lambda functions and their execution metrics",
                    mimeType="application/json"
                ),
                Resource(
                    uri="infra://aws/rds/databases",
                    name="AWS RDS Databases",
                    description="RDS database instances and their health",
                    mimeType="application/json"
                ),
                Resource(
                    uri="infra://aws/elb/loadbalancers",
                    name="AWS Load Balancers",
                    description="Load balancers and target health",
                    mimeType="application/json"
                )
            ])
        
        # Kubernetes Resources
        if "kubernetes" in self.config.platforms:
            resources.extend([
                Resource(
                    uri="infra://kubernetes/pods",
                    name="Kubernetes Pods",
                    description="All pods and their status",
                    mimeType="application/json"
                ),
                Resource(
                    uri="infra://kubernetes/deployments",
                    name="Kubernetes Deployments",
                    description="All deployments and replica status",
                    mimeType="application/json"
                ),
                Resource(
                    uri="infra://kubernetes/services",
                    name="Kubernetes Services",
                    description="All services and endpoints",
                    mimeType="application/json"
                ),
                Resource(
                    uri="infra://kubernetes/nodes",
                    name="Kubernetes Nodes",
                    description="Cluster nodes and their capacity",
                    mimeType="application/json"
                )
            ])
        
        # Overall Infrastructure Status
        resources.append(Resource(
            uri="infra://status/overall",
            name="Overall Infrastructure Status",
            description="Aggregated health status of all infrastructure",
            mimeType="application/json"
        ))
        
        return resources
    
    async def read_resource(self, uri: str) -> str:
        """
        Read infrastructure state for a specific resource URI.
        
        Args:
            uri: Resource URI (e.g., "infra://aws/ec2/instances")
        
        Returns:
            JSON string containing infrastructure data.
        """
        # Check cache
        if self._is_cached(uri):
            logger.debug(f"Returning cached infrastructure data for {uri}")
            return self.cache[uri]
        
        # Parse URI
        parts = uri.replace("infra://", "").split("/")
        platform = parts[0] if parts else "unknown"
        service = parts[1] if len(parts) > 1 else "all"
        resource_type = parts[2] if len(parts) > 2 else "all"
        
        # Fetch data based on platform
        if platform == "aws":
            data = await self._get_aws_resources(service, resource_type)
        elif platform == "kubernetes":
            data = await self._get_kubernetes_resources(service)
        elif platform == "status":
            data = await self._get_overall_status()
        else:
            data = {"error": f"Unknown platform: {platform}"}
        
        # Cache the result
        result = json.dumps(data, indent=2)
        self._cache_result(uri, result)
        
        return result
    
    async def _get_aws_resources(self, service: str, resource_type: str) -> Dict[str, Any]:
        """Fetch AWS resources."""
        # TODO: Integrate with boto3 for real AWS data
        # For now, return mock data
        
        if service == "ec2" and resource_type == "instances":
            return {
                "platform": "aws",
                "service": "ec2",
                "resource_type": "instances",
                "region": self.config.aws_region if hasattr(self.config, 'aws_region') else "us-east-1",
                "timestamp": datetime.utcnow().isoformat(),
                "instances": [
                    {
                        "instance_id": "i-1234567890abcdef0",
                        "type": "t3.medium",
                        "state": "running",
                        "launch_time": "2025-01-15T10:30:00Z",
                        "availability_zone": "us-east-1a",
                        "private_ip": "10.0.1.100",
                        "public_ip": "54.123.45.67",
                        "tags": {
                            "Name": "api-server-01",
                            "Environment": "production",
                            "Service": "api"
                        },
                        "health_status": "healthy",
                        "cpu_utilization": 45.2,
                        "memory_utilization": 68.5
                    },
                    {
                        "instance_id": "i-0987654321fedcba0",
                        "type": "t3.medium",
                        "state": "running",
                        "launch_time": "2025-01-15T10:30:00Z",
                        "availability_zone": "us-east-1b",
                        "private_ip": "10.0.2.100",
                        "public_ip": "54.123.45.68",
                        "tags": {
                            "Name": "api-server-02",
                            "Environment": "production",
                            "Service": "api"
                        },
                        "health_status": "degraded",
                        "cpu_utilization": 82.1,
                        "memory_utilization": 88.7,
                        "issues": ["High memory usage", "CPU throttling"]
                    }
                ],
                "summary": {
                    "total_instances": 2,
                    "running": 2,
                    "stopped": 0,
                    "healthy": 1,
                    "degraded": 1,
                    "unhealthy": 0
                }
            }
        
        elif service == "ecs" and resource_type == "clusters":
            return {
                "platform": "aws",
                "service": "ecs",
                "resource_type": "clusters",
                "region": self.config.aws_region if hasattr(self.config, 'aws_region') else "us-east-1",
                "timestamp": datetime.utcnow().isoformat(),
                "clusters": [
                    {
                        "cluster_name": "production-cluster",
                        "status": "ACTIVE",
                        "registered_container_instances": 3,
                        "running_tasks": 12,
                        "pending_tasks": 0,
                        "services": [
                            {
                                "service_name": "api-service",
                                "status": "ACTIVE",
                                "desired_count": 4,
                                "running_count": 4,
                                "pending_count": 0,
                                "health_status": "healthy"
                            },
                            {
                                "service_name": "worker-service",
                                "status": "ACTIVE",
                                "desired_count": 2,
                                "running_count": 1,
                                "pending_count": 1,
                                "health_status": "degraded",
                                "issues": ["Task failing health checks"]
                            }
                        ]
                    }
                ]
            }
        
        elif service == "lambda" and resource_type == "functions":
            return {
                "platform": "aws",
                "service": "lambda",
                "resource_type": "functions",
                "region": self.config.aws_region if hasattr(self.config, 'aws_region') else "us-east-1",
                "timestamp": datetime.utcnow().isoformat(),
                "functions": [
                    {
                        "function_name": "api-handler",
                        "runtime": "python3.11",
                        "memory_size": 512,
                        "timeout": 30,
                        "last_modified": "2025-01-15T10:00:00Z",
                        "invocations_24h": 15234,
                        "errors_24h": 23,
                        "error_rate": 0.0015,
                        "avg_duration_ms": 245.5,
                        "health_status": "healthy"
                    },
                    {
                        "function_name": "data-processor",
                        "runtime": "python3.11",
                        "memory_size": 1024,
                        "timeout": 300,
                        "last_modified": "2025-01-14T15:30:00Z",
                        "invocations_24h": 3421,
                        "errors_24h": 342,
                        "error_rate": 0.10,
                        "avg_duration_ms": 1823.7,
                        "health_status": "critical",
                        "issues": ["High error rate", "Timeout issues"]
                    }
                ]
            }
        
        elif service == "rds" and resource_type == "databases":
            return {
                "platform": "aws",
                "service": "rds",
                "resource_type": "databases",
                "region": self.config.aws_region if hasattr(self.config, 'aws_region') else "us-east-1",
                "timestamp": datetime.utcnow().isoformat(),
                "databases": [
                    {
                        "db_instance_identifier": "production-db",
                        "engine": "postgres",
                        "engine_version": "15.4",
                        "db_instance_class": "db.r5.large",
                        "status": "available",
                        "allocated_storage": 100,
                        "storage_type": "gp3",
                        "multi_az": True,
                        "endpoint": "production-db.abc123.us-east-1.rds.amazonaws.com",
                        "port": 5432,
                        "cpu_utilization": 35.2,
                        "connections": 45,
                        "free_storage_space_gb": 72,
                        "health_status": "healthy"
                    }
                ]
            }
        
        elif service == "elb" and resource_type == "loadbalancers":
            return {
                "platform": "aws",
                "service": "elb",
                "resource_type": "loadbalancers",
                "region": self.config.aws_region if hasattr(self.config, 'aws_region') else "us-east-1",
                "timestamp": datetime.utcnow().isoformat(),
                "load_balancers": [
                    {
                        "name": "api-alb",
                        "type": "application",
                        "scheme": "internet-facing",
                        "dns_name": "api-alb-123456789.us-east-1.elb.amazonaws.com",
                        "state": "active",
                        "availability_zones": ["us-east-1a", "us-east-1b"],
                        "target_groups": [
                            {
                                "name": "api-targets",
                                "protocol": "HTTP",
                                "port": 80,
                                "health_check_path": "/health",
                                "healthy_targets": 3,
                                "unhealthy_targets": 1,
                                "health_status": "degraded"
                            }
                        ],
                        "requests_per_second": 1250.5,
                        "active_connections": 342
                    }
                ]
            }
        
        else:
            return {"error": f"Unknown AWS service or resource: {service}/{resource_type}"}
    
    async def _get_kubernetes_resources(self, resource_type: str) -> Dict[str, Any]:
        """Fetch Kubernetes resources."""
        # TODO: Integrate with kubernetes python client
        # For now, return mock data
        
        namespace = self.config.k8s_namespace if hasattr(self.config, 'k8s_namespace') else "default"
        
        if resource_type == "pods":
            return {
                "platform": "kubernetes",
                "resource_type": "pods",
                "namespace": namespace,
                "timestamp": datetime.utcnow().isoformat(),
                "pods": [
                    {
                        "name": "api-deployment-abc123-xyz",
                        "namespace": namespace,
                        "status": "Running",
                        "phase": "Running",
                        "node": "node-01",
                        "pod_ip": "10.244.0.10",
                        "start_time": "2025-01-15T10:00:00Z",
                        "restart_count": 0,
                        "containers": [
                            {
                                "name": "api",
                                "ready": True,
                                "restart_count": 0,
                                "state": "running"
                            }
                        ],
                        "health_status": "healthy"
                    },
                    {
                        "name": "worker-deployment-def456-abc",
                        "namespace": namespace,
                        "status": "CrashLoopBackOff",
                        "phase": "Running",
                        "node": "node-02",
                        "pod_ip": "10.244.1.20",
                        "start_time": "2025-01-15T11:30:00Z",
                        "restart_count": 5,
                        "containers": [
                            {
                                "name": "worker",
                                "ready": False,
                                "restart_count": 5,
                                "state": "waiting",
                                "reason": "CrashLoopBackOff"
                            }
                        ],
                        "health_status": "unhealthy",
                        "issues": ["Container restarting frequently"]
                    }
                ]
            }
        
        elif resource_type == "deployments":
            return {
                "platform": "kubernetes",
                "resource_type": "deployments",
                "namespace": namespace,
                "timestamp": datetime.utcnow().isoformat(),
                "deployments": [
                    {
                        "name": "api-deployment",
                        "namespace": namespace,
                        "replicas": 3,
                        "ready_replicas": 3,
                        "available_replicas": 3,
                        "updated_replicas": 3,
                        "strategy": "RollingUpdate",
                        "health_status": "healthy"
                    },
                    {
                        "name": "worker-deployment",
                        "namespace": namespace,
                        "replicas": 2,
                        "ready_replicas": 1,
                        "available_replicas": 1,
                        "updated_replicas": 2,
                        "strategy": "RollingUpdate",
                        "health_status": "degraded",
                        "issues": ["Not all replicas are ready"]
                    }
                ]
            }
        
        elif resource_type == "services":
            return {
                "platform": "kubernetes",
                "resource_type": "services",
                "namespace": namespace,
                "timestamp": datetime.utcnow().isoformat(),
                "services": [
                    {
                        "name": "api-service",
                        "namespace": namespace,
                        "type": "LoadBalancer",
                        "cluster_ip": "10.96.0.10",
                        "external_ip": "54.123.45.69",
                        "ports": [
                            {"port": 80, "target_port": 8080, "protocol": "TCP"}
                        ],
                        "endpoints_count": 3,
                        "health_status": "healthy"
                    }
                ]
            }
        
        elif resource_type == "nodes":
            return {
                "platform": "kubernetes",
                "resource_type": "nodes",
                "timestamp": datetime.utcnow().isoformat(),
                "nodes": [
                    {
                        "name": "node-01",
                        "status": "Ready",
                        "roles": ["worker"],
                        "version": "v1.28.0",
                        "capacity": {
                            "cpu": "4",
                            "memory": "16Gi",
                            "pods": "110"
                        },
                        "allocatable": {
                            "cpu": "3.8",
                            "memory": "14Gi",
                            "pods": "110"
                        },
                        "conditions": [
                            {"type": "Ready", "status": "True"},
                            {"type": "MemoryPressure", "status": "False"},
                            {"type": "DiskPressure", "status": "False"}
                        ],
                        "health_status": "healthy"
                    },
                    {
                        "name": "node-02",
                        "status": "Ready",
                        "roles": ["worker"],
                        "version": "v1.28.0",
                        "capacity": {
                            "cpu": "4",
                            "memory": "16Gi",
                            "pods": "110"
                        },
                        "allocatable": {
                            "cpu": "3.8",
                            "memory": "14Gi",
                            "pods": "110"
                        },
                        "conditions": [
                            {"type": "Ready", "status": "True"},
                            {"type": "MemoryPressure", "status": "True"},
                            {"type": "DiskPressure", "status": "False"}
                        ],
                        "health_status": "degraded",
                        "issues": ["Memory pressure detected"]
                    }
                ]
            }
        
        else:
            return {"error": f"Unknown Kubernetes resource type: {resource_type}"}
    
    async def _get_overall_status(self) -> Dict[str, Any]:
        """Get overall infrastructure health status."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "degraded",
            "platforms": {
                "aws": {
                    "status": "degraded",
                    "healthy_resources": 8,
                    "degraded_resources": 3,
                    "unhealthy_resources": 1,
                    "issues": [
                        "EC2 instance i-0987654321fedcba0: High memory usage",
                        "Lambda function data-processor: High error rate"
                    ]
                },
                "kubernetes": {
                    "status": "degraded",
                    "healthy_resources": 15,
                    "degraded_resources": 2,
                    "unhealthy_resources": 1,
                    "issues": [
                        "Pod worker-deployment-def456-abc: CrashLoopBackOff",
                        "Node node-02: Memory pressure"
                    ]
                }
            },
            "summary": {
                "total_resources": 30,
                "healthy": 23,
                "degraded": 5,
                "unhealthy": 2,
                "critical_issues": 2,
                "warnings": 3
            },
            "recommendations": [
                "Investigate high memory usage on EC2 instance i-0987654321fedcba0",
                "Review Lambda function data-processor logs for error patterns",
                "Restart worker pod in CrashLoopBackOff state",
                "Investigate memory pressure on Kubernetes node-02"
            ]
        }
    
    def _is_cached(self, uri: str) -> bool:
        """Check if resource is in cache and still valid."""
        if uri not in self.cache:
            return False
        
        cache_age = (datetime.utcnow() - self.cache_timestamp[uri]).total_seconds()
        refresh_interval = self.config.refresh_interval if hasattr(self.config, 'refresh_interval') else 300
        return cache_age < refresh_interval
    
    def _cache_result(self, uri: str, result: str) -> None:
        """Cache resource result."""
        self.cache[uri] = result
        self.cache_timestamp[uri] = datetime.utcnow()