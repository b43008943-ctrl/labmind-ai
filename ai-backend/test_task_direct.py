"""Run the analysis task directly with verbose error output."""
import traceback, sys

# Disable SQLAlchemy echo to reduce noise
import os
os.environ.setdefault("DEBUG", "false")

try:
    from app.db.database import SessionLocal, engine
    engine.echo = False

    from sqlalchemy import text
    db = SessionLocal()
    row = db.execute(text("SELECT id, status FROM analysis_runs ORDER BY queued_at DESC LIMIT 1")).fetchone()
    db.close()
    
    if not row:
        print("No analysis runs found")
        sys.exit(1)
    
    run_id = str(row[0])
    print(f"Run: {run_id}, status={row[1]}")
    
    if row[1] != 'queued':
        print(f"Status is '{row[1]}', not 'queued' — nothing to do")
        sys.exit(0)
    
    # Call the task function directly
    from app.workers.tasks_analysis import run_analysis_task
    print("Executing task...")
    result = run_analysis_task(run_id)
    print(f"RESULT: {result}")
    
except Exception as ex:
    print(f"\nFATAL ERROR: {type(ex).__name__}: {ex}")
    traceback.print_exc()
    
    # Write to file for safe reading
    with open("d:/New folder/ai-backend/task_exec_error.txt", "w") as f:
        f.write(f"ERROR: {type(ex).__name__}: {ex}\n\n")
        f.write(traceback.format_exc())
