"""
Audit Script: Clinical Bacteria Detection Dataset
===================================================
Analyzes the DeepDataSet/DetectionDataSet structure to understand
image counts, label formats, class distributions, and split files
before YOLOv8 training.
"""

import os
import json
import random
from pathlib import Path
from collections import Counter, defaultdict

# ──────────────────────────────────────────────────────────────────
# PATHS — adjusted for the nested directory structure
# ──────────────────────────────────────────────────────────────────
BASE = Path(r"D:\New folder\ai-backend\dataset_microbiology\dataset_microbiology\DeepDataSet")
DETECTION = BASE / "DetectionDataSet"
DATASET_640 = BASE / "640DataSet"

IMAGES_DIR = DETECTION / "images"
LABELS_DIR = DETECTION / "labels"
TXT_DIR = DETECTION / "txt"
JSON_DIR = DATASET_640 / "json"

SEPARATOR = "=" * 70


def section(title):
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


# ──────────────────────────────────────────────────────────────────
# 1. Count images
# ──────────────────────────────────────────────────────────────────
section("1. IMAGE COUNT")
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
if IMAGES_DIR.exists():
    image_files = sorted([f for f in IMAGES_DIR.iterdir() if f.suffix.lower() in IMG_EXTS])
    print(f"  Directory : {IMAGES_DIR}")
    print(f"  Total images: {len(image_files)}")
    ext_counter = Counter(f.suffix.lower() for f in image_files)
    for ext, cnt in ext_counter.most_common():
        print(f"    {ext:8s} → {cnt}")
else:
    image_files = []
    print(f"  ⚠ Directory NOT FOUND: {IMAGES_DIR}")

# ──────────────────────────────────────────────────────────────────
# 2. Count labels
# ──────────────────────────────────────────────────────────────────
section("2. LABEL COUNT")
if LABELS_DIR.exists():
    label_files = sorted([f for f in LABELS_DIR.iterdir() if f.suffix.lower() == ".txt"])
    print(f"  Directory : {LABELS_DIR}")
    print(f"  Total label files: {len(label_files)}")
else:
    label_files = []
    print(f"  ⚠ Directory NOT FOUND: {LABELS_DIR}")

# ──────────────────────────────────────────────────────────────────
# 3. Sample label content
# ──────────────────────────────────────────────────────────────────
section("3. SAMPLE LABEL FILES (first 5)")
samples = label_files[:5] if len(label_files) >= 5 else label_files
for lf in samples:
    print(f"\n  ── {lf.name} ──")
    content = lf.read_text(encoding="utf-8", errors="replace").strip()
    lines = content.split("\n")
    for line in lines[:15]:  # cap at 15 lines per file
        print(f"    {line}")
    if len(lines) > 15:
        print(f"    ... ({len(lines)} lines total)")

# ──────────────────────────────────────────────────────────────────
# 4. Annotations per class ID
# ──────────────────────────────────────────────────────────────────
section("4. ANNOTATIONS PER CLASS ID")
class_counter = Counter()
total_annotations = 0
empty_labels = 0
malformed_lines = 0

for lf in label_files:
    content = lf.read_text(encoding="utf-8", errors="replace").strip()
    if not content:
        empty_labels += 1
        continue
    for line in content.split("\n"):
        parts = line.strip().split()
        if len(parts) >= 5:
            try:
                cls_id = int(parts[0])
                class_counter[cls_id] += 1
                total_annotations += 1
            except ValueError:
                malformed_lines += 1
        elif len(parts) > 0:
            malformed_lines += 1

print(f"  Total annotations: {total_annotations}")
print(f"  Empty label files: {empty_labels}")
print(f"  Malformed lines  : {malformed_lines}")
print(f"  Unique class IDs : {len(class_counter)}")
print()
for cls_id in sorted(class_counter.keys()):
    pct = class_counter[cls_id] / total_annotations * 100 if total_annotations else 0
    print(f"    Class {cls_id:3d} → {class_counter[cls_id]:6d} annotations ({pct:5.1f}%)")

# ──────────────────────────────────────────────────────────────────
# 5. Image dimensions (sample 10)
# ──────────────────────────────────────────────────────────────────
section("5. IMAGE DIMENSIONS (10 random samples)")
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("  ⚠ Pillow not installed — skipping dimension check")

if HAS_PIL and image_files:
    sample_imgs = random.sample(image_files, min(10, len(image_files)))
    dim_counter = Counter()
    for img_path in sample_imgs:
        try:
            with Image.open(img_path) as img:
                w, h = img.size
                dim_counter[(w, h)] += 1
                print(f"    {img_path.name:40s} → {w} x {h}")
        except Exception as e:
            print(f"    {img_path.name:40s} → ERROR: {e}")
    print(f"\n  Unique dimensions in sample: {len(dim_counter)}")
    for (w, h), cnt in dim_counter.most_common():
        print(f"    {w} x {h} → {cnt} image(s)")

# ──────────────────────────────────────────────────────────────────
# 6. Look for class-mapping files
# ──────────────────────────────────────────────────────────────────
section("6. CLASS MAPPING FILES (data.yaml, classes.txt, etc.)")
search_roots = [BASE, DETECTION, DATASET_640, BASE.parent]
MAPPING_NAMES = {"data.yaml", "data.yml", "classes.txt", "classes.names", "obj.names", "notes.json", "README.md", "README.txt"}

found_any = False
for root in search_roots:
    if not root.exists():
        continue
    for f in root.rglob("*"):
        if f.name.lower() in {n.lower() for n in MAPPING_NAMES}:
            found_any = True
            print(f"\n  Found: {f}")
            try:
                text = f.read_text(encoding="utf-8", errors="replace")[:2000]
                print(f"  Content (first 2000 chars):\n{text}")
            except Exception as e:
                print(f"  Could not read: {e}")

if not found_any:
    print("  ⚠ No standard class-mapping files found.")

# ──────────────────────────────────────────────────────────────────
# 7. txt\ folder contents (train/val/test splits)
# ──────────────────────────────────────────────────────────────────
section("7. TXT FOLDER (train/val/test splits)")
if TXT_DIR.exists():
    txt_files = sorted(TXT_DIR.iterdir())
    print(f"  Directory: {TXT_DIR}")
    print(f"  Files found: {len(txt_files)}")
    for tf in txt_files:
        if tf.is_file():
            line_count = sum(1 for _ in open(tf, encoding="utf-8", errors="replace"))
            print(f"    {tf.name:25s} → {line_count} lines")
            # Show first 3 lines
            with open(tf, encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh):
                    if i >= 3:
                        break
                    print(f"      {line.strip()}")
else:
    print(f"  ⚠ Directory NOT FOUND: {TXT_DIR}")

# ──────────────────────────────────────────────────────────────────
# 8. json\ folder in 640DataSet (COCO annotations)
# ──────────────────────────────────────────────────────────────────
section("8. JSON FOLDER — 640DataSet (COCO class definitions)")
if JSON_DIR.exists():
    json_files = sorted(JSON_DIR.iterdir())
    print(f"  Directory: {JSON_DIR}")
    print(f"  Files found: {len(json_files)}")
    for jf in json_files[:5]:
        print(f"\n  ── {jf.name} ──")
        if jf.suffix.lower() == ".json":
            try:
                with open(jf, encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    print(f"    Top-level keys: {list(data.keys())}")
                    # COCO format: look for 'categories'
                    if "categories" in data:
                        cats = data["categories"]
                        print(f"    Categories ({len(cats)}):")
                        for cat in cats:
                            print(f"      id={cat.get('id')}, name='{cat.get('name')}', supercategory='{cat.get('supercategory', 'N/A')}'")
                    # Also check 'images' count and 'annotations' count
                    if "images" in data:
                        print(f"    Images in JSON: {len(data['images'])}")
                    if "annotations" in data:
                        print(f"    Annotations in JSON: {len(data['annotations'])}")
                elif isinstance(data, list):
                    print(f"    Root is a list with {len(data)} items.")
                    if data:
                        print(f"    First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}")
            except Exception as e:
                print(f"    ERROR reading JSON: {e}")
        else:
            print(f"    (not a .json file)")
else:
    print(f"  ⚠ Directory NOT FOUND: {JSON_DIR}")

# ──────────────────────────────────────────────────────────────────
# 9. Comprehensive Summary
# ──────────────────────────────────────────────────────────────────
section("9. COMPREHENSIVE SUMMARY")

image_stems = {f.stem for f in image_files}
label_stems = {f.stem for f in label_files}
imgs_without_labels = image_stems - label_stems
labels_without_imgs = label_stems - image_stems

print(f"  Total images         : {len(image_files)}")
print(f"  Total label files    : {len(label_files)}")
print(f"  Empty label files    : {empty_labels}")
print(f"  Total annotations    : {total_annotations}")
print(f"  Unique class IDs     : {len(class_counter)}")
print(f"  Malformed lines      : {malformed_lines}")
print()
print(f"  Images WITHOUT labels: {len(imgs_without_labels)}")
if imgs_without_labels and len(imgs_without_labels) <= 20:
    for s in sorted(imgs_without_labels):
        print(f"    - {s}")
elif imgs_without_labels:
    for s in sorted(imgs_without_labels)[:10]:
        print(f"    - {s}")
    print(f"    ... and {len(imgs_without_labels) - 10} more")

print(f"  Labels WITHOUT images: {len(labels_without_imgs)}")
if labels_without_imgs and len(labels_without_imgs) <= 20:
    for s in sorted(labels_without_imgs):
        print(f"    - {s}")
elif labels_without_imgs:
    for s in sorted(labels_without_imgs)[:10]:
        print(f"    - {s}")
    print(f"    ... and {len(labels_without_imgs) - 10} more")

print()
print("  Annotations per class:")
for cls_id in sorted(class_counter.keys()):
    bar_len = int(class_counter[cls_id] / max(class_counter.values()) * 30) if class_counter else 0
    bar = "█" * bar_len
    print(f"    Class {cls_id:3d}: {class_counter[cls_id]:6d}  {bar}")

print(f"\n{SEPARATOR}")
print("  AUDIT COMPLETE")
print(SEPARATOR)
