"""
LabMind AI — Build Clean Dataset
==================================
Single-pass script that:
  1. Reclassifies existing crops using adjusted quality rules
  2. Scans new erythrocytesIDB external data
  3. Builds a unified clean dataset (dataset_clean/)
  4. Prints a comprehensive summary
  5. Creates a visual quality comparison grid

Usage:
    python build_clean_dataset.py

SAFETY:
    - NEVER modifies dataset_v1_2class/, source_erythrocytesIDB/, or dataset_robust/
    - All output goes to dataset_clean/ only
    - Uses shutil.copy2 to preserve metadata
"""

import json
import os
import random
import shutil
import sys
import traceback
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    print("[ERROR] OpenCV + NumPy required: pip install opencv-python-headless numpy")
    sys.exit(1)

# ── Paths ────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
AUDIT_JSON = BASE / "crop_quality_audit_report.json"
DATASET_V1 = BASE / "dataset_v1_2class"
ERYDB_BASE = BASE / "dataset_robust" / "raw" / "source_erythrocytesIDB" / "individual cells"
DATASET_CLEAN = BASE / "dataset_clean"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
TARGET_SIZE = (128, 128)
JPEG_QUALITY = 95

# ── Adjusted quality thresholds ──
BLUR_CRITICAL = 15.0       # Laplacian var < 15 = extremely blurry, no signal
CONTOUR_AREA_PCT = 0.05    # contour > 5% of image area to count as significant
FOREGROUND_MIN_PCT = 10.0  # < 10% foreground = too empty


def is_image(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS


# ═══════════════════════════════════════════════════════════════
#  Quality Checks (for new images not in the audit JSON)
# ═══════════════════════════════════════════════════════════════

def compute_quality(img_path: Path) -> dict:
    """Compute quality metrics for a single image file."""
    img = cv2.imread(str(img_path))
    if img is None:
        return {"error": "unreadable", "must_remove": True, "reason": "UNREADABLE"}

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_area = h * w

    # Blur
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Multi-cell
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = img_area * CONTOUR_AREA_PCT
    sig_contours = sum(1 for c in contours if cv2.contourArea(c) > min_area)
    is_multi = sig_contours > 1

    # Foreground
    fg_px = int(np.count_nonzero(thresh))
    fg_pct = (fg_px / img_area) * 100.0 if img_area > 0 else 0
    is_empty = fg_pct < FOREGROUND_MIN_PCT

    # Decision
    reasons = []
    if is_multi:
        reasons.append("MULTI_CELL")
    if is_empty:
        reasons.append("TOO_EMPTY")
    if lap_var < BLUR_CRITICAL:
        reasons.append("EXTREME_BLUR")

    must_remove = len(reasons) > 0

    return {
        "width": w,
        "height": h,
        "laplacian_variance": round(lap_var, 2),
        "significant_contours": sig_contours,
        "foreground_pct": round(fg_pct, 2),
        "is_multi_cell": is_multi,
        "is_too_empty": is_empty,
        "must_remove": must_remove,
        "reason": " + ".join(reasons) if reasons else None,
    }


# ═══════════════════════════════════════════════════════════════
#  Image Processing
# ═══════════════════════════════════════════════════════════════

def normalize_and_save(src: Path, dst: Path):
    """Read image, resize to 128×128 if needed, save as JPEG Q95."""
    img = cv2.imread(str(src))
    if img is None:
        raise ValueError(f"Cannot read: {src}")

    h, w = img.shape[:2]
    if (w, h) != TARGET_SIZE:
        if w > TARGET_SIZE[0] or h > TARGET_SIZE[1]:
            interp = cv2.INTER_AREA
        else:
            interp = cv2.INTER_CUBIC
        img = cv2.resize(img, TARGET_SIZE, interpolation=interp)

    # Ensure .jpg extension
    dst = dst.with_suffix(".jpg")
    cv2.imwrite(str(dst), img, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    return dst


# ═══════════════════════════════════════════════════════════════
#  STEP 1 — Classify existing crops from audit JSON
# ═══════════════════════════════════════════════════════════════

def classify_existing_from_audit():
    """Load audit JSON and reclassify every crop with adjusted rules."""
    print("\n" + "=" * 80)
    print("  STEP 1: Reclassify existing crops from audit data")
    print("=" * 80)

    if not AUDIT_JSON.exists():
        print(f"  ⚠ {AUDIT_JSON.name} not found — will scan dataset_v1_2class directly")
        return classify_existing_direct()

    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        audit = json.load(f)

    # Only use dataset_v1_2class directories (skip dataset_robust which is a copy)
    v1_labels = {
        "dataset_v1_2class/train/normal",
        "dataset_v1_2class/train/sickle",
        "dataset_v1_2class/val/normal",
        "dataset_v1_2class/val/sickle",
    }

    usable = {"normal": [], "sickle": []}
    removed = {"normal": [], "sickle": []}

    for dir_entry in audit.get("directories", []):
        label = dir_entry.get("label", "")
        if label not in v1_labels:
            continue

        expected_class = dir_entry.get("expected_class", "unknown")
        if expected_class not in ("normal", "sickle"):
            continue

        for f in dir_entry.get("files", []):
            path = f.get("path", "")
            if not path or not Path(path).exists():
                continue

            # Extract metrics
            is_multi = f.get("multi_cell", {}).get("is_multi_cell", False)
            is_empty = f.get("foreground", {}).get("is_too_empty", False)
            lap_var = f.get("blur", {}).get("laplacian_variance", 999)

            # Apply adjusted rules
            reasons = []
            if is_multi:
                reasons.append("MULTI_CELL")
            if is_empty:
                reasons.append("TOO_EMPTY")
            if lap_var < BLUR_CRITICAL:
                reasons.append("EXTREME_BLUR")

            entry = {
                "path": path,
                "filename": f.get("filename", ""),
                "class": expected_class,
                "source": "dataset_v1_2class",
                "dir_label": label,
                "laplacian_variance": lap_var,
                "significant_contours": f.get("multi_cell", {}).get("significant_contours", 0),
                "foreground_pct": f.get("foreground", {}).get("foreground_pct", 0),
            }

            if reasons:
                entry["reason"] = " + ".join(reasons)
                removed[expected_class].append(entry)
            else:
                usable[expected_class].append(entry)

    for cls in ["normal", "sickle"]:
        total = len(usable[cls]) + len(removed[cls])
        pct = (len(usable[cls]) / total * 100) if total > 0 else 0
        print(f"\n  {cls.upper()}:")
        print(f"    Usable:  {len(usable[cls]):>5d}")
        print(f"    Removed: {len(removed[cls]):>5d}")
        print(f"    Total:   {total:>5d}  ({pct:.1f}% kept)")

    # Breakdown of removal reasons
    for cls in ["normal", "sickle"]:
        if removed[cls]:
            reason_counts = defaultdict(int)
            for r in removed[cls]:
                reason_counts[r["reason"]] += 1
            print(f"\n  {cls} removal reasons:")
            for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
                print(f"    {reason}: {count}")

    return usable, removed


def classify_existing_direct():
    """Fallback: scan dataset_v1_2class directly if audit JSON is missing."""
    usable = {"normal": [], "sickle": []}
    removed = {"normal": [], "sickle": []}

    for split in ["train", "val"]:
        for cls in ["normal", "sickle"]:
            dir_path = DATASET_V1 / split / cls
            if not dir_path.exists():
                continue
            for img_path in sorted(dir_path.iterdir()):
                if not is_image(img_path):
                    continue
                q = compute_quality(img_path)
                entry = {
                    "path": str(img_path),
                    "filename": img_path.name,
                    "class": cls,
                    "source": "dataset_v1_2class",
                    "dir_label": f"dataset_v1_2class/{split}/{cls}",
                    "laplacian_variance": q.get("laplacian_variance", 0),
                    "significant_contours": q.get("significant_contours", 0),
                    "foreground_pct": q.get("foreground_pct", 0),
                }
                if q["must_remove"]:
                    entry["reason"] = q["reason"]
                    removed[cls].append(entry)
                else:
                    usable[cls].append(entry)

    for cls in ["normal", "sickle"]:
        total = len(usable[cls]) + len(removed[cls])
        pct = (len(usable[cls]) / total * 100) if total > 0 else 0
        print(f"  {cls}: {len(usable[cls])} usable / {len(removed[cls])} removed ({pct:.1f}% kept)")

    return usable, removed


# ═══════════════════════════════════════════════════════════════
#  STEP 2 — Scan new erythrocytesIDB data
# ═══════════════════════════════════════════════════════════════

def scan_erythrocytes_idb():
    """Scan erythrocytesIDB external data and quality-check each image."""
    print("\n" + "=" * 80)
    print("  STEP 2: Scanning erythrocytesIDB external data")
    print("=" * 80)

    # Map IDB categories to our classes
    category_map = {
        "circular": "normal",
        "elongated": "sickle",
        # "other" is skipped
    }

    erydb_usable = {"normal": [], "sickle": []}
    erydb_removed = {"normal": [], "sickle": []}

    if not ERYDB_BASE.exists():
        print(f"  ⚠ erythrocytesIDB not found at: {ERYDB_BASE}")
        print(f"    Skipping — download via DOWNLOAD_GUIDE.md")
        return erydb_usable, erydb_removed

    for category, our_class in category_map.items():
        cat_dir = ERYDB_BASE / category
        if not cat_dir.exists():
            print(f"  ⚠ {category}/ not found — skipping")
            continue

        images = sorted([f for f in cat_dir.iterdir() if is_image(f)])
        print(f"\n  {category}/ (→ {our_class}): {len(images)} images")

        for i, img_path in enumerate(images):
            try:
                q = compute_quality(img_path)
                entry = {
                    "path": str(img_path),
                    "filename": img_path.name,
                    "class": our_class,
                    "source": "erythrocytesIDB",
                    "category": category,
                    "width": q.get("width"),
                    "height": q.get("height"),
                    "laplacian_variance": q.get("laplacian_variance", 0),
                    "significant_contours": q.get("significant_contours", 0),
                    "foreground_pct": q.get("foreground_pct", 0),
                }

                if q["must_remove"]:
                    entry["reason"] = q["reason"]
                    erydb_removed[our_class].append(entry)
                else:
                    erydb_usable[our_class].append(entry)

            except Exception as e:
                print(f"    ✗ Error: {img_path.name}: {e}")
                erydb_removed[our_class].append({
                    "path": str(img_path),
                    "filename": img_path.name,
                    "class": our_class,
                    "source": "erythrocytesIDB",
                    "reason": f"PROCESSING_ERROR: {e}",
                })

            if (i + 1) % 50 == 0:
                print(f"    [{i+1}/{len(images)}]", end="\r")

        u = len(erydb_usable[our_class])
        r = len(erydb_removed[our_class])
        print(f"    Usable: {u}  |  Removed: {r}")

        # Show removal reasons
        if erydb_removed[our_class]:
            reason_counts = defaultdict(int)
            for entry in erydb_removed[our_class]:
                reason_counts[entry.get("reason", "UNKNOWN")] += 1
            for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
                print(f"      {reason}: {count}")

    # Also report "other" stats (skipped but counted)
    other_dir = ERYDB_BASE / "other"
    if other_dir.exists():
        other_count = sum(1 for f in other_dir.iterdir() if is_image(f))
        print(f"\n  other/: {other_count} images — SKIPPED (not normal or sickle)")

    return erydb_usable, erydb_removed


# ═══════════════════════════════════════════════════════════════
#  STEP 3 — Build clean dataset
# ═══════════════════════════════════════════════════════════════

def build_clean_dataset(existing_usable, existing_removed,
                        erydb_usable, erydb_removed):
    """Copy and normalize all usable crops into dataset_clean/."""
    print("\n" + "=" * 80)
    print("  STEP 3: Building clean dataset")
    print("=" * 80)

    # Create directory structure
    for d in [
        DATASET_CLEAN / "normal",
        DATASET_CLEAN / "sickle",
        DATASET_CLEAN / "removed" / "normal",
        DATASET_CLEAN / "removed" / "sickle",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    build_log = []
    stats = {
        "orig_normal_kept": 0, "orig_normal_removed": 0,
        "orig_sickle_kept": 0, "orig_sickle_removed": 0,
        "erydb_normal_kept": 0, "erydb_normal_removed": 0,
        "erydb_sickle_kept": 0, "erydb_sickle_removed": 0,
        "resize_count": 0, "copy_errors": 0,
    }

    # ── Process existing USABLE crops ──
    print("\n  Copying existing usable crops...")
    for cls in ["normal", "sickle"]:
        for entry in existing_usable[cls]:
            src = Path(entry["path"])
            if not src.exists():
                stats["copy_errors"] += 1
                continue

            dst_name = f"orig_{src.stem}.jpg"
            dst = DATASET_CLEAN / cls / dst_name

            try:
                final_dst = normalize_and_save(src, dst)
                entry["clean_path"] = str(final_dst)
                entry["status"] = "kept"
                stats[f"orig_{cls}_kept"] += 1

                # Check if resize was needed
                img_check = cv2.imread(str(src))
                if img_check is not None:
                    h, w = img_check.shape[:2]
                    if (w, h) != TARGET_SIZE:
                        stats["resize_count"] += 1

                build_log.append({
                    "source_path": str(src),
                    "clean_path": str(final_dst),
                    "class": cls,
                    "origin": "existing",
                    "prefix": "orig_",
                    "status": "kept",
                })
            except Exception as e:
                stats["copy_errors"] += 1
                build_log.append({
                    "source_path": str(src),
                    "class": cls,
                    "origin": "existing",
                    "status": "error",
                    "error": str(e),
                })

    print(f"    Normal: {stats['orig_normal_kept']} kept")
    print(f"    Sickle: {stats['orig_sickle_kept']} kept")

    # ── Process existing REMOVED crops ──
    print("\n  Copying removed crops to removed/ ...")
    for cls in ["normal", "sickle"]:
        for entry in existing_removed[cls]:
            src = Path(entry["path"])
            if not src.exists():
                continue

            dst_name = f"orig_{src.stem}.jpg"
            dst = DATASET_CLEAN / "removed" / cls / dst_name

            try:
                shutil.copy2(str(src), str(dst))
                stats[f"orig_{cls}_removed"] += 1
                build_log.append({
                    "source_path": str(src),
                    "clean_path": str(dst),
                    "class": cls,
                    "origin": "existing",
                    "prefix": "orig_",
                    "status": "removed",
                    "reason": entry.get("reason", "unknown"),
                })
            except Exception:
                pass

    # ── Process erythrocytesIDB USABLE crops ──
    print("\n  Copying erythrocytesIDB usable crops...")
    for cls in ["normal", "sickle"]:
        for entry in erydb_usable[cls]:
            src = Path(entry["path"])
            if not src.exists():
                stats["copy_errors"] += 1
                continue

            dst_name = f"erydb_{src.stem}.jpg"
            dst = DATASET_CLEAN / cls / dst_name

            try:
                final_dst = normalize_and_save(src, dst)
                entry["clean_path"] = str(final_dst)
                entry["status"] = "kept"
                stats[f"erydb_{cls}_kept"] += 1

                # Check resize
                img_check = cv2.imread(str(src))
                if img_check is not None:
                    h, w = img_check.shape[:2]
                    if (w, h) != TARGET_SIZE:
                        stats["resize_count"] += 1

                build_log.append({
                    "source_path": str(src),
                    "clean_path": str(final_dst),
                    "class": cls,
                    "origin": "erythrocytesIDB",
                    "prefix": "erydb_",
                    "status": "kept",
                })
            except Exception as e:
                stats["copy_errors"] += 1
                build_log.append({
                    "source_path": str(src),
                    "class": cls,
                    "origin": "erythrocytesIDB",
                    "status": "error",
                    "error": str(e),
                })

    print(f"    Normal (circular): {stats['erydb_normal_kept']} kept")
    print(f"    Sickle (elongated): {stats['erydb_sickle_kept']} kept")

    # ── Process erythrocytesIDB REMOVED crops ──
    print("\n  Copying erythrocytesIDB removed crops...")
    for cls in ["normal", "sickle"]:
        for entry in erydb_removed[cls]:
            src = Path(entry["path"])
            if not src.exists():
                continue

            dst_name = f"erydb_{src.stem}.jpg"
            dst = DATASET_CLEAN / "removed" / cls / dst_name

            try:
                shutil.copy2(str(src), str(dst))
                stats[f"erydb_{cls}_removed"] += 1
                build_log.append({
                    "source_path": str(src),
                    "clean_path": str(dst),
                    "class": cls,
                    "origin": "erythrocytesIDB",
                    "prefix": "erydb_",
                    "status": "removed",
                    "reason": entry.get("reason", "unknown"),
                })
            except Exception:
                pass

    return stats, build_log


# ═══════════════════════════════════════════════════════════════
#  STEP 4 — Final summary
# ═══════════════════════════════════════════════════════════════

def print_final_summary(stats):
    """Print comprehensive final report."""
    print("\n" + "=" * 80)
    print("  STEP 4: FINAL SUMMARY")
    print("=" * 80)

    # Existing data
    ex_n_total = stats["orig_normal_kept"] + stats["orig_normal_removed"]
    ex_s_total = stats["orig_sickle_kept"] + stats["orig_sickle_removed"]
    ex_n_pct = (stats["orig_normal_kept"] / ex_n_total * 100) if ex_n_total > 0 else 0
    ex_s_pct = (stats["orig_sickle_kept"] / ex_s_total * 100) if ex_s_total > 0 else 0

    print(f"\n  ── EXISTING DATA (dataset_v1_2class) ──")
    print(f"    Normal: {stats['orig_normal_kept']:>4d} usable / "
          f"{stats['orig_normal_removed']:>4d} removed  ({ex_n_pct:.1f}% kept)")
    print(f"    Sickle: {stats['orig_sickle_kept']:>4d} usable / "
          f"{stats['orig_sickle_removed']:>4d} removed  ({ex_s_pct:.1f}% kept)")

    # New erythrocytesIDB data
    print(f"\n  ── NEW erythrocytesIDB DATA ──")
    print(f"    Circular → normal:   {stats['erydb_normal_kept']:>4d} usable / "
          f"{stats['erydb_normal_removed']:>4d} removed")
    print(f"    Elongated → sickle:  {stats['erydb_sickle_kept']:>4d} usable / "
          f"{stats['erydb_sickle_removed']:>4d} removed")

    # Combined
    total_normal = stats["orig_normal_kept"] + stats["erydb_normal_kept"]
    total_sickle = stats["orig_sickle_kept"] + stats["erydb_sickle_kept"]
    total = total_normal + total_sickle
    ratio = round(total_normal / total_sickle, 2) if total_sickle > 0 else float("inf")
    normal_gap = max(0, 500 - total_normal)
    sickle_gap = max(0, 500 - total_sickle)
    is_sufficient = total_normal >= 500 and total_sickle >= 500

    print(f"\n  ╔═══════════════════════════════════════════════════╗")
    print(f"  ║  COMBINED CLEAN DATASET (dataset_clean/)          ║")
    print(f"  ╠═══════════════════════════════════════════════════╣")
    print(f"  ║  normal/:                         {total_normal:>5d} images   ║")
    print(f"  ║  sickle/:                         {total_sickle:>5d} images   ║")
    print(f"  ║  TOTAL:                           {total:>5d} images   ║")
    print(f"  ╠═══════════════════════════════════════════════════╣")
    print(f"  ║  Balance ratio (normal:sickle):     {ratio}:1       ║")
    print(f"  ║  Normal gap to 500:                {normal_gap:>5d}           ║")
    print(f"  ║  Sickle gap to 500:                {sickle_gap:>5d}           ║")
    print(f"  ║  Sufficient for training?        {'  YES ✓' if is_sufficient else '   NO ⚠'}          ║")
    print(f"  ╚═══════════════════════════════════════════════════╝")

    if stats["resize_count"] > 0:
        print(f"\n  {stats['resize_count']} images were resized to {TARGET_SIZE[0]}×{TARGET_SIZE[1]}")
    if stats["copy_errors"] > 0:
        print(f"  ⚠ {stats['copy_errors']} images failed to copy (see build_report.json)")

    return {
        "total_normal": total_normal,
        "total_sickle": total_sickle,
        "total": total,
        "balance_ratio": ratio,
        "normal_gap_to_500": normal_gap,
        "sickle_gap_to_500": sickle_gap,
        "is_sufficient": is_sufficient,
        "orig_normal_kept": stats["orig_normal_kept"],
        "orig_normal_removed": stats["orig_normal_removed"],
        "orig_sickle_kept": stats["orig_sickle_kept"],
        "orig_sickle_removed": stats["orig_sickle_removed"],
        "erydb_normal_kept": stats["erydb_normal_kept"],
        "erydb_normal_removed": stats["erydb_normal_removed"],
        "erydb_sickle_kept": stats["erydb_sickle_kept"],
        "erydb_sickle_removed": stats["erydb_sickle_removed"],
        "resize_count": stats["resize_count"],
        "copy_errors": stats["copy_errors"],
    }


# ═══════════════════════════════════════════════════════════════
#  STEP 5 — Visual quality grid
# ═══════════════════════════════════════════════════════════════

def build_quality_grid(stats):
    """Create a visual comparison grid of clean crops by source."""
    print("\n" + "=" * 80)
    print("  STEP 5: Building visual quality comparison grid")
    print("=" * 80)

    CELL = 128
    COLS = 5
    PAD = 4
    TITLE_H = 24

    row_defs = [
        ("EXISTING Normal (orig_)", DATASET_CLEAN / "normal", "orig_"),
        ("NEW erythrocytesIDB Normal (erydb_)", DATASET_CLEAN / "normal", "erydb_"),
        ("EXISTING Sickle (orig_)", DATASET_CLEAN / "sickle", "orig_"),
        ("NEW erythrocytesIDB Sickle (erydb_)", DATASET_CLEAN / "sickle", "erydb_"),
        ("REMOVED (quality issues)", None, None),  # special row
    ]

    # Collect removed files for the last row
    removed_files = []
    for cls in ["normal", "sickle"]:
        rem_dir = DATASET_CLEAN / "removed" / cls
        if rem_dir.exists():
            removed_files.extend([f for f in rem_dir.iterdir() if is_image(f)])

    # Calculate grid dimensions
    num_rows = len(row_defs)
    row_h = TITLE_H + CELL + 20  # title + image + label
    total_h = PAD + num_rows * (row_h + PAD)
    total_w = PAD + COLS * (CELL + PAD)

    canvas = np.ones((total_h, total_w, 3), dtype=np.uint8) * 35

    y = PAD
    for row_title, src_dir, prefix in row_defs:
        # Title
        cv2.putText(canvas, row_title, (PAD + 4, y + 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1, cv2.LINE_AA)
        y += TITLE_H

        # Collect matching files
        if prefix is None:
            # Removed row
            sample_files = random.sample(removed_files, min(COLS, len(removed_files)))
        elif src_dir and src_dir.exists():
            matching = [f for f in src_dir.iterdir()
                        if is_image(f) and f.name.startswith(prefix)]
            sample_files = random.sample(matching, min(COLS, len(matching)))
        else:
            sample_files = []

        for col in range(COLS):
            x = PAD + col * (CELL + PAD)

            if col < len(sample_files):
                fpath = sample_files[col]
                img = cv2.imread(str(fpath))
                if img is not None:
                    cell_img = cv2.resize(img, (CELL, CELL), interpolation=cv2.INTER_AREA)
                    canvas[y:y + CELL, x:x + CELL] = cell_img

                # Label
                label = fpath.stem[:20]
                color = (0, 0, 255) if prefix is None else (0, 220, 0)
                cv2.putText(canvas, label, (x + 2, y + CELL + 14),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.28, color, 1, cv2.LINE_AA)
            else:
                cv2.rectangle(canvas, (x, y), (x + CELL, y + CELL), (70, 70, 70), 1)
                cv2.putText(canvas, "N/A", (x + 48, y + 68),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (90, 90, 90), 1)

        y += CELL + 20 + PAD  # image + label gap + padding

    grid_path = DATASET_CLEAN / "quality_comparison.png"
    cv2.imwrite(str(grid_path), canvas, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    print(f"  ✓ Saved: {grid_path}")
    return grid_path


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 80)
    print("  LabMind AI — Build Clean Dataset")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("═" * 80)

    # Safety: warn if dataset_clean already exists
    if DATASET_CLEAN.exists():
        normal_dir = DATASET_CLEAN / "normal"
        sickle_dir = DATASET_CLEAN / "sickle"
        existing = 0
        if normal_dir.exists():
            existing += sum(1 for _ in normal_dir.iterdir())
        if sickle_dir.exists():
            existing += sum(1 for _ in sickle_dir.iterdir())
        if existing > 0:
            print(f"\n  ⚠ dataset_clean/ already contains {existing} files.")
            print(f"    Delete it first to rebuild from scratch.")
            resp = input("  Continue and overwrite? (y/N): ").strip().lower()
            if resp != "y":
                print("  Aborted.")
                return

    # Step 1: Classify existing crops
    existing_usable, existing_removed = classify_existing_from_audit()

    # Step 2: Scan erythrocytesIDB
    erydb_usable, erydb_removed = scan_erythrocytes_idb()

    # Step 3: Build clean dataset
    stats, build_log = build_clean_dataset(
        existing_usable, existing_removed,
        erydb_usable, erydb_removed,
    )

    # Step 4: Summary
    summary = print_final_summary(stats)

    # Save build report
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "thresholds": {
            "blur_critical": BLUR_CRITICAL,
            "contour_area_pct": CONTOUR_AREA_PCT,
            "foreground_min_pct": FOREGROUND_MIN_PCT,
            "target_size": list(TARGET_SIZE),
            "jpeg_quality": JPEG_QUALITY,
        },
        "summary": summary,
        "build_log": build_log,
    }

    report_path = DATASET_CLEAN / "build_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  ✓ Build report saved to: {report_path}")

    # Step 5: Visual grid
    try:
        build_quality_grid(stats)
    except Exception as e:
        print(f"  ⚠ Could not build visual grid: {e}")

    # Verify final file counts on disk
    actual_normal = sum(1 for f in (DATASET_CLEAN / "normal").iterdir() if is_image(f))
    actual_sickle = sum(1 for f in (DATASET_CLEAN / "sickle").iterdir() if is_image(f))
    print(f"\n  ── VERIFIED ON DISK ──")
    print(f"    dataset_clean/normal/: {actual_normal} files")
    print(f"    dataset_clean/sickle/: {actual_sickle} files")

    print("\n" + "═" * 80)
    print("  DONE — dataset_clean/ is ready for training")
    print("═" * 80 + "\n")


if __name__ == "__main__":
    main()
