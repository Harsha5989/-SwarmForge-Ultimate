"""Code Executor — Sandboxed command runner for tests and security scans."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import structlog

from config import get_settings

log = structlog.get_logger()


class CodeExecutor:
    """Runs commands in the sandbox container or locally."""

    def __init__(self):
        self.settings = get_settings()

    async def run_command(
        self, command: list[str], workdir: str, timeout: Optional[int] = None
    ) -> tuple[str, str, int]:
        """Run a shell command and return (stdout, stderr, returncode)."""
        timeout = timeout or self.settings.sandbox_timeout_sec
        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                cwd=workdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return (
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace"),
                proc.returncode or 0,
            )
        except asyncio.TimeoutError:
            proc.kill()
            return "", f"Command timed out after {timeout}s", 1
        except FileNotFoundError:
            return "", f"Command not found: {command[0]}", 1
        except Exception as e:
            return "", str(e), 1

    async def run_pytest(self, project_dir: str) -> dict:
        """Run pytest with coverage and return results."""
        stdout, stderr, code = await self.run_command(
            ["python", "-m", "pytest", "--cov=.", "--cov-report=json", "-v", "--tb=short"],
            workdir=project_dir,
        )

        result = {
            "coverage_pct": 0.0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "output": stdout[:5000],
        }

        # Try to parse coverage JSON
        cov_file = Path(project_dir) / "coverage.json"
        if cov_file.exists():
            try:
                cov_data = json.loads(cov_file.read_text())
                result["coverage_pct"] = cov_data.get("totals", {}).get("percent_covered", 0)
            except Exception:
                pass

        # Parse pytest output for pass/fail counts
        for line in stdout.split("\n"):
            if "passed" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "passed" and i > 0:
                        try:
                            result["passed"] = int(parts[i - 1])
                        except ValueError:
                            pass
                    if p == "failed" and i > 0:
                        try:
                            result["failed"] = int(parts[i - 1])
                        except ValueError:
                            pass

        return result

    async def run_bandit(self, project_dir: str) -> dict:
        """Run bandit security scanner and return findings."""
        stdout, stderr, code = await self.run_command(
            ["python", "-m", "bandit", "-r", ".", "-f", "json", "-ll"],
            workdir=project_dir,
        )

        try:
            data = json.loads(stdout)
            findings = []
            for result in data.get("results", []):
                findings.append({
                    "severity": result.get("issue_severity", "LOW"),
                    "test_id": result.get("test_id", ""),
                    "filename": result.get("filename", ""),
                    "line": result.get("line_number", 0),
                    "issue_text": result.get("issue_text", ""),
                })
            return {"findings": findings}
        except Exception:
            return {"findings": []}
