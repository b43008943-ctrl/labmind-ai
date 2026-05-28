"""Cross-reference YOLO class IDs with LabelMe JSON labels to decode the class mapping."""
import json
from pathlib import Path
from collections import Counter, defaultdict

JSON_DIR = Path(r"D:\New folder\ai-backend\dataset_microbiology\dataset_microbiology\DeepDataSet\640DataSet\json")
LABELS_DIR = Path(r"D:\New folder\ai-backend\dataset_microbiology\dataset_microbiology\DeepDataSet\DetectionDataSet\labels")

# For files that exist in both JSON and YOLO labels, map YOLO class_id -> LabelMe label
# This works when a file has exactly 1 annotation in both
mapping = defaultdict(Counter)  # yolo_class_id -> Counter of labelme names

json_files = {f.stem: f for f in JSON_DIR.glob("*.json")}
label_files = {f.stem: f for f in LABELS_DIR.glob("*.txt")}

common = set(json_files) & set(label_files)
print(f"Files in both JSON and YOLO labels: {len(common)}")

checked = 0
for stem in sorted(common):
    if checked >= 2000:
        break
    # Read YOLO
    yolo_lines = [l.strip() for l in label_files[stem].read_text().strip().split("\n") if l.strip()]
    # Read LabelMe
    with open(json_files[stem], encoding="utf-8") as f:
        data = json.load(f)
    shapes = data.get("shapes", [])

    # Only useful if counts match (same number of annotations)
    if len(yolo_lines) == len(shapes) == 1:
        cls_id = int(yolo_lines[0].split()[0])
        labelme_name = shapes[0].get("label", "?")
        mapping[cls_id][labelme_name] += 1
        checked += 1
    elif len(yolo_lines) == len(shapes):
        # Multiple annotations - still try to map if all same class
        yolo_ids = set(int(l.split()[0]) for l in yolo_lines)
        labelme_names = set(s.get("label") for s in shapes)
        if len(yolo_ids) == 1 and len(labelme_names) == 1:
            mapping[list(yolo_ids)[0]][list(labelme_names)[0]] += 1
            checked += 1

print(f"Successfully cross-referenced: {checked} files\n")
print("YOLO Class ID -> LabelMe Name mapping:")
for cls_id in sorted(mapping):
    print(f"  Class {cls_id}:")
    for name, cnt in mapping[cls_id].most_common():
        print(f'    "{name}" -> {cnt} matches')

# Also check if file naming patterns encode class info 
print("\n\nFILE NAMING PATTERN ANALYSIS:")
# Check 900xxx.jpg files (augmented?) vs 000xxx_N_M.jpg pattern
aug_stems = [s for s in label_files if s.startswith("90")]
orig_stems = [s for s in label_files if s.startswith("000")]
print(f"  Original pattern (000xxx_N_M): {len(orig_stems)} files")
print(f"  Augmented pattern (90xxxx): {len(aug_stems)} files")
print(f"  Other: {len(label_files) - len(aug_stems) - len(orig_stems)} files")

# Check class distribution in each subset
for prefix, name in [("000", "Original"), ("90", "Augmented")]:
    print(f"\n  {name} subset class distribution:")
    sub_counter = Counter()
    for stem in label_files:
        if stem.startswith(prefix):
            for line in label_files[stem].read_text().strip().split("\n"):
                parts = line.strip().split()
                if len(parts) >= 5:
                    sub_counter[int(parts[0])] += 1
    for cls_id in sorted(sub_counter):
        print(f"    Class {cls_id}: {sub_counter[cls_id]}")
