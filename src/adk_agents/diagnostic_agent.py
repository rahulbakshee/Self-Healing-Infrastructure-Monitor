"""DiagnosticAgent stub

Performs lightweight collection and root-cause suggestion using prompts.
This is a minimal async stub that returns a structured response for testing.
"""
from typing import Any, Dict, Optional
import asyncio


class DiagnosticAgent:
    def __init__(self, config: Optional[dict] = None, client: Optional[Any] = None):
        self.config = config or {}
        self.client = client

    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a diagnostic request and return a structured response.

        Expected minimal request shape (flexible):
          {"id": str, "alert": {...}, "resources": [...], "settings": {...}}
        """
        # Minimal simulated work: pretend to call model and return a diagnosis
        await asyncio.sleep(0)  # allow cooperative scheduling

        alert = request.get("alert", {})
        summary = f"Diagnostic summary for alert: {alert.get('message', '<no-message>')}"

        response = {
            "id": request.get("id"),
            "status": "ok",
            "summary": summary,
            "details": {
                "root_causes": [
                    {"id": "rc1", "description": "Example suspected cause: high CPU"}
                ],
                "evidence": [
                    {"type": "metric", "uri": "metrics://example/cpu"}
                ]
            },
            "actions": [
                {
                    "action_id": "remediate_restart_service",
                    "description": "Restart the service on the affected host (dry-run suggested)",
                    "tool": "remediate_restart_service",
                    "args": {"service": "myapp"},
                    "risk": "medium",
                }
            ]
        }

        return response
