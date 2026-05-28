"""Print error lines one by one to stdout."""
lines = open("d:/New folder/ai-backend/err_error.txt").read().split("\n")
for i, line in enumerate(lines):
    print(f"L{i}: {line[:120]}")
