"""
LabMind AI — Patient Service
"""

from sqlalchemy.orm import Session

from app.core.constants import AuditAction
from app.core.exceptions import ConflictException, NotFoundException
from app.db.models.patient import Patient
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services.audit_service import AuditService


class PatientService:
    def __init__(self, db: Session):
        self.repo = PatientRepository(db)
        self.audit = AuditService(db)

    def create(self, data: PatientCreate, user_id, ip: str | None = None) -> Patient:
        existing = self.repo.get_by_code(data.patient_code)
        if existing:
            raise ConflictException(detail=f"Patient code '{data.patient_code}' already exists.")

        patient = Patient(
            patient_code=data.patient_code,
            full_name=data.full_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            blood_type=data.blood_type,
            contact_phone=data.contact_phone,
            notes=data.notes,
        )
        created = self.repo.create(patient)

        self.audit.log(
            action=AuditAction.PATIENT_CREATED,
            user_id=user_id,
            entity_type="patient",
            entity_id=created.id,
            details={"patient_code": data.patient_code, "full_name": data.full_name},
            ip_address=ip,
        )
        return created

    def get(self, patient_id) -> Patient:
        patient = self.repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundException(detail="Patient not found.")
        return patient

    def update(self, patient_id, data: PatientUpdate) -> Patient:
        patient = self.get(patient_id)
        updates = data.model_dump(exclude_unset=True)
        return self.repo.update(patient, updates)

    def list_all(self, skip: int = 0, limit: int = 50, search: str | None = None):
        return self.repo.list_all(skip=skip, limit=limit, search=search)
