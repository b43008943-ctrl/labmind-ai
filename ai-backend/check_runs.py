"""Check latest analysis run statuses."""
from sqlalchemy import create_engine, text
e = create_engine("postgresql+psycopg://labmind:labmind_secret@localhost:5432/labmind_db")
with e.connect() as c:
    rows = c.execute(text("SELECT id, status, error_message FROM analysis_runs ORDER BY queued_at DESC LIMIT 5")).fetchall()
    for row in rows:
        err = str(row[2])[:150] if row[2] else "none"
        print(f"status={row[1]} | err={err}")
