"""Test V1Provider analysis + ORM operations step by step."""
import traceback

# Step 1: Can we connect and query?
print("Step 1: DB connection...")
from app.db.database import SessionLocal, engine
engine.echo = False
db = SessionLocal()

from sqlalchemy import text
row = db.execute(text("SELECT id, case_id, asset_id, status FROM analysis_runs ORDER BY queued_at DESC LIMIT 1")).fetchone()
if not row:
    print("No analysis runs"); exit(1)
run_id, case_id, asset_id, status = str(row[0]), str(row[1]), str(row[2]), row[3]
print(f"  Run: {run_id[:8]}... status={status}")
db.close()

# Step 2: Can we load the ORM model?
print("\nStep 2: Loading AnalysisRun via ORM...")
db = SessionLocal()
try:
    from app.repositories.analysis_repository import AnalysisRepository
    repo = AnalysisRepository(db)
    run = repo.get_run(run_id)
    if run:
        print(f"  ORM loaded: {run}")
    else:
        print("  FAIL: run not found via ORM")
        exit(1)
except Exception as ex:
    print(f"  FAIL: {type(ex).__name__}: {ex}")
    traceback.print_exc()
    exit(1)

# Step 3: Can we update status?
print("\nStep 3: Updating status to running...")
try:
    from app.core.constants import AnalysisStatus
    repo.update_status(run, AnalysisStatus.RUNNING)
    print(f"  Updated to RUNNING")
except Exception as ex:
    print(f"  FAIL: {type(ex).__name__}: {ex}")
    traceback.print_exc()
    exit(1)

# Step 4: Can we get the asset?
print("\nStep 4: Loading asset...")
try:
    from app.repositories.asset_repository import AssetRepository
    asset_repo = AssetRepository(db)
    asset = asset_repo.get_by_id(run.asset_id)
    if asset:
        print(f"  Asset: {asset.original_filename}, key={asset.storage_key}")
    else:
        print("  FAIL: asset not found")
        exit(1)
except Exception as ex:
    print(f"  FAIL: {type(ex).__name__}: {ex}")
    traceback.print_exc()
    exit(1)

# Step 5: Can we download the image?
print("\nStep 5: Downloading image...")
try:
    from app.providers.storage_provider_local import LocalStorageProvider
    storage = LocalStorageProvider()
    image_data = storage.download(asset.storage_key)
    print(f"  Downloaded {len(image_data)} bytes")
except Exception as ex:
    print(f"  FAIL: {type(ex).__name__}: {ex}")
    traceback.print_exc()
    exit(1)

# Step 6: Can we run V1Provider?
print("\nStep 6: Running V1Provider...")
try:
    import os, tempfile
    fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
    os.write(fd, image_data)
    os.close(fd)
    
    from app.providers.ai_provider_v1 import V1Provider
    provider = V1Provider()
    result = provider.analyze(tmp_path)
    os.unlink(tmp_path)
    print(f"  Analysis result: total_cells={result['total_cells']}, sickle={result['sickle_count']}")
except Exception as ex:
    print(f"  FAIL: {type(ex).__name__}: {ex}")
    traceback.print_exc()
    exit(1)

# Step 7: Mark as completed
print("\nStep 7: Marking as completed...")
try:
    repo.update_status(run, AnalysisStatus.COMPLETED, duration_ms=1000)
    print(f"  Marked as COMPLETED")
except Exception as ex:
    print(f"  FAIL: {type(ex).__name__}: {ex}")
    traceback.print_exc()
    exit(1)

db.close()
print("\n=== ALL STEPS PASSED ===")
