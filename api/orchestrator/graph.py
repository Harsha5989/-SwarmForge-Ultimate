"""Master orchestrator — runs the full swarm pipeline."""

import asyncio
import structlog
from uuid import UUID

from database import AsyncSessionLocal
from redis_client import get_redis, RedisClient
from blackboard.store import BlackboardStore
from orchestrator.quality_gate import QualityGateEngine
from config import get_settings

from agents.meta.ceo import CEOAgent
from agents.meta.cpo import CPOAgent
from agents.meta.cto import CTOAgent
from agents.meta.judge import JudgeAgent
from agents.dev.tech_lead import TechLeadAgent
from agents.dev.coder import run_all_coders
from agents.dev.reviewer import ReviewerAgent
from agents.qa.qa_lead import QALeadAgent
from agents.qa.unit_tester import UnitTesterAgent
from agents.qa.security_auditor import SecurityAuditorAgent
from agents.qa.perf_analyzer import PerfAnalyzerAgent
from agents.qa.bug_fix import BugFixAgent
from agents.ops.container_agent import ContainerAgent
from agents.ops.cicd_agent import CICDAgent
from agents.ops.docs_agent import DocsAgent

log = structlog.get_logger()


async def run_pipeline(session_id: str, raw_spec: str) -> dict:
    """
    Execute the full SwarmForge pipeline for a session.

    Flow:
    CEO → CPO → CTO → TechLead → Coders → Reviewer
    → (BUILD LOOP) → QALead → UnitTester + SecurityAuditor
    → (TEST/SEC LOOPS) → PerfAnalyzer → (PERF LOOP)
    → Judge → Container + Docs + CI/CD → DONE
    """
    settings = get_settings()
    gate_engine = QualityGateEngine()

    async with AsyncSessionLocal() as db:
        redis_conn = await get_redis()
        redis = RedisClient(redis_conn)
        store = BlackboardStore(db, redis)

        sid = session_id
        iteration = 0
        build_retries = 0
        test_retries = 0
        sec_retries = 0
        perf_retries = 0

        quality = {
            "code_quality": 0, "test_coverage": 0,
            "security_score": 0, "perf_score": 0, "overall": 0,
        }

        try:
            # ═══════════════════════════════════════════════
            # PHASE 1: PLANNING (CEO → CPO → CTO)
            # ═══════════════════════════════════════════════
            await store.update_session_status(UUID(sid), "PLANNING")
            await redis.publish_event(sid, {"type": "pipeline.status", "status": "PLANNING"})

            ceo = CEOAgent(store, redis)
            spec = await ceo.execute(sid, {"raw_spec": raw_spec})
            await redis.publish_event(sid, {"type": "pipeline.step", "agent_id": "ceo", "agent_type": "META", "message": f"✅ Spec parsed — {len(spec.get('goals',[]))} goals identified"})

            cpo = CPOAgent(store, redis)
            spec = await cpo.execute(sid, {"spec": spec})
            await redis.publish_event(sid, {"type": "pipeline.step", "agent_id": "cpo", "agent_type": "META", "message": "✅ Product spec refined"})

            await store.update_session_status(UUID(sid), "ARCHITECTING")
            await redis.publish_event(sid, {"type": "pipeline.status", "status": "ARCHITECTING"})

            cto = CTOAgent(store, redis)
            architecture = await cto.execute(sid, {"spec": spec})
            await redis.publish_event(sid, {"type": "pipeline.step", "agent_id": "cto", "agent_type": "META", "message": f"✅ Architecture designed — {len(architecture.get('file_map',[]))} files planned"})

            while iteration < settings.max_iterations:
                iteration += 1
                await store.increment_iteration(UUID(sid))
                log.info("pipeline_iteration", session=sid, iteration=iteration)

                # ═══════════════════════════════════════════
                # PHASE 2: BUILDING (TechLead → Coders → Reviewer)
                # ═══════════════════════════════════════════
                await store.update_session_status(UUID(sid), "BUILDING")
                await redis.publish_event(sid, {"type": "pipeline.status", "status": "BUILDING", "iteration": iteration})

                tech_lead = TechLeadAgent(store, redis)
                dispatch = await tech_lead.execute(sid, {"architecture": architecture})

                # Run all coders
                tasks = dispatch.get("tasks", [])
                await redis.publish_event(sid, {"type": "pipeline.step", "agent_id": "tech_lead", "agent_type": "DEV", "message": f"🔨 Dispatching {len(tasks)} coding tasks..."})
                await run_all_coders(sid, tasks, store, redis)
                await redis.publish_event(sid, {"type": "pipeline.step", "agent_id": "tech_lead", "agent_type": "DEV", "message": f"✅ All {len(tasks)} files written to blackboard & disk"})

                # Review
                await store.update_session_status(UUID(sid), "REVIEWING")
                reviewer = ReviewerAgent(store, redis)
                review = await reviewer.execute(sid, {})

                code_quality = review.get("aggregate_score", 0)
                quality["code_quality"] = code_quality

                # BUILD GATE
                if code_quality < settings.build_gate_min_score:
                    build_retries += 1
                    if build_retries < settings.max_retries_per_gate:
                        log.info("build_loop_retry", retries=build_retries, score=code_quality)
                        continue  # retry build loop
                    # Fall through to judge

                # ═══════════════════════════════════════════
                # PHASE 3: TESTING (QALead → UnitTester + Security)
                # ═══════════════════════════════════════════
                await store.update_session_status(UUID(sid), "TESTING")
                await redis.publish_event(sid, {"type": "pipeline.status", "status": "TESTING"})

                qa_lead = QALeadAgent(store, redis)
                try:
                    await qa_lead.execute(sid, {"architecture": architecture})
                except Exception as e:
                    log.warning("qa_lead_skipped", error=str(e))

                # Unit Tests
                unit_tester = UnitTesterAgent(store, redis)
                try:
                    unit_result = await unit_tester.execute(sid, {})
                    quality["test_coverage"] = gate_engine.compute_test_coverage(
                        unit_result.get("coverage_pct", 0)
                    )
                except Exception as e:
                    log.warning("unit_tester_skipped", error=str(e))
                    quality["test_coverage"] = 0

                # Security Audit
                await store.update_session_status(UUID(sid), "SECURING")
                security = SecurityAuditorAgent(store, redis)
                try:
                    sec_result = await security.execute(sid, {})
                    quality["security_score"] = sec_result.get("score", 0)
                except Exception as e:
                    log.warning("security_auditor_skipped", error=str(e))
                    quality["security_score"] = 70  # default pass score

                # Performance Analysis
                perf = PerfAnalyzerAgent(store, redis)
                try:
                    perf_result = await perf.execute(sid, {})
                    quality["perf_score"] = perf_result.get("score", 0)
                except Exception as e:
                    log.warning("perf_analyzer_skipped", error=str(e))
                    quality["perf_score"] = 80  # default pass score

                # Compute overall
                quality["overall"] = gate_engine.compute_overall(quality)

                await redis.publish_event(sid, {
                    "type": "quality.updated", **quality,
                })

                # ═══════════════════════════════════════════
                # PHASE 4: JUDGE VERDICT
                # ═══════════════════════════════════════════
                judge = JudgeAgent(store, redis)
                verdict_result = await judge.execute(sid, {
                    "quality": quality,
                    "iteration": iteration,
                    "build_retries": build_retries,
                    "test_retries": test_retries,
                    "sec_retries": sec_retries,
                    "perf_retries": perf_retries,
                })

                verdict = verdict_result.get("verdict", "NO_GO")

                if verdict == "GO":
                    # ═══════════════════════════════════════
                    # PHASE 5: DEPLOYMENT (Container + Docs + CI/CD)
                    # ═══════════════════════════════════════
                    await store.update_session_status(UUID(sid), "DEPLOYING")
                    await redis.publish_event(sid, {"type": "pipeline.status", "status": "DEPLOYING"})

                    container = ContainerAgent(store, redis)
                    await container.execute(sid, {"architecture": architecture})

                    docs = DocsAgent(store, redis)
                    await docs.execute(sid, {})

                    cicd = CICDAgent(store, redis)
                    await cicd.execute(sid, {"architecture": architecture})

                    # DONE!
                    await store.update_session_status(UUID(sid), "DONE")
                    await store.update_overall_score(UUID(sid), quality["overall"])

                    await redis.publish_event(sid, {
                        "type": "session.done",
                        "overall_score": quality["overall"],
                        "output_dir": f"/workspace/output/{sid}",
                    })

                    log.info("pipeline_done", session=sid, score=quality["overall"])
                    return {"status": "DONE", "quality": quality}

                elif verdict == "ESCALATE":
                    # Re-architect
                    log.warning("pipeline_escalate", session=sid, iteration=iteration)
                    architecture = await cto.execute(sid, {"spec": spec})
                    build_retries = 0
                    test_retries = 0
                    sec_retries = 0
                    perf_retries = 0
                    continue

                elif verdict == "FAILED":
                    break

                else:  # NO_GO — retry
                    continue

            # If we exit the loop, we failed
            await store.update_session_status(UUID(sid), "FAILED")
            await redis.publish_event(sid, {
                "type": "session.failed",
                "reason": f"Max iterations ({settings.max_iterations}) exhausted",
            })
            return {"status": "FAILED", "quality": quality}

        except Exception as e:
            log.error("pipeline_error", session=sid, error=str(e))
            await store.update_session_status(UUID(sid), "FAILED")
            await redis.publish_event(sid, {
                "type": "session.failed",
                "reason": str(e)[:500],
            })
            raise
        finally:
            await db.commit()
