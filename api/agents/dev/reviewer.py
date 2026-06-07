"""Reviewer Agent — Code quality scorer, comment generator."""

import json
from uuid import UUID

from agents.base import BaseAgent


SYSTEM_PROMPT = """You are an expert code reviewer. Review each source file and score it.

For each file, score on these criteria (total 100):
- Logic correctness (40 pts): Does code do what it should? Are there bugs?
- Code style (20 pts): Clean, readable, follows language conventions?
- Security (20 pts): No injections, no hardcoded secrets, proper input validation?
- Completeness (20 pts): No stubs/TODOs, handles edge cases, error handling?

Output VALID JSON:
{
  "files": {
    "relative/path/to/file.py": {
      "score": 85,
      "logic": 35,
      "style": 18,
      "security": 17,
      "completeness": 15,
      "comments": [
        {"line": 42, "severity": "ERROR", "message": "SQL injection vulnerability"},
        {"line": 15, "severity": "WARN", "message": "Missing input validation"},
        {"line": 88, "severity": "INFO", "message": "Consider using a constant"}
      ]
    }
  },
  "aggregate_score": 82.5,
  "summary": "Brief overall assessment"
}

Be thorough but fair. Real production code typically scores 70-90.
Output ONLY the JSON.
"""


class ReviewerAgent(BaseAgent):
    """Reviews all code files and assigns quality scores."""

    def __init__(self, store, redis):
        super().__init__(
            agent_id="reviewer",
            agent_type="DEV",
            model_name="reviewer-agent",
            store=store,
            redis=redis,
        )

    async def run(self, session_id: str, input_data: dict) -> dict:
        await self.set_status(session_id, "RUNNING", "Reviewing all source files...")

        # Get all code files from blackboard
        code_files = await self.store.get_all_code_files(UUID(session_id))

        if not code_files:
            self.log.warning("no_files_to_review")
            return {"aggregate_score": 0, "file_count": 0}

        # Build review input — send files in batches if too many
        files_text = ""
        for cf in code_files:
            files_text += f"\n=== FILE: {cf.file_path} ({cf.language}) ===\n"
            files_text += cf.content[:3000]  # Limit per file for context window
            files_text += "\n=== END FILE ===\n"

        result = await self.model.complete_json(
            system=SYSTEM_PROMPT,
            user=f"Review these {len(code_files)} source files:\n{files_text}",
        )

        file_reviews = result.get("files", {})
        aggregate = result.get("aggregate_score", 0)

        # Update each file's review in the blackboard
        for cf in code_files:
            review = file_reviews.get(cf.file_path, {})
            score = review.get("score", 50)
            comments = review.get("comments", [])
            status = "APPROVED" if score >= 80 else "NEEDS_REVISION"

            await self.store.update_code_review(
                session_id=UUID(session_id),
                file_path=cf.file_path,
                review_score=score,
                comments=comments,
                status=status,
            )

            await self.emit_event(session_id, "file.updated", {
                "file_path": cf.file_path,
                "review_score": score,
                "status": status,
                "comments_count": len(comments),
            })

        # Emit gate result
        gate_passed = aggregate >= 80
        await self.emit_event(session_id, "gate.build", {
            "score": aggregate,
            "passed": gate_passed,
            "files_reviewed": len(code_files),
        })

        self.log.info("review_complete", aggregate=aggregate, passed=gate_passed)

        return {
            "aggregate_score": aggregate,
            "file_count": len(code_files),
            "gate_passed": gate_passed,
            "summary": result.get("summary", ""),
        }
