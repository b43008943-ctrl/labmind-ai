"""
LabMind AI — Lab Case ORM Model
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import CasePriority, CaseStatus, Department
from app.db.database import Base


class LabCase(Base):
    __tablename__ = "lab_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_number: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False
    )
    clinician_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    department: Mapped[Department] = mapped_column(
        Enum(Department, name="department_enum", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    test_type: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[CasePriority] = mapped_column(
        Enum(CasePriority, name="case_priority_enum", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CasePriority.ROUTINE,
    )
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status_enum", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CaseStatus.OPEN,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    patient = relationship("Patient", back_populates="cases", lazy="joined")
    assets = relationship("CaseAsset", back_populates="case", lazy="select")

    def __repr__(self) -> str:
        return f"<LabCase {self.case_number} [{self.status.value}]>"

