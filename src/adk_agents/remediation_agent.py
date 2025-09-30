"""RemediationAgent stub

Produces remediation plans and enforces dry-run / approval semantics.
"""
from typing import Any, Dict, Optional
import asyncio


class RemediationAgent:
    def __init__(self, config: Optional[dict] = None, client: Optional[Any] = None):
        self.config = config or {}
        self.client = client

    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Return a remediation plan. Honor `settings.dry_run` and `settings.require_approval`.
        Minimal request shape used for testing only.
        """
        await asyncio.sleep(0)
        settings = request.get("settings", {}) or {}
        dry_run = settings.get("dry_run", True)
        require_approval = settings.get("require_approval", True)

        plan = {
            "id": request.get("id"),
            "status": "requires_approval" if require_approval else "ok",
            "summary": "Remediation plan generated",
            "details": {
                "steps": [
                    {"step": 1, "action": "notify_oncall", "args": {}},
                    {"step": 2, "action": "restart_service", "args": {"service": "myapp"}},
                ],
                "dry_run": dry_run,
            },
        }

        return plan
