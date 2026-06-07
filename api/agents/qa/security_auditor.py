"""Security Auditor Agent — Vulnerability scanner and patch generator."""

import json
from uuid import UUID

from agents.base import BaseAgent
from tools.code_executor import CodeExecutor


SYSTEM_PROMPT = """You are an expert application security auditor. Analyze code for vulnerabilities.

Check for:
1. SQL injection
2. XSS (Cross-Site Scripting)
3. Hardcoded secrets/credentials
4. Missing input validation
5. Insecure deserialization
6. Path traversal
7. Command injection
8. Missing authentication/authorization checks
9. Insecure cryptographic practices
10. Sensitive data exposure

For each finding, provide a severity and a specific fix.

Output VALID JSON:
{
  "findings": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "file_path": "path/to/file.py",
      "line": 42,
      "rule": "SQL_INJECTION",
      "description": "Raw SQL query with string formatting",
      "fix": "Use parameterized query: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))"
    }
  ],
  "score": 85,
  "summary": "Brief overall security assessment"
}

Output ONLY the JSON.
"""


class SecurityAuditorAgent(BaseAgent):
    """Scans code for security vulnerabilities and generates patches."""

    def __init__(self, store, redis):
        super().__init__(
            agent_id="security_auditor",
            agent_type="QA",
            model_name="security-agent",
            store=store,
            redis=redis,
        )
        self.executor = CodeExecutor()

    async def run(self, session_id: str, input_data: dict) -> dict:
        await self.set_status(session_id, "RUNNING", "Scanning for vulnerabilities...")

        code_files = await self.store.get_all_code_files(UUID(session_id))

        if not code_files:
            return {"score": 100, "findings_count": 0, "gate_passed": True}

        # Build code context for LLM review
        code_text = ""
        for cf in code_files:
            if cf.language in ("python", "javascript", "typescript"):
                code_text += f"\n=== FILE: {cf.file_path} ===\n"
                code_text += cf.content[:2000]
                code_text += "\n=== END ===\n"

        # LLM security review
        result = await self.model.complete_json(
            system=SYSTEM_PROMPT,
            user=f"Perform a security audit on these source files:\n{code_text}",
        )

        findings = result.get("findings", [])

        # Compute score
        penalties = {"CRITICAL": 25, "HIGH": 10, "MEDIUM": 5, "LOW": 1}
        total_penalty = sum(
            penalties.get(f.get("severity", "LOW"), 0)
            for f in findings
        )
        score = max(0.0, 100.0 - total_penalty)

        # Write results
        await self.store.write_test_result(
            session_id=UUID(session_id),
            test_type="SECURITY",
            score=score,
            findings=findings,
            tests_total=len(code_files),
            tests_passed=len(code_files) - len([f for f in findings if f.get("severity") in ("CRITICAL", "HIGH")]),
            tests_failed=len([f for f in findings if f.get("severity") in ("CRITICAL", "HIGH")]),
        )

        gate_passed = score >= 85 and not any(
            f.get("severity") == "CRITICAL" for f in findings
        )

        await self.emit_event(session_id, "gate.security", {
            "score": score,
            "findings_count": len(findings),
            "critical_count": len([f for f in findings if f.get("severity") == "CRITICAL"]),
            "passed": gate_passed,
        })

        return {
            "score": score,
            "findings": findings,
            "findings_count": len(findings),
            "gate_passed": gate_passed,
        }
