"""Bug Fix Agent — Targeted patch generator for test failures."""

import json
from uuid import UUID
from pathlib import Path

from agents.base import BaseAgent
from config import get_settings


SYSTEM_PROMPT = """You are an expert debugger. Fix ONLY the reported issues.

Rules:
1. Make MINIMAL changes — fix the bug, nothing else
2. Preserve all existing logic that works
3. Include all original imports
4. If fixing a security issue, explain the fix in a comment
5. Output the COMPLETE fixed file content

Output ONLY the fixed file content. No markdown fences, no explanation.
"""


class BugFixAgent(BaseAgent):
    """Applies targeted patches for test/security/perf failures."""

    def __init__(self, store, redis):
        super().__init__(
            agent_id="bug_fix",
            agent_type="QA",
            model_name="qa-agent",
            store=store,
            redis=redis,
        )

    async def run(self, session_id: str, input_data: dict) -> dict:
        fix_context = input_data.get("fix_context", {})
        fix_type = fix_context.get("type", "UNIT")
        failures = fix_context.get("failures", [])
        file_paths = fix_context.get("file_paths", [])

        await self.set_status(session_id, "RUNNING", f"Fixing {len(failures)} {fix_type} issues...")

        settings = get_settings()
        patched_count = 0

        for failure in failures[:10]:  # Limit to 10 fixes per run
            file_path = failure.get("file_path", "")
            if not file_path:
                continue

            # Get current file content
            code_file = await self.store.get_code_file(UUID(session_id), file_path)
            if not code_file:
                continue

            # Generate fix
            content, _, _ = await self.model.complete(
                system=SYSTEM_PROMPT,
                user=(
                    f"Fix this issue in {file_path}:\n\n"
                    f"Issue type: {fix_type}\n"
                    f"Description: {failure.get('description', failure.get('message', 'Unknown'))}\n"
                    f"Line: {failure.get('line', 'unknown')}\n"
                    f"Severity: {failure.get('severity', 'HIGH')}\n\n"
                    f"Current file content:\n{code_file.content}\n\n"
                    f"Fix the issue and return the complete fixed file."
                ),
            )

            # Clean markdown fences
            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)

            # Update blackboard
            await self.store.write_code_file(
                session_id=UUID(session_id),
                module_name=code_file.module_name,
                file_path=file_path,
                language=code_file.language,
                content=content,
                assigned_to=self.agent_id,
            )

            # Update filesystem
            output_path = Path(settings.output_dir) / session_id / file_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")

            patched_count += 1

        await self.emit_event(session_id, "bugfix.applied", {
            "fix_type": fix_type,
            "files_patched": patched_count,
            "total_failures": len(failures),
        })

        return {
            "fix_type": fix_type,
            "files_patched": patched_count,
        }
