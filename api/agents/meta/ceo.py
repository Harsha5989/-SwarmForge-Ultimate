"""CEO Agent — Goal decomposer, spec analyzer."""

import json
from uuid import UUID

from agents.base import BaseAgent


SYSTEM_PROMPT = """You are the CEO of SwarmForge, an autonomous software factory.
Your job is to analyze a user's natural language specification and decompose it into
a structured software project definition.

You must output VALID JSON matching this exact schema:
{
  "project_name": "string - short snake_case name for the project",
  "goals": [
    {
      "id": "G1",
      "title": "short goal title",
      "priority": "HIGH|MEDIUM|LOW",
      "description": "detailed description of this goal",
      "acceptance_criteria": ["criterion 1", "criterion 2"]
    }
  ],
  "tech_req": {
    "primary_language": "python|javascript|typescript|go|rust",
    "framework": "fastapi|express|django|flask|nextjs|none",
    "db_type": "postgresql|mongodb|sqlite|mysql|none",
    "auth_type": "jwt|session|oauth|apikey|none",
    "api_style": "rest|graphql|grpc",
    "frontend": "react|vue|svelte|none",
    "additional": ["list of other specific requirements"]
  },
  "constraints": ["constraint strings - e.g. must be containerized"],
  "estimated_complexity": "LOW|MEDIUM|HIGH"
}

Rules:
1. Be thorough - extract every requirement from the spec.
2. If the spec is vague, make reasonable assumptions and note them in constraints.
3. Break complex features into separate goals.
4. Each goal MUST have at least 2 acceptance criteria.
5. Output ONLY the JSON object, no markdown fences, no explanation.
"""


class CEOAgent(BaseAgent):
    """Parses natural language specs into structured project definitions."""

    def __init__(self, store, redis):
        super().__init__(
            agent_id="ceo",
            agent_type="META",
            model_name="meta-agent",
            store=store,
            redis=redis,
        )

    async def run(self, session_id: str, input_data: dict) -> dict:
        raw_spec = input_data.get("raw_spec", "")
        self.log.info("parsing_spec", spec_length=len(raw_spec))

        await self.set_status(session_id, "RUNNING", "Analyzing specification...")

        # Call LLM to decompose the spec
        result = await self.model.complete_json(
            system=SYSTEM_PROMPT,
            user=f"Here is the user's software specification:\n\n{raw_spec}\n\nDecompose this into a structured project definition.",
        )

        # Validate required fields
        goals = result.get("goals", [])
        tech_req = result.get("tech_req", {})
        constraints = result.get("constraints", [])

        if not goals:
            raise ValueError("CEO agent produced no goals from the spec")

        # Write to blackboard
        spec = await self.store.write_spec_artifact(
            session_id=UUID(session_id),
            goals=goals,
            tech_req=tech_req,
            constraints=constraints,
        )

        await self.emit_event(session_id, "spec.ready", {
            "goals_count": len(goals),
            "project_name": result.get("project_name", "unknown"),
            "complexity": result.get("estimated_complexity", "MEDIUM"),
        })

        self.log.info("spec_parsed", goals=len(goals), complexity=result.get("estimated_complexity"))

        return {
            "spec_id": str(spec.id),
            "project_name": result.get("project_name", "unknown"),
            "goals": goals,
            "tech_req": tech_req,
            "constraints": constraints,
        }
