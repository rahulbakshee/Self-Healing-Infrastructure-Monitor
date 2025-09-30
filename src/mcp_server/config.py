"""
Configuration management for MCP Server.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import yaml


class MetricsConfig(BaseModel):
    """Configuration for metrics resource provider."""
    enabled: bool = True
    providers: List[str] = Field(default_factory=lambda: ["prometheus", "cloudwatch"])
    prometheus_url: Optional[str] = None
    aws_region: Optional[str] = "us-east-1"
    cache_ttl: int = 60  # seconds


class LogsConfig(BaseModel):
    """Configuration for logs resource provider."""
    enabled: bool = True
    sources: List[str] = Field(default_factory=lambda: ["cloudwatch", "kubernetes"])
    retention_days: int = 30
    max_lines: int = 10000


class InfraConfig(BaseModel):
    """Configuration for infrastructure resource provider."""
    enabled: bool = True
    platforms: List[str] = Field(default_factory=lambda: ["aws", "kubernetes"])
    aws_region: Optional[str] = "us-east-1"
    k8s_namespace: Optional[str] = "default"
    refresh_interval: int = 300  # seconds


class DiagnosticsConfig(BaseModel):
    """Configuration for diagnostics tools."""
    timeout: int = 30  # seconds
    max_depth: int = 5  # max depth for root cause analysis
    enable_ml: bool = False  # ML-based anomaly detection


class RemediationConfig(BaseModel):
    """Configuration for remediation tools."""
    dry_run_only: bool = False
    require_approval: bool = True
    max_retries: int = 3
    rollback_on_failure: bool = True
    allowed_actions: List[str] = Field(
        default_factory=lambda: [
            "restart_service",
            "scale_up",
            "scale_down",
            "clear_cache",
            "restart_pod"
        ]
    )


class RollbackConfig(BaseModel):
    """Configuration for rollback tools."""
    enabled: bool = True
    history_retention_days: int = 7
    auto_rollback_on_failure: bool = True


class ServerConfig(BaseSettings):
    """Main server configuration."""
    name: str = "self-healing-infra-monitor"
    version: str = "1.0.0"
    log_level: str = "INFO"
    
    # Sub-configurations
    metrics_config: MetricsConfig = Field(default_factory=MetricsConfig)
    logs_config: LogsConfig = Field(default_factory=LogsConfig)
    infra_config: InfraConfig = Field(default_factory=InfraConfig)
    diagnostics_config: DiagnosticsConfig = Field(default_factory=DiagnosticsConfig)
    remediation_config: RemediationConfig = Field(default_factory=RemediationConfig)
    rollback_config: RollbackConfig = Field(default_factory=RollbackConfig)
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/shim.db"
    
    # API Keys (loaded from environment)
    adk_api_key: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    class Config:
        env_prefix = "SHIM_"
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config(config_path: Optional[str] = None) -> ServerConfig:
    """
    Load configuration from YAML file and environment variables.
    
    Args:
        config_path: Path to YAML config file. If None, uses default location.
    
    Returns:
        ServerConfig instance with loaded configuration.
    """
    # Default config path
    if config_path is None:
        config_path = os.getenv("SHIM_CONFIG_PATH", "config/mcp_config.yaml")
    
    # Load from YAML if exists
    config_data = {}
    if Path(config_path).exists():
        with open(config_path, 'r') as f:
            yaml_data = yaml.safe_load(f)
            if yaml_data:
                config_data = _flatten_config(yaml_data)
    
    # Merge with environment variables (env vars take precedence)
    return ServerConfig(**config_data)


def _flatten_config(data: Dict[str, Any], parent_key: str = '') -> Dict[str, Any]:
    """Flatten nested config dictionary for Pydantic."""
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}_{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_config(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)