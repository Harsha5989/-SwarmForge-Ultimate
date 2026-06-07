"""Tech Lead Agent — Module decomposer, task assigner."""

from uuid import UUID
from agents.base import BaseAgent


class TechLeadAgent(BaseAgent):
    """Breaks architecture into tasks and assigns to coder agents."""

    def __init__(self, store, redis):
        super().__init__(
            agent_id="tech_lead",
            agent_type="DEV",
            model_name="meta-agent",
            store=store,
            redis=redis,
        )

    async def run(self, session_id: str, input_data: dict) -> dict:
        architecture = input_data.get("architecture", {})
        file_map = architecture.get("file_map", [])
        tech_stack = architecture.get("tech_stack", {})
        api_contracts = architecture.get("api_contracts", [])
        db_schema = architecture.get("db_schema", {})

        await self.set_status(session_id, "RUNNING", f"Dispatching {len(file_map)} tasks...")

        # Assign each file to the right coder based on type
        tasks = []
        for entry in file_map:
            file_path = entry.get("file_path", "")
            language = entry.get("language", "python")
            coder_type = entry.get("coder_type", "backend")

            # Map coder_type to model name
            model_map = {
                "backend": "coder-backend",
                "frontend": "coder-frontend",
                "database": "coder-database",
                "api": "coder-api",
            }

            task = {
                "module": entry.get("module", "main"),
                "file_path": file_path,
                "language": language,
                "responsibility": entry.get("responsibility", ""),
                "coder_model": model_map.get(coder_type, "coder-backend"),
                "tech_stack": tech_stack,
                "api_contracts": api_contracts,
                "db_schema": db_schema,
            }

            tasks.append(task)
            await self.redis.push_task(session_id, "dev", task)

        await self.emit_event(session_id, "dev.tasks_dispatched", {
            "count": len(tasks),
            "modules": list(set(t["module"] for t in tasks)),
        })

        self.log.info("tasks_dispatched", count=len(tasks))

        return {
            "tasks_count": len(tasks),
            "tasks": tasks,
        }
