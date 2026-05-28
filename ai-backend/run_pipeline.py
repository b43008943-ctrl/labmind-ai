"""Re-run pipeline test capturing output to file."""
import subprocess, sys
result = subprocess.run(
    [sys.executable, "test_full_pipeline.py"],
    capture_output=True, text=True, encoding="utf-8",
    cwd="d:/New folder/ai-backend", timeout=120
)
with open("d:/New folder/ai-backend/pipeline_output.txt", "w", encoding="utf-8") as f:
    f.write(result.stdout)
    if result.stderr:
        f.write("\n--- STDERR ---\n")
        f.write(result.stderr)
print(f"Exit: {result.returncode}")
print(f"Stdout: {len(result.stdout)} chars")
