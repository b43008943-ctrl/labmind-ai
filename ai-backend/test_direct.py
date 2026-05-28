"""Directly test case creation via ORM, bypassing API."""
import time, sys, traceback
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql+psycopg://labmind:labmind_secret@localhost:5432/labmind_db"
eng = create_engine(DB_URL, echo=True)

# Register enums
@event.listens_for(eng, "connect")
def on_connect(dbapi_conn, conn_record):
    from psycopg.types import TypeInfo
    for name in ["department_enum", "case_priority_enum", "case_status_enum"]:
        info = TypeInfo.fetch(dbapi_conn, name)
        if info:
            info.register(dbapi_conn)
            print(f"  Registered {name} (OID {info.oid})")

Session = sessionmaker(bind=eng)
db = Session()

try:
    # Step 1: try inserting a LabCase directly via SQL
    from sqlalchemy import text
    
    # First get a valid patient and user ID
    user_row = db.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
    patient_row = db.execute(text("SELECT id FROM patients LIMIT 1")).fetchone()
    
    if not user_row or not patient_row:
        print("No user or patient found - create one first")
        sys.exit(1)
    
    user_id = user_row[0]
    patient_id = patient_row[0]
    print(f"User: {user_id}, Patient: {patient_id}")
    
    # Step 2: Try a raw INSERT
    ts = int(time.time())
    result = db.execute(
        text("""
            INSERT INTO lab_cases (id, case_number, patient_id, clinician_id, department, test_type, priority, status, created_at, updated_at)
            VALUES (gen_random_uuid(), :cn, :pid, :uid, :dept, :tt, :pri, :stat, now(), now())
            RETURNING id, case_number
        """),
        {"cn": f"LC-2026-TEST-{ts}", "pid": patient_id, "uid": user_id,
         "dept": "hematology", "tt": "blood_smear", "pri": "routine", "stat": "open"}
    )
    db.commit()
    row = result.fetchone()
    print(f"RAW INSERT OK: {row}")
    
except Exception as ex:
    print(f"ERROR: {type(ex).__name__}: {ex}")
    traceback.print_exc()
finally:
    db.close()
