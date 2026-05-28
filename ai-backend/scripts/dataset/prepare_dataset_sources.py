"""
LabMind AI — Robust Dataset Preparation Script
=================================================
Prepares a production-grade dataset directory structure, normalizes
existing training data to a uniform 128×128 size, and generates a
guide for downloading additional public sickle cell datasets.

Usage:
    python prepare_dataset_sources.py

Output:
    - dataset_robust/             (full directory tree)
    - dataset_robust/DOWNLOAD_GUIDE.md
    - dataset_robust/raw/source_manifest.json
    - dataset_robust/dataset_build_log.json
    - Console status report

SAFETY:
    - READ-ONLY on dataset_v1_2class/ (copies only, never modifies)
    - All writes go to dataset_robust/ exclusively
"""

import json
import os
import shutil
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("[WARN] OpenCV not found — will attempt PIL fallback for resizing")
    try:
        from PIL import Image as PILImage
        HAS_PIL = True
    except ImportError:
        HAS_PIL = False
        print("[ERROR] Neither OpenCV nor PIL available — cannot resize images")
        print("        Install with: pip install opencv-python-headless Pillow")
        sys.exit(1)

# ── Paths ────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
DATASET_V1 = BASE / "dataset_v1_2class"
DATASET_ROBUST = BASE / "dataset_robust"

TARGET_SIZE = (128, 128)  # width, height
JPEG_QUALITY = 95
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
MIN_PER_CLASS = 500


def is_image(p: Path) -> bool:
    return p.suffix.lower() in IMAGE_EXTENSIONS


# ═══════════════════════════════════════════════════════════════
#  PART 1 — Create directory structure
# ═══════════════════════════════════════════════════════════════

def create_directory_structure():
    """Create the full dataset_robust/ directory tree."""
    print("\n" + "=" * 70)
    print("  PART 1: Creating directory structure")
    print("=" * 70)

    dirs = [
        # Raw sources
        DATASET_ROBUST / "raw" / "source_erythrocytesIDB",
        DATASET_ROBUST / "raw" / "source_kaggle_scd",
        DATASET_ROBUST / "raw" / "source_kaggle_sickle_anemia",
        DATASET_ROBUST / "raw" / "source_manual_crops" / "normal",
        DATASET_ROBUST / "raw" / "source_manual_crops" / "sickle",
        # Processed
        DATASET_ROBUST / "processed" / "normal",
        DATASET_ROBUST / "processed" / "sickle",
        # Splits
        DATASET_ROBUST / "splits" / "train" / "normal",
        DATASET_ROBUST / "splits" / "train" / "sickle",
        DATASET_ROBUST / "splits" / "val" / "normal",
        DATASET_ROBUST / "splits" / "val" / "sickle",
        DATASET_ROBUST / "splits" / "test" / "normal",
        DATASET_ROBUST / "splits" / "test" / "sickle",
    ]

    created = 0
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        created += 1

    print(f"  ✓ Created {created} directories under dataset_robust/")

    # Write source manifest
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "target_size": f"{TARGET_SIZE[0]}x{TARGET_SIZE[1]}",
        "jpeg_quality": JPEG_QUALITY,
        "min_per_class": MIN_PER_CLASS,
        "sources": {
            "source_manual_crops": {
                "description": "Existing hand-curated crops from dataset_v1_2class (train + val splits)",
                "origin": str(DATASET_V1),
                "classes": ["normal", "sickle"],
                "status": "auto-populated by this script",
            },
            "source_erythrocytesIDB": {
                "description": "erythrocytesIDB — labeled red blood cell morphology dataset",
                "origin": "https://github.com/MauroBaraldi/erythrocytesIDB",
                "classes": ["normal (discocyte)", "sickle (drepanocyte)", "other morphologies"],
                "status": "awaiting download — see DOWNLOAD_GUIDE.md",
            },
            "source_kaggle_scd": {
                "description": "Kaggle Sickle Cell Detection dataset(s)",
                "origin": "https://www.kaggle.com/search?q=sickle+cell+detection",
                "classes": ["normal", "sickle"],
                "status": "awaiting download — see DOWNLOAD_GUIDE.md",
            },
            "source_kaggle_sickle_anemia": {
                "description": "Kaggle Sickle Cell Anemia image collections",
                "origin": "https://www.kaggle.com/search?q=sickle+cell+anemia",
                "classes": ["normal", "sickle", "other"],
                "status": "awaiting download — see DOWNLOAD_GUIDE.md",
            },
        },
    }

    manifest_path = DATASET_ROBUST / "raw" / "source_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"  ✓ Wrote source_manifest.json")

    return manifest


# ═══════════════════════════════════════════════════════════════
#  PART 2 — Copy and normalize existing data
# ═══════════════════════════════════════════════════════════════

def get_image_dimensions(path: Path):
    """Read image dimensions. Returns (width, height) or (None, None)."""
    if HAS_CV2:
        img = cv2.imread(str(path))
        if img is not None:
            h, w = img.shape[:2]
            return w, h
        return None, None
    elif HAS_PIL:
        try:
            with PILImage.open(str(path)) as im:
                return im.size  # (width, height)
        except Exception:
            return None, None
    return None, None


def resize_and_save(src: Path, dst: Path, target_w: int, target_h: int):
    """Resize image to target dimensions and save as JPEG."""
    if HAS_CV2:
        img = cv2.imread(str(src))
        if img is None:
            raise ValueError(f"cv2.imread returned None for {src}")
        h, w = img.shape[:2]
        # Choose interpolation based on whether we're upscaling or downscaling
        if w > target_w or h > target_h:
            interp = cv2.INTER_AREA  # best for downscaling
        else:
            interp = cv2.INTER_CUBIC  # best for upscaling
        resized = cv2.resize(img, (target_w, target_h), interpolation=interp)
        cv2.imwrite(str(dst), resized, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    elif HAS_PIL:
        with PILImage.open(str(src)) as im:
            w, h = im.size
            if w > target_w or h > target_h:
                resample = PILImage.LANCZOS
            else:
                resample = PILImage.BICUBIC
            resized = im.resize((target_w, target_h), resample=resample)
            resized = resized.convert("RGB")
            resized.save(str(dst), "JPEG", quality=JPEG_QUALITY)


def copy_directly(src: Path, dst: Path):
    """Copy image directly (already correct size). Re-save as JPEG for consistency."""
    if HAS_CV2:
        img = cv2.imread(str(src))
        if img is None:
            raise ValueError(f"cv2.imread returned None for {src}")
        cv2.imwrite(str(dst), img, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    elif HAS_PIL:
        with PILImage.open(str(src)) as im:
            im = im.convert("RGB")
            im.save(str(dst), "JPEG", quality=JPEG_QUALITY)


def copy_and_normalize():
    """Copy all images from dataset_v1_2class into dataset_robust, normalizing sizes."""
    print("\n" + "=" * 70)
    print("  PART 2: Copying and normalizing existing data")
    print("=" * 70)

    build_log = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "source": str(DATASET_V1),
        "target_size": f"{TARGET_SIZE[0]}x{TARGET_SIZE[1]}",
        "files": [],
        "errors": [],
    }

    stats = {
        "copied_total": 0,
        "resized": 0,
        "already_correct": 0,
        "errors": 0,
        "per_class": {"normal": 0, "sickle": 0},
    }

    if not DATASET_V1.exists():
        print(f"  ⚠ Source directory NOT FOUND: {DATASET_V1}")
        print(f"    Skipping copy — dataset_robust/ will have empty processed/ dirs")
        build_log["error"] = "Source dataset_v1_2class not found"
        return build_log, stats

    # Iterate over both splits (train, val) and both classes (normal, sickle)
    for split_name in ["train", "val"]:
        for class_name in ["normal", "sickle"]:
            src_dir = DATASET_V1 / split_name / class_name
            raw_dst_dir = DATASET_ROBUST / "raw" / "source_manual_crops" / class_name
            proc_dst_dir = DATASET_ROBUST / "processed" / class_name

            if not src_dir.exists():
                print(f"  ⚠ {split_name}/{class_name}/ not found — skipping")
                continue

            images = sorted([f for f in src_dir.iterdir() if f.is_file() and is_image(f)])
            print(f"\n  Processing {split_name}/{class_name}/: {len(images)} images")

            for img_path in images:
                entry = {
                    "original_path": str(img_path),
                    "filename": img_path.name,
                    "source": "source_manual_crops",
                    "split_origin": split_name,
                    "class": class_name,
                }

                try:
                    # Step 1: Copy raw file (preserving metadata)
                    raw_dst = raw_dst_dir / img_path.name
                    # Avoid filename collisions between train/val splits
                    if raw_dst.exists():
                        stem = img_path.stem
                        suffix = img_path.suffix
                        raw_dst = raw_dst_dir / f"{stem}_{split_name}{suffix}"

                    shutil.copy2(str(img_path), str(raw_dst))
                    entry["raw_copy"] = str(raw_dst)

                    # Step 2: Get original dimensions
                    orig_w, orig_h = get_image_dimensions(img_path)
                    entry["original_width"] = orig_w
                    entry["original_height"] = orig_h

                    # Step 3: Normalize to 128×128
                    # Use the raw_dst filename for the processed file to keep names unique
                    proc_dst = proc_dst_dir / raw_dst.name
                    # Ensure .jpg extension
                    if proc_dst.suffix.lower() not in [".jpg", ".jpeg"]:
                        proc_dst = proc_dst.with_suffix(".jpg")

                    if orig_w == TARGET_SIZE[0] and orig_h == TARGET_SIZE[1]:
                        # Already correct size — copy directly
                        copy_directly(img_path, proc_dst)
                        entry["action"] = "copied_direct"
                        entry["resized"] = False
                        stats["already_correct"] += 1
                    else:
                        # Needs resizing
                        resize_and_save(img_path, proc_dst, TARGET_SIZE[0], TARGET_SIZE[1])
                        entry["action"] = "resized"
                        entry["resized"] = True
                        entry["resize_from"] = f"{orig_w}x{orig_h}"
                        entry["resize_to"] = f"{TARGET_SIZE[0]}x{TARGET_SIZE[1]}"
                        stats["resized"] += 1

                    entry["processed_path"] = str(proc_dst)
                    entry["processed_size_bytes"] = proc_dst.stat().st_size
                    entry["status"] = "ok"

                    stats["copied_total"] += 1
                    stats["per_class"][class_name] += 1

                except Exception as e:
                    entry["status"] = "error"
                    entry["error"] = str(e)
                    entry["traceback"] = traceback.format_exc()
                    stats["errors"] += 1
                    build_log["errors"].append({
                        "file": str(img_path),
                        "error": str(e),
                    })
                    print(f"    ✗ Error processing {img_path.name}: {e}")

                build_log["files"].append(entry)

    build_log["completed_at"] = datetime.now(timezone.utc).isoformat()
    build_log["stats"] = stats

    # Save build log
    log_path = DATASET_ROBUST / "dataset_build_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(build_log, f, indent=2, default=str)
    print(f"\n  ✓ Build log saved to: {log_path}")

    return build_log, stats


# ═══════════════════════════════════════════════════════════════
#  PART 3 — Generate download guide
# ═══════════════════════════════════════════════════════════════

def generate_download_guide():
    """Create DOWNLOAD_GUIDE.md with instructions for acquiring external datasets."""
    print("\n" + "=" * 70)
    print("  PART 3: Generating DOWNLOAD_GUIDE.md")
    print("=" * 70)

    guide = r"""# LabMind AI — External Dataset Download Guide

> **Goal**: Expand the sickle cell training set to **500+ images per class minimum**
> (1,000–5,000+ recommended for clinical-grade CNN performance).
>
> Current dataset is severely limited (~194 sickle, ~425 normal) and the model
> overfits to training data. Adding diverse external sources is **critical**.

---

## Quick Reference

| # | Source | Expected Images | Target Folder |
|---|--------|----------------|---------------|
| 1 | erythrocytesIDB | ~200 labeled RBCs | `raw/source_erythrocytesIDB/` |
| 2 | Kaggle SCD Datasets | ~500–3,000+ | `raw/source_kaggle_scd/` |
| 3 | Kaggle Sickle Anemia Collections | ~200–1,000+ | `raw/source_kaggle_sickle_anemia/` |
| 4 | BCCD Dataset (supplemental) | ~300+ normal RBCs | `raw/source_kaggle_scd/` |

---

## 1. erythrocytesIDB Dataset

**Description**: A curated research dataset of individual red blood cell images
classified by morphology, including normal (discocyte) and sickle (drepanocyte) cells.

**Where to download**:
- Primary: [https://github.com/MauroBaraldi/erythrocytesIDB](https://github.com/MauroBaraldi/erythrocytesIDB)
- Alternative: Search Google Scholar for "erythrocytesIDB dataset"

**Download steps**:
1. Clone or download the repository:
   ```bash
   git clone https://github.com/MauroBaraldi/erythrocytesIDB.git
   ```
2. Look for image folders organized by cell type (e.g., `discocyte/`, `drepanocyte/`, etc.)
3. Copy files into the target folder

**Target folder**: `dataset_robust/raw/source_erythrocytesIDB/`

**Expected file format**: `.jpg` or `.png` images, individual cell crops

**Class mapping**:
| erythrocytesIDB Category | Our Label |
|--------------------------|-----------|
| `discocyte` | **normal** |
| `drepanocyte` (sickle) | **sickle** |
| `echinocyte`, `stomatocyte`, `elliptocyte`, etc. | ❌ Exclude (other morphologies) |

**Recommended structure after download**:
```
raw/source_erythrocytesIDB/
├── normal/       ← copy discocyte images here
└── sickle/       ← copy drepanocyte images here
```

---

## 2. Kaggle Sickle Cell Detection Datasets

**Description**: Multiple community-contributed datasets on Kaggle containing
blood smear images with labeled normal and sickle cells.

**Search URLs**:
- [Kaggle: "sickle cell detection"](https://www.kaggle.com/search?q=sickle+cell+detection+dataset)
- [Kaggle: "sickle cell anemia dataset"](https://www.kaggle.com/search?q=sickle+cell+anemia+dataset)
- [Kaggle: "blood cell classification sickle"](https://www.kaggle.com/search?q=blood+cell+classification+sickle)

**Known datasets (search by name)**:
| Dataset Name | Approx Size | Notes |
|-------------|-------------|-------|
| "SCD-Dataset" | ~500 images | Pre-labeled normal/sickle |
| "Sickle Cell Anemia Detection" | ~300 images | Includes cell crops |
| "Blood Cell Images" | ~12,000+ images | Mixed types, filter for RBCs |
| "Sickle Cell Disease Detection" | ~1,000+ images | Multiple contributors |

**Download steps**:
1. Create a Kaggle account at [kaggle.com](https://www.kaggle.com)
2. Search for the dataset names above
3. Click "Download" on the dataset page
4. Extract the ZIP file
5. Sort images into `normal/` and `sickle/` subfolders

**Target folder**: `dataset_robust/raw/source_kaggle_scd/`

**Expected file format**: `.jpg`, `.png`, or `.jpeg` — individual cell crops or full smears

**Class mapping** (varies by dataset — check each dataset's README):
| Common Labels | Our Label |
|--------------|-----------|
| `normal`, `healthy`, `discocyte`, `RBC` | **normal** |
| `sickle`, `drepanocyte`, `SCD`, `sickle_cell` | **sickle** |
| other types | ❌ Exclude |

**Recommended structure after download**:
```
raw/source_kaggle_scd/
├── normal/       ← all normal/healthy cell images
└── sickle/       ← all sickle/drepanocyte images
```

---

## 3. Kaggle Sickle Cell Anemia Collections

**Description**: Additional image collections specifically focused on sickle cell
anemia blood smears and cell-level annotations.

**Search URLs**:
- [Kaggle: "sickle cell anemia"](https://www.kaggle.com/search?q=sickle+cell+anemia)
- [Kaggle: "sickle cell image"](https://www.kaggle.com/search?q=sickle+cell+image)

**Download steps**:
1. Same as Kaggle instructions above
2. May contain full blood smear images — you'll need to crop individual cells
3. Use `manual_crop_tool.py` or `pipeline_stage2_cropping.py` if crops are needed

**Target folder**: `dataset_robust/raw/source_kaggle_sickle_anemia/`

**Expected file format**: `.jpg`, `.png` — may be full smears or cell crops

**Class mapping**:
| Label | Our Label |
|-------|-----------|
| Normal blood smear / healthy cells | **normal** |
| Sickle cells / SCD positive | **sickle** |

**Recommended structure after download**:
```
raw/source_kaggle_sickle_anemia/
├── normal/
└── sickle/
```

---

## 4. BCCD Dataset (Supplemental — Normal Cells Only)

**Description**: Blood Cell Count Detection dataset with labeled blood cell images.
Useful primarily for augmenting the **normal** class.

**Where to download**:
- Primary: [https://github.com/Shenggan/BCCD_Dataset](https://github.com/Shenggan/BCCD_Dataset)
- Kaggle mirror: search "BCCD Dataset"

**Download steps**:
1. Clone or download:
   ```bash
   git clone https://github.com/Shenggan/BCCD_Dataset.git
   ```
2. Look for `BCCD/JPEGImages/` — contains annotated blood smear images
3. Use XML annotations in `BCCD/Annotations/` to crop individual RBCs
4. RBCs from this dataset are predominantly normal morphology

**Target folder**: Place in `dataset_robust/raw/source_kaggle_scd/` (general sources)

**Important**: This dataset does NOT contain sickle cells. Use only for normal class.

---

## After Downloading — Next Steps

1. **Organize** each download into `normal/` and `sickle/` subfolders within the
   appropriate `raw/source_*` directory.

2. **Run the processing pipeline** (to be created) that will:
   - Scan all `raw/source_*/` directories
   - Resize all images to 128×128
   - Deduplicate images
   - Move processed images to `processed/normal/` and `processed/sickle/`
   - Split into train/val/test (70/15/15 ratio)

3. **Quality-check**: Visually inspect a random sample from each source to verify
   correct labeling. Mislabeled images in the training set are worse than having
   a smaller dataset.

4. **Target counts**:
   | Class | Current | Minimum Target | Recommended |
   |-------|---------|---------------|-------------|
   | Normal | ~425 | 500 | 1,000–2,000 |
   | Sickle | ~194 | 500 | 1,000–2,000 |

---

## Data Quality Checklist

Before adding any external images to the processed set, verify:

- [ ] Images are individual cell crops (not full smear fields)
- [ ] Resolution is at least 64×64 pixels (will be resized to 128×128)
- [ ] Labels are correct (sickle cells have characteristic crescent/elongated shape)
- [ ] No extreme artifacts (blank images, heavily blurred, text overlays)
- [ ] Images are actual microscopy images (not illustrations or diagrams)

---

*Generated by `prepare_dataset_sources.py` on {timestamp}*
""".replace("{timestamp}", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    guide_path = DATASET_ROBUST / "DOWNLOAD_GUIDE.md"
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(guide)

    print(f"  ✓ DOWNLOAD_GUIDE.md written ({len(guide)} chars)")
    return guide_path


# ═══════════════════════════════════════════════════════════════
#  PART 4 — Print status report
# ═══════════════════════════════════════════════════════════════

def print_status_report(stats: dict):
    """Print a clear final status report."""
    print("\n" + "=" * 70)
    print("  PART 4: STATUS REPORT")
    print("=" * 70)

    normal_count = stats["per_class"].get("normal", 0)
    sickle_count = stats["per_class"].get("sickle", 0)
    total = stats["copied_total"]

    print(f"""
  ┌─────────────────────────────────────────────────────┐
  │  DATASET PREPARATION COMPLETE                       │
  ├─────────────────────────────────────────────────────┤
  │                                                     │
  │  Images copied from dataset_v1_2class:  {total:>5}        │
  │                                                     │
  │  Resized to 128×128:                    {stats['resized']:>5}        │
  │  Already correct size:                  {stats['already_correct']:>5}        │
  │  Errors:                                {stats['errors']:>5}        │
  │                                                     │
  │  ── Processed Counts ──                             │
  │  processed/normal/:                     {normal_count:>5}        │
  │  processed/sickle/:                     {sickle_count:>5}        │
  │                                                     │
  │  ── Gap to Minimum (500/class) ──                   │
  │  Normal:  {max(0, MIN_PER_CLASS - normal_count):>5} more needed{' ✓ MET' if normal_count >= MIN_PER_CLASS else '  ⚠ BELOW'}                │
  │  Sickle:  {max(0, MIN_PER_CLASS - sickle_count):>5} more needed{' ✓ MET' if sickle_count >= MIN_PER_CLASS else '  ⚠ BELOW'}                │
  │                                                     │
  └─────────────────────────────────────────────────────┘
""")

    if normal_count < MIN_PER_CLASS or sickle_count < MIN_PER_CLASS:
        print("  ⚠ DATASET IS STILL INSUFFICIENT FOR ROBUST TRAINING")
        print(f"    Need {MIN_PER_CLASS}+ images per class minimum.")
        print(f"    For clinical-grade models, aim for 1,000–5,000+ per class.")
        print()
        print("  ➜  NEXT STEP: Follow dataset_robust/DOWNLOAD_GUIDE.md")
        print("     to download external sickle cell datasets and fill the gap.")
    else:
        print("  ✓ Minimum threshold met!")
        print("    Consider adding more data for clinical robustness (1,000+ per class).")

    print()


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 70)
    print("  LabMind AI — Dataset Preparation Script")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print(f"  Source: {DATASET_V1}")
    print(f"  Target: {DATASET_ROBUST}")
    print("═" * 70)

    # Safety check: do not overwrite if dataset_robust already has processed data
    proc_normal = DATASET_ROBUST / "processed" / "normal"
    proc_sickle = DATASET_ROBUST / "processed" / "sickle"
    if proc_normal.exists() and any(proc_normal.iterdir()):
        existing_n = len(list(proc_normal.glob("*")))
        existing_s = len(list(proc_sickle.glob("*"))) if proc_sickle.exists() else 0
        print(f"\n  ⚠ dataset_robust/processed/ already contains data:")
        print(f"    normal: {existing_n} files, sickle: {existing_s} files")
        print(f"    Re-running will add duplicates. Delete dataset_robust/ first to start fresh.")
        response = input("\n  Continue anyway? (y/N): ").strip().lower()
        if response != "y":
            print("  Aborted.")
            return

    # Part 1
    manifest = create_directory_structure()

    # Part 2
    build_log, stats = copy_and_normalize()

    # Part 3
    guide_path = generate_download_guide()

    # Part 4
    print_status_report(stats)

    print("═" * 70)
    print(f"  All files written under: {DATASET_ROBUST}")
    print("═" * 70 + "\n")


if __name__ == "__main__":
    main()
