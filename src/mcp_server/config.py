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

    # Load from YAML if exists and convert into the shape expected by
    # ServerConfig (nested sub-models). Environment variables still take
    # precedence via BaseSettings behavior.
    config_data: Dict[str, Any] = {}
    if Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f) or {}
            if yaml_data:
                config_data = _map_yaml_to_config(yaml_data)

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


def _map_yaml_to_config(yaml_data: Dict[str, Any]) -> Dict[str, Any]:
    """Map existing YAML example structure to ServerConfig kwargs.

    The repository's example `config/mcp_config.yaml` uses sections like
    `server`, `resources`, `tools`, and `api`. This helper picks sensible
    keys from those sections and returns a flat dict suitable for
    constructing `ServerConfig(**mapped)` where nested sub-models are
    automatically parsed by Pydantic.
    """
    mapped: Dict[str, Any] = {}

    # server -> name/version/logging
    server = yaml_data.get("server") or {}
    if isinstance(server, dict):
        mapped.update({k: v for k, v in server.items() if not isinstance(v, dict)})

    # resources -> metrics, logs, infrastructure
    resources = yaml_data.get("resources") or {}
    metrics = resources.get("metrics") or yaml_data.get("metrics")
    if metrics is not None:
        mapped["metrics_config"] = metrics

    logs = resources.get("logs") or yaml_data.get("logs")
    if logs is not None:
        mapped["logs_config"] = logs

    infra = resources.get("infrastructure") or resources.get("infra") or yaml_data.get("infrastructure") or yaml_data.get("infra")
    if infra is not None:
        mapped["infra_config"] = infra

    # tools -> diagnostics, remediation, rollback
    tools = yaml_data.get("tools") or {}
    diagnostics = tools.get("diagnostics") or yaml_data.get("diagnostics")
    if diagnostics is not None:
        mapped["diagnostics_config"] = diagnostics

    remediation = tools.get("remediation") or yaml_data.get("remediation")
    if remediation is not None:
        mapped["remediation_config"] = remediation

    rollback = tools.get("rollback") or yaml_data.get("rollback")
    if rollback is not None:
        mapped["rollback_config"] = rollback

    # api -> adk api key
    api = yaml_data.get("api") or {}
    if isinstance(api, dict) and api.get("key"):
        mapped["adk_api_key"] = api.get("key")

    # database_url top-level
    if yaml_data.get("database_url"):
        mapped["database_url"] = yaml_data.get("database_url")

    return mapped