"""Capture raw case response to file."""
import time, json, requests

BASE = "http://localhost:8000"
r = requests.post(f"{BASE}/api/auth/token", json={"email": "test@labmind.ai", "password": "TestPass123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

ts = int(time.time())
r = requests.post(f"{BASE}/api/patients/", json={"patient_code": f"T-{ts}", "full_name": f"Test {ts}"}, headers=headers)
pid = r.json()["id"]

r2 = requests.post(
    f"{BASE}/api/cases/",
    json={"patient_id": pid, "department": "hematology", "test_type": "blood_smear"},
    headers=headers,
)

# Write the raw JSON response to a file
with open("d:/New folder/ai-backend/case_raw.json", "wb") as f:
    f.write(r2.content)

# Also extract error type if JSON
try:
    data = r2.json()
    err_type = data.get("type", "unknown")
    err_msg = data.get("error", "unknown")[:200]
    with open("d:/New folder/ai-backend/error_summary.txt", "w") as f:
        f.write(f"status: {r2.status_code}\n")
        f.write(f"type: {err_type}\n")
        f.write(f"error (first 200 chars): {err_msg}\n")
except:
    with open("d:/New folder/ai-backend/error_summary.txt", "w") as f:
        f.write(f"status: {r2.status_code}\n")
        f.write(f"raw (first 200): {r2.text[:200]}\n")

print("Done")
