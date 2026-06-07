"""Container Agent — Generates Dockerfiles and compose files for output app."""

import json
from pathlib import Path
from uuid import UUID

from agents.base import BaseAgent
from config import get_settings


SYSTEM_PROMPT = """You are a DevOps expert. Generate optimized Docker configuration.

Create a multi-stage Dockerfile that:
1. Uses the appropriate base image for the tech stack
2. Installs dependencies in a cached layer
3. Copies source code
4. Exposes the correct port
5. Uses a non-root user for security
6. Has a proper healthcheck
7. Is optimized for small image size

Output ONLY the Dockerfile content. No markdown fences.
"""


class ContainerAgent(BaseAgent):
    """Generates Dockerfiles and docker-compose for the output project."""

    def __init__(self, store, redis):
        super().__init__(
            agent_id="container_agent",
            agent_type="OPS",
            model_name="ops-agent",
            store=store,
            redis=redis,
        )

    async def run(self, session_id: str, input_data: dict) -> dict:
        settings = get_settings()
        await self.set_status(session_id, "RUNNING", "Generating Docker configs...")

        architecture = input_data.get("architecture", {})
        tech_stack = architecture.get("tech_stack", {})

        # Generate Dockerfile
        content, _, _ = await self.model.complete(
            system=SYSTEM_PROMPT,
            user=f"Generate a production Dockerfile for:\nTech stack: {json.dumps(tech_stack, indent=2)}",
        )

        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        # Write files
        output_dir = Path(settings.output_dir) / session_id
        output_dir.mkdir(parents=True, exist_ok=True)

        (output_dir / "Dockerfile").write_text(content, encoding="utf-8")

        # Write .dockerignore
        dockerignore = "__pycache__\n*.pyc\n.git\n.env\nnode_modules\n.venv\n*.egg-info\n"
        (output_dir / ".dockerignore").write_text(dockerignore, encoding="utf-8")

        # Store in blackboard
        await self.store.write_code_file(
            session_id=UUID(session_id), module_name="infrastructure",
            file_path="Dockerfile", language="dockerfile",
            content=content, assigned_to=self.agent_id,
        )

        await self.emit_event(session_id, "container.ready", {
            "files": ["Dockerfile", ".dockerignore"],
        })

        return {"files_generated": ["Dockerfile", ".dockerignore"]}
