"""
Self-Healing Infrastructure Monitor - MCP Server

This module implements the main MCP server that exposes infrastructure resources
and tools for monitoring, diagnostics, and remediation.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import BaseModel, Field

from .resources.metrics import MetricsResourceProvider
from .resources.logs import LogsResourceProvider
from .resources.infrastructure import InfrastructureResourceProvider
from .tools.diagnostics import DiagnosticsTool
from .tools.remediation import RemediationTool
from .tools.rollback import RollbackTool
from .config import ServerConfig, load_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InfrastructureMonitorServer:
    """
    Main MCP Server for Self-Healing Infrastructure Monitor.
    
    This server exposes:
    - Resources: Metrics, Logs, Infrastructure State
    - Tools: Diagnostics, Remediation, Rollback
    """
    
    def __init__(self, config: ServerConfig):
        """Initialize the MCP server with configuration."""
        self.config = config
        self.server = Server(config.name)
        
        # Initialize resource providers
        self.metrics_provider = MetricsResourceProvider(config.metrics_config)
        self.logs_provider = LogsResourceProvider(config.logs_config)
        self.infra_provider = InfrastructureResourceProvider(config.infra_config)
        
        # Initialize tools
        self.diagnostics_tool = DiagnosticsTool(config.diagnostics_config)
        self.remediation_tool = RemediationTool(config.remediation_config)
        self.rollback_tool = RollbackTool(config.rollback_config)
        
        # Register handlers
        self._register_resource_handlers()
        self._register_tool_handlers()
        
        logger.info(f"Initialized {config.name} v{config.version}")
    
    def _register_resource_handlers(self) -> None:
        """Register all resource handlers with the MCP server."""
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List all available resources."""
            resources = []
            
            # Metrics resources
            if self.config.metrics_config.enabled:
                resources.extend(await self.metrics_provider.list_resources())
            
            # Logs resources
            if self.config.logs_config.enabled:
                resources.extend(await self.logs_provider.list_resources())
            
            # Infrastructure resources
            if self.config.infra_config.enabled:
                resources.extend(await self.infra_provider.list_resources())
            
            logger.info(f"Listed {len(resources)} resources")
            return resources
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a specific resource by URI."""
            logger.info(f"Reading resource: {uri}")
            
            # Route to appropriate provider based on URI scheme
            if uri.startswith("metrics://"):
                return await self.metrics_provider.read_resource(uri)
            elif uri.startswith("logs://"):
                return await self.logs_provider.read_resource(uri)
            elif uri.startswith("infra://"):
                return await self.infra_provider.read_resource(uri)
            else:
                raise ValueError(f"Unknown resource URI scheme: {uri}")
    
    def _register_tool_handlers(self) -> None:
        """Register all tool handlers with the MCP server."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available tools."""
            tools = []
            
            # Diagnostics tools
            tools.extend(await self.diagnostics_tool.list_tools())
            
            # Remediation tools
            if not self.config.remediation_config.dry_run_only:
                tools.extend(await self.remediation_tool.list_tools())
            
            # Rollback tools
            tools.extend(await self.rollback_tool.list_tools())
            
            logger.info(f"Listed {len(tools)} tools")
            return tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute a tool with given arguments."""
            logger.info(f"Calling tool: {name} with args: {arguments}")
            
            try:
                # Route to appropriate tool
                if name.startswith("diagnose_"):
                    result = await self.diagnostics_tool.execute(name, arguments)
                elif name.startswith("remediate_"):
                    result = await self.remediation_tool.execute(name, arguments)
                elif name.startswith("rollback_"):
                    result = await self.rollback_tool.execute(name, arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            
            except Exception as e:
                logger.error(f"Tool execution failed: {str(e)}")
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "tool": name,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                )]
    
    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting MCP server...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main() -> None:
    """Main entry point for the MCP server."""
    # Load configuration
    config = load_config()
    
    # Create and run server
    server = InfrastructureMonitorServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())