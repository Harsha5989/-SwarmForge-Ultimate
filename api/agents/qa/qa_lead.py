"""QA Lead Agent — Test strategy planner."""

import json
from uuid import UUID
from agents.base import BaseAgent


SYSTEM_PROMPT = """You are a Senior QA Lead. Create a comprehensive test strategy.

Analyze the codebase and architecture to produce:
1. Unit test targets (functions/classes to test)
2. Integration test scenarios (API endpoint flows)
3. Performance test scenarios (endpoints to load test)

Output VALID JSON:
{
  "unit_tests": [
    {
      "module": "module_name",
      "file_path": "path/to/test_file.py",
      "targets": ["function_or_class_to_test"],
      "test_cases": ["test case description"]
    }
  ],
  "integration_tests": [
    {
      "name": "test_name",
      "flow": ["step 1", "step 2"],
      "endpoints": ["/api/endpoint"],
      "expected": "expected outcome"
    }
  ],
  "perf_scenarios": [
    {
      "endpoint": "/api/endpoint",
      "method": "GET|POST",
      "users": 10,
      "duration_sec": 60,
      "expected_p95_ms": 200
    }
  ]
}

Output ONLY the JSON.
"""


class QALeadAgent(BaseAgent):
    """Generates comprehensive test strategy."""

    def __init__(self, store, redis):
        super().__init__(
            agent_id="qa_lead",
            agent_type="QA",
            model_name="meta-agent",
            store=store,
            redis=redis,
        )

    async def run(self, session_id: str, input_data: dict) -> dict:
        await self.set_status(session_id, "RUNNING", "Planning test strategy...")

        architecture = input_data.get("architecture", {})
        code_files = await self.store.get_all_code_files(UUID(session_id))

        # Build context
        code_summary = ""
        for cf in code_files[:15]:
            code_summary += f"\n--- {cf.file_path} ({cf.language}) ---\n"
            code_summary += cf.content[:500]
            code_summary += "\n"

        result = await self.model.complete_json(
            system=SYSTEM_PROMPT,
            user=(
                f"Architecture:\n{json.dumps(architecture.get('api_contracts', []), indent=2)}\n\n"
                f"DB Schema:\n{json.dumps(architecture.get('db_schema', {}), indent=2)}\n\n"
                f"Source files:\n{code_summary}\n\n"
                f"Create a comprehensive test strategy."
            ),
        )

        # Save test plan to Redis
        await self.redis.set_json(
            f"session:{session_id}:test_plan",
            result,
            ttl=3600,
        )

        await self.emit_event(session_id, "qa.plan_ready", {
            "unit_tests_count": len(result.get("unit_tests", [])),
            "integration_count": len(result.get("integration_tests", [])),
            "perf_scenarios": len(result.get("perf_scenarios", [])),
        })

        return result
