"""
LabMind AI — Report Repository
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import ReportStatus
from app.db.models.diagnostic_report import DiagnosticReport
from app.db.models.report_review import ReportReview


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Reports ──

    def create(self, report: DiagnosticReport) -> DiagnosticReport:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_by_id(self, report_id: UUID) -> DiagnosticReport | None:
        return self.db.get(DiagnosticReport, report_id)

    def update(self, report: DiagnosticReport, updates: dict) -> DiagnosticReport:
        for key, value in updates.items():
            if value is not None:
                setattr(report, key, value)
        report.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(report)
        return report

    def update_status(self, report: DiagnosticReport, status: ReportStatus) -> DiagnosticReport:
        report.status = status
        report.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(report)
        return report

    def list_by_case(self, case_id: UUID) -> list[DiagnosticReport]:
        stmt = (
            select(DiagnosticReport)
            .where(DiagnosticReport.case_id == case_id)
            .order_by(DiagnosticReport.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_by_status(self, status: ReportStatus, skip: int = 0, limit: int = 50) -> list[DiagnosticReport]:
        stmt = (
            select(DiagnosticReport)
            .where(DiagnosticReport.status == status)
            .order_by(DiagnosticReport.updated_at.desc())
            .offset(skip).limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_by_user(self, user_id: UUID, skip: int = 0, limit: int = 50) -> list[DiagnosticReport]:
        stmt = (
            select(DiagnosticReport)
            .where(DiagnosticReport.created_by == user_id)
            .order_by(DiagnosticReport.updated_at.desc())
            .offset(skip).limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_by_user_and_status(self, user_id: UUID, status: ReportStatus) -> list[DiagnosticReport]:
        stmt = (
            select(DiagnosticReport)
            .where(DiagnosticReport.created_by == user_id)
            .where(DiagnosticReport.status == status)
            .order_by(DiagnosticReport.updated_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    # ── Reviews ──

    def add_review(self, review: ReportReview) -> ReportReview:
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_reviews(self, report_id: UUID) -> list[ReportReview]:
        stmt = (
            select(ReportReview)
            .where(ReportReview.report_id == report_id)
            .order_by(ReportReview.reviewed_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
