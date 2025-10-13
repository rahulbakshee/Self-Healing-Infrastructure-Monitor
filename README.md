# 🔧 Self-Healing Infrastructure Monitor

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-enabled-green.svg)](https://modelcontextprotocol.io/)
[![ADK](https://img.shields.io/badge/ADK-Google-orange.svg)](https://developers.google.com/adk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent infrastructure monitoring system that combines **Model Context Protocol (MCP)** and **Google's Agent Development Kit (ADK)** to automatically detect, diagnose, and remediate infrastructure issues with human oversight.

## 🌟 Key Features

- **🤖 AI-Powered Diagnosis**: Multi-agent system for intelligent root cause analysis
- **🔄 Self-Healing**: Automatic remediation with safety guardrails
- **👁️ Human-in-the-Loop**: Approval workflows for critical operations
- **📊 Multi-Cloud Support**: AWS, GCP, Kubernetes integration
- **📝 Complete Audit Trail**: Every action logged and reversible
- **🔌 Extensible Architecture**: Plugin system for custom monitors
- **⚡ Real-time Monitoring**: Continuous health checks and alerting

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                   │
│              (AWS, GCP, Kubernetes, etc.)               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓ metrics, logs, events
┌─────────────────────────────────────────────────────────┐
│                    MCP Server Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Metrics    │  │     Logs     │  │Infrastructure│ │
│  │  Resources   │  │  Resources   │  │   Resources  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Diagnostic   │  │ Remediation  │  │   Rollback   │ │
│  │    Tools     │  │    Tools     │  │    Tools     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓ MCP Protocol
┌─────────────────────────────────────────────────────────┐
│                   ADK Agent Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Diagnostic   │  │ Remediation  │  │   Analysis   │ │
│  │    Agent     │  │    Agent     │  │    Agent     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Orchestration Engine                        │
│  • Workflow State Machine                               │
│  • Human Approval System                                │
│  • Audit Logging & Rollback                            │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional, for containerized deployment)
- AWS/GCP credentials (for cloud integrations)
- Google ADK API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/self-healing-infra-monitor.git
cd self-healing-infra-monitor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Or using poetry
poetry install
```

### Configuration

```bash
# Copy example config
cp config/mcp_config.yaml.example config/mcp_config.yaml
cp config/adk_config.yaml.example config/adk_config.yaml

# Edit with your credentials
vim config/mcp_config.yaml
```

### Running the Server

```bash
# Start MCP server
python -m src.mcp_server.server

# Or use the convenience script
./scripts/run_server.sh
```

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

## 📖 Usage Examples

### Basic Health Check Monitoring

```python
from src.orchestrator.workflow import HealthMonitor
from src.integrations.aws import AWSIntegration

# Initialize monitor
monitor = HealthMonitor(
    integrations=[AWSIntegration()],
    check_interval=60
)

# Start monitoring
monitor.start()
```

### Custom Remediation Action

```python
from src.mcp_server.tools.remediation import RemediationTool
from src.models.remediation import RemediationAction

# Define custom remediation
action = RemediationAction(
    name="restart_service",
    description="Restart unhealthy service",
    command="systemctl restart myapp",
    requires_approval=True,
    rollback_command="systemctl stop myapp"
)

# Register with MCP server
remediation_tool = RemediationTool()
remediation_tool.register_action(action)
```

### Kubernetes Pod Auto-Healing

```python
from src.integrations.kubernetes import K8sIntegration
from src.orchestrator.workflow import Orchestrator

# Setup K8s integration
k8s = K8sIntegration(
    namespace="production",
    auto_remediate=True
)

# Create orchestrator
orchestrator = Orchestrator(
    integrations=[k8s],
    approval_required=True
)

# Monitor and heal
orchestrator.run()
```

## 🔧 Configuration

### MCP Server Configuration (`config/mcp_config.yaml`)

```yaml
server:
  name: "self-healing-infra-monitor"
  version: "1.0.0"
  transport: "stdio"

resources:
  metrics:
    enabled: true
    providers:
      - prometheus
      - cloudwatch
  
  logs:
    enabled: true
    retention_days: 30

tools:
  diagnostics:
    timeout: 30
  remediation:
    dry_run: false
    require_approval: true
```

### ADK Agent Configuration (`config/adk_config.yaml`)

```yaml
agents:
  diagnostic:
    model: "gemini-2.0-flash-exp"
    temperature: 0.3
    max_tokens: 2000
    
  remediation:
    model: "gemini-2.0-flash-exp"
    temperature: 0.1
    max_tokens: 1500
    
  analysis:
    model: "gemini-2.0-flash-exp"
    temperature: 0.5
    max_tokens: 3000

api:
  key: "your-adk-api-key"
  timeout: 60
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test suite
pytest tests/test_mcp_server.py

# Run integration tests
pytest tests/integration/
```

## 📚 Documentation

- [Architecture Guide](docs/architecture.md)
- [Getting Started](docs/getting-started.md)
- [MCP Protocol Details](docs/mcp-protocol.md)
- [ADK Agent Guide](docs/adk-agents.md)
- [Deployment Guide](docs/deployment.md)
- [API Reference](docs/api-reference.md)

## 🔌 Integrations

### Currently Supported

- ✅ AWS (EC2, ECS, Lambda, CloudWatch)
- ✅ Kubernetes (Pods, Deployments, Services)
- ✅ Prometheus (Metrics & Alerting)

### Coming Soon

- 🚧 Google Cloud Platform
- 🚧 Azure
- 🚧 Datadog
- 🚧 PagerDuty

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Fork the repo
# Create feature branch
git checkout -b feature/amazing-feature

# Commit changes
git commit -m 'Add amazing feature'

# Push to branch
git push origin feature/amazing-feature

# Open Pull Request
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- [Google Agent Development Kit](https://developers.google.com/adk)
- Built with inspiration from modern SRE practices

## 📧 Contact

- **Author**: Rahul Bakshee
- **LinkedIn**: (https://linkedin.com/in/rahulbakshee)

## 🗺️ Roadmap

- [x] Core MCP server implementation
- [x] ADK agent integration
- [x] AWS integration
- [x] Kubernetes integration
- [ ] GCP integration
- [ ] ML-based anomaly detection
- [ ] Predictive maintenance
- [ ] Cost optimization recommendations
- [ ] Slack/Teams notifications
- [ ] Web dashboard UI

---

**⭐ Star this repo if you find it useful!**
