"""Redis client for event bus, pub/sub, queues, and caching."""

import json
from datetime import datetime
from typing import Any, Optional

import redis.asyncio as aioredis
import structlog

from config import get_settings

log = structlog.get_logger()

_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Return a cached Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        settings = get_settings()
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=50,
        )
    return _redis_pool


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None


class RedisClient:
    """High-level Redis operations for SwarmForge."""

    def __init__(self, redis: aioredis.Redis):
        self.r = redis

    # ── Session Status ─────────────────────────────────────────
    async def set_session_status(self, session_id: str, status: str) -> None:
        await self.r.set(f"session:{session_id}:status", status)

    async def get_session_status(self, session_id: str) -> Optional[str]:
        return await self.r.get(f"session:{session_id}:status")

    # ── Agent Status ───────────────────────────────────────────
    async def set_agent_status(
        self, session_id: str, agent_id: str, status_dict: dict
    ) -> None:
        status_dict["ts"] = datetime.utcnow().isoformat()
        await self.r.hset(
            f"session:{session_id}:agents",
            agent_id,
            json.dumps(status_dict),
        )

    async def get_agent_status(
        self, session_id: str, agent_id: str
    ) -> Optional[dict]:
        raw = await self.r.hget(f"session:{session_id}:agents", agent_id)
        return json.loads(raw) if raw else None

    async def get_all_agents(self, session_id: str) -> dict:
        raw = await self.r.hgetall(f"session:{session_id}:agents")
        return {k: json.loads(v) for k, v in raw.items()}

    # ── Task Queues ────────────────────────────────────────────
    async def push_task(self, session_id: str, queue_name: str, task: dict) -> None:
        key = f"queue:{session_id}:{queue_name}"
        await self.r.rpush(key, json.dumps(task))

    async def pop_task(
        self, session_id: str, queue_name: str, timeout: int = 0
    ) -> Optional[dict]:
        key = f"queue:{session_id}:{queue_name}"
        if timeout > 0:
            result = await self.r.blpop(key, timeout=timeout)
            return json.loads(result[1]) if result else None
        raw = await self.r.lpop(key)
        return json.loads(raw) if raw else None

    async def queue_length(self, session_id: str, queue_name: str) -> int:
        return await self.r.llen(f"queue:{session_id}:{queue_name}")

    # ── Event Stream ───────────────────────────────────────────
    async def add_stream_event(self, session_id: str, event: dict) -> str:
        event["ts"] = datetime.utcnow().isoformat()
        stream_key = f"session:{session_id}:events"
        msg_id = await self.r.xadd(stream_key, {"data": json.dumps(event)}, maxlen=10000)
        return msg_id

    async def get_stream_events(
        self, session_id: str, count: int = 100, last_id: str = "0-0"
    ) -> list[dict]:
        stream_key = f"session:{session_id}:events"
        entries = await self.r.xrange(stream_key, min=last_id, count=count)
        events = []
        for entry_id, fields in entries:
            event = json.loads(fields["data"])
            event["_id"] = entry_id
            events.append(event)
        return events

    # ── Pub/Sub ────────────────────────────────────────────────
    async def publish_event(self, session_id: str, event: dict) -> None:
        channel = f"channel:session:{session_id}"
        await self.r.publish(channel, json.dumps(event))

    def subscribe(self, session_id: str) -> aioredis.client.PubSub:
        pubsub = self.r.pubsub()
        return pubsub

    # ── JSON Key/Value ─────────────────────────────────────────
    async def set_json(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> None:
        data = json.dumps(value)
        if ttl:
            await self.r.setex(key, ttl, data)
        else:
            await self.r.set(key, data)

    async def get_json(self, key: str) -> Optional[Any]:
        raw = await self.r.get(key)
        return json.loads(raw) if raw else None

    # ── Distributed Locks ──────────────────────────────────────
    async def acquire_lock(
        self, resource: str, session_id: str, ttl: int = 30
    ) -> bool:
        key = f"lock:{session_id}:{resource}"
        return await self.r.set(key, "1", ex=ttl, nx=True)

    async def release_lock(self, resource: str, session_id: str) -> None:
        key = f"lock:{session_id}:{resource}"
        await self.r.delete(key)

    # ── Rate Limit Tracking ────────────────────────────────────
    async def increment_rate(self, provider: str) -> int:
        from datetime import date
        key = f"ratelimit:{provider}:{date.today().isoformat()}"
        count = await self.r.incr(key)
        await self.r.expire(key, 86400)
        return count

    async def get_rate_count(self, provider: str) -> int:
        from datetime import date
        key = f"ratelimit:{provider}:{date.today().isoformat()}"
        val = await self.r.get(key)
        return int(val) if val else 0
