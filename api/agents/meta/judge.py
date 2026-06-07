"""Judge Agent — Quality arbiter, gate decider, escalation authority."""

from uuid import UUID
from agents.base import BaseAgent
from config import get_settings


SYSTEM_PROMPT = """You are the impartial Quality Judge of SwarmForge, an autonomous software factory.
You analyze quality scores from all pipeline gates and make a verdict.

You receive:
- code_quality score (0-100) — from code reviewer
- test_coverage score (0-100) — from unit tests
- security_score (0-100) — from security auditor
- perf_score (0-100) — from performance analyzer
- overall weighted score (0-100)
- iteration count and retry counts

Your decision must be one of:
- "GO" — all gates pass, software is production-ready. Deploy it.
- "NO_GO" — some gates failed but retries available. Fix and retry.
- "ESCALATE" — too many retries exhausted. Need re-architecture.
- "FAILED" — max iterations reached. Stop the pipeline.

Output VALID JSON:
{
  "verdict": "GO|NO_GO|ESCALATE|FAILED",
  "reason": "Brief explanation of your decision",
  "failing_gates": ["list of gate names that failed"],
  "recommendations": ["specific improvement suggestions"]
}

Be strict but fair. Only issue GO if quality is genuinely production-ready.
Output ONLY the JSON.
"""


class JudgeAgent(BaseAgent):
    """Makes Go/No-Go decisions based on quality gate scores."""

    def __init__(self, store, redis):
        super().__init__(
            agent_id="judge",
            agent_type="META",
            model_name="judge-agent",
            store=store,
            redis=redis,
        )

    async def run(self, session_id: str, input_data: dict) -> dict:
        settings = get_settings()
        quality = input_data.get("quality", {})
        iteration = input_data.get("iteration", 0)
        build_retries = input_data.get("build_retries", 0)
        test_retries = input_data.get("test_retries", 0)
        sec_retries = input_data.get("sec_retries", 0)
        perf_retries = input_data.get("perf_retries", 0)

        await self.set_status(session_id, "RUNNING", "Evaluating quality gates...")

        # Check if we've exceeded max iterations
        if iteration >= settings.max_iterations:
            verdict = "FAILED"
            reason = f"Maximum iterations ({settings.max_iterations}) reached."
        else:
            # Let the LLM make a nuanced decision
            result = await self.model.complete_json(
                system=SYSTEM_PROMPT,
                user=(
                    f"Quality Scores:\n"
                    f"- code_quality: {quality.get('code_quality', 0):.1f} (threshold: {settings.build_gate_min_score})\n"
                    f"- test_coverage: {quality.get('test_coverage', 0):.1f} (threshold: {settings.test_gate_min_coverage})\n"
                    f"- security_score: {quality.get('security_score', 0):.1f} (threshold: {settings.security_gate_min_score})\n"
                    f"- perf_score: {quality.get('perf_score', 0):.1f} (threshold: 80)\n"
                    f"- overall: {quality.get('overall', 0):.1f} (threshold: {settings.final_gate_min_score})\n\n"
                    f"Iteration: {iteration}/{settings.max_iterations}\n"
                    f"Build retries: {build_retries}/{settings.max_retries_per_gate}\n"
                    f"Test retries: {test_retries}/{settings.max_retries_per_gate}\n"
                    f"Security retries: {sec_retries}/{settings.max_retries_per_gate}\n"
                    f"Perf retries: {perf_retries}/{settings.max_retries_per_gate}\n\n"
                    f"Make your verdict."
                ),
            )
            verdict = result.get("verdict", "NO_GO")
            reason = result.get("reason", "No reason provided")

        # Override with deterministic logic for edge cases
        overall = quality.get("overall", 0)
        all_gates_pass = all([
            quality.get("code_quality", 0) >= settings.build_gate_min_score,
            quality.get("test_coverage", 0) >= settings.test_gate_min_coverage,
            quality.get("security_score", 0) >= settings.security_gate_min_score,
            quality.get("perf_score", 0) >= 80,
        ])

        if overall >= settings.final_gate_min_score and all_gates_pass:
            verdict = "GO"
        elif any(r >= settings.max_retries_per_gate for r in [build_retries, test_retries, sec_retries, perf_retries]):
            verdict = "ESCALATE"

        # Write quality score to blackboard
        await self.store.write_quality_score(
            session_id=UUID(session_id),
            iteration=iteration,
            code_quality=quality.get("code_quality", 0),
            test_coverage=quality.get("test_coverage", 0),
            security_score=quality.get("security_score", 0),
            perf_score=quality.get("perf_score", 0),
            overall=overall,
            gate_passed=(verdict == "GO"),
            gate_details=quality,
        )

        await self.emit_event(session_id, "verdict", {
            "verdict": verdict,
            "reason": reason,
            "overall_score": overall,
        })

        return {
            "verdict": verdict,
            "reason": reason,
            "overall_score": overall,
        }
