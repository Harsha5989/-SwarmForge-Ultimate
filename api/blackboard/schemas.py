"""Pydantic v2 schemas for API request/response models."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════
# SESSION
# ═══════════════════════════════════════════════
class SessionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    spec: str = Field(..., min_length=10)


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: str
    iteration: int
    overall_score: float
    raw_spec: str
    created_at: datetime
    updated_at: datetime


class SessionDetail(SessionResponse):
    output_dir: Optional[str] = None


# ═══════════════════════════════════════════════
# SPEC ARTIFACT
# ═══════════════════════════════════════════════
class SpecArtifactCreate(BaseModel):
    session_id: UUID
    goals: list[dict[str, Any]]
    tech_req: dict[str, Any]
    constraints: list[str] = []
    feasibility: Optional[str] = None


class SpecArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    version: int
    goals: list[dict[str, Any]]
    tech_req: dict[str, Any]
    constraints: list[Any]
    feasibility: Optional[str]
    created_at: datetime


# ═══════════════════════════════════════════════
# ARCHITECTURE BLUEPRINT
# ═══════════════════════════════════════════════
class ArchitectureBlueprintCreate(BaseModel):
    session_id: UUID
    tech_stack: dict[str, Any]
    components: list[dict[str, Any]]
    api_contracts: list[dict[str, Any]]
    db_schema: dict[str, Any]
    file_map: list[dict[str, Any]]


class ArchitectureBlueprintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    version: int
    tech_stack: dict[str, Any]
    components: list[dict[str, Any]]
    api_contracts: list[dict[str, Any]]
    db_schema: dict[str, Any]
    file_map: list[dict[str, Any]]
    created_at: datetime


# ═══════════════════════════════════════════════
# CODEBASE STATE
# ═══════════════════════════════════════════════
class CodebaseStateCreate(BaseModel):
    session_id: UUID
    module_name: str
    file_path: str
    language: str
    content: str
    assigned_to: Optional[str] = None


class CodebaseStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    module_name: str
    file_path: str
    language: str
    content: str
    review_score: float
    status: str
    comments: list[dict[str, Any]]
    version: int
    updated_at: datetime


class CodebaseFileSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_path: str
    module_name: str
    language: str
    status: str
    review_score: float
    version: int


# ═══════════════════════════════════════════════
# TEST RESULTS
# ═══════════════════════════════════════════════
class TestResultCreate(BaseModel):
    session_id: UUID
    test_type: str
    coverage_pct: Optional[float] = None
    tests_total: Optional[int] = None
    tests_passed: Optional[int] = None
    tests_failed: Optional[int] = None
    score: Optional[float] = None
    findings: list[dict[str, Any]] = []
    raw_output: Optional[str] = None


class TestResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    test_type: str
    coverage_pct: Optional[float]
    tests_total: Optional[int]
    tests_passed: Optional[int]
    tests_failed: Optional[int]
    score: Optional[float]
    findings: list[dict[str, Any]]
    run_at: datetime


# ═══════════════════════════════════════════════
# QUALITY SCORE
# ═══════════════════════════════════════════════
class QualityScoreCreate(BaseModel):
    session_id: UUID
    iteration: int
    code_quality: float = 0.0
    test_coverage: float = 0.0
    security_score: float = 0.0
    perf_score: float = 0.0
    overall: float = 0.0
    gate_passed: bool = False
    gate_details: dict[str, Any] = {}


class QualityScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    iteration: int
    code_quality: float
    test_coverage: float
    security_score: float
    perf_score: float
    overall: float
    gate_passed: bool
    gate_details: dict[str, Any]
    computed_at: datetime


# ═══════════════════════════════════════════════
# ERROR REGISTRY
# ═══════════════════════════════════════════════
class ErrorRegistryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_id: str
    agent_type: str
    error_type: str
    description: Optional[str]
    retry_count: int
    resolved: bool
    created_at: datetime


# ═══════════════════════════════════════════════
# AGENT LOG
# ═══════════════════════════════════════════════
class AgentLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_id: str
    agent_type: str
    action: str
    summary: Optional[str]
    tokens_in: int
    tokens_out: int
    duration_ms: int
    model_used: Optional[str]
    ts: datetime


# ═══════════════════════════════════════════════
# COMPOSITE
# ═══════════════════════════════════════════════
class AgentStatus(BaseModel):
    agent_id: str
    status: str
    action: str
    model: Optional[str] = None
    ts: Optional[str] = None


class BlackboardSnapshot(BaseModel):
    spec: Optional[SpecArtifactResponse] = None
    architecture: Optional[ArchitectureBlueprintResponse] = None
    files: list[CodebaseStateResponse] = []
    tests: list[TestResultResponse] = []
    quality: Optional[QualityScoreResponse] = None
    errors: list[ErrorRegistryResponse] = []


class PipelineVerdict(BaseModel):
    verdict: str  # GO | NO_GO | ESCALATE | FAILED
    reason: str
    overall_score: float
    gate_details: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    services: dict[str, str]
