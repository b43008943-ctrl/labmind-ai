"""
LabMind AI — Analysis Result ORM Model
Stores the output of a completed V34 diagnostic run.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_runs.id"), unique=True, nullable=False
    )
    total_cells: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sickle_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    normal_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sickle_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cell_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    annotated_image_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AnalysisResult run={self.run_id} cells={self.total_cells}>"

