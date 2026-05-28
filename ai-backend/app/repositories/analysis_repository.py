"""
LabMind AI — Analysis Repository
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import AnalysisStatus
from app.db.models.analysis_result import AnalysisResult
from app.db.models.analysis_run import AnalysisRun


class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Runs ──
    def create_run(self, run: AnalysisRun) -> AnalysisRun:
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_run(self, run_id: UUID) -> AnalysisRun | None:
        return self.db.get(AnalysisRun, run_id)

    def update_status(
        self,
        run: AnalysisRun,
        status: AnalysisStatus,
        error_message: str | None = None,
        duration_ms: int | None = None,
    ) -> AnalysisRun:
        run.status = status
        if status == AnalysisStatus.RUNNING:
            run.started_at = datetime.now(timezone.utc)
        elif status in (AnalysisStatus.COMPLETED, AnalysisStatus.FAILED):
            run.completed_at = datetime.now(timezone.utc)
        if error_message:
            run.error_message = error_message
        if duration_ms is not None:
            run.duration_ms = duration_ms
        self.db.commit()
        self.db.refresh(run)
        return run

    def list_by_case(self, case_id: UUID) -> list[AnalysisRun]:
        stmt = (
            select(AnalysisRun)
            .where(AnalysisRun.case_id == case_id)
            .order_by(AnalysisRun.queued_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def has_active_run(self, asset_id: UUID) -> bool:
        """Check if an asset already has a QUEUED or RUNNING analysis."""
        stmt = (
            select(AnalysisRun)
            .where(AnalysisRun.asset_id == asset_id)
            .where(AnalysisRun.status.in_([AnalysisStatus.QUEUED, AnalysisStatus.RUNNING]))
        )
        return self.db.execute(stmt).scalar_one_or_none() is not None

    # ── Results ──
    def create_result(self, result: AnalysisResult) -> AnalysisResult:
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def get_result_by_run(self, run_id: UUID) -> AnalysisResult | None:
        stmt = select(AnalysisResult).where(AnalysisResult.run_id == run_id)
        return self.db.execute(stmt).scalar_one_or_none()
