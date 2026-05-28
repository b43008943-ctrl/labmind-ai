"""
LabMind AI — Crop Quality Deep Analysis
==========================================
Re-analyzes crop_quality_audit_report.json with smarter, calibrated
thresholds to separate REAL quality problems from false alarms.

Does NOT re-scan images — works entirely from the existing audit JSON.

Usage:
    python crop_quality_deep_analysis.py

Output:
    - crop_quality_deep_analysis.json   (actionable file lists)
    - Console report with tables
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
AUDIT_REPORT = BASE / "crop_quality_audit_report.json"
OUTPUT_PATH = BASE / "crop_quality_deep_analysis.json"

MIN_PER_CLASS = 500


# ═══════════════════════════════════════════════════════════════
#  Load Audit Data
# ═══════════════════════════════════════════════════════════════

def load_audit():
    if not AUDIT_REPORT.exists():
        print(f"  ✗ ERROR: {AUDIT_REPORT} not found.")
        print(f"    Run crop_quality_audit.py first.")
        sys.exit(1)

    with open(AUDIT_REPORT, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Flatten all file results into a single list, tagged with directory label
    all_files = []
    for dir_entry in data.get("directories", []):
        label = dir_entry.get("label", "unknown")
        for file_entry in dir_entry.get("files", []):
            file_entry["_dir_label"] = label
            all_files.append(file_entry)

    print(f"  Loaded {len(all_files)} file records from audit report")
    return data, all_files


# ═══════════════════════════════════════════════════════════════
#  PART 1 — Threshold Sensitivity Analysis
# ═══════════════════════════════════════════════════════════════

def threshold_sensitivity(all_files: list):
    print("\n" + "=" * 90)
    print("  PART 1: BLUR THRESHOLD SENSITIVITY ANALYSIS")
    print("=" * 90)

    thresholds = [10, 15, 20, 30, 50, 80, 100, 150]

    # Gather laplacian values per class
    normal_vars = []
    sickle_vars = []
    all_vars = []

    for f in all_files:
        blur = f.get("blur", {})
        lap = blur.get("laplacian_variance")
        if lap is None:
            continue
        ec = f.get("expected_class", "unknown")
        all_vars.append(lap)
        if ec == "normal":
            normal_vars.append(lap)
        elif ec == "sickle":
            sickle_vars.append(lap)

    total = len(all_vars)
    total_n = len(normal_vars)
    total_s = len(sickle_vars)

    # Stats
    if all_vars:
        all_vars_sorted = sorted(all_vars)
        print(f"\n  Laplacian variance statistics across {total} crops:")
        print(f"    Min:    {min(all_vars):.1f}")
        print(f"    P10:    {all_vars_sorted[int(len(all_vars_sorted)*0.10)]:.1f}")
        print(f"    P25:    {all_vars_sorted[int(len(all_vars_sorted)*0.25)]:.1f}")
        print(f"    Median: {all_vars_sorted[len(all_vars_sorted)//2]:.1f}")
        print(f"    P75:    {all_vars_sorted[int(len(all_vars_sorted)*0.75)]:.1f}")
        print(f"    P90:    {all_vars_sorted[int(len(all_vars_sorted)*0.90)]:.1f}")
        print(f"    Max:    {max(all_vars):.1f}")

    # Table
    print(f"\n  {'Threshold':<12s}{'Normal':<16s}{'Sickle':<16s}{'Total':<14s}{'% of total':<12s}")
    print(f"  {'─'*68}")

    for t in thresholds:
        n_count = sum(1 for v in normal_vars if v < t)
        s_count = sum(1 for v in sickle_vars if v < t)
        t_count = sum(1 for v in all_vars if v < t)
        pct = (t_count / total * 100) if total > 0 else 0
        marker = " ◀ current" if t == 50 else ""
        n_ratio = f"{n_count}/{total_n}"
        s_ratio = f"{s_count}/{total_s}"
        t_ratio = f"{t_count}/{total}"
        print(f"  var < {t:<5d}{n_ratio:<14s}{s_ratio:<14s}{t_ratio:<12s}{pct:>5.1f}%{marker}")

    # Also show how many are ABOVE each threshold (i.e., would pass)
    print(f"\n  {'Threshold':<12s}{'Would PASS':<14s}{'% passing':<12s}")
    print(f"  {'─'*38}")
    for t in thresholds:
        passing = sum(1 for v in all_vars if v >= t)
        pct = (passing / total * 100) if total > 0 else 0
        print(f"  var >= {t:<4d}{passing:>6d}         {pct:>5.1f}%")

    return all_vars, normal_vars, sickle_vars


# ═══════════════════════════════════════════════════════════════
#  PART 2 — Adjusted Quality Classification
# ═══════════════════════════════════════════════════════════════

def classify_adjusted(f: dict) -> str:
    """
    Assign CRITICAL / POOR / ACCEPTABLE / GOOD using calibrated thresholds.

    Key insight: BORDER_CUT alone is NOT a disqualifier for tight cell crops.
    """
    # Handle error/unreadable files
    if f.get("verdict") == "ERROR" or f.get("error"):
        return "CRITICAL"

    blur = f.get("blur", {})
    multi = f.get("multi_cell", {})
    foreground = f.get("foreground", {})
    size_check = f.get("size_check", {})
    lap_var = blur.get("laplacian_variance", 0)
    is_multi = multi.get("is_multi_cell", False)
    is_empty = foreground.get("is_too_empty", False)
    is_full = foreground.get("is_too_full", False)
    is_wrong_size = size_check.get("is_wrong_size", False)

    # ── CRITICAL: definitely bad ──
    if is_multi:
        return "CRITICAL"
    if is_empty:
        return "CRITICAL"
    if is_full:
        return "CRITICAL"
    if lap_var < 15:
        return "CRITICAL"

    # ── POOR: probably bad ──
    if lap_var < 30:
        return "POOR"
    if is_wrong_size:
        return "POOR"

    # ── GOOD: high quality ──
    if lap_var >= 50 and not is_wrong_size:
        return "GOOD"

    # ── ACCEPTABLE: usable despite imperfections ──
    return "ACCEPTABLE"


def run_adjusted_classification(all_files: list):
    print("\n" + "=" * 90)
    print("  PART 2: ADJUSTED QUALITY CLASSIFICATION")
    print("=" * 90)
    print(f"\n  Adjusted thresholds:")
    print(f"    CRITICAL: multi_cell OR too_empty OR too_full OR blur_var < 15")
    print(f"    POOR:     blur_var 15–30 OR wrong_size")
    print(f"    ACCEPTABLE: blur_var 30–50, border_cut OK")
    print(f"    GOOD:     blur_var >= 50, no multi/empty/size issues")

    # Classify every file
    for f in all_files:
        f["_adjusted_verdict"] = classify_adjusted(f)

    # Group by directory and class
    by_dir = defaultdict(list)
    for f in all_files:
        by_dir[f["_dir_label"]].append(f)

    # Build file lists
    critical_list = []
    poor_list = []
    acceptable_list = []
    good_list = []

    for f in all_files:
        v = f["_adjusted_verdict"]
        path = f.get("path", f.get("filename", "unknown"))
        if v == "CRITICAL":
            critical_list.append(path)
        elif v == "POOR":
            poor_list.append(path)
        elif v == "ACCEPTABLE":
            acceptable_list.append(path)
        elif v == "GOOD":
            good_list.append(path)

    return by_dir, critical_list, poor_list, acceptable_list, good_list


# ═══════════════════════════════════════════════════════════════
#  PART 3 — Print Report
# ═══════════════════════════════════════════════════════════════

def print_report(all_files, by_dir, critical_list, poor_list, acceptable_list, good_list):
    print("\n" + "=" * 100)
    print("  PART 3: ADJUSTED QUALITY REPORT")
    print("=" * 100)

    # Per-directory table
    header = (
        f"  {'Directory':<42s}"
        f"{'Total':>6s}"
        f"{'CRITICAL':>10s}"
        f"{'POOR':>7s}"
        f"{'ACCEPT':>8s}"
        f"{'GOOD':>7s}"
        f"{'Usable':>8s}"
        f"{'Usable%':>9s}"
    )
    print(f"\n{header}")
    print(f"  {'─' * 95}")

    dir_order = [
        "dataset_v1_2class/train/normal",
        "dataset_v1_2class/train/sickle",
        "dataset_v1_2class/val/normal",
        "dataset_v1_2class/val/sickle",
        "dataset_robust/processed/normal",
        "dataset_robust/processed/sickle",
        "validation_cells/normal",
        "validation_cells/sickle",
    ]

    # Include any dirs in by_dir not already in dir_order
    for k in by_dir:
        if k not in dir_order:
            dir_order.append(k)

    grand_total = 0
    grand_critical = 0
    grand_poor = 0
    grand_acceptable = 0
    grand_good = 0

    for dir_label in dir_order:
        files = by_dir.get(dir_label, [])
        if not files:
            continue
        total = len(files)
        critical = sum(1 for f in files if f["_adjusted_verdict"] == "CRITICAL")
        poor = sum(1 for f in files if f["_adjusted_verdict"] == "POOR")
        acceptable = sum(1 for f in files if f["_adjusted_verdict"] == "ACCEPTABLE")
        good = sum(1 for f in files if f["_adjusted_verdict"] == "GOOD")
        usable = acceptable + good
        usable_pct = (usable / total * 100) if total > 0 else 0

        print(f"  {dir_label:<42s}{total:>6d}{critical:>10d}{poor:>7d}"
              f"{acceptable:>8d}{good:>7d}{usable:>8d}{usable_pct:>8.1f}%")

        grand_total += total
        grand_critical += critical
        grand_poor += poor
        grand_acceptable += acceptable
        grand_good += good

    grand_usable = grand_acceptable + grand_good
    grand_usable_pct = (grand_usable / grand_total * 100) if grand_total > 0 else 0

    print(f"  {'─' * 95}")
    print(f"  {'TOTAL':<42s}{grand_total:>6d}{grand_critical:>10d}{grand_poor:>7d}"
          f"{grand_acceptable:>8d}{grand_good:>7d}{grand_usable:>8d}{grand_usable_pct:>8.1f}%")

    # ── Usable by class ──
    # Only count from training directories (dataset_v1_2class + dataset_robust/processed)
    # Validation cells are not training data
    training_dirs_normal = [
        "dataset_v1_2class/train/normal",
        "dataset_v1_2class/val/normal",
        "dataset_robust/processed/normal",
    ]
    training_dirs_sickle = [
        "dataset_v1_2class/train/sickle",
        "dataset_v1_2class/val/sickle",
        "dataset_robust/processed/sickle",
    ]

    # But dataset_robust/processed is a copy of dataset_v1_2class, so count unique files
    # For now, count from dataset_v1_2class only (avoid double-counting)
    primary_normal_dirs = [
        "dataset_v1_2class/train/normal",
        "dataset_v1_2class/val/normal",
    ]
    primary_sickle_dirs = [
        "dataset_v1_2class/train/sickle",
        "dataset_v1_2class/val/sickle",
    ]

    usable_normal = 0
    usable_sickle = 0
    for f in all_files:
        v = f["_adjusted_verdict"]
        if v not in ("ACCEPTABLE", "GOOD"):
            continue
        dl = f["_dir_label"]
        ec = f.get("expected_class", "unknown")
        if dl in primary_normal_dirs and ec == "normal":
            usable_normal += 1
        elif dl in primary_sickle_dirs and ec == "sickle":
            usable_sickle += 1

    normal_gap = max(0, MIN_PER_CLASS - usable_normal)
    sickle_gap = max(0, MIN_PER_CLASS - usable_sickle)
    is_sufficient = usable_normal >= MIN_PER_CLASS and usable_sickle >= MIN_PER_CLASS

    print(f"\n  ── USABLE TRAINING DATA (dataset_v1_2class only, de-duplicated) ──")
    print(f"    Usable normal:  {usable_normal}")
    print(f"    Usable sickle:  {usable_sickle}")
    print(f"    Total usable:   {usable_normal + usable_sickle}")

    print(f"\n  ── GAP TO MINIMUM ({MIN_PER_CLASS}/class) ──")
    print(f"    Normal gap:  {normal_gap} more needed"
          + (" ✓ MET" if normal_gap == 0 else " ⚠ BELOW"))
    print(f"    Sickle gap:  {sickle_gap} more needed"
          + (" ✓ MET" if sickle_gap == 0 else " ⚠ BELOW"))
    print(f"    Sufficient:  {'YES' if is_sufficient else 'NO ⚠'}")

    # ── CRITICAL files to remove ──
    print(f"\n  ── CRITICAL FILES (must remove from training): {len(critical_list)} ──")

    # Group criticals by reason
    critical_reasons = defaultdict(list)
    for f in all_files:
        if f["_adjusted_verdict"] != "CRITICAL":
            continue
        fname = f.get("filename", "unknown")
        reasons = []
        if f.get("multi_cell", {}).get("is_multi_cell"):
            reasons.append("MULTI_CELL")
        if f.get("foreground", {}).get("is_too_empty"):
            reasons.append("TOO_EMPTY")
        if f.get("foreground", {}).get("is_too_full"):
            reasons.append("TOO_FULL")
        lap = f.get("blur", {}).get("laplacian_variance", 0)
        if lap < 15:
            reasons.append(f"EXTREME_BLUR(var={lap:.1f})")
        if f.get("error"):
            reasons.append("UNREADABLE")
        key = " + ".join(reasons) if reasons else "UNKNOWN"
        critical_reasons[key].append(fname)

    for reason, files in sorted(critical_reasons.items(), key=lambda x: -len(x[1])):
        print(f"    {reason}: {len(files)} files")
        for fn in files[:5]:
            print(f"      - {fn}")
        if len(files) > 5:
            print(f"      ... and {len(files) - 5} more")

    # ── POOR files ──
    print(f"\n  ── POOR FILES (should review manually): {len(poor_list)} ──")
    poor_reasons = defaultdict(int)
    for f in all_files:
        if f["_adjusted_verdict"] != "POOR":
            continue
        lap = f.get("blur", {}).get("laplacian_variance", 0)
        is_wrong = f.get("size_check", {}).get("is_wrong_size", False)
        if 15 <= lap < 30:
            poor_reasons["MODERATE_BLUR (15<=var<30)"] += 1
        if is_wrong:
            poor_reasons["WRONG_SIZE"] += 1

    for reason, count in sorted(poor_reasons.items(), key=lambda x: -x[1]):
        print(f"    {reason}: {count} files")

    # ── Comparison with original thresholds ──
    orig_good = sum(1 for f in all_files if f.get("verdict") == "GOOD")
    orig_quest = sum(1 for f in all_files if f.get("verdict") == "QUESTIONABLE")
    orig_bad = sum(1 for f in all_files if f.get("verdict") == "BAD")

    print(f"\n  ── ORIGINAL vs ADJUSTED COMPARISON ──")
    print(f"    {'Category':<20s}{'Original':>10s}{'Adjusted':>10s}{'Change':>10s}")
    print(f"    {'─' * 48}")
    print(f"    {'Unusable':<20s}{orig_bad:>10d}{grand_critical:>10d}"
          f"{grand_critical - orig_bad:>+10d}")
    print(f"    {'Needs review':<20s}{orig_quest:>10d}{grand_poor:>10d}"
          f"{grand_poor - orig_quest:>+10d}")
    print(f"    {'Usable':<20s}{orig_good:>10d}{grand_usable:>10d}"
          f"{grand_usable - orig_good:>+10d}")

    return {
        "total_scanned": grand_total,
        "critical_count": grand_critical,
        "poor_count": grand_poor,
        "acceptable_count": grand_acceptable,
        "good_count": grand_good,
        "usable_total": grand_usable,
        "usable_normal": usable_normal,
        "usable_sickle": usable_sickle,
        "is_sufficient": is_sufficient,
        "normal_gap_to_500": normal_gap,
        "sickle_gap_to_500": sickle_gap,
    }


# ═══════════════════════════════════════════════════════════════
#  PART 4 — Save Actionable Output
# ═══════════════════════════════════════════════════════════════

def save_output(critical_list, poor_list, acceptable_list, good_list, summary, all_files):
    print("\n" + "=" * 90)
    print("  PART 4: SAVING ACTIONABLE OUTPUT")
    print("=" * 90)

    # Build detailed critical entries (with reasons)
    critical_detailed = []
    for f in all_files:
        if f["_adjusted_verdict"] != "CRITICAL":
            continue
        reasons = []
        if f.get("multi_cell", {}).get("is_multi_cell"):
            reasons.append("MULTI_CELL")
        if f.get("foreground", {}).get("is_too_empty"):
            reasons.append("TOO_EMPTY")
        if f.get("foreground", {}).get("is_too_full"):
            reasons.append("TOO_FULL")
        lap = f.get("blur", {}).get("laplacian_variance", 0)
        if lap < 15:
            reasons.append("EXTREME_BLUR")
        if f.get("error"):
            reasons.append("UNREADABLE")

        critical_detailed.append({
            "path": f.get("path", ""),
            "filename": f.get("filename", ""),
            "expected_class": f.get("expected_class", "unknown"),
            "directory": f.get("_dir_label", "unknown"),
            "reasons": reasons,
            "laplacian_variance": f.get("blur", {}).get("laplacian_variance"),
            "significant_contours": f.get("multi_cell", {}).get("significant_contours"),
            "foreground_pct": f.get("foreground", {}).get("foreground_pct"),
        })

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "adjusted_thresholds": {
            "critical_blur_max": 15,
            "poor_blur_max": 30,
            "good_blur_min": 50,
            "border_cut_disqualifies": False,
            "multi_cell_disqualifies": True,
            "empty_disqualifies": True,
        },
        "summary": summary,
        "critical_remove_list": critical_list,
        "critical_detailed": critical_detailed,
        "poor_review_list": poor_list,
        "acceptable_files": acceptable_list,
        "good_files": good_list,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n  ✓ Saved to: {OUTPUT_PATH}")
    print(f"    critical_remove_list: {len(critical_list)} files")
    print(f"    poor_review_list:     {len(poor_list)} files")
    print(f"    acceptable_files:     {len(acceptable_list)} files")
    print(f"    good_files:           {len(good_list)} files")


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 90)
    print("  LabMind AI — Crop Quality Deep Analysis")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("═" * 90)

    data, all_files = load_audit()

    # Part 1
    threshold_sensitivity(all_files)

    # Part 2
    by_dir, critical_list, poor_list, acceptable_list, good_list = \
        run_adjusted_classification(all_files)

    # Part 3
    summary = print_report(all_files, by_dir, critical_list, poor_list,
                           acceptable_list, good_list)

    # Part 4
    save_output(critical_list, poor_list, acceptable_list, good_list, summary, all_files)

    print("\n" + "═" * 90)
    print("  DONE — Use critical_remove_list to clean training data before retraining")
    print("═" * 90 + "\n")


if __name__ == "__main__":
    main()
