"""Extract full error from case_raw.json - write each field to separate files."""
import json

with open("d:/New folder/ai-backend/case_raw.json") as f:
    data = json.load(f)

# Write error to separate file  
with open("d:/New folder/ai-backend/err_error.txt", "w") as f:
    f.write(data.get("error", "NO ERROR KEY"))

with open("d:/New folder/ai-backend/err_type.txt", "w") as f:
    f.write(data.get("type", "NO TYPE KEY"))

with open("d:/New folder/ai-backend/err_tb.txt", "w") as f:
    f.write(data.get("tb", "NO TB KEY"))

print(f"type: {data.get('type', 'none')}")
print(f"error length: {len(data.get('error', ''))}")
print(f"tb length: {len(data.get('tb', ''))}")
