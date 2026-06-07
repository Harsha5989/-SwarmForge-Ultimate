"""CPO Agent — Feasibility validator, acceptance criteria definer."""

from uuid import UUID
from agents.base import BaseAgent


SYSTEM_PROMPT = """You are the CPO (Chief Product Officer) of SwarmForge, an autonomous software factory.
You receive a structured spec artifact from the CEO agent. Your job is to:

1. Assess feasibility of each goal — is it realistic and well-defined?
2. Enrich each goal with concrete, measurable acceptance criteria.
3. Flag any unclear, conflicting, or impossible requirements.
4. Add a feasibility assessment summary.

Output VALID JSON matching this schema:
{
  "goals": [
    {
      "id": "G1",
      "title": "...",
      "priority": "HIGH|MEDIUM|LOW",
      "description": "...",
      "acceptance_criteria": ["enriched criterion 1", "enriched criterion 2", "..."],
      "feasibility": "FEASIBLE|NEEDS_CLARIFICATION|RISKY",
      "notes": "any notes about this goal"
    }
  ],
  "feasibility_summary": "Overall assessment of project feasibility",
  "risks": ["risk 1", "risk 2"],
  "suggestions": ["suggestion 1", "suggestion 2"]
}

Rules:
1. Keep all original goals but enrich them.
2. Each goal MUST have at least 3 acceptance criteria that are measurable.
3. Be specific — "User can log in" is too vague. "User can log in with email/password and receives a JWT token" is better.
4. Output ONLY the JSON, no markdown.
"""


class CPOAgent(BaseAgent):
    """Validates feasibility and enriches acceptance criteria."""

    def __init__(self, store, redis):
        super().__init__(
            agent_id="cpo",
            agent_type="META",
            model_name="meta-agent",
            store=store,
            redis=redis,
        )

    async def run(self, session_id: str, input_data: dict) -> dict:
        spec = input_data.get("spec", {})
        goals = spec.get("goals", [])
        tech_req = spec.get("tech_req", {})

        await self.set_status(session_id, "RUNNING", "Validating feasibility...")

        result = await self.model.complete_json(
            system=SYSTEM_PROMPT,
            user=(
                f"Here is the spec artifact to validate:\n\n"
                f"Goals: {goals}\n\n"
                f"Tech Requirements: {tech_req}\n\n"
                f"Constraints: {spec.get('constraints', [])}\n\n"
                f"Enrich and validate these goals."
            ),
        )

        enriched_goals = result.get("goals", goals)
        feasibility = result.get("feasibility_summary", "Assessment complete")

        # Update the spec artifact with enriched goals
        await self.store.write_spec_artifact(
            session_id=UUID(session_id),
            goals=enriched_goals,
            tech_req=tech_req,
            constraints=spec.get("constraints", []),
            feasibility=feasibility,
        )

        await self.emit_event(session_id, "planning.complete", {
            "feasibility": feasibility[:200],
            "risks_count": len(result.get("risks", [])),
        })

        return {
            "goals": enriched_goals,
            "tech_req": tech_req,
            "constraints": spec.get("constraints", []),
            "feasibility": feasibility,
            "risks": result.get("risks", []),
        }
