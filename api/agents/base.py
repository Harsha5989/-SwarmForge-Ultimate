"""BaseAgent — abstract foundation for all SwarmForge agents."""

import time
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

import structlog

from agents.llm_client import LLMClient
from blackboard.store import BlackboardStore
from redis_client import RedisClient


class BaseAgent(ABC):
    """Abstract base class for all swarm agents."""

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        model_name: str,
        store: BlackboardStore,
        redis: RedisClient,
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.model_name = model_name
        self.model = LLMClient(model_name)
        self.store = store
        self.redis = redis
        self.log = structlog.get_logger().bind(agent_id=agent_id, agent_type=agent_type)

    async def emit_event(self, session_id: str, event_type: str, payload: dict = None) -> None:
        """Publish an event to Redis stream + pub/sub channel."""
        event = {
            "type": event_type,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            **(payload or {}),
        }
        await self.redis.add_stream_event(session_id, event)
        await self.redis.publish_event(session_id, event)
        self.log.info("event_emitted", event_type=event_type)

    async def set_status(self, session_id: str, status: str, action: str) -> None:
        """Update agent status in Redis."""
        await self.redis.set_agent_status(session_id, self.agent_id, {
            "status": status,
            "action": action,
            "model": self.model_name,
        })

    async def log_action(
        self, session_id: str, action: str, summary: str = None,
        tokens_in: int = 0, tokens_out: int = 0, duration_ms: int = 0,
    ) -> None:
        """Write an audit log entry to the database."""
        await self.store.log_agent_action(
            session_id=UUID(session_id),
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action=action,
            summary=summary,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            duration_ms=duration_ms,
            model_used=self.model_name,
        )

    async def execute(self, session_id: str, input_data: dict) -> dict:
        """
        Wrapper around run() that handles status updates, timing,
        event emission, error logging, and audit logging.
        """
        start = time.time()
        try:
            await self.set_status(session_id, "RUNNING", "Starting...")
            await self.emit_event(session_id, "agent.started", {
                "model": self.model_name,
            })

            result = await self.run(session_id, input_data)

            duration_ms = int((time.time() - start) * 1000)
            await self.set_status(session_id, "DONE", "Completed")
            await self.emit_event(session_id, "agent.done", {
                "duration_ms": duration_ms,
                "output_summary": str(result)[:200],
            })

            return result

        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            self.log.error("agent_failed", error=str(e))
            await self.set_status(session_id, "ERROR", str(e)[:100])
            await self.emit_event(session_id, "agent.error", {
                "error_type": type(e).__name__,
                "message": str(e)[:500],
            })
            await self.store.log_error(
                session_id=UUID(session_id),
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                error_type=type(e).__name__,
                description=str(e),
            )
            raise

    @abstractmethod
    async def run(self, session_id: str, input_data: dict) -> dict:
        """Implement agent logic. Called by execute()."""
        pass
