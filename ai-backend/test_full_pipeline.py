"""Full E2E pipeline with state transition tracking."""
import time, requests, json, subprocess, sys

BASE = "http://localhost:8000"
DB_URL = "postgresql+psycopg://labmind:labmind_secret@localhost:5432/labmind_db"

# ── Login ──
r = requests.post(f"{BASE}/api/auth/token", json={"email": "test@labmind.ai", "password": "TestPass123"})
assert r.status_code == 200, f"LOGIN FAIL: {r.status_code}"
token = r.json()["access_token"]
H = {"Authorization": f"Bearer {token}"}
print("LOGIN .............. OK")

# ── Auth/me ──
r = requests.get(f"{BASE}/api/auth/me", headers=H)
print(f"AUTH/ME ............ {'OK' if r.status_code == 200 else 'FAIL'} ({r.status_code})")

# ── Patient ──
ts = int(time.time())
r = requests.post(f"{BASE}/api/patients/", json={"patient_code": f"CEL-{ts}", "full_name": f"Celery Test {ts}"}, headers=H)
assert r.status_code == 201, f"PATIENT FAIL: {r.status_code} {r.text[:200]}"
pid = r.json()["id"]
print("PATIENT ............ OK")

# ── Case ──
r = requests.post(f"{BASE}/api/cases/", json={"patient_id": pid, "department": "hematology", "test_type": "blood_smear"}, headers=H)
assert r.status_code == 201, f"CASE FAIL: {r.status_code} {r.text[:200]}"
case_id = r.json()["id"]
print(f"CASE ............... OK ({r.json().get('case_number')})")

# ── Upload ──
with open("d:/New folder/ai-backend/test_images/Sickle_Cell_Blood_Smear.jpg", "rb") as f:
    r = requests.post(f"{BASE}/api/cases/{case_id}/assets", files={"file": ("test.jpg", f, "image/jpeg")}, data={"asset_type": "blood_smear"}, headers=H)
assert r.status_code == 201, f"UPLOAD FAIL: {r.status_code} {r.text[:200]}"
asset_id = r.json()["id"]
print("UPLOAD ............. OK")

# ── Trigger ──
r = requests.post(f"{BASE}/api/analyses/trigger", json={"case_id": case_id, "asset_id": asset_id}, headers=H)
assert r.status_code in (200, 201, 202), f"TRIGGER FAIL: {r.status_code} {r.text[:200]}"
run_id = r.json()["id"]
print(f"TRIGGER ............ OK (run_id={run_id[:12]}...)")

# ── Poll with state transition tracking ──
print("\nSTATE TRANSITIONS:")
seen_states = []
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
eng = create_engine(DB_URL)
Sess = sessionmaker(bind=eng)

for i in range(60):
    time.sleep(1)
    db = Sess()
    row = db.execute(text("SELECT status, error_message, duration_ms FROM analysis_runs WHERE id = :rid"), {"rid": run_id}).fetchone()
    db.close()
    if row:
        st = row[0]
        if not seen_states or seen_states[-1] != st:
            seen_states.append(st)
            err = f" error={row[1][:100]}" if row[1] else ""
            dur = f" duration={row[2]}ms" if row[2] else ""
            print(f"  [{i+1:2d}s] {st}{err}{dur}")
        if st in ("completed", "failed"):
            break

print(f"\nFINAL STATE: {seen_states[-1] if seen_states else 'unknown'}")
print(f"TRANSITIONS: {' -> '.join(seen_states)}")

# ── Verify results via API ──
if seen_states and seen_states[-1] == "completed":
    print("\nRESULT VERIFICATION:")
    r = requests.get(f"{BASE}/api/analyses/runs/{run_id}", headers=H)
    if r.status_code == 200:
        data = r.json()
        run_data = data.get("run", {})
        result = data.get("result", {})
        print(f"  API status endpoint .... OK ({r.status_code})")
        print(f"  run.status ............. {run_data.get('status')}")
        print(f"  run.duration_ms ........ {run_data.get('duration_ms')}")
        print(f"  result.total_cells ..... {result.get('total_cells')}")
        print(f"  result.sickle_count .... {result.get('sickle_count')}")
        print(f"  result.normal_count .... {result.get('normal_count')}")
        print(f"  result.sickle_pct ...... {result.get('sickle_percentage')}%")
        cd = result.get("cell_details")
        det_count = len(cd.get("detections", [])) if isinstance(cd, dict) else "N/A"
        print(f"  cell_details type ...... {type(cd).__name__}")
        print(f"  detections count ....... {det_count}")
        if isinstance(cd, dict) and cd.get("detections"):
            d0 = cd["detections"][0]
            print(f"  sample detection keys .. {sorted(d0.keys())}")
        
        # Check annotated image endpoint
        r2 = requests.get(f"{BASE}/api/analyses/runs/{run_id}/annotated-image", headers=H)
        print(f"  annotated image ep ..... {'OK' if r2.status_code == 200 else f'FAIL ({r2.status_code})'}")
        
        # Save full response
        with open("d:/New folder/ai-backend/celery_e2e_result.json", "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"\n  Full result saved to celery_e2e_result.json")
    else:
        print(f"  API status endpoint .... FAIL ({r.status_code})")

elif seen_states and seen_states[-1] == "failed":
    print("\nFAILED — checking error:")
    db = Sess()
    row = db.execute(text("SELECT error_message FROM analysis_runs WHERE id = :rid"), {"rid": run_id}).fetchone()
    db.close()
    if row and row[0]:
        print(f"  Error: {row[0]}")
    
    # Also check audit_logs for traceback
    db = Sess()
    row = db.execute(text("SELECT details FROM audit_logs WHERE entity_id = :rid AND action = 'analysis_failed' ORDER BY created_at DESC LIMIT 1"), {"rid": run_id}).fetchone()
    db.close()
    if row and row[0]:
        details = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        print(f"  Traceback:\n{details.get('traceback', 'N/A')}")
else:
    print("\nTIMEOUT — analysis did not complete in 60s")

print("\n" + "=" * 50)
print("DONE")
