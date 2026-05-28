"""
LabMind AI — End-to-End Pipeline Diagnostic
Tests each stage of the Hematology pipeline and reports exact errors.
"""
import sys, os, traceback, json

sys.path.insert(0, os.getcwd())

def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")

# ── TEST 1: Database connectivity & tables ──
section("1. DATABASE CONNECTION + TABLE CHECK")
try:
    from app.db.database import engine, SessionLocal
    from sqlalchemy import inspect, text
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("DB connection: OK")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables found ({len(tables)}): {sorted(tables)}")
    
    required = ["users", "patients", "lab_cases", "case_assets", 
                "analysis_runs", "analysis_results", "audit_logs"]
    missing = [t for t in required if t not in tables]
    if missing:
        print(f"*** MISSING TABLES: {missing} ***")
    else:
        print("All required tables: PRESENT")
        
    # Check alembic version
    try:
        with engine.connect() as conn:
            r = conn.execute(text("SELECT version_num FROM alembic_version"))
            ver = r.scalar()
            print(f"Alembic version: {ver}")
    except Exception as e:
        print(f"Alembic version check failed: {e}")
        
except Exception as e:
    print(f"DB FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# ── TEST 2: Register + Login ──
section("2. AUTH: REGISTER + LOGIN")
from app.db.database import SessionLocal
db = SessionLocal()
try:
    from app.services.auth_service import AuthService
    from app.schemas.auth import RegisterRequest
    auth = AuthService(db)
    
    # Try register
    try:
        from app.db.models.user import User
        from sqlalchemy import select
        existing = db.execute(select(User).where(User.email == "diag@test.com")).scalar_one_or_none()
        if existing:
            print(f"Test user exists: id={existing.id}")
            user = existing
        else:
            req = RegisterRequest(email="diag@test.com", password="Test1234!", full_name="Diag User")
            user = auth.register(req, ip="127.0.0.1")
            print(f"Registered user: id={user.id}")
    except Exception as e:
        print(f"Register error: {e}")
        # Try login instead
        
    # Login
    token_data = auth.login(email="diag@test.com", password="Test1234!", ip="127.0.0.1")
    token = token_data.get("access_token") if isinstance(token_data, dict) else getattr(token_data, "access_token", None)
    print(f"Login OK, token: {str(token)[:40]}...")
    user_id = user.id
    
except Exception as e:
    print(f"AUTH FAILED: {e}")
    traceback.print_exc()
    db.close()
    sys.exit(1)
finally:
    db.close()

# ── TEST 3: Create Patient ──
section("3. CREATE PATIENT")
db = SessionLocal()
try:
    from app.services.patient_service import PatientService
    from app.schemas.patient import PatientCreate
    svc = PatientService(db)
    p = svc.create(
        PatientCreate(patient_code=f"DIAG-{int(__import__('time').time())}", full_name="Diag Patient"),
        user_id=user_id, ip="127.0.0.1"
    )
    print(f"Patient created: id={p.id}, code={p.patient_code}")
    patient_id = p.id
except Exception as e:
    print(f"CREATE PATIENT FAILED: {e}")
    traceback.print_exc()
    db.close()
    sys.exit(1)
finally:
    db.close()

# ── TEST 4: Create Case ──
section("4. CREATE CASE")
db = SessionLocal()
try:
    from app.services.case_service import CaseService
    from app.schemas.case import CaseCreate
    svc = CaseService(db)
    c = svc.create(
        CaseCreate(patient_id=patient_id, department="hematology", test_type="blood_smear"),
        user_id=user_id, ip="127.0.0.1"
    )
    print(f"Case created: id={c.id}, number={c.case_number}")
    case_id = c.id
except Exception as e:
    print(f"CREATE CASE FAILED: {e}")
    traceback.print_exc()
    db.close()
    sys.exit(1)
finally:
    db.close()

# ── TEST 5: Upload Asset ──
section("5. UPLOAD ASSET")
db = SessionLocal()
try:
    from app.services.asset_service import AssetService
    from app.providers.storage_provider_local import LocalStorageProvider
    import numpy as np
    import cv2
    
    storage = LocalStorageProvider(root_dir="uploads")
    svc = AssetService(db, storage)
    
    # Create a small test image
    test_img = np.zeros((100, 100, 3), dtype=np.uint8)
    test_img[:] = (128, 64, 64)
    _, img_bytes = cv2.imencode('.jpg', test_img)
    file_data = img_bytes.tobytes()
    
    asset = svc.upload(
        case_id=case_id, user_id=user_id,
        filename="diag_test.jpg", file_data=file_data,
        content_type="image/jpeg", asset_type="blood_smear", ip="127.0.0.1"
    )
    print(f"Asset uploaded: id={asset.id if hasattr(asset, 'id') else asset}")
    asset_id = asset.id if hasattr(asset, 'id') else asset.get("id")
except Exception as e:
    print(f"UPLOAD ASSET FAILED: {e}")
    traceback.print_exc()
    db.close()
    sys.exit(1)
finally:
    db.close()

# ── TEST 6: Trigger Analysis ──
section("6. TRIGGER ANALYSIS")
db = SessionLocal()
try:
    from app.services.analysis_service import AnalysisService
    svc = AnalysisService(db)
    run = svc.trigger(case_id=case_id, asset_id=asset_id, user_id=user_id, ip="127.0.0.1")
    print(f"Analysis triggered: run_id={run.id}, status={run.status}")
    run_id = run.id
except Exception as e:
    print(f"TRIGGER ANALYSIS FAILED: {e}")
    traceback.print_exc()
    db.close()
    sys.exit(1)
finally:
    db.close()

# ── TEST 7: V1Provider loading ──
section("7. V1PROVIDER MODEL CHECK")
try:
    from app.providers.ai_provider_v1 import V1Provider
    v1 = V1Provider()
    mode = v1._classifier_mode_label()
    print(f"V1Provider loaded. Mode: {mode}")
    print(f"CNN model: {v1._cnn_model is not None}")
    print(f"Num classes: {v1._cnn_num_classes}")
    print(f"YOLO model: {v1._yolo_model is not None}")
except Exception as e:
    print(f"V1PROVIDER FAILED: {e}")
    traceback.print_exc()

section("DIAGNOSTIC COMPLETE")
print("If all tests pass, the pipeline should work.")
print("If any test failed, the traceback above shows the exact root cause.")
