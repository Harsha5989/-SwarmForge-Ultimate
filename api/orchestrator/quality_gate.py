"""Quality Gate Engine — Scoring formulas and gate evaluation."""

from config import get_settings


class QualityGateEngine:
    """Computes quality scores and evaluates gate thresholds."""

    def compute_code_quality(self, reviewer_score: float) -> float:
        return min(100.0, max(0.0, reviewer_score))

    def compute_test_coverage(self, coverage_pct: float) -> float:
        return min(100.0, (coverage_pct / 90.0) * 100)

    def compute_security_score(self, findings: list) -> float:
        penalties = {"CRITICAL": 25, "HIGH": 10, "MEDIUM": 5, "LOW": 1}
        total = sum(penalties.get(f.get("severity", "LOW"), 0) for f in findings)
        return max(0.0, 100.0 - total)

    def compute_perf_score(self, p95_ms: float) -> float:
        if p95_ms <= 100:
            return 100.0
        if p95_ms <= 200:
            return 80.0
        if p95_ms <= 500:
            return 50.0
        return 0.0

    def compute_overall(self, scores: dict) -> float:
        weights = {
            "code_quality": 0.30,
            "test_coverage": 0.25,
            "security_score": 0.25,
            "perf_score": 0.20,
        }
        return sum(scores.get(k, 0) * w for k, w in weights.items())

    def evaluate_gates(self, scores: dict) -> dict:
        settings = get_settings()
        gates = {}

        gates["build"] = {
            "score": scores.get("code_quality", 0),
            "threshold": settings.build_gate_min_score,
            "passed": scores.get("code_quality", 0) >= settings.build_gate_min_score,
        }
        gates["test"] = {
            "score": scores.get("test_coverage", 0),
            "threshold": settings.test_gate_min_coverage,
            "passed": scores.get("test_coverage", 0) >= settings.test_gate_min_coverage,
        }
        gates["security"] = {
            "score": scores.get("security_score", 0),
            "threshold": settings.security_gate_min_score,
            "passed": scores.get("security_score", 0) >= settings.security_gate_min_score,
        }
        gates["perf"] = {
            "score": scores.get("perf_score", 0),
            "threshold": 80,
            "passed": scores.get("perf_score", 0) >= 80,
        }

        overall = self.compute_overall(scores)
        gates["overall"] = {
            "score": overall,
            "threshold": settings.final_gate_min_score,
            "passed": overall >= settings.final_gate_min_score,
        }

        return gates
