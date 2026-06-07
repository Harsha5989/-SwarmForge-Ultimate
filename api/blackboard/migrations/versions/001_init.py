"""Initial schema — all 8 SwarmForge tables.

Revision ID: 001_init
Revises:
Create Date: 2024-01-01 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ── Sessions ───────────────────────────────────────────
    op.create_table(
        "sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("raw_spec", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("iteration", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overall_score", sa.Float(), server_default="0.0"),
        sa.Column("output_dir", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()")),
    )

    # ── Spec Artifacts ─────────────────────────────────────
    op.create_table(
        "spec_artifacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("goals", JSONB(), nullable=False),
        sa.Column("tech_req", JSONB(), nullable=False),
        sa.Column("constraints", JSONB(), nullable=False, server_default="[]"),
        sa.Column("feasibility", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_spec_session", "spec_artifacts", ["session_id"])

    # ── Architecture Blueprints ────────────────────────────
    op.create_table(
        "architecture_blueprints",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tech_stack", JSONB(), nullable=False),
        sa.Column("components", JSONB(), nullable=False),
        sa.Column("api_contracts", JSONB(), nullable=False),
        sa.Column("db_schema", JSONB(), nullable=False),
        sa.Column("file_map", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_arch_session", "architecture_blueprints", ["session_id"])

    # ── Codebase State ─────────────────────────────────────
    op.create_table(
        "codebase_state",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("language", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("review_score", sa.Float(), server_default="0.0"),
        sa.Column("status", sa.String(50), server_default="DRAFT"),
        sa.Column("comments", JSONB(), server_default="[]"),
        sa.Column("assigned_to", sa.String(100), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_code_session", "codebase_state", ["session_id"])
    op.create_unique_constraint("uq_session_file", "codebase_state", ["session_id", "file_path"])

    # ── Test Results ───────────────────────────────────────
    op.create_table(
        "test_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_type", sa.String(50), nullable=False),
        sa.Column("coverage_pct", sa.Float(), nullable=True),
        sa.Column("tests_total", sa.Integer(), nullable=True),
        sa.Column("tests_passed", sa.Integer(), nullable=True),
        sa.Column("tests_failed", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("findings", JSONB(), server_default="[]"),
        sa.Column("raw_output", sa.Text(), nullable=True),
        sa.Column("run_at", sa.DateTime(), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_test_session", "test_results", ["session_id"])

    # ── Quality Scores ─────────────────────────────────────
    op.create_table(
        "quality_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("iteration", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("code_quality", sa.Float(), server_default="0.0"),
        sa.Column("test_coverage", sa.Float(), server_default="0.0"),
        sa.Column("security_score", sa.Float(), server_default="0.0"),
        sa.Column("perf_score", sa.Float(), server_default="0.0"),
        sa.Column("overall", sa.Float(), server_default="0.0"),
        sa.Column("gate_passed", sa.Boolean(), server_default="false"),
        sa.Column("gate_details", JSONB(), server_default="{}"),
        sa.Column("computed_at", sa.DateTime(), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_quality_session", "quality_scores", ["session_id"])

    # ── Error Registry ─────────────────────────────────────
    op.create_table(
        "error_registry",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(100), nullable=False),
        sa.Column("agent_type", sa.String(100), nullable=False),
        sa.Column("error_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("context", JSONB(), server_default="{}"),
        sa.Column("retry_count", sa.Integer(), server_default="0"),
        sa.Column("resolved", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_error_session", "error_registry", ["session_id"])

    # ── Agent Logs ─────────────────────────────────────────
    op.create_table(
        "agent_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(100), nullable=False),
        sa.Column("agent_type", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("tokens_in", sa.Integer(), server_default="0"),
        sa.Column("tokens_out", sa.Integer(), server_default="0"),
        sa.Column("duration_ms", sa.Integer(), server_default="0"),
        sa.Column("model_used", sa.String(200), nullable=True),
        sa.Column("ts", sa.DateTime(), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_log_session", "agent_logs", ["session_id"])
    op.create_index("ix_log_ts", "agent_logs", ["ts"])


def downgrade() -> None:
    op.drop_table("agent_logs")
    op.drop_table("error_registry")
    op.drop_table("quality_scores")
    op.drop_table("test_results")
    op.drop_table("codebase_state")
    op.drop_table("architecture_blueprints")
    op.drop_table("spec_artifacts")
    op.drop_table("sessions")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
