"""
LabMind AI — Crop Quality Audit
=================================
Automatically inspects every crop in training and validation data,
flagging quality issues: blur, multi-cell, border cuts, artifacts,
wrong sizes.

Usage:
    python crop_quality_audit.py

Output:
    - crop_quality_audit_report.json   (detailed per-file results)
    - crop_quality_audit_grid.png      (visual example grid)
    - Console summary table

SAFETY:
    - READ-ONLY — does NOT modify or delete any existing files
    - Handles missing directories and corrupted images gracefully
"""

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    print("[ERROR] OpenCV + NumPy required. Install with: pip install opencv-python-headless numpy")
    sys.exit(1)

# ── Paths ────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent

SCAN_DIRS = [
    ("dataset_v1_2class/train/normal",     BASE / "dataset_v1_2class" / "train" / "normal",     "normal"),
    ("dataset_v1_2class/train/sickle",     BASE / "dataset_v1_2class" / "train" / "sickle",     "sickle"),
    ("dataset_v1_2class/val/normal",       BASE / "dataset_v1_2class" / "val" / "normal",       "normal"),
    ("dataset_v1_2class/val/sickle",       BASE / "dataset_v1_2class" / "val" / "sickle",       "sickle"),
    ("dataset_robust/processed/normal",    BASE / "dataset_robust" / "processed" / "normal",    "normal"),
    ("dataset_robust/processed/sickle",    BASE / "dataset_robust" / "processed" / "sickle",    "sickle"),
    ("validation_cells/normal",            BASE / "validation_cells" / "normal",                "normal"),
    ("validation_cells/sickle",            BASE / "validation_cells" / "sickle",                "sickle"),
]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

# ── Thresholds (recording raw values so they can be adjusted later) ──
BLUR_THRESHOLD = 50.0            # Laplacian variance below this = blurry
CONTOUR_AREA_PCT = 0.05          # Contour must be > 5% of image area to count
BORDER_MARGIN_PX = 3             # Contour within this many px of edge = border cut
FOREGROUND_MIN_PCT = 10.0        # < 10% foreground = too empty
FOREGROUND_MAX_PCT = 90.0        # > 90% foreground = too full
ACCEPTED_SIZES = [(128, 128), (64, 64)]  # Valid crop dimensions


def is_image(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS


# ═══════════════════════════════════════════════════════════════
#  Quality Checks
# ═══════════════════════════════════════════════════════════════

def check_blur(gray: np.ndarray) -> dict:
    """A) Laplacian variance blur detection."""
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return {
        "laplacian_variance": round(lap_var, 2),
        "is_blurry": lap_var < BLUR_THRESHOLD,
    }


def check_multi_cell(gray: np.ndarray, img_area: int) -> dict:
    """B) Multi-cell detection via Otsu + contour counting."""
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_contour_area = img_area * CONTOUR_AREA_PCT
    significant = [c for c in contours if cv2.contourArea(c) > min_contour_area]

    return {
        "total_contours": len(contours),
        "significant_contours": len(significant),
        "is_multi_cell": len(significant) > 1,
    }


def check_border_cut(gray: np.ndarray, img_h: int, img_w: int) -> dict:
    """C) Border cut detection — check if foreground touches image edges."""
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = img_h * img_w * CONTOUR_AREA_PCT
    borders_touched = set()

    for cnt in contours:
        if cv2.contourArea(cnt) < min_area:
            continue
        for pt in cnt:
            x, y = pt[0]
            if x <= BORDER_MARGIN_PX:
                borders_touched.add("left")
            if x >= img_w - 1 - BORDER_MARGIN_PX:
                borders_touched.add("right")
            if y <= BORDER_MARGIN_PX:
                borders_touched.add("top")
            if y >= img_h - 1 - BORDER_MARGIN_PX:
                borders_touched.add("bottom")

    return {
        "borders_touched": sorted(borders_touched),
        "is_border_cut": len(borders_touched) > 0,
    }


def check_foreground(gray: np.ndarray) -> dict:
    """D) Empty/artifact detection via foreground percentage."""
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    total_px = gray.shape[0] * gray.shape[1]
    fg_px = int(np.count_nonzero(thresh))
    fg_pct = (fg_px / total_px) * 100.0

    return {
        "foreground_pixels": fg_px,
        "total_pixels": total_px,
        "foreground_pct": round(fg_pct, 2),
        "is_too_empty": fg_pct < FOREGROUND_MIN_PCT,
        "is_too_full": fg_pct > FOREGROUND_MAX_PCT,
    }


def check_size(img_w: int, img_h: int) -> dict:
    """E) Size validation."""
    is_accepted = (img_w, img_h) in ACCEPTED_SIZES
    return {
        "width": img_w,
        "height": img_h,
        "is_wrong_size": not is_accepted,
    }


# ═══════════════════════════════════════════════════════════════
#  Per-Image Audit
# ═══════════════════════════════════════════════════════════════

def audit_single_image(img_path: Path) -> dict:
    """Run all quality checks on a single image. Returns results dict."""
    result = {
        "filename": img_path.name,
        "path": str(img_path),
        "file_size_bytes": img_path.stat().st_size,
    }

    img = cv2.imread(str(img_path))
    if img is None:
        result["error"] = "cv2.imread returned None (corrupted or unreadable)"
        result["verdict"] = "ERROR"
        result["flags"] = ["UNREADABLE"]
        return result

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_area = h * w

    # Run all checks
    blur = check_blur(gray)
    multi = check_multi_cell(gray, img_area)
    border = check_border_cut(gray, h, w)
    foreground = check_foreground(gray)
    size = check_size(w, h)

    # Collect flags
    flags = []
    if blur["is_blurry"]:
        flags.append("BLURRY")
    if multi["is_multi_cell"]:
        flags.append("MULTI_CELL")
    if border["is_border_cut"]:
        flags.append("BORDER_CUT")
    if foreground["is_too_empty"]:
        flags.append("TOO_EMPTY")
    if foreground["is_too_full"]:
        flags.append("TOO_FULL")
    if size["is_wrong_size"]:
        flags.append("WRONG_SIZE")

    # Verdict
    if len(flags) == 0:
        verdict = "GOOD"
    elif len(flags) == 1:
        verdict = "QUESTIONABLE"
    else:
        verdict = "BAD"

    result.update({
        "dimensions": f"{w}x{h}",
        "blur": blur,
        "multi_cell": multi,
        "border_cut": border,
        "foreground": foreground,
        "size_check": size,
        "flags": flags,
        "flag_count": len(flags),
        "verdict": verdict,
    })

    return result


# ═══════════════════════════════════════════════════════════════
#  Directory Scanner
# ═══════════════════════════════════════════════════════════════

def scan_directory(label: str, dir_path: Path, expected_class: str) -> dict:
    """Audit all images in a directory."""
    dir_report = {
        "label": label,
        "path": str(dir_path),
        "expected_class": expected_class,
        "exists": dir_path.exists(),
        "files": [],
        "summary": {},
    }

    if not dir_path.exists():
        print(f"  ⚠ MISSING: {label}")
        dir_report["summary"] = {
            "total": 0, "good": 0, "questionable": 0, "bad": 0, "errors": 0,
            "blurry": 0, "multi_cell": 0, "border_cut": 0,
            "too_empty": 0, "too_full": 0, "wrong_size": 0,
        }
        return dir_report

    images = sorted([f for f in dir_path.iterdir() if is_image(f)])
    total = len(images)

    counts = {
        "total": total, "good": 0, "questionable": 0, "bad": 0, "errors": 0,
        "blurry": 0, "multi_cell": 0, "border_cut": 0,
        "too_empty": 0, "too_full": 0, "wrong_size": 0,
    }

    for i, img_path in enumerate(images):
        try:
            result = audit_single_image(img_path)
            result["expected_class"] = expected_class
        except Exception as e:
            result = {
                "filename": img_path.name,
                "path": str(img_path),
                "error": str(e),
                "traceback": traceback.format_exc(),
                "verdict": "ERROR",
                "flags": ["PROCESSING_ERROR"],
                "expected_class": expected_class,
            }

        # Update counts
        v = result.get("verdict", "ERROR")
        if v == "GOOD":
            counts["good"] += 1
        elif v == "QUESTIONABLE":
            counts["questionable"] += 1
        elif v == "BAD":
            counts["bad"] += 1
        else:
            counts["errors"] += 1

        for flag in result.get("flags", []):
            flag_lower = flag.lower()
            if flag_lower in counts:
                counts[flag_lower] += 1

        dir_report["files"].append(result)

        # Progress indicator every 100 images
        if (i + 1) % 100 == 0 or (i + 1) == total:
            print(f"    [{i+1}/{total}] processed", end="\r")

    if total > 0:
        print()  # newline after progress

    dir_report["summary"] = counts
    return dir_report


# ═══════════════════════════════════════════════════════════════
#  Visual Grid
# ═══════════════════════════════════════════════════════════════

def build_visual_grid(all_results: list[dict], output_path: Path):
    """Create a 4-row visual grid showing example crops by verdict."""
    CELL_SIZE = 128
    COLS = 5
    ROWS = 4
    LABEL_H = 24
    ROW_H = CELL_SIZE + LABEL_H
    PAD = 4

    grid_w = COLS * (CELL_SIZE + PAD) + PAD
    grid_h = ROWS * (ROW_H + PAD) + PAD + 30  # +30 for row titles
    grid_total_h = 30 + ROWS * (ROW_H + 30 + PAD)  # extra spacing for titles

    # Collect examples
    good_normal = [r for r in all_results if r.get("verdict") == "GOOD" and r.get("expected_class") == "normal"]
    good_sickle = [r for r in all_results if r.get("verdict") == "GOOD" and r.get("expected_class") == "sickle"]
    bad_all = [r for r in all_results if r.get("verdict") == "BAD"]
    questionable_all = [r for r in all_results if r.get("verdict") == "QUESTIONABLE"]

    rows_data = [
        ("GOOD Normal", good_normal[:COLS]),
        ("GOOD Sickle", good_sickle[:COLS]),
        ("BAD (2+ flags)", bad_all[:COLS]),
        ("QUESTIONABLE (1 flag)", questionable_all[:COLS]),
    ]

    # Calculate total height
    total_h = PAD
    for _ in rows_data:
        total_h += 22 + PAD + ROW_H + PAD  # title + gap + cell row + gap

    canvas = np.ones((total_h, grid_w, 3), dtype=np.uint8) * 40  # dark gray bg

    y_cursor = PAD
    for row_title, row_items in rows_data:
        # Row title
        cv2.putText(canvas, row_title, (PAD + 4, y_cursor + 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)
        y_cursor += 22 + PAD

        for col_idx in range(COLS):
            x_offset = PAD + col_idx * (CELL_SIZE + PAD)

            if col_idx < len(row_items):
                item = row_items[col_idx]
                img_path = item.get("path", "")
                img = cv2.imread(img_path)

                if img is not None:
                    # Resize to CELL_SIZE x CELL_SIZE
                    cell_img = cv2.resize(img, (CELL_SIZE, CELL_SIZE), interpolation=cv2.INTER_AREA)
                    canvas[y_cursor:y_cursor + CELL_SIZE, x_offset:x_offset + CELL_SIZE] = cell_img
                else:
                    # Red X for unreadable
                    cv2.line(canvas, (x_offset, y_cursor), (x_offset + CELL_SIZE, y_cursor + CELL_SIZE), (0, 0, 200), 2)
                    cv2.line(canvas, (x_offset + CELL_SIZE, y_cursor), (x_offset, y_cursor + CELL_SIZE), (0, 0, 200), 2)

                # Label below image
                flags = item.get("flags", [])
                if flags:
                    label_text = ", ".join(flags)
                    # Truncate if too long
                    if len(label_text) > 20:
                        label_text = label_text[:18] + ".."
                    # Color: red for BAD, yellow for QUESTIONABLE
                    label_color = (0, 0, 255) if item.get("verdict") == "BAD" else (0, 200, 255)
                else:
                    label_text = item.get("filename", "")[:18]
                    label_color = (0, 255, 0)

                cv2.putText(canvas,
                            label_text,
                            (x_offset + 2, y_cursor + CELL_SIZE + 16),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.32, label_color, 1, cv2.LINE_AA)
            else:
                # Empty slot
                cv2.rectangle(canvas,
                              (x_offset, y_cursor),
                              (x_offset + CELL_SIZE, y_cursor + CELL_SIZE),
                              (80, 80, 80), 1)
                cv2.putText(canvas, "N/A",
                            (x_offset + 48, y_cursor + 68),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

        y_cursor += ROW_H + PAD

    cv2.imwrite(str(output_path), canvas, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    print(f"\n  ✓ Visual grid saved to: {output_path}")


# ═══════════════════════════════════════════════════════════════
#  Summary Printer
# ═══════════════════════════════════════════════════════════════

def print_summary_table(dir_reports: list[dict]):
    """Print a formatted summary table."""
    print("\n" + "=" * 120)
    print("  CROP QUALITY AUDIT — SUMMARY TABLE")
    print("=" * 120)

    header = (
        f"  {'Directory':<40s}"
        f"{'Total':>6s}"
        f"{'Good':>7s}"
        f"{'Quest':>7s}"
        f"{'Bad':>6s}"
        f"{'Blurry':>8s}"
        f"{'Multi':>7s}"
        f"{'Border':>8s}"
        f"{'Empty':>7s}"
        f"{'Full':>6s}"
        f"{'WrSize':>8s}"
    )
    print(header)
    print("  " + "─" * 116)

    totals = {
        "total": 0, "good": 0, "questionable": 0, "bad": 0,
        "blurry": 0, "multi_cell": 0, "border_cut": 0,
        "too_empty": 0, "too_full": 0, "wrong_size": 0,
    }

    for dr in dir_reports:
        s = dr["summary"]
        if s["total"] == 0 and not dr["exists"]:
            print(f"  {dr['label']:<40s}   ── MISSING ──")
            continue

        row = (
            f"  {dr['label']:<40s}"
            f"{s['total']:>6d}"
            f"{s['good']:>7d}"
            f"{s['questionable']:>7d}"
            f"{s['bad']:>6d}"
            f"{s['blurry']:>8d}"
            f"{s['multi_cell']:>7d}"
            f"{s['border_cut']:>8d}"
            f"{s['too_empty']:>7d}"
            f"{s['too_full']:>6d}"
            f"{s['wrong_size']:>8d}"
        )
        print(row)

        for k in totals:
            totals[k] += s.get(k, 0)

    print("  " + "─" * 116)
    total_row = (
        f"  {'TOTAL':<40s}"
        f"{totals['total']:>6d}"
        f"{totals['good']:>7d}"
        f"{totals['questionable']:>7d}"
        f"{totals['bad']:>6d}"
        f"{totals['blurry']:>8d}"
        f"{totals['multi_cell']:>7d}"
        f"{totals['border_cut']:>8d}"
        f"{totals['too_empty']:>7d}"
        f"{totals['too_full']:>6d}"
        f"{totals['wrong_size']:>8d}"
    )
    print(total_row)
    print("=" * 120)

    # Percentages
    if totals["total"] > 0:
        t = totals["total"]
        print(f"\n  Verdict distribution:")
        print(f"    GOOD:          {totals['good']:>5d}  ({totals['good']/t*100:.1f}%)")
        print(f"    QUESTIONABLE:  {totals['questionable']:>5d}  ({totals['questionable']/t*100:.1f}%)")
        print(f"    BAD:           {totals['bad']:>5d}  ({totals['bad']/t*100:.1f}%)")

        print(f"\n  Flag frequency:")
        for flag_name, key in [("BLURRY", "blurry"), ("MULTI_CELL", "multi_cell"),
                                ("BORDER_CUT", "border_cut"), ("TOO_EMPTY", "too_empty"),
                                ("TOO_FULL", "too_full"), ("WRONG_SIZE", "wrong_size")]:
            cnt = totals[key]
            print(f"    {flag_name:<15s} {cnt:>5d}  ({cnt/t*100:.1f}%)")

    return totals


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 120)
    print("  LabMind AI — Crop Quality Audit")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print(f"  Thresholds: blur<{BLUR_THRESHOLD}, contour>{CONTOUR_AREA_PCT*100:.0f}%area, "
          f"border={BORDER_MARGIN_PX}px, fg<{FOREGROUND_MIN_PCT}%=empty, fg>{FOREGROUND_MAX_PCT}%=full")
    print("═" * 120)

    all_dir_reports = []
    all_file_results = []

    for label, dir_path, expected_class in SCAN_DIRS:
        print(f"\n  Scanning: {label}")
        dir_report = scan_directory(label, dir_path, expected_class)
        all_dir_reports.append(dir_report)
        all_file_results.extend(dir_report["files"])

    # Print summary table
    totals = print_summary_table(all_dir_reports)

    # Collect BAD and QUESTIONABLE files for the report
    bad_files = [
        {"path": r["path"], "filename": r["filename"], "flags": r["flags"],
         "expected_class": r.get("expected_class", "unknown")}
        for r in all_file_results if r.get("verdict") == "BAD"
    ]
    questionable_files = [
        {"path": r["path"], "filename": r["filename"], "flags": r["flags"],
         "expected_class": r.get("expected_class", "unknown")}
        for r in all_file_results if r.get("verdict") == "QUESTIONABLE"
    ]

    print(f"\n  BAD files:          {len(bad_files)}")
    print(f"  QUESTIONABLE files: {len(questionable_files)}")

    # Show top BAD examples
    if bad_files:
        print(f"\n  ── Top BAD files (up to 10) ──")
        for bf in bad_files[:10]:
            print(f"    {bf['filename']:<45s}  flags: {', '.join(bf['flags'])}")

    # Build visual grid
    grid_path = BASE / "crop_quality_audit_grid.png"
    try:
        build_visual_grid(all_file_results, grid_path)
    except Exception as e:
        print(f"\n  ⚠ Could not build visual grid: {e}")

    # Save full JSON report
    full_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "thresholds": {
            "blur_threshold": BLUR_THRESHOLD,
            "contour_area_pct": CONTOUR_AREA_PCT,
            "border_margin_px": BORDER_MARGIN_PX,
            "foreground_min_pct": FOREGROUND_MIN_PCT,
            "foreground_max_pct": FOREGROUND_MAX_PCT,
            "accepted_sizes": [list(s) for s in ACCEPTED_SIZES],
        },
        "directories": [
            {
                "label": dr["label"],
                "path": dr["path"],
                "exists": dr["exists"],
                "expected_class": dr["expected_class"],
                "summary": dr["summary"],
                # Include per-file details (without the raw image data)
                "files": dr["files"],
            }
            for dr in all_dir_reports
        ],
        "overall_summary": totals,
        "bad_files": bad_files,
        "questionable_files": questionable_files,
    }

    report_path = BASE / "crop_quality_audit_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, default=str)
    print(f"\n  ✓ Full report saved to: {report_path}")

    print("═" * 120 + "\n")


if __name__ == "__main__":
    main()
