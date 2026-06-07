"""Docs Agent — README, architecture docs, and API docs generator."""

import json
from pathlib import Path
from uuid import UUID

from agents.base import BaseAgent
from config import get_settings


SYSTEM_PROMPT = """You are a technical writer. Generate professional documentation.

Create a comprehensive README.md with:
1. Project title and description
2. Features list
3. Tech stack
4. Prerequisites
5. Installation / Quick Start instructions
6. Environment variables table
7. API endpoints table
8. Project structure
9. Development guide
10. Testing instructions
11. License section

Use proper Markdown formatting with headers, tables, code blocks, and badges.
Output ONLY the Markdown content.
"""


class DocsAgent(BaseAgent):
    """Generates project documentation."""

    def __init__(self, store, redis):
        super().__init__(
            agent_id="docs_agent",
            agent_type="OPS",
            model_name="ops-agent",
            store=store,
            redis=redis,
        )

    async def run(self, session_id: str, input_data: dict) -> dict:
        settings = get_settings()
        await self.set_status(session_id, "RUNNING", "Generating documentation...")

        spec = await self.store.get_spec_artifact(UUID(session_id))
        arch = await self.store.get_architecture(UUID(session_id))
        code_files = await self.store.get_all_code_files(UUID(session_id))

        spec_text = json.dumps({"goals": spec.goals, "tech_req": spec.tech_req}, indent=2) if spec else "{}"
        arch_text = json.dumps({
            "tech_stack": arch.tech_stack,
            "api_contracts": arch.api_contracts,
            "components": arch.components,
        }, indent=2) if arch else "{}"

        file_list = [cf.file_path for cf in code_files]

        content, _, _ = await self.model.complete(
            system=SYSTEM_PROMPT,
            user=(
                f"Generate README.md for this project:\n\n"
                f"Spec: {spec_text}\n\n"
                f"Architecture: {arch_text}\n\n"
                f"Files: {file_list}\n"
            ),
        )

        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        output_dir = Path(settings.output_dir) / session_id
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "README.md").write_text(content, encoding="utf-8")

        await self.store.write_code_file(
            session_id=UUID(session_id), module_name="docs",
            file_path="README.md", language="markdown",
            content=content, assigned_to=self.agent_id,
        )

        await self.emit_event(session_id, "docs.generated", {
            "files": ["README.md"],
        })

        return {"files_generated": ["README.md"]}
