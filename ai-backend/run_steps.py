"""Redirect step test output to file."""
import subprocess, sys
result = subprocess.run(
    [sys.executable, "test_steps.py"],
    capture_output=True, text=True, encoding="utf-8", cwd="d:/New folder/ai-backend"
)
with open("d:/New folder/ai-backend/steps_output.txt", "w", encoding="utf-8") as f:
    f.write("=== STDOUT ===\n")
    f.write(result.stdout)
    f.write("\n\n=== STDERR ===\n")
    f.write(result.stderr)
print(f"Exit code: {result.returncode}")
print(f"Stdout: {len(result.stdout)} chars")
print(f"Stderr: {len(result.stderr)} chars")
