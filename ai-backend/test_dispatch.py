"""Test if run_analysis_task.delay() actually sends to Redis."""
from app.workers.tasks_analysis import run_analysis_task
result = run_analysis_task.delay("TEST-FAKE-ID-123")
print(f"Task sent via .delay(): id={result.id}")
print(f"Task state: {result.state}")
