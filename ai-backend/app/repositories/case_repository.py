"""
LabMind AI — Lab Case Repository
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.constants import CaseStatus
from app.db.models.lab_case import LabCase


class CaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, case_id: UUID) -> LabCase | None:
        stmt = (
            select(LabCase)
            .options(joinedload(LabCase.patient), joinedload(LabCase.assets))
            .where(LabCase.id == case_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def create(self, case: LabCase) -> LabCase:
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def update_status(self, case: LabCase, new_status: CaseStatus) -> LabCase:
        case.status = new_status
        self.db.commit()
        self.db.refresh(case)
        return case

    def list_all(
        self,
        skip: int = 0,
        limit: int = 50,
        status: CaseStatus | None = None,
        department: str | None = None,
    ) -> list[LabCase]:
        stmt = select(LabCase).order_by(LabCase.created_at.desc())
        if status:
            stmt = stmt.where(LabCase.status == status)
        if department:
            stmt = stmt.where(LabCase.department == department)
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def generate_case_number(self) -> str:
        """Generate next sequential case number: LC-YYYY-NNNNN"""
        from datetime import datetime, timezone

        year = datetime.now(timezone.utc).year
        prefix = f"LC-{year}-"
        stmt = (
            select(func.count())
            .select_from(LabCase)
            .where(LabCase.case_number.like(f"{prefix}%"))
        )
        count = self.db.execute(stmt).scalar() or 0
        return f"{prefix}{count + 1:05d}"
