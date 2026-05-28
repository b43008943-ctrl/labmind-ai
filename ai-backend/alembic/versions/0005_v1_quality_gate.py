"""Add quality gate columns to analysis_results

Revision ID: 0005
Revises: 0004_sprint4_reports
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0005_v1_quality_gate"
down_revision = "0004_sprint4_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("analysis_results", sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column("analysis_results", sa.Column("quality_status", sa.String(20), nullable=True))
    op.add_column("analysis_results", sa.Column("rejection_reason", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("analysis_results", "rejection_reason")
    op.drop_column("analysis_results", "quality_status")
    op.drop_column("analysis_results", "quality_score")
