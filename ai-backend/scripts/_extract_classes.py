import json
from pathlib import Path
from collections import Counter

JSON_DIR = Path(r"D:\New folder\ai-backend\dataset_microbiology\dataset_microbiology\DeepDataSet\640DataSet\json")
class_names = Counter()
all_files = sorted(JSON_DIR.glob("*.json"))
for jf in all_files:
    with open(jf, encoding="utf-8") as f:
        data = json.load(f)
    for shape in data.get("shapes", []):
        class_names[shape.get("label", "UNKNOWN")] += 1

print("ALL CLASS NAMES from LabelMe JSON (all files):")
for name, cnt in class_names.most_common():
    print(f'  "{name}" -> {cnt} annotations')
print(f"\nTotal unique classes: {len(class_names)}")
print(f"Total files scanned: {len(all_files)}")

# Sample a file that has a non-G label
for jf in all_files:
    with open(jf, encoding="utf-8") as f:
        data = json.load(f)
    labels = set(s.get("label") for s in data.get("shapes", []))
    if labels - {"G", "G+"}:
        print(f"\nSample file with other labels: {jf.name}")
        for s in data["shapes"]:
            print(f'  label="{s["label"]}", shape_type={s.get("shape_type")}')
        break
