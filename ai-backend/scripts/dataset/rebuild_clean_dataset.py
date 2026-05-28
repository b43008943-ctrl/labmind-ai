"""
LabMind AI — Rebuild Clean Dataset
====================================
Rebuilds dataset_clean/ from scratch with relaxed, source-aware filters.

Filters:
  - Existing crops (dataset_v1_2class): remove if Laplacian < 5 OR foreground < 10%
  - erythrocytesIDB circular → normal:  remove if Laplacian < 5
  - erythrocytesIDB elongated → sickle: remove if Laplacian < 5 (multi-cell OK)
  - erythrocytesIDB other: SKIPPED

Usage:
    python rebuild_clean_dataset.py

SAFETY: Does NOT touch dataset_v1_2class/ or source_erythrocytesIDB/.
"""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    print("[ERROR] OpenCV + NumPy required: pip install opencv-python-headless numpy")
    sys.exit(1)

BASE = Path(__file__).resolve().parent
DATASET_V1 = BASE / "dataset_v1_2class"
ERYDB_BASE = BASE / "dataset_robust" / "raw" / "source_erythrocytesIDB" / "individual cells"
DATASET_CLEAN = BASE / "dataset_clean"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
TARGET_SIZE = (128, 128)
JPEG_QUALITY = 95
BLUR_FLOOR = 5.0
FG_MIN_PCT = 10.0


def is_image(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS


def lap_var(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def fg_pct(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return float(np.count_nonzero(thresh)) / (gray.shape[0] * gray.shape[1]) * 100.0


def resize_and_save(src: Path, dst: Path):
    img = cv2.imread(str(src))
    if img is None:
        raise ValueError(f"Unreadable: {src}")
    h, w = img.shape[:2]
    if (w, h) != TARGET_SIZE:
        interp = cv2.INTER_AREA if w > TARGET_SIZE[0] else cv2.INTER_CUBIC
        img = cv2.resize(img, TARGET_SIZE, interpolation=interp)
    dst = dst.with_suffix(".jpg")
    cv2.imwrite(str(dst), img, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    return dst


def main():
    print("\n" + "=" * 70)
    print("  Rebuild Clean Dataset")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    # ── STEP 1: Wipe and recreate ──
    print("\n  STEP 1: Recreating dataset_clean/ from scratch")
    if DATASET_CLEAN.exists():
        shutil.rmtree(DATASET_CLEAN)
        print("    Deleted existing dataset_clean/")

    for d in [
        DATASET_CLEAN / "normal",
        DATASET_CLEAN / "sickle",
        DATASET_CLEAN / "removed" / "normal",
        DATASET_CLEAN / "removed" / "sickle",
    ]:
        d.mkdir(parents=True, exist_ok=True)
    print("    Created fresh directory structure")

    log = []
    stats = {
        "orig_normal_kept": 0, "orig_normal_removed": 0,
        "orig_sickle_kept": 0, "orig_sickle_removed": 0,
        "erydb_normal_kept": 0, "erydb_normal_removed": 0,
        "erydb_sickle_kept": 0, "erydb_sickle_removed": 0,
        "errors": 0,
    }

    # ── STEP 2: Process existing dataset_v1_2class ──
    print("\n  STEP 2: Processing dataset_v1_2class/")
    for split in ["train", "val"]:
        for cls in ["normal", "sickle"]:
            src_dir = DATASET_V1 / split / cls
            if not src_dir.exists():
                continue
            images = sorted([f for f in src_dir.iterdir() if is_image(f)])
            kept = 0
            removed = 0
            for img_path in images:
                try:
                    img = cv2.imread(str(img_path))
                    if img is None:
                        stats["errors"] += 1
                        continue
                    lv = lap_var(img)
                    fg = fg_pct(img)
                    reason = None
                    if lv < BLUR_FLOOR:
                        reason = "EXTREME_BLUR"
                    elif cls == "normal" and fg < FG_MIN_PCT:
                        reason = "TOO_EMPTY"
                    elif cls == "sickle" and fg < FG_MIN_PCT:
                        reason = "TOO_EMPTY"

                    dst_name = f"orig_{img_path.stem}"
                    if reason:
                        dst = DATASET_CLEAN / "removed" / cls / f"{dst_name}.jpg"
                        shutil.copy2(str(img_path), str(dst))
                        stats[f"orig_{cls}_removed"] += 1
                        removed += 1
                        log.append({"src": str(img_path), "dst": str(dst),
                                    "cls": cls, "origin": "v1", "status": "removed",
                                    "reason": reason, "lap": round(lv, 2), "fg": round(fg, 2)})
                    else:
                        dst = DATASET_CLEAN / cls / f"{dst_name}.jpg"
                        resize_and_save(img_path, dst)
                        stats[f"orig_{cls}_kept"] += 1
                        kept += 1
                        log.append({"src": str(img_path), "dst": str(dst),
                                    "cls": cls, "origin": "v1", "status": "kept",
                                    "lap": round(lv, 2), "fg": round(fg, 2)})
                except Exception as e:
                    stats["errors"] += 1
                    log.append({"src": str(img_path), "cls": cls, "origin": "v1",
                                "status": "error", "error": str(e)})

            print(f"    {split}/{cls}: {kept} kept, {removed} removed")

    # ── STEP 3: Process erythrocytesIDB ──
    print("\n  STEP 3: Processing erythrocytesIDB")

    erydb_map = [
        ("circular", "normal", "erydb_c_"),
        ("elongated", "sickle", "erydb_e_"),
    ]

    for folder, cls, prefix in erydb_map:
        src_dir = ERYDB_BASE / folder
        if not src_dir.exists():
            print(f"    ⚠ {folder}/ not found — skipping")
            continue
        images = sorted([f for f in src_dir.iterdir() if is_image(f)])
        kept = 0
        removed = 0
        for img_path in images:
            try:
                img = cv2.imread(str(img_path))
                if img is None:
                    stats["errors"] += 1
                    continue
                lv = lap_var(img)
                reason = None
                if lv < BLUR_FLOOR:
                    reason = "EXTREME_BLUR"

                dst_name = f"{prefix}{img_path.stem}"
                if reason:
                    dst = DATASET_CLEAN / "removed" / cls / f"{dst_name}.jpg"
                    shutil.copy2(str(img_path), str(dst))
                    stats[f"erydb_{cls}_removed"] += 1
                    removed += 1
                    log.append({"src": str(img_path), "dst": str(dst),
                                "cls": cls, "origin": "erythrocytesIDB", "status": "removed",
                                "reason": reason, "lap": round(lv, 2)})
                else:
                    dst = DATASET_CLEAN / cls / f"{dst_name}.jpg"
                    resize_and_save(img_path, dst)
                    stats[f"erydb_{cls}_kept"] += 1
                    kept += 1
                    log.append({"src": str(img_path), "dst": str(dst),
                                "cls": cls, "origin": "erythrocytesIDB", "status": "kept",
                                "lap": round(lv, 2)})
            except Exception as e:
                stats["errors"] += 1
                log.append({"src": str(img_path), "cls": cls, "origin": "erythrocytesIDB",
                            "status": "error", "error": str(e)})

        print(f"    {folder} → {cls}: {kept} kept, {removed} removed")

    other_dir = ERYDB_BASE / "other"
    if other_dir.exists():
        cnt = sum(1 for f in other_dir.iterdir() if is_image(f))
        print(f"    other/: {cnt} images — SKIPPED")

    # ── STEP 4: Final counts ──
    total_normal = stats["orig_normal_kept"] + stats["erydb_normal_kept"]
    total_sickle = stats["orig_sickle_kept"] + stats["erydb_sickle_kept"]
    total = total_normal + total_sickle
    ratio = round(total_normal / total_sickle, 2) if total_sickle > 0 else float("inf")
    normal_gap = max(0, 500 - total_normal)
    sickle_gap = max(0, 500 - total_sickle)
    sufficient = total_normal >= 500 and total_sickle >= 500

    # Verify on disk
    actual_n = sum(1 for f in (DATASET_CLEAN / "normal").iterdir() if is_image(f))
    actual_s = sum(1 for f in (DATASET_CLEAN / "sickle").iterdir() if is_image(f))

    print(f"\n  {'=' * 56}")
    print(f"  FINAL CLEAN DATASET")
    print(f"  {'=' * 56}")
    print(f"  dataset_clean/normal/:  {actual_n:>5d}  (orig: {stats['orig_normal_kept']}, erydb: {stats['erydb_normal_kept']})")
    print(f"  dataset_clean/sickle/:  {actual_s:>5d}  (orig: {stats['orig_sickle_kept']}, erydb: {stats['erydb_sickle_kept']})")
    print(f"  removed/ normal:        {stats['orig_normal_removed'] + stats['erydb_normal_removed']:>5d}")
    print(f"  removed/ sickle:        {stats['orig_sickle_removed'] + stats['erydb_sickle_removed']:>5d}")
    print(f"  errors:                 {stats['errors']:>5d}")
    print(f"  {'─' * 56}")
    print(f"  TOTAL USABLE:           {actual_n + actual_s:>5d}")
    print(f"  Balance (normal:sickle): {ratio}:1")
    print(f"  Normal gap to 500:      {normal_gap:>5d}{'  ✓' if normal_gap == 0 else '  ⚠'}")
    print(f"  Sickle gap to 500:      {sickle_gap:>5d}{'  ✓' if sickle_gap == 0 else '  ⚠'}")
    print(f"  Sufficient for training: {'YES ✓' if sufficient else 'NO ⚠'}")
    print(f"  {'=' * 56}")

    # ── STEP 5: Save report ──
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "thresholds": {"blur_floor": BLUR_FLOOR, "fg_min_pct": FG_MIN_PCT,
                       "target_size": list(TARGET_SIZE), "jpeg_quality": JPEG_QUALITY},
        "summary": {
            "total_normal": actual_n, "total_sickle": actual_s,
            "total": actual_n + actual_s, "balance_ratio": ratio,
            "normal_gap_to_500": normal_gap, "sickle_gap_to_500": sickle_gap,
            "is_sufficient": sufficient, **stats,
        },
        "build_log": log,
    }
    report_path = DATASET_CLEAN / "build_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  ✓ Report: {report_path}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
