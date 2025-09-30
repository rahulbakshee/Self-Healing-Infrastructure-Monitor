# Self-Healing Infrastructure Monitor - Project Setup Script (Windows)
# Run this with: powershell -ExecutionPolicy Bypass -File setup_project_clean.ps1

Write-Host "Setting up Self-Healing Infrastructure Monitor..." -ForegroundColor Green

# Create directory structure
Write-Host "Creating directory structure..." -ForegroundColor Cyan

$directories = @(
    "src\mcp_server\resources",
    "src\mcp_server\tools",
    "src\adk_agents\prompts",
    "src\orchestrator",
    "src\integrations",
    "src\models",
    "src\utils",
    "config",
    "tests\fixtures",
    "tests\integration",
    "examples",
    "scripts",
    "docs",
    "data",
    ".github\workflows"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Write-Host "  Created: $dir" -ForegroundColor Gray
}

# Create __init__.py files
Write-Host "Creating __init__.py files..." -ForegroundColor Cyan

$initFiles = @(
    "src\__init__.py",
    "src\mcp_server\__init__.py",
    "src\mcp_server\resources\__init__.py",
    "src\mcp_server\tools\__init__.py",
    "src\adk_agents\__init__.py",
    "src\orchestrator\__init__.py",
    "src\integrations\__init__.py",
    "src\models\__init__.py",
    "src\utils\__init__.py",
    "tests\__init__.py"
)

foreach ($file in $initFiles) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}

# Create .gitignore
Write-Host "Creating .gitignore..." -ForegroundColor Cyan

$gitignoreContent = @"
# Python
__pycache__/
*.py[cod]
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
coverage.xml
*.cover

# Environment variables
.env
.env.local

# Database
*.db
*.sqlite
*.sqlite3
data/*.db

# Logs
*.log
logs/

# Config (keep examples)
config/mcp_config.yaml
config/adk_config.yaml
config/infrastructure.yaml
!config/*.example

# Secrets
secrets/
*.pem
*.key
credentials.json

# OS
.DS_Store
Thumbs.db

# Documentation builds
site/
docs/_build/

# MyPy
.mypy_cache/
.dmypy.json
dmypy.json
"@

Set-Content -Path ".gitignore" -Value $gitignoreContent -Encoding UTF8

# Create .env.example
Write-Host "Creating .env.example..." -ForegroundColor Cyan

$envExampleContent = @"
# Self-Healing Infrastructure Monitor - Environment Variables

# Server Configuration
SHIM_NAME=self-healing-infra-monitor
SHIM_VERSION=1.0.0
SHIM_LOG_LEVEL=INFO

# Google ADK
SHIM_ADK_API_KEY=your-adk-api-key-here

# AWS Credentials (optional - can use AWS CLI config)
# SHIM_AWS_ACCESS_KEY_ID=your-aws-access-key
# SHIM_AWS_SECRET_ACCESS_KEY=your-aws-secret-key
SHIM_AWS_REGION=us-east-1

# Database
SHIM_DATABASE_URL=sqlite+aiosqlite:///./data/shim.db

# Prometheus (if using)
SHIM_PROMETHEUS_URL=http://localhost:9090

# Kubernetes (if using)
SHIM_K8S_NAMESPACE=default
"@

Set-Content -Path ".env.example" -Value $envExampleContent -Encoding UTF8

# Create example config files
Write-Host "Creating example config files..." -ForegroundColor Cyan

# MCP Config
$mcpConfigContent = @"
server:
  name: "self-healing-infra-monitor"
  version: "1.0.0"
  log_level: "INFO"

resources:
  metrics:
    enabled: true
    providers:
      - prometheus
      - cloudwatch
    prometheus_url: "http://localhost:9090"
    aws_region: "us-east-1"
    cache_ttl: 60
  
  logs:
    enabled: true
    sources:
      - cloudwatch
      - kubernetes
    retention_days: 30
    max_lines: 10000
  
  infrastructure:
    enabled: true
    platforms:
      - aws
      - kubernetes
    aws_region: "us-east-1"
    k8s_namespace: "default"
    refresh_interval: 300

tools:
  diagnostics:
    timeout: 30
    max_depth: 5
    enable_ml: false
  
  remediation:
    dry_run_only: false
    require_approval: true
    max_retries: 3
    rollback_on_failure: true
    allowed_actions:
      - restart_service
      - scale_up
      - scale_down
      - clear_cache
      - restart_pod
  
  rollback:
    enabled: true
    history_retention_days: 7
    auto_rollback_on_failure: true

database:
  url: "sqlite+aiosqlite:///./data/shim.db"
"@

Set-Content -Path "config\mcp_config.yaml.example" -Value $mcpConfigContent -Encoding UTF8

# ADK Config
$adkConfigContent = @"
agents:
  diagnostic:
    model: "gemini-2.0-flash-exp"
    temperature: 0.3
    max_tokens: 2000
    system_prompt: "You are an expert infrastructure diagnostic agent."
    
  remediation:
    model: "gemini-2.0-flash-exp"
    temperature: 0.1
    max_tokens: 1500
    system_prompt: "You are an expert remediation agent focused on safe infrastructure fixes."
    
  analysis:
    model: "gemini-2.0-flash-exp"
    temperature: 0.5
    max_tokens: 3000
    system_prompt: "You are an expert at root cause analysis."

api:
  timeout: 60
  retry_attempts: 3
  retry_delay: 2
"@

Set-Content -Path "config\adk_config.yaml.example" -Value $adkConfigContent -Encoding UTF8

# Thresholds Config
$thresholdsConfigContent = @"
# Infrastructure health thresholds

metrics:
  cpu:
    warning: 70
    critical: 85
  memory:
    warning: 75
    critical: 90
  disk:
    warning: 80
    critical: 95
  
alerts:
  error_rate:
    warning: 0.05
    critical: 0.10
  
  response_time:
    warning: 1000
    critical: 3000
"@

Set-Content -Path "config\thresholds.yaml.example" -Value $thresholdsConfigContent -Encoding UTF8

# Create LICENSE
Write-Host "Creating LICENSE..." -ForegroundColor Cyan

$licenseContent = @"
MIT License

Copyright (c) 2025 Self-Healing Infrastructure Monitor Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"@

Set-Content -Path "LICENSE" -Value $licenseContent -Encoding UTF8

Write-Host ""
Write-Host "SUCCESS: Directory structure created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Copy the README.md, pyproject.toml, and requirements.txt files from artifacts"
Write-Host "2. Copy all source code files I provide into their respective directories"
Write-Host "3. Run: Copy-Item .env.example .env"
Write-Host "4. Edit .env with your actual API keys"
Write-Host "5. Copy config files by removing .example extension"
Write-Host ""
Write-Host "Setup complete! Ready for code files." -ForegroundColor Green