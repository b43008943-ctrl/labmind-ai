"""Sprint 3 — analysis_runs and analysis_results tables

Revision ID: 0003_sprint3_analysis
Revises: 0002_sprint2_data_layer
Create Date: 2026-03-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_sprint3_analysis"
down_revision: Union[str, None] = "0002_sprint2_data_layer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Create analysis_status_enum ──
    analysis_status_enum = postgresql.ENUM(
        "queued", "running", "completed", "failed",
        name="analysis_status_enum", create_type=False,
    )
    analysis_status_enum.create(op.get_bind(), checkfirst=True)

    # ── analysis_runs ──
    op.create_table(
        "analysis_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lab_cases.id"), nullable=False, index=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("case_assets.id"), nullable=False),
        sa.Column("triggered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("engine_version", sa.String(20), nullable=False, server_default="V34"),
        sa.Column("status", analysis_status_enum, nullable=False, server_default="queued"),
        sa.Column("config_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── analysis_results ──
    op.create_table(
        "analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_runs.id"), unique=True, nullable=False),
        sa.Column("total_cells", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sickle_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("normal_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sickle_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("cell_details", postgresql.JSONB(), nullable=True),
        sa.Column("annotated_image_key", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("analysis_results")
    op.drop_table("analysis_runs")
    postgresql.ENUM(name="analysis_status_enum").drop(op.get_bind(), checkfirst=True)
