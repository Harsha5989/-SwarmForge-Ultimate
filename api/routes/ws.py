"""WebSocket hub — Real-time event streaming to dashboard."""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

from redis_client import get_redis, RedisClient

log = structlog.get_logger()
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections grouped by session_id."""

    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if session_id not in self.active:
            self.active[session_id] = []
        self.active[session_id].append(websocket)
        log.info("ws_connected", session=session_id, total=len(self.active[session_id]))

    async def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        if session_id in self.active:
            self.active[session_id] = [
                ws for ws in self.active[session_id] if ws != websocket
            ]
            if not self.active[session_id]:
                del self.active[session_id]
        log.info("ws_disconnected", session=session_id)

    async def broadcast(self, session_id: str, message: dict) -> None:
        if session_id not in self.active:
            return
        dead = []
        for ws in self.active[session_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(session_id, ws)


manager = ConnectionManager()


@router.websocket("/ws/swarm/{session_id}")
async def swarm_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time swarm event streaming."""
    await manager.connect(session_id, websocket)

    # Start Redis subscriber in background
    redis_conn = await get_redis()
    pubsub = redis_conn.pubsub()
    channel = f"channel:session:{session_id}"
    await pubsub.subscribe(channel)

    async def listen_redis():
        """Forward Redis pub/sub events to WebSocket."""
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        event = json.loads(message["data"])
                        await manager.broadcast(session_id, event)
                    except Exception as e:
                        log.warning("ws_broadcast_error", error=str(e))
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    redis_task = asyncio.create_task(listen_redis())

    try:
        # Keep connection alive, handle pings
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send keepalive
                try:
                    await websocket.send_json({"type": "keepalive"})
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.warning("ws_error", session=session_id, error=str(e))
    finally:
        redis_task.cancel()
        await manager.disconnect(session_id, websocket)
