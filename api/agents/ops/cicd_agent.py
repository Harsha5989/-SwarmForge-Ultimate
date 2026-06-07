"""CI/CD Agent — GitHub Actions workflow generator."""

import json
from pathlib import Path
from uuid import UUID

from agents.base import BaseAgent
from config import get_settings


SYSTEM_PROMPT = """You are a CI/CD expert. Generate a comprehensive GitHub Actions workflow.

The workflow should:
1. Run on push to main and pull requests
2. Jobs: lint → test → security-scan → build → deploy (placeholder)
3. Use appropriate language-specific linters and test runners
4. Include caching for dependencies
5. Set proper environment variables

Output ONLY the YAML content. No markdown fences.
"""


class CICDAgent(BaseAgent):
    """Generates GitHub Actions CI/CD workflows."""

    def __init__(self, store, redis):
        super().__init__(
            agent_id="cicd_agent",
            agent_type="OPS",
            model_name="ops-agent",
            store=store,
            redis=redis,
        )

    async def run(self, session_id: str, input_data: dict) -> dict:
        settings = get_settings()
        await self.set_status(session_id, "RUNNING", "Generating CI/CD pipeline...")

        architecture = input_data.get("architecture", {})
        tech_stack = architecture.get("tech_stack", {})

        content, _, _ = await self.model.complete(
            system=SYSTEM_PROMPT,
            user=f"Generate a GitHub Actions CI/CD workflow for:\nTech stack: {json.dumps(tech_stack, indent=2)}",
        )

        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        output_dir = Path(settings.output_dir) / session_id / ".github" / "workflows"
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "ci.yml").write_text(content, encoding="utf-8")

        await self.store.write_code_file(
            session_id=UUID(session_id), module_name="infrastructure",
            file_path=".github/workflows/ci.yml", language="yaml",
            content=content, assigned_to=self.agent_id,
        )

        await self.emit_event(session_id, "cicd.configured", {
            "files": [".github/workflows/ci.yml"],
        })

        return {"files_generated": [".github/workflows/ci.yml"]}
