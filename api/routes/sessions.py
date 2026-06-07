"""Session routes — Create and manage pipeline sessions."""

import asyncio
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from blackboard.schemas import SessionCreate, SessionResponse, SessionDetail
from blackboard.store import BlackboardStore
from config import get_settings
from database import get_db
from orchestrator.graph import run_pipeline
from redis_client import RedisClient, get_redis
from tools.file_manager import FileManager

router = APIRouter(prefix="/sessions", tags=["sessions"])


async def get_store(db: AsyncSession = Depends(get_db)) -> BlackboardStore:
    redis_conn = await get_redis()
    redis = RedisClient(redis_conn)
    return BlackboardStore(db, redis)


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    body: SessionCreate,
    background_tasks: BackgroundTasks,
    store: BlackboardStore = Depends(get_store),
):
    """Create a new pipeline session and start execution in background."""
    session = await store.create_session(name=body.name, raw_spec=body.spec)
    session_id = str(session.id)

    # Launch pipeline in background
    background_tasks.add_task(run_pipeline, session_id, body.spec)

    return session


@router.get("", response_model=list[SessionResponse])
async def list_sessions(store: BlackboardStore = Depends(get_store)):
    """List all pipeline sessions."""
    return await store.list_sessions()


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: UUID,
    store: BlackboardStore = Depends(get_store),
):
    """Get detailed session information."""
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}/download")
async def download_session(session_id: UUID):
    """Download the generated project as a ZIP file."""
    settings = get_settings()
    fm = FileManager(settings.output_dir)
    try:
        zip_bytes = await fm.create_zip(str(session_id))
        return StreamingResponse(
            iter([zip_bytes]),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={session_id}.zip"},
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No output files found")


@router.post("/{session_id}/cancel")
async def cancel_session(
    session_id: UUID,
    store: BlackboardStore = Depends(get_store),
):
    """Cancel a running pipeline session."""
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status in ("DONE", "FAILED"):
        raise HTTPException(status_code=400, detail="Session already completed")

    await store.update_session_status(session_id, "CANCELLED")
    return {"status": "cancelled", "session_id": str(session_id)}


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: UUID,
    store: BlackboardStore = Depends(get_store),
):
    """Delete a session."""
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    success = await store.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete session")
    return None
