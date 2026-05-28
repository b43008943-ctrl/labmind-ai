"""Sprint 2 — patients, lab_cases, case_assets, rasha_sessions, rasha_messages

Revision ID: 0002_sprint2_data_layer
Revises: 0001_sprint1_foundation
Create Date: 2026-03-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_sprint2_data_layer"
down_revision: Union[str, None] = "0001_sprint1_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Create enum types ──
    gender_enum = postgresql.ENUM("male", "female", "other", name="gender_enum", create_type=False)
    gender_enum.create(op.get_bind(), checkfirst=True)

    department_enum = postgresql.ENUM(
        "hematology", "urinalysis", "parasitology", "biochemistry", "microbiology", "bloodbank",
        name="department_enum", create_type=False,
    )
    department_enum.create(op.get_bind(), checkfirst=True)

    case_priority_enum = postgresql.ENUM("routine", "urgent", "stat", name="case_priority_enum", create_type=False)
    case_priority_enum.create(op.get_bind(), checkfirst=True)

    case_status_enum = postgresql.ENUM("open", "in_progress", "completed", "cancelled", name="case_status_enum", create_type=False)
    case_status_enum.create(op.get_bind(), checkfirst=True)

    asset_type_enum = postgresql.ENUM("blood_smear", "urine_sediment", "stool_sample", "other", name="asset_type_enum", create_type=False)
    asset_type_enum.create(op.get_bind(), checkfirst=True)

    rasha_role_enum = postgresql.ENUM("user", "rasha", name="rasha_role_enum", create_type=False)
    rasha_role_enum.create(op.get_bind(), checkfirst=True)

    # ── patients ──
    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("patient_code", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", gender_enum, nullable=True),
        sa.Column("blood_type", sa.String(5), nullable=True),
        sa.Column("contact_phone", sa.String(20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── lab_cases ──
    op.create_table(
        "lab_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_number", sa.String(30), unique=True, nullable=False, index=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("clinician_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("department", department_enum, nullable=False),
        sa.Column("test_type", sa.String(100), nullable=False),
        sa.Column("priority", case_priority_enum, nullable=False, server_default="routine"),
        sa.Column("status", case_status_enum, nullable=False, server_default="open"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── case_assets ──
    op.create_table(
        "case_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lab_cases.id"), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("asset_type", asset_type_enum, nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(50), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── rasha_sessions ──
    op.create_table(
        "rasha_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("context_screen", sa.String(50), nullable=True),
        sa.Column("context_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── rasha_messages ──
    op.create_table(
        "rasha_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rasha_sessions.id"), nullable=False, index=True),
        sa.Column("role", rasha_role_enum, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("rasha_messages")
    op.drop_table("rasha_sessions")
    op.drop_table("case_assets")
    op.drop_table("lab_cases")
    op.drop_table("patients")
    for name in ["rasha_role_enum", "asset_type_enum", "case_status_enum", "case_priority_enum", "department_enum", "gender_enum"]:
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
