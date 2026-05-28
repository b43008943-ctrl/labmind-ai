"""
LabMind AI — Diagnose Rejected Sickle Cells
=============================================
Investigates why ALL 211 erythrocytesIDB elongated (sickle) images
were rejected by the quality filters in build_clean_dataset.py.

Hypothesis: the Otsu + contour-based filters are biased against
elongated cell morphology from external staining protocols.

Usage:
    python diagnose_rejected_sickle.py

SAFETY: READ-ONLY — does not modify any files or datasets.
"""

import json
import random
import sys
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
BUILD_REPORT = BASE / "dataset_clean" / "build_report.json"
ERYDB_ELONGATED = BASE / "dataset_robust" / "raw" / "source_erythrocytesIDB" / "individual cells" / "elongated"
ERYDB_CIRCULAR = BASE / "dataset_robust" / "raw" / "source_erythrocytesIDB" / "individual cells" / "circular"
CLEAN_NORMAL = BASE / "dataset_clean" / "normal"
CLEAN_SICKLE = BASE / "dataset_clean" / "sickle"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

# Thresholds used in build_clean_dataset.py (for reference)
BLUR_CRITICAL = 15.0
CONTOUR_AREA_PCT = 0.05
FOREGROUND_MIN_PCT = 10.0


def is_image(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS


def compute_full_metrics(img_path: Path) -> dict:
    """Compute all quality metrics for a single image."""
    img = cv2.imread(str(img_path))
    if img is None:
        return {"error": "unreadable", "filename": img_path.name}

    h, w = img.shape[:2]
    img_area = h * w
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Blur
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Otsu
    otsu_val, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = img_area * CONTOUR_AREA_PCT
    sig_contours = [c for c in contours if cv2.contourArea(c) > min_area]
    all_contour_areas = [cv2.contourArea(c) for c in contours]

    # Foreground
    fg_px = int(np.count_nonzero(thresh))
    fg_pct = (fg_px / img_area) * 100.0

    # Mean RGB
    means = cv2.mean(img)[:3]  # BGR

    # What the filter would decide
    reasons = []
    if len(sig_contours) > 1:
        reasons.append("MULTI_CELL")
    if fg_pct < FOREGROUND_MIN_PCT:
        reasons.append("TOO_EMPTY")
    if lap_var < BLUR_CRITICAL:
        reasons.append("EXTREME_BLUR")

    return {
        "filename": img_path.name,
        "path": str(img_path),
        "width": w,
        "height": h,
        "laplacian_variance": round(lap_var, 2),
        "otsu_threshold": round(float(otsu_val), 2),
        "total_contours": len(contours),
        "significant_contours": len(sig_contours),
        "all_contour_areas": sorted([round(a, 1) for a in all_contour_areas], reverse=True)[:10],
        "foreground_pct": round(fg_pct, 2),
        "mean_B": round(means[0], 2),
        "mean_G": round(means[1], 2),
        "mean_R": round(means[2], 2),
        "would_reject": len(reasons) > 0,
        "rejection_reasons": reasons,
    }


# ═══════════════════════════════════════════════════════════════
#  STEP 1 — Analyze rejection reasons from build report
# ═══════════════════════════════════════════════════════════════

def step1_analyze_rejections():
    print("\n" + "=" * 80)
    print("  STEP 1: Analyze rejection reasons from build report")
    print("=" * 80)

    # Try loading build report first
    erydb_sickle_rejected = []

    if BUILD_REPORT.exists():
        with open(BUILD_REPORT, "r", encoding="utf-8") as f:
            report = json.load(f)

        for entry in report.get("build_log", []):
            if (entry.get("origin") == "erythrocytesIDB"
                    and entry.get("class") == "sickle"
                    and entry.get("status") == "removed"):
                erydb_sickle_rejected.append(entry)

        print(f"\n  Found {len(erydb_sickle_rejected)} rejected erythrocytesIDB sickle entries in build log")

    # Whether from build log or not, let's scan the actual source files
    # to compute fresh metrics (build log may not have full details)
    print(f"\n  Scanning source files directly: {ERYDB_ELONGATED}")

    if not ERYDB_ELONGATED.exists():
        print(f"  ⚠ Directory not found: {ERYDB_ELONGATED}")
        return [], {}

    images = sorted([f for f in ERYDB_ELONGATED.iterdir() if is_image(f)])
    print(f"  Found {len(images)} elongated (sickle) images")

    # Compute metrics for every image
    all_metrics = []
    for i, img_path in enumerate(images):
        m = compute_full_metrics(img_path)
        all_metrics.append(m)
        if (i + 1) % 50 == 0:
            print(f"    [{i+1}/{len(images)}]", end="\r")
    if images:
        print(f"    [{len(images)}/{len(images)}] done")

    # Count rejection reasons
    reason_counts = defaultdict(int)
    multi_only = 0
    blur_only = 0
    empty_only = 0
    multiple = 0
    no_reject = 0

    for m in all_metrics:
        if m.get("error"):
            reason_counts["UNREADABLE"] += 1
            continue
        reasons = m.get("rejection_reasons", [])
        if not reasons:
            no_reject += 1
            continue
        if len(reasons) > 1:
            multiple += 1
            reason_counts["MULTIPLE"] += 1
        elif reasons[0] == "MULTI_CELL":
            multi_only += 1
        elif reasons[0] == "EXTREME_BLUR":
            blur_only += 1
        elif reasons[0] == "TOO_EMPTY":
            empty_only += 1

        for r in reasons:
            reason_counts[r] += 1

    rejected_total = len(all_metrics) - no_reject
    print(f"\n  ┌───────────────────────────────────────────────────┐")
    print(f"  │  REJECTION BREAKDOWN ({rejected_total} rejected / {no_reject} would pass) │")
    print(f"  ├───────────────────────────┬───────┬───────────────┤")
    print(f"  │  Reason                   │ Count │ % of rejected │")
    print(f"  ├───────────────────────────┼───────┼───────────────┤")
    print(f"  │  MULTI_CELL only          │ {multi_only:>5d} │ {multi_only/max(rejected_total,1)*100:>11.1f}%  │")
    print(f"  │  EXTREME_BLUR only        │ {blur_only:>5d} │ {blur_only/max(rejected_total,1)*100:>11.1f}%  │")
    print(f"  │  TOO_EMPTY only           │ {empty_only:>5d} │ {empty_only/max(rejected_total,1)*100:>11.1f}%  │")
    print(f"  │  Multiple reasons         │ {multiple:>5d} │ {multiple/max(rejected_total,1)*100:>11.1f}%  │")
    print(f"  ├───────────────────────────┼───────┼───────────────┤")
    print(f"  │  TOTAL REJECTED           │ {rejected_total:>5d} │      100.0%  │")
    print(f"  │  Would actually PASS      │ {no_reject:>5d} │              │")
    print(f"  └───────────────────────────┴───────┴───────────────┘")

    # Flag-level breakdown (flags can overlap)
    print(f"\n  Flags triggered (may overlap):")
    for flag in ["MULTI_CELL", "EXTREME_BLUR", "TOO_EMPTY"]:
        cnt = reason_counts.get(flag, 0)
        print(f"    {flag:<20s} {cnt:>5d}  ({cnt/max(len(all_metrics),1)*100:.1f}% of all)")

    return all_metrics, reason_counts


# ═══════════════════════════════════════════════════════════════
#  STEP 2 — Compare metrics between sources
# ═══════════════════════════════════════════════════════════════

def step2_compare_metrics(sickle_metrics: list):
    print("\n" + "=" * 80)
    print("  STEP 2: Compare metrics between accepted normals and rejected sickle")
    print("=" * 80)

    # Collect accepted normal crops
    normal_metrics = []
    if CLEAN_NORMAL.exists():
        clean_files = [f for f in CLEAN_NORMAL.iterdir() if is_image(f)]
        sample_size = min(30, len(clean_files))
        sample_files = random.sample(clean_files, sample_size)
        print(f"\n  Computing metrics for {sample_size} accepted normal crops...")
        for img_path in sample_files:
            m = compute_full_metrics(img_path)
            if not m.get("error"):
                normal_metrics.append(m)

    # Also compute metrics for accepted circular crops from source
    if ERYDB_CIRCULAR.exists():
        circ_files = [f for f in ERYDB_CIRCULAR.iterdir() if is_image(f)]
        circ_sample = random.sample(circ_files, min(20, len(circ_files)))
        print(f"  Computing metrics for {len(circ_sample)} source circular (normal) crops...")
        circ_metrics = []
        for img_path in circ_sample:
            m = compute_full_metrics(img_path)
            if not m.get("error"):
                circ_metrics.append(m)
    else:
        circ_metrics = []

    # Filter valid sickle metrics
    valid_sickle = [m for m in sickle_metrics if not m.get("error")]

    def avg(lst, key):
        vals = [m[key] for m in lst if key in m and m[key] is not None]
        return round(sum(vals) / len(vals), 2) if vals else 0

    def med(lst, key):
        vals = sorted([m[key] for m in lst if key in m and m[key] is not None])
        if not vals:
            return 0
        return round(vals[len(vals) // 2], 2)

    # Comparison table
    metrics_to_compare = [
        ("Laplacian variance", "laplacian_variance"),
        ("Otsu threshold", "otsu_threshold"),
        ("Significant contours", "significant_contours"),
        ("Foreground %", "foreground_pct"),
        ("Mean R", "mean_R"),
        ("Mean G", "mean_G"),
        ("Mean B", "mean_B"),
        ("Width", "width"),
        ("Height", "height"),
    ]

    print(f"\n  {'Metric':<24s}{'Accepted Normal':>17s}{'Src Circular':>14s}{'Rejected Sickle':>17s}{'Diff (N-S)':>12s}")
    print(f"  {'─' * 82}")

    comparison_data = {}
    for label, key in metrics_to_compare:
        n_avg = avg(normal_metrics, key)
        c_avg = avg(circ_metrics, key)
        s_avg = avg(valid_sickle, key)
        diff = round(n_avg - s_avg, 2)
        print(f"  {label:<24s}{n_avg:>17.2f}{c_avg:>14.2f}{s_avg:>17.2f}{diff:>+12.2f}")
        comparison_data[key] = {
            "accepted_normal_avg": n_avg,
            "source_circular_avg": c_avg,
            "rejected_sickle_avg": s_avg,
            "difference": diff,
        }

    # Distribution of key metrics for sickle images
    print(f"\n  ── REJECTED SICKLE: Laplacian Variance Distribution ──")
    lap_vals = sorted([m["laplacian_variance"] for m in valid_sickle])
    if lap_vals:
        buckets = [(0, 5), (5, 10), (10, 15), (15, 30), (30, 50), (50, 100), (100, 500), (500, 99999)]
        for lo, hi in buckets:
            cnt = sum(1 for v in lap_vals if lo <= v < hi)
            bar = "█" * (cnt // 2)
            label = f"{lo}-{hi}" if hi < 99999 else f"{lo}+"
            print(f"    {label:>8s}: {cnt:>4d}  {bar}")

    print(f"\n  ── REJECTED SICKLE: Significant Contour Distribution ──")
    cnt_vals = [m["significant_contours"] for m in valid_sickle]
    for n in range(max(cnt_vals) + 1 if cnt_vals else 0):
        cnt = sum(1 for v in cnt_vals if v == n)
        bar = "█" * (cnt // 2)
        print(f"    {n} contours: {cnt:>4d}  {bar}")

    print(f"\n  ── REJECTED SICKLE: Foreground % Distribution ──")
    fg_vals = sorted([m["foreground_pct"] for m in valid_sickle])
    if fg_vals:
        fg_buckets = [(0, 5), (5, 10), (10, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
        for lo, hi in fg_buckets:
            cnt = sum(1 for v in fg_vals if lo <= v < hi)
            bar = "█" * (cnt // 2)
            print(f"    {lo:>2d}-{hi:>3d}%: {cnt:>4d}  {bar}")

    # Show a few individual examples
    print(f"\n  ── SAMPLE REJECTED SICKLE IMAGES (first 10) ──")
    print(f"  {'Filename':<18s}{'Dims':>10s}{'Lap.Var':>9s}{'Otsu':>7s}{'Cont':>6s}{'FG%':>7s}{'Reason'}")
    print(f"  {'─' * 80}")
    for m in valid_sickle[:10]:
        dims = f"{m['width']}x{m['height']}"
        reasons = ", ".join(m.get("rejection_reasons", []))
        print(f"  {m['filename']:<18s}{dims:>10s}{m['laplacian_variance']:>9.1f}"
              f"{m['otsu_threshold']:>7.1f}{m['significant_contours']:>6d}"
              f"{m['foreground_pct']:>7.1f}  {reasons}")

    return comparison_data, normal_metrics, circ_metrics, valid_sickle


# ═══════════════════════════════════════════════════════════════
#  STEP 3 — Visual diagnosis grid
# ═══════════════════════════════════════════════════════════════

def step3_visual_grid(normal_metrics, sickle_metrics):
    print("\n" + "=" * 80)
    print("  STEP 3: Building visual diagnosis grid")
    print("=" * 80)

    CELL = 128
    PAD = 4
    TITLE_H = 22
    LABEL_H = 30

    # Select samples
    accepted_normals = [m for m in normal_metrics if not m.get("error")][:5]
    rejected_sickle = [m for m in sickle_metrics if not m.get("error")]

    # Row 1: 5 accepted normals with Laplacian
    # Row 2: 5 rejected sickle with Laplacian + reason
    # Row 3: 5 more rejected sickle with contour count + fg%
    # Row 4: 3 rejected sickle side-by-side: original | Otsu mask | contours drawn

    row1_items = accepted_normals[:5]
    row2_items = rejected_sickle[:5]
    row3_items = rejected_sickle[5:10] if len(rejected_sickle) > 5 else rejected_sickle[:5]
    row4_items = rejected_sickle[:3]

    COLS = 5
    ROW4_COLS = 9  # 3 images × 3 views each
    total_w = PAD + max(COLS, ROW4_COLS) * (CELL + PAD)

    # Calculate height
    row_h = TITLE_H + CELL + LABEL_H + PAD
    total_h = PAD + 4 * row_h + PAD

    canvas = np.ones((total_h, total_w, 3), dtype=np.uint8) * 30

    def draw_image(canvas, img_path, x, y, size=CELL):
        img = cv2.imread(str(img_path))
        if img is not None:
            resized = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
            canvas[y:y + size, x:x + size] = resized

    def draw_otsu_mask(canvas, img_path, x, y, size=CELL):
        img = cv2.imread(str(img_path))
        if img is None:
            return
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        mask_bgr = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        resized = cv2.resize(mask_bgr, (size, size), interpolation=cv2.INTER_NEAREST)
        canvas[y:y + size, x:x + size] = resized

    def draw_contours(canvas, img_path, x, y, size=CELL):
        img = cv2.imread(str(img_path))
        if img is None:
            return
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = h * w * CONTOUR_AREA_PCT
        vis = img.copy()
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                cv2.drawContours(vis, [cnt], -1, (0, 0, 255), 2)  # red = significant
            else:
                cv2.drawContours(vis, [cnt], -1, (128, 128, 128), 1)  # gray = insignificant
        resized = cv2.resize(vis, (size, size), interpolation=cv2.INTER_AREA)
        canvas[y:y + size, x:x + size] = resized

    y = PAD

    # ── Row 1: Accepted normals ──
    cv2.putText(canvas, "ACCEPTED Normal — Laplacian variance", (PAD + 4, y + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 0), 1, cv2.LINE_AA)
    y += TITLE_H
    for col, m in enumerate(row1_items):
        x = PAD + col * (CELL + PAD)
        draw_image(canvas, m["path"], x, y)
        label = f"Lap={m['laplacian_variance']:.0f}"
        cv2.putText(canvas, label, (x + 2, y + CELL + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(canvas, m["filename"][:16], (x + 2, y + CELL + 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.26, (160, 160, 160), 1, cv2.LINE_AA)
    y += CELL + LABEL_H + PAD

    # ── Row 2: Rejected sickle with blur + reason ──
    cv2.putText(canvas, "REJECTED Sickle — Laplacian + Reason", (PAD + 4, y + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 255), 1, cv2.LINE_AA)
    y += TITLE_H
    for col, m in enumerate(row2_items):
        x = PAD + col * (CELL + PAD)
        draw_image(canvas, m["path"], x, y)
        reasons = ",".join(m.get("rejection_reasons", []))[:20]
        cv2.putText(canvas, f"Lap={m['laplacian_variance']:.0f}", (x + 2, y + CELL + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1, cv2.LINE_AA)
        cv2.putText(canvas, reasons, (x + 2, y + CELL + 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.26, (0, 140, 255), 1, cv2.LINE_AA)
    y += CELL + LABEL_H + PAD

    # ── Row 3: Rejected sickle with contour + fg% ──
    cv2.putText(canvas, "REJECTED Sickle — Contours + Foreground%", (PAD + 4, y + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 255), 1, cv2.LINE_AA)
    y += TITLE_H
    for col, m in enumerate(row3_items):
        x = PAD + col * (CELL + PAD)
        draw_image(canvas, m["path"], x, y)
        cv2.putText(canvas, f"Cont={m['significant_contours']} FG={m['foreground_pct']:.0f}%",
                    (x + 2, y + CELL + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.30, (0, 140, 255), 1, cv2.LINE_AA)
        cv2.putText(canvas, m["filename"][:16], (x + 2, y + CELL + 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.26, (160, 160, 160), 1, cv2.LINE_AA)
    y += CELL + LABEL_H + PAD

    # ── Row 4: Side-by-side diagnosis (original | mask | contours) ──
    cv2.putText(canvas, "DIAGNOSIS: Original | Otsu Mask | Contours (red=significant)", (PAD + 4, y + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 200, 255), 1, cv2.LINE_AA)
    y += TITLE_H
    for idx, m in enumerate(row4_items):
        base_x = PAD + idx * 3 * (CELL + PAD)
        # Original
        draw_image(canvas, m["path"], base_x, y)
        cv2.putText(canvas, "Original", (base_x + 2, y + CELL + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.30, (200, 200, 200), 1, cv2.LINE_AA)
        # Otsu mask
        draw_otsu_mask(canvas, m["path"], base_x + CELL + PAD, y)
        cv2.putText(canvas, "Otsu Mask", (base_x + CELL + PAD + 2, y + CELL + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.30, (200, 200, 200), 1, cv2.LINE_AA)
        # Contours
        draw_contours(canvas, m["path"], base_x + 2 * (CELL + PAD), y)
        cv2.putText(canvas, f"Contours({m['significant_contours']}sig)",
                    (base_x + 2 * (CELL + PAD) + 2, y + CELL + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.30, (0, 0, 255), 1, cv2.LINE_AA)

    grid_path = BASE / "diagnose_rejected_sickle_grid.png"
    cv2.imwrite(str(grid_path), canvas, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    print(f"  ✓ Saved: {grid_path}")
    return grid_path


# ═══════════════════════════════════════════════════════════════
#  STEP 4 — Recommendation
# ═══════════════════════════════════════════════════════════════

def step4_recommendation(sickle_metrics, reason_counts, comparison_data):
    print("\n" + "=" * 80)
    print("  STEP 4: DIAGNOSIS & RECOMMENDATION")
    print("=" * 80)

    valid = [m for m in sickle_metrics if not m.get("error")]
    total = len(valid)
    if total == 0:
        print("  No valid sickle images to analyze.")
        return {}

    # Count each flag
    multi_count = sum(1 for m in valid if "MULTI_CELL" in m.get("rejection_reasons", []))
    blur_count = sum(1 for m in valid if "EXTREME_BLUR" in m.get("rejection_reasons", []))
    empty_count = sum(1 for m in valid if "TOO_EMPTY" in m.get("rejection_reasons", []))
    pass_count = sum(1 for m in valid if not m.get("would_reject", True))

    # Compute what would happen with adjusted thresholds
    print(f"\n  ── ROOT CAUSE ANALYSIS ──\n")

    # Primary cause
    causes = []
    if multi_count > total * 0.3:
        causes.append("MULTI_CELL")
    if blur_count > total * 0.3:
        causes.append("EXTREME_BLUR")
    if empty_count > total * 0.3:
        causes.append("TOO_EMPTY")

    for cause in causes:
        if cause == "MULTI_CELL":
            print(f"  🔴 MULTI_CELL ({multi_count}/{total} = {multi_count/total*100:.0f}%)")
            print(f"     The contour-based multi-cell detector is BIASED against elongated shapes.")
            print(f"     Sickle cells are long and thin — Otsu thresholding on these images")
            print(f"     creates fragmented foreground with multiple disconnected regions,")
            print(f"     each counting as a separate 'cell' contour.")
            print(f"     This is a FALSE POSITIVE — the image has ONE cell, detected as many.")
        elif cause == "EXTREME_BLUR":
            print(f"  🔴 EXTREME_BLUR ({blur_count}/{total} = {blur_count/total*100:.0f}%)")
            print(f"     The Laplacian blur threshold of {BLUR_CRITICAL} is too strict for")
            print(f"     the erythrocytesIDB staining protocol, which has softer edges.")
            s_avg = comparison_data.get("laplacian_variance", {}).get("rejected_sickle_avg", 0)
            print(f"     Average Laplacian for rejected sickle: {s_avg:.1f}")
        elif cause == "TOO_EMPTY":
            print(f"  🔴 TOO_EMPTY ({empty_count}/{total} = {empty_count/total*100:.0f}%)")
            print(f"     The erythrocytesIDB staining creates different foreground/background")
            print(f"     contrast than our dataset. Otsu thresholding gives wrong segmentation.")

    # Simulate adjusted thresholds
    print(f"\n  ── THRESHOLD SIMULATION ──\n")
    simulations = [
        ("Original thresholds", BLUR_CRITICAL, True, FOREGROUND_MIN_PCT),
        ("Disable MULTI_CELL check", BLUR_CRITICAL, False, FOREGROUND_MIN_PCT),
        ("Blur < 10 + disable MULTI_CELL", 10.0, False, FOREGROUND_MIN_PCT),
        ("Blur < 8 + disable MULTI_CELL", 8.0, False, FOREGROUND_MIN_PCT),
        ("Blur < 5 + disable MULTI_CELL", 5.0, False, FOREGROUND_MIN_PCT),
        ("Disable ALL checks (keep all)", 0.0, False, 0.0),
    ]

    print(f"  {'Configuration':<38s}{'Pass':>6s}{'Reject':>8s}{'Pass%':>8s}")
    print(f"  {'─' * 58}")

    best_config = None
    for label, blur_t, multi_check, fg_min in simulations:
        would_pass = 0
        for m in valid:
            reject = False
            if multi_check and m.get("significant_contours", 0) > 1:
                reject = True
            if m.get("foreground_pct", 100) < fg_min:
                reject = True
            if m.get("laplacian_variance", 999) < blur_t:
                reject = True
            if not reject:
                would_pass += 1

        would_reject = total - would_pass
        pct = (would_pass / total * 100)
        marker = ""
        if would_pass > total * 0.8 and best_config is None:
            best_config = label
            marker = " ◀ RECOMMENDED"
        print(f"  {label:<38s}{would_pass:>6d}{would_reject:>8d}{pct:>7.1f}%{marker}")

    # Final recommendation
    print(f"\n  ╔═══════════════════════════════════════════════════════════════════╗")
    print(f"  ║  RECOMMENDED FIX                                                ║")
    print(f"  ╠═══════════════════════════════════════════════════════════════════╣")

    recommendations = []

    if multi_count > total * 0.3:
        rec = (
            "DISABLE the MULTI_CELL check for erythrocytesIDB source.\n"
            "  ║  The Otsu + contour pipeline fragments elongated cells into\n"
            "  ║  multiple pieces. This is a segmentation artifact, not real\n"
            "  ║  multi-cell detection. For external sources with different\n"
            "  ║  staining, skip this check or use a cell-count-aware approach."
        )
        print(f"  ║  1. {rec}  ║")
        recommendations.append({
            "change": "disable_multi_cell_for_external_sources",
            "reason": f"MULTI_CELL false positive rate: {multi_count/total*100:.0f}%",
            "detail": "Otsu segmentation fragments elongated cells into multiple contours",
        })

    if blur_count > total * 0.3:
        lap_vals = [m["laplacian_variance"] for m in valid]
        p25 = sorted(lap_vals)[int(len(lap_vals) * 0.25)]
        rec_threshold = max(5.0, round(p25 * 0.5, 1))
        rec = (
            f"LOWER blur threshold to {rec_threshold} for external sources.\n"
            f"  ║  Current threshold {BLUR_CRITICAL} rejects {blur_count/total*100:.0f}% of sickle images.\n"
            f"  ║  25th percentile Laplacian is {p25:.1f} — threshold of {rec_threshold} retains most."
        )
        print(f"  ║  2. {rec}  ║")
        recommendations.append({
            "change": f"lower_blur_threshold_to_{rec_threshold}",
            "reason": f"EXTREME_BLUR false positive rate: {blur_count/total*100:.0f}%",
            "current_threshold": BLUR_CRITICAL,
            "recommended_threshold": rec_threshold,
        })

    if empty_count > total * 0.3:
        rec = (
            f"LOWER foreground threshold to 5% for external sources.\n"
            f"  ║  Different staining protocols create different Otsu results."
        )
        print(f"  ║  3. {rec}  ║")
        recommendations.append({
            "change": "lower_foreground_threshold_to_5pct",
            "reason": f"TOO_EMPTY false positive rate: {empty_count/total*100:.0f}%",
        })

    print(f"  ║                                                                 ║")
    print(f"  ║  Quick fix: In build_clean_dataset.py, for erythrocytesIDB      ║")
    print(f"  ║  source, ONLY reject if Laplacian < 5 (extreme noise).          ║")
    print(f"  ║  Skip MULTI_CELL and TOO_EMPTY checks entirely for this source. ║")
    print(f"  ╚═══════════════════════════════════════════════════════════════════╝")

    return {
        "primary_causes": causes,
        "multi_cell_count": multi_count,
        "extreme_blur_count": blur_count,
        "too_empty_count": empty_count,
        "would_pass_with_original": pass_count,
        "recommendations": recommendations,
    }


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 80)
    print("  LabMind AI — Diagnose Rejected Sickle Cells")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("═" * 80)

    # Step 1
    sickle_metrics, reason_counts = step1_analyze_rejections()
    if not sickle_metrics:
        print("\n  No data to analyze. Exiting.")
        return

    # Step 2
    comparison_data, normal_metrics, circ_metrics, valid_sickle = \
        step2_compare_metrics(sickle_metrics)

    # Step 3
    try:
        grid_path = step3_visual_grid(normal_metrics, valid_sickle)
    except Exception as e:
        print(f"  ⚠ Could not build grid: {e}")
        grid_path = None

    # Step 4
    rec = step4_recommendation(sickle_metrics, reason_counts, comparison_data)

    # Save report
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sickle_metrics": sickle_metrics,
        "comparison": comparison_data,
        "recommendation": rec,
    }

    report_path = BASE / "diagnose_rejected_sickle_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n  ✓ Report saved to: {report_path}")
    print("═" * 80 + "\n")


if __name__ == "__main__":
    main()
