"""Sprint 4 — diagnostic_reports, report_reviews, and alerts tables

Revision ID: 0004_sprint4_reports
Revises: 0003_sprint3_analysis
Create Date: 2026-03-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004_sprint4_reports"
down_revision: Union[str, None] = "0003_sprint3_analysis"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Create enums ──
    report_status_enum = postgresql.ENUM(
        "draft", "processing", "preliminary", "pending_review",
        "approved", "rejected", "archived",
        name="report_status_enum", create_type=False,
    )
    report_status_enum.create(op.get_bind(), checkfirst=True)

    review_decision_enum = postgresql.ENUM(
        "approved", "rejected", "request_changes",
        name="review_decision_enum", create_type=False,
    )
    review_decision_enum.create(op.get_bind(), checkfirst=True)

    alert_type_enum = postgresql.ENUM(
        "critical_finding", "review_required", "report_rejected", "system",
        name="alert_type_enum", create_type=False,
    )
    alert_type_enum.create(op.get_bind(), checkfirst=True)

    alert_priority_enum = postgresql.ENUM(
        "low", "medium", "high", "critical",
        name="alert_priority_enum", create_type=False,
    )
    alert_priority_enum.create(op.get_bind(), checkfirst=True)

    # ── diagnostic_reports ──
    op.create_table(
        "diagnostic_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lab_cases.id"), nullable=False, index=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_runs.id"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", report_status_enum, nullable=False, server_default="draft"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("findings", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("clinician_notes", sa.Text(), nullable=True),
        sa.Column("ai_summary", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── report_reviews ──
    op.create_table(
        "report_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("diagnostic_reports.id"), nullable=False, index=True),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", review_decision_enum, nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── alerts ──
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("alert_type", alert_type_enum, nullable=False),
        sa.Column("priority", alert_priority_enum, nullable=False, server_default="medium"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("dismissed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("report_reviews")
    op.drop_table("diagnostic_reports")
    postgresql.ENUM(name="alert_priority_enum").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="alert_type_enum").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="review_decision_enum").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="report_status_enum").drop(op.get_bind(), checkfirst=True)
