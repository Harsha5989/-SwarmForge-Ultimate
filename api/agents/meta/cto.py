"""CTO Agent — Architecture designer, tech stack selector."""

from uuid import UUID
from agents.base import BaseAgent


SYSTEM_PROMPT = """You are the CTO of SwarmForge, an autonomous software factory.
You receive a validated spec with goals and tech requirements. Your job is to design
the complete system architecture.

Output VALID JSON matching this schema:
{
  "tech_stack": {
    "backend": {"language": "python", "framework": "fastapi", "runtime": "uvicorn"},
    "frontend": {"framework": "react", "bundler": "vite"},
    "database": {"type": "postgresql", "orm": "sqlalchemy"},
    "infrastructure": {"containerization": "docker", "ci_cd": "github_actions"}
  },
  "components": [
    {
      "name": "component_name",
      "type": "backend|frontend|database|service",
      "responsibility": "What this component does",
      "dependencies": ["other_component_names"]
    }
  ],
  "api_contracts": [
    {
      "path": "/api/resource",
      "method": "GET|POST|PUT|DELETE",
      "description": "What this endpoint does",
      "request_body": {"field": "type"},
      "response": {"field": "type"},
      "auth_required": true
    }
  ],
  "db_schema": {
    "tables": [
      {
        "name": "table_name",
        "columns": [
          {"name": "id", "type": "UUID", "primary_key": true},
          {"name": "field", "type": "VARCHAR(255)", "nullable": false}
        ],
        "indexes": ["index_name ON (column)"]
      }
    ]
  },
  "file_map": [
    {
      "module": "module_name",
      "file_path": "relative/path/to/file.py",
      "language": "python",
      "responsibility": "What this file contains",
      "coder_type": "backend|frontend|database|api"
    }
  ]
}

Rules:
1. Design for production — include error handling, validation, authentication.
2. file_map MUST list EVERY file that needs to be created.
3. Each file must have a clear, single responsibility.
4. Include config files, Dockerfiles, requirements/package files.
5. API contracts must cover all CRUD operations for each resource.
6. DB schema must include proper types, constraints, and indexes.
7. Output ONLY the JSON, no markdown.
"""


class CTOAgent(BaseAgent):
    """Designs system architecture, selects tech stack, creates blueprints."""

    def __init__(self, store, redis):
        super().__init__(
            agent_id="cto",
            agent_type="META",
            model_name="meta-agent",
            store=store,
            redis=redis,
        )

    async def run(self, session_id: str, input_data: dict) -> dict:
        spec = input_data.get("spec", input_data)
        goals = spec.get("goals", [])
        tech_req = spec.get("tech_req", {})
        constraints = spec.get("constraints", [])

        await self.set_status(session_id, "RUNNING", "Designing architecture...")

        result = await self.model.complete_json(
            system=SYSTEM_PROMPT,
            user=(
                f"Design the architecture for this project:\n\n"
                f"Goals:\n{goals}\n\n"
                f"Tech Requirements:\n{tech_req}\n\n"
                f"Constraints:\n{constraints}\n\n"
                f"Create a complete architecture blueprint."
            ),
        )

        tech_stack = result.get("tech_stack", {})
        components = result.get("components", [])
        api_contracts = result.get("api_contracts", [])
        db_schema = result.get("db_schema", {})
        file_map = result.get("file_map", [])

        if not file_map:
            raise ValueError("CTO agent produced no file_map")

        # Write to blackboard
        blueprint = await self.store.write_architecture(
            session_id=UUID(session_id),
            tech_stack=tech_stack,
            components=components,
            api_contracts=api_contracts,
            db_schema=db_schema,
            file_map=file_map,
        )

        await self.emit_event(session_id, "architecture.ready", {
            "components_count": len(components),
            "files_count": len(file_map),
            "api_endpoints": len(api_contracts),
        })

        return {
            "blueprint_id": str(blueprint.id),
            "tech_stack": tech_stack,
            "components": components,
            "api_contracts": api_contracts,
            "db_schema": db_schema,
            "file_map": file_map,
        }
