"""
Prepare Clinical Bacteria DetectionDataSet for YOLOv8 Training
===============================================================
Reads existing YOLO-format labels and author-provided train/val/test
split files, then organises everything into the standard YOLOv8 directory
layout with a generated data.yaml.

Class mapping (4 classes):
  0: G-_Bacillus   (Gram-negative bacilli / rods)
  1: G+_Coccus     (Gram-positive cocci / spheres)
  2: G-_Coccus     (Gram-negative cocci / spheres)
  3: G+_Bacillus   (Gram-positive bacilli / rods)
"""

import shutil
import yaml
from pathlib import Path
from collections import Counter, defaultdict

# ──────────────────────────────────────────────────────────────────
# PATHS  (handles the nested dataset_microbiology directory)
# ──────────────────────────────────────────────────────────────────
# Try both possible root locations
_ROOT_A = Path(r"D:\New folder\ai-backend\dataset_microbiology\DeepDataSet\DetectionDataSet")
_ROOT_B = Path(r"D:\New folder\ai-backend\dataset_microbiology\dataset_microbiology\DeepDataSet\DetectionDataSet")

if _ROOT_A.exists():
    SRC_ROOT = _ROOT_A
elif _ROOT_B.exists():
    SRC_ROOT = _ROOT_B
else:
    raise FileNotFoundError("Cannot find DetectionDataSet in either expected location.")

SRC_IMAGES = SRC_ROOT / "images"
SRC_LABELS = SRC_ROOT / "labels"
SRC_TXT    = SRC_ROOT / "txt"

OUT_ROOT = Path(r"D:\New folder\ai-backend\dataset_microbiology\yolo_dataset")

CLASS_NAMES = ["G-_Bacillus", "G+_Coccus", "G-_Coccus", "G+_Bacillus"]
NC = len(CLASS_NAMES)
SPLITS = ["train", "val", "test"]

SEP = "=" * 70


def section(title: str):
    print(f"\n{SEP}\n  {title}\n{SEP}")


# ──────────────────────────────────────────────────────────────────
# 1. Parse split files
# ──────────────────────────────────────────────────────────────────
section("1. PARSING SPLIT FILES")

split_map: dict[str, str] = {}          # filename (lower) -> split
split_counts: dict[str, int] = {}

for split in SPLITS:
    txt_path = SRC_TXT / f"{split}.txt"
    if not txt_path.exists():
        print(f"  WARNING: {txt_path} not found, skipping split '{split}'")
        continue

    lines = [l.strip() for l in txt_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    count = 0
    for line in lines:
        # Extract just the filename from the full path
        fname = Path(line).name          # e.g. "000001_2_3.jpg"
        key = fname.lower()
        if key not in split_map:
            split_map[key] = split
            count += 1
        # else: duplicate across splits — keep first assignment
    split_counts[split] = count
    print(f"  {split:6s}: {count:5d} filenames extracted from {txt_path.name}")

total_assigned = sum(split_counts.values())
print(f"  TOTAL : {total_assigned} unique filenames assigned to splits")

# ──────────────────────────────────────────────────────────────────
# 2. Build a case-insensitive index of source images
# ──────────────────────────────────────────────────────────────────
section("2. INDEXING SOURCE FILES")

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

src_image_index: dict[str, Path] = {}   # lower(filename) -> actual Path
for f in SRC_IMAGES.iterdir():
    if f.suffix.lower() in IMG_EXTS:
        src_image_index[f.name.lower()] = f

src_label_index: dict[str, Path] = {}   # lower(stem) -> actual Path
for f in SRC_LABELS.iterdir():
    if f.suffix.lower() == ".txt":
        src_label_index[f.stem.lower()] = f

print(f"  Source images indexed : {len(src_image_index)}")
print(f"  Source labels indexed : {len(src_label_index)}")

# ──────────────────────────────────────────────────────────────────
# 3. Create output directory structure
# ──────────────────────────────────────────────────────────────────
section("3. CREATING OUTPUT DIRECTORIES")

if OUT_ROOT.exists():
    print(f"  Removing existing output: {OUT_ROOT}")
    shutil.rmtree(OUT_ROOT)

for split in SPLITS:
    (OUT_ROOT / "images" / split).mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "labels" / split).mkdir(parents=True, exist_ok=True)
    print(f"  Created: images/{split}/  labels/{split}/")

# ──────────────────────────────────────────────────────────────────
# 4. Copy images and labels into split folders
# ──────────────────────────────────────────────────────────────────
section("4. COPYING FILES TO SPLIT FOLDERS")

copied = defaultdict(int)               # split -> count
missing_images = []
missing_labels = []
annotation_counts = defaultdict(Counter) # split -> Counter(class_id)

for fname_lower, split in split_map.items():
    # --- Image ---
    if fname_lower not in src_image_index:
        missing_images.append(fname_lower)
        continue
    img_src = src_image_index[fname_lower]
    img_dst = OUT_ROOT / "images" / split / img_src.name
    shutil.copy2(img_src, img_dst)

    # --- Label ---
    stem_lower = Path(fname_lower).stem
    if stem_lower not in src_label_index:
        missing_labels.append(fname_lower)
        # Still count the image as copied (background image, no annotations)
        copied[split] += 1
        continue
    lbl_src = src_label_index[stem_lower]
    lbl_dst = OUT_ROOT / "labels" / split / lbl_src.name
    shutil.copy2(lbl_src, lbl_dst)

    # --- Count annotations per class ---
    for line in lbl_src.read_text(encoding="utf-8").strip().splitlines():
        parts = line.strip().split()
        if len(parts) >= 5:
            try:
                annotation_counts[split][int(parts[0])] += 1
            except ValueError:
                pass

    copied[split] += 1

for split in SPLITS:
    print(f"  {split:6s}: {copied[split]:5d} image+label pairs copied")

if missing_images:
    print(f"\n  WARNING: {len(missing_images)} filenames in split files had no matching image")
    for m in missing_images[:10]:
        print(f"    - {m}")
    if len(missing_images) > 10:
        print(f"    ... and {len(missing_images) - 10} more")

if missing_labels:
    print(f"\n  WARNING: {len(missing_labels)} images had no matching label file")
    for m in missing_labels[:10]:
        print(f"    - {m}")

# ──────────────────────────────────────────────────────────────────
# 5. Generate data.yaml
# ──────────────────────────────────────────────────────────────────
section("5. GENERATING data.yaml")

data_yaml = {
    "path": str(OUT_ROOT).replace("\\", "/"),
    "train": "images/train",
    "val": "images/val",
    "test": "images/test",
    "nc": NC,
    "names": CLASS_NAMES,
}

yaml_path = OUT_ROOT / "data.yaml"
with open(yaml_path, "w", encoding="utf-8") as f:
    yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f"  Written to: {yaml_path}")
print(f"\n  Content:")
print(f"  {'-' * 40}")
for line in yaml_path.read_text(encoding="utf-8").splitlines():
    print(f"  {line}")
print(f"  {'-' * 40}")

# ──────────────────────────────────────────────────────────────────
# 6. Summary
# ──────────────────────────────────────────────────────────────────
section("6. FINAL SUMMARY")

print(f"  Output root: {OUT_ROOT}\n")

# Images per split
print("  Images per split:")
total_imgs = 0
for split in SPLITS:
    n = copied[split]
    total_imgs += n
    print(f"    {split:6s}: {n:5d}")
print(f"    {'TOTAL':6s}: {total_imgs:5d}\n")

# Annotations per class per split
print("  Annotations per class per split:")
header = f"    {'Class':<18s}"
for split in SPLITS:
    header += f" {split:>7s}"
header += f" {'TOTAL':>7s}"
print(header)
print(f"    {'-' * (18 + 8 * (len(SPLITS) + 1))}")

grand_total = 0
for cls_id in range(NC):
    row = f"    {cls_id}: {CLASS_NAMES[cls_id]:<14s}"
    row_total = 0
    for split in SPLITS:
        c = annotation_counts[split][cls_id]
        row += f" {c:>7d}"
        row_total += c
    row += f" {row_total:>7d}"
    grand_total += row_total
    print(row)
print(f"    {'TOTAL':<18s}", end="")
for split in SPLITS:
    s = sum(annotation_counts[split].values())
    print(f" {s:>7d}", end="")
print(f" {grand_total:>7d}")

# Missing files
print(f"\n  Missing images : {len(missing_images)}")
print(f"  Missing labels : {len(missing_labels)}")

# Sample label
print(f"\n  Sample label content (first file in train/):")
train_labels = sorted((OUT_ROOT / "labels" / "train").glob("*.txt"))
if train_labels:
    sample = train_labels[0]
    print(f"    File: {sample.name}")
    for line in sample.read_text(encoding="utf-8").strip().splitlines()[:5]:
        print(f"    {line}")

# Verify counts
print(f"\n  Verification:")
for split in SPLITS:
    ni = len(list((OUT_ROOT / "images" / split).glob("*")))
    nl = len(list((OUT_ROOT / "labels" / split).glob("*")))
    status = "OK" if ni == nl else f"MISMATCH (imgs={ni}, lbls={nl})"
    print(f"    {split:6s}: {ni} images, {nl} labels  [{status}]")

print(f"\n{SEP}")
print(f"  DATASET PREPARATION COMPLETE")
print(f"  Ready for: yolo detect train data={yaml_path}")
print(f"{SEP}")
