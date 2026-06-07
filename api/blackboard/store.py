"""BlackboardStore — CRUD operations for the shared state layer."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from blackboard.models import (
    SessionModel, SpecArtifact, ArchitectureBlueprint,
    CodebaseState, TestResult, QualityScore,
    ErrorRegistry, AgentLog,
)
from blackboard.schemas import BlackboardSnapshot
from redis_client import RedisClient


class BlackboardStore:
    """Central data access layer for the SwarmForge blackboard."""

    def __init__(self, db: AsyncSession, redis: RedisClient):
        self.db = db
        self.redis = redis

    # ── Session CRUD ───────────────────────────────────────────
    async def create_session(self, name: str, raw_spec: str) -> SessionModel:
        session = SessionModel(name=name, raw_spec=raw_spec, status="PENDING")
        self.db.add(session)
        await self.db.flush()
        await self.redis.set_session_status(str(session.id), "PENDING")
        return session

    async def get_session(self, session_id: UUID) -> Optional[SessionModel]:
        result = await self.db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_sessions(self) -> list[SessionModel]:
        result = await self.db.execute(
            select(SessionModel).order_by(desc(SessionModel.created_at))
        )
        return list(result.scalars().all())

    async def update_session_status(self, session_id: UUID, status: str) -> None:
        session = await self.get_session(session_id)
        if session:
            session.status = status
            await self.db.flush()
            await self.redis.set_session_status(str(session_id), status)

    async def update_overall_score(self, session_id: UUID, score: float) -> None:
        session = await self.get_session(session_id)
        if session:
            session.overall_score = score
            await self.db.flush()

    async def increment_iteration(self, session_id: UUID) -> int:
        session = await self.get_session(session_id)
        if session:
            session.iteration += 1
            await self.db.flush()
            return session.iteration
        return 0

    async def delete_session(self, session_id: UUID) -> bool:
        session = await self.get_session(session_id)
        if session:
            await self.db.delete(session)
            await self.db.flush()
            return True
        return False

    # ── Spec Artifact ──────────────────────────────────────────
    async def write_spec_artifact(
        self, session_id: UUID, goals: list, tech_req: dict,
        constraints: list, feasibility: str = None
    ) -> SpecArtifact:
        existing = await self.get_spec_artifact(session_id)
        version = (existing.version + 1) if existing else 1

        spec = SpecArtifact(
            session_id=session_id, version=version,
            goals=goals, tech_req=tech_req,
            constraints=constraints, feasibility=feasibility,
        )
        self.db.add(spec)
        await self.db.flush()
        return spec

    async def get_spec_artifact(self, session_id: UUID) -> Optional[SpecArtifact]:
        result = await self.db.execute(
            select(SpecArtifact)
            .where(SpecArtifact.session_id == session_id)
            .order_by(desc(SpecArtifact.version))
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ── Architecture Blueprint ─────────────────────────────────
    async def write_architecture(
        self, session_id: UUID, tech_stack: dict, components: list,
        api_contracts: list, db_schema: dict, file_map: list
    ) -> ArchitectureBlueprint:
        existing = await self.get_architecture(session_id)
        version = (existing.version + 1) if existing else 1

        blueprint = ArchitectureBlueprint(
            session_id=session_id, version=version,
            tech_stack=tech_stack, components=components,
            api_contracts=api_contracts, db_schema=db_schema,
            file_map=file_map,
        )
        self.db.add(blueprint)
        await self.db.flush()
        return blueprint

    async def get_architecture(self, session_id: UUID) -> Optional[ArchitectureBlueprint]:
        result = await self.db.execute(
            select(ArchitectureBlueprint)
            .where(ArchitectureBlueprint.session_id == session_id)
            .order_by(desc(ArchitectureBlueprint.version))
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ── Code Files ─────────────────────────────────────────────
    async def write_code_file(
        self, session_id: UUID, module_name: str, file_path: str,
        language: str, content: str, assigned_to: str = None
    ) -> CodebaseState:
        # Check if file already exists for this session
        result = await self.db.execute(
            select(CodebaseState).where(
                CodebaseState.session_id == session_id,
                CodebaseState.file_path == file_path,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.content = content
            existing.version += 1
            existing.status = "DRAFT"
            existing.assigned_to = assigned_to
            await self.db.flush()
            return existing

        code = CodebaseState(
            session_id=session_id, module_name=module_name,
            file_path=file_path, language=language,
            content=content, assigned_to=assigned_to,
        )
        self.db.add(code)
        await self.db.flush()
        return code

    async def get_code_file(self, session_id: UUID, file_path: str) -> Optional[CodebaseState]:
        result = await self.db.execute(
            select(CodebaseState).where(
                CodebaseState.session_id == session_id,
                CodebaseState.file_path == file_path,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_code_files(self, session_id: UUID) -> list[CodebaseState]:
        result = await self.db.execute(
            select(CodebaseState)
            .where(CodebaseState.session_id == session_id)
            .order_by(CodebaseState.module_name, CodebaseState.file_path)
        )
        return list(result.scalars().all())

    async def update_code_review(
        self, session_id: UUID, file_path: str,
        review_score: float, comments: list, status: str
    ) -> None:
        code = await self.get_code_file(session_id, file_path)
        if code:
            code.review_score = review_score
            code.comments = comments
            code.status = status
            await self.db.flush()

    # ── Test Results ───────────────────────────────────────────
    async def write_test_result(
        self, session_id: UUID, test_type: str,
        coverage_pct: float = None, tests_total: int = None,
        tests_passed: int = None, tests_failed: int = None,
        score: float = None, findings: list = None,
        raw_output: str = None
    ) -> TestResult:
        result = TestResult(
            session_id=session_id, test_type=test_type,
            coverage_pct=coverage_pct, tests_total=tests_total,
            tests_passed=tests_passed, tests_failed=tests_failed,
            score=score, findings=findings or [],
            raw_output=raw_output,
        )
        self.db.add(result)
        await self.db.flush()
        return result

    async def get_test_results(
        self, session_id: UUID, test_type: str = None
    ) -> list[TestResult]:
        query = select(TestResult).where(TestResult.session_id == session_id)
        if test_type:
            query = query.where(TestResult.test_type == test_type)
        query = query.order_by(desc(TestResult.run_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ── Quality Scores ─────────────────────────────────────────
    async def write_quality_score(
        self, session_id: UUID, iteration: int,
        code_quality: float, test_coverage: float,
        security_score: float, perf_score: float,
        overall: float, gate_passed: bool,
        gate_details: dict
    ) -> QualityScore:
        qs = QualityScore(
            session_id=session_id, iteration=iteration,
            code_quality=code_quality, test_coverage=test_coverage,
            security_score=security_score, perf_score=perf_score,
            overall=overall, gate_passed=gate_passed,
            gate_details=gate_details,
        )
        self.db.add(qs)
        await self.db.flush()
        return qs

    async def get_latest_quality_score(self, session_id: UUID) -> Optional[QualityScore]:
        result = await self.db.execute(
            select(QualityScore)
            .where(QualityScore.session_id == session_id)
            .order_by(desc(QualityScore.computed_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ── Error Registry ─────────────────────────────────────────
    async def log_error(
        self, session_id: UUID, agent_id: str, agent_type: str,
        error_type: str, description: str, context: dict = None
    ) -> ErrorRegistry:
        err = ErrorRegistry(
            session_id=session_id, agent_id=agent_id,
            agent_type=agent_type, error_type=error_type,
            description=description, context=context or {},
        )
        self.db.add(err)
        await self.db.flush()
        return err

    async def get_errors(self, session_id: UUID, resolved: bool = None) -> list[ErrorRegistry]:
        query = select(ErrorRegistry).where(ErrorRegistry.session_id == session_id)
        if resolved is not None:
            query = query.where(ErrorRegistry.resolved == resolved)
        result = await self.db.execute(query.order_by(desc(ErrorRegistry.created_at)))
        return list(result.scalars().all())

    # ── Agent Logs ─────────────────────────────────────────────
    async def log_agent_action(
        self, session_id: UUID, agent_id: str, agent_type: str,
        action: str, summary: str = None, tokens_in: int = 0,
        tokens_out: int = 0, duration_ms: int = 0, model_used: str = None
    ) -> AgentLog:
        log = AgentLog(
            session_id=session_id, agent_id=agent_id,
            agent_type=agent_type, action=action,
            summary=summary, tokens_in=tokens_in,
            tokens_out=tokens_out, duration_ms=duration_ms,
            model_used=model_used,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_agent_logs(
        self, session_id: UUID, agent_type: str = None,
        limit: int = 100, offset: int = 0
    ) -> list[AgentLog]:
        query = select(AgentLog).where(AgentLog.session_id == session_id)
        if agent_type:
            query = query.where(AgentLog.agent_type == agent_type)
        query = query.order_by(desc(AgentLog.ts)).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ── Full Snapshot ──────────────────────────────────────────
    async def get_full_snapshot(self, session_id: UUID) -> dict:
        spec = await self.get_spec_artifact(session_id)
        arch = await self.get_architecture(session_id)
        files = await self.get_all_code_files(session_id)
        tests = await self.get_test_results(session_id)
        quality = await self.get_latest_quality_score(session_id)
        errors = await self.get_errors(session_id)

        return {
            "spec": spec,
            "architecture": arch,
            "files": files,
            "tests": tests,
            "quality": quality,
            "errors": errors,
        }
