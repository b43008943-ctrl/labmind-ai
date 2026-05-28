"""
LabMind AI — Patient Repository
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.patient import Patient


class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, patient_id: UUID) -> Patient | None:
        return self.db.get(Patient, patient_id)

    def get_by_code(self, patient_code: str) -> Patient | None:
        stmt = select(Patient).where(Patient.patient_code == patient_code)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, patient: Patient) -> Patient:
        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def update(self, patient: Patient, updates: dict) -> Patient:
        for key, value in updates.items():
            if value is not None:
                setattr(patient, key, value)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def list_all(
        self, skip: int = 0, limit: int = 50, search: str | None = None
    ) -> list[Patient]:
        stmt = select(Patient).order_by(Patient.created_at.desc())
        if search:
            stmt = stmt.where(
                Patient.full_name.ilike(f"%{search}%")
                | Patient.patient_code.ilike(f"%{search}%")
            )
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
