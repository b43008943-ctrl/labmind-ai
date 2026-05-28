"""Test case ORM insertion directly with StrEnumDumper."""
import time, traceback
from datetime import datetime, timezone
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.core.constants import Department, CasePriority, CaseStatus

DB_URL = "postgresql+psycopg://labmind:labmind_secret@localhost:5432/labmind_db"
eng = create_engine(DB_URL, echo=False)

@event.listens_for(eng, "connect")
def on_connect(dbapi_conn, conn_record):
    from psycopg.adapt import Dumper
    from app.core.constants import (
        Department, CasePriority, CaseStatus, AssetType,
        Gender, RashaRole, UserRole, AnalysisStatus,
        ReportStatus, ReviewDecision, AlertType, AlertPriority,
        AuditAction,
    )
    class StrEnumDumper(Dumper):
        def dump(self, obj):
            return obj.value.encode("utf-8") if hasattr(obj, "value") else str(obj).encode("utf-8")
    for cls in [Department, CasePriority, CaseStatus, AssetType,
                Gender, RashaRole, UserRole, AnalysisStatus,
                ReportStatus, ReviewDecision, AlertType, AlertPriority,
                AuditAction]:
        dbapi_conn.adapters.register_dumper(cls, StrEnumDumper)
    print("StrEnumDumper registered for all enums")

from app.db.models.lab_case import LabCase

Sess = sessionmaker(bind=eng)
db = Sess()

try:
    user_row = db.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
    pat_row = db.execute(text("SELECT id FROM patients LIMIT 1")).fetchone()
    
    ts = int(time.time())
    case = LabCase(
        case_number=f"LC-2026-DUMPER-{ts}",
        patient_id=pat_row[0],
        clinician_id=user_row[0],
        department=Department.HEMATOLOGY,
        test_type="blood_smear",
        priority=CasePriority.ROUTINE,
        status=CaseStatus.OPEN,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    print(f"SUCCESS! Case: {case.id} / {case.case_number}")
    
except Exception as ex:
    print(f"FAILED: {type(ex).__name__}: {ex}")
    traceback.print_exc()
finally:
    db.close()
