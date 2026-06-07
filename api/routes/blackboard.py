"""Blackboard routes — Access shared state data."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from blackboard.schemas import (
    BlackboardSnapshot, SpecArtifactResponse,
    ArchitectureBlueprintResponse, CodebaseStateResponse,
    CodebaseFileSummary, TestResultResponse,
    QualityScoreResponse, AgentLogResponse,
)
from blackboard.store import BlackboardStore
from config import get_settings
from database import get_db
from redis_client import RedisClient, get_redis
from tools.file_manager import FileManager

router = APIRouter(prefix="/sessions/{session_id}", tags=["blackboard"])


async def get_store(db: AsyncSession = Depends(get_db)) -> BlackboardStore:
    redis_conn = await get_redis()
    redis = RedisClient(redis_conn)
    return BlackboardStore(db, redis)


@router.get("/blackboard")
async def get_blackboard(
    session_id: UUID,
    store: BlackboardStore = Depends(get_store),
):
    """Get full blackboard snapshot for a session."""
    snapshot = await store.get_full_snapshot(session_id)
    return snapshot


@router.get("/files")
async def list_files(session_id: UUID):
    """List all generated files on disk."""
    settings = get_settings()
    fm = FileManager(settings.output_dir)
    return await fm.list_files(str(session_id))


@router.get("/files/{file_path:path}")
async def get_file_content(
    session_id: UUID,
    file_path: str,
    store: BlackboardStore = Depends(get_store),
):
    """Get content of a specific generated file."""
    settings = get_settings()
    fm = FileManager(settings.output_dir)
    content = await fm.read_file(str(session_id), file_path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"file_path": file_path, "content": content}


@router.get("/agents")
async def get_agents(session_id: UUID):
    """Get all agent statuses from Redis."""
    redis_conn = await get_redis()
    redis = RedisClient(redis_conn)
    return await redis.get_all_agents(str(session_id))


@router.get("/logs", response_model=list[AgentLogResponse])
async def get_logs(
    session_id: UUID,
    agent_type: str = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    store: BlackboardStore = Depends(get_store),
):
    """Get agent audit logs with optional filtering."""
    return await store.get_agent_logs(
        session_id, agent_type=agent_type,
        limit=limit, offset=offset,
    )


@router.get("/quality", response_model=QualityScoreResponse)
async def get_quality(
    session_id: UUID,
    store: BlackboardStore = Depends(get_store),
):
    """Get latest quality scores."""
    qs = await store.get_latest_quality_score(session_id)
    if not qs:
        raise HTTPException(status_code=404, detail="No quality scores yet")
    return qs


@router.get("/events")
async def get_events(
    session_id: UUID,
    count: int = Query(100, le=1000),
    last_id: str = Query("0-0"),
):
    """Get event stream entries."""
    redis_conn = await get_redis()
    redis = RedisClient(redis_conn)
    events = await redis.get_stream_events(str(session_id), count=count, last_id=last_id)
    return events
