"""Coder Agent — Generates complete source files from task specs."""

import json
import os
from pathlib import Path
from uuid import UUID

from agents.base import BaseAgent
from config import get_settings

BACKEND_PROMPT = """You are an expert Python backend developer. Write production-quality code.

Rules:
1. Write COMPLETE, working code — no TODO, no pass, no placeholder, no "..."
2. Include ALL imports at the top of the file
3. Use type hints on all function parameters and returns
4. Write docstrings for all public functions and classes
5. Follow PEP8 strictly
6. Handle errors with proper try/except blocks
7. Use async/await where appropriate
8. Security: never hardcode secrets, validate all inputs, use parameterized queries
9. The code must run without any modifications

Output ONLY the complete file content. No markdown fences, no explanation."""

FRONTEND_PROMPT = """You are an expert React/JavaScript developer. Write modern, production-quality code.

Rules:
1. Write modern React 18 with hooks (useState, useEffect, useCallback)
2. Use proper JSX syntax
3. Import all dependencies at the top
4. Handle loading and error states in components
5. Make components reusable with proper props
6. Use CSS modules or styled-components for styling
7. No console.log in production code
8. Include proper error boundaries

Output ONLY the complete file content. No markdown fences."""

DATABASE_PROMPT = """You are an expert database developer. Write production-quality SQL/ORM code.

Rules:
1. Write complete migration files or model definitions
2. Include proper indexes for query performance
3. Use appropriate data types and constraints
4. Add foreign keys with proper CASCADE/SET NULL behavior
5. Include created_at/updated_at timestamps
6. Never use raw SQL without parameterization

Output ONLY the complete file content. No markdown fences."""

API_PROMPT = """You are an expert API developer. Write production-quality API route handlers.

Rules:
1. Write complete route handlers with proper HTTP methods
2. Include request validation using Pydantic models
3. Return proper HTTP status codes (201 for create, 404 for not found, etc.)
4. Include authentication/authorization checks where needed
5. Handle all edge cases and errors gracefully
6. Write comprehensive docstrings for API documentation
7. Use dependency injection for database sessions

Output ONLY the complete file content. No markdown fences."""


class CoderAgent(BaseAgent):
    """Generates complete source files from architecture tasks."""

    PROMPTS = {
        "coder-backend": BACKEND_PROMPT,
        "coder-frontend": FRONTEND_PROMPT,
        "coder-database": DATABASE_PROMPT,
        "coder-api": API_PROMPT,
    }

    def __init__(self, coder_model: str, store, redis):
        agent_id = f"coder_{coder_model.split('-')[-1]}"
        super().__init__(
            agent_id=agent_id,
            agent_type="DEV",
            model_name=coder_model,
            store=store,
            redis=redis,
        )

    async def run(self, session_id: str, input_data: dict) -> dict:
        task = input_data.get("task", input_data)
        file_path = task.get("file_path", "unknown.py")
        module = task.get("module", "main")
        language = task.get("language", "python")
        responsibility = task.get("responsibility", "")
        tech_stack = task.get("tech_stack", {})
        api_contracts = task.get("api_contracts", [])
        db_schema = task.get("db_schema", {})

        await self.set_status(session_id, "RUNNING", f"Writing {file_path}...")

        # Get context from existing files in same module
        existing_files = await self.store.get_all_code_files(UUID(session_id))
        related = [f for f in existing_files if f.module_name == module and f.file_path != file_path]
        context = ""
        for f in related[:5]:  # Limit context to 5 related files
            context += f"\n--- {f.file_path} ---\n{f.content[:1000]}\n"

        system_prompt = self.PROMPTS.get(self.model_name, BACKEND_PROMPT)

        user_prompt = (
            f"Generate the complete source file for:\n\n"
            f"File: {file_path}\n"
            f"Module: {module}\n"
            f"Language: {language}\n"
            f"Responsibility: {responsibility}\n\n"
            f"Tech Stack: {json.dumps(tech_stack, indent=2)}\n\n"
            f"API Contracts (relevant):\n{json.dumps(api_contracts[:10], indent=2)}\n\n"
            f"DB Schema:\n{json.dumps(db_schema, indent=2)}\n\n"
        )

        if context:
            user_prompt += f"Related files already written (for import reference):\n{context}\n\n"

        user_prompt += "Write the COMPLETE file content now."

        content, tokens_in, tokens_out = await self.model.complete(
            system=system_prompt,
            user=user_prompt,
        )

        # Clean markdown fences if LLM included them
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = lines[1:]  # Remove opening fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        # Write to blackboard
        await self.store.write_code_file(
            session_id=UUID(session_id),
            module_name=module,
            file_path=file_path,
            language=language,
            content=content,
            assigned_to=self.agent_id,
        )

        # Write to filesystem
        settings = get_settings()
        output_path = Path(settings.output_dir) / session_id / file_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

        await self.log_action(
            session_id, "COMPLETED",
            summary=f"Generated {file_path} ({len(content)} chars)",
            tokens_in=tokens_in, tokens_out=tokens_out,
        )

        await self.emit_event(session_id, "file.created", {
            "file_path": file_path,
            "module": module,
            "language": language,
            "size_bytes": len(content),
        })

        return {
            "file_path": file_path,
            "module": module,
            "language": language,
            "content_length": len(content),
        }


async def run_all_coders(session_id: str, tasks: list, store, redis) -> list[dict]:
    """Run all coder tasks — processes them sequentially to respect rate limits."""
    results = []
    for task in tasks:
        coder_model = task.get("coder_model", "coder-backend")
        coder = CoderAgent(coder_model=coder_model, store=store, redis=redis)
        result = await coder.execute(session_id, {"task": task})
        results.append(result)
    return results
