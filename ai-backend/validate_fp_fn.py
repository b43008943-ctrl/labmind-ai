"""
FP/FN Validation Script — V1Provider Sickle Decision Logic
Runs against normal and sickle validation smears to verify threshold rebalance.
"""
import os
import sys
import glob

# Ensure the app package is importable
sys.path.insert(0, os.path.dirname(__file__))

from app.providers.ai_provider_v1 import V1Provider

NORMAL_DIR = os.path.join(os.path.dirname(__file__), "validation_smears", "normal")
SICKLE_DIR = os.path.join(os.path.dirname(__file__), "validation_smears", "sickle")

def run_validation():
    provider = V1Provider()
    print(f"Classifier mode: {provider._classifier_mode}")
    print("=" * 70)

    # ── Normal smears ──
    normal_files = sorted(glob.glob(os.path.join(NORMAL_DIR, "*.jpg")))
    if not normal_files:
        normal_files = sorted(glob.glob(os.path.join(NORMAL_DIR, "*.jpg.jpg")))
    print(f"\n{'NORMAL SMEARS':=^70}")
    print(f"Found {len(normal_files)} normal smear(s)\n")

    normal_fp = 0
    for img_path in normal_files:
        name = os.path.basename(img_path)
        try:
            result = provider.analyze(img_path)
            sickle = result.get("sickle_count", 0)
            total = result.get("total_cells", 0)
            normal = result.get("normal_count", 0)
            qs = result.get("quality_status", "?")
            fp_flag = " *** FALSE POSITIVE ***" if sickle > 0 else ""
            if sickle > 0:
                normal_fp += 1
            print(f"  {name:<30s}  total={total:<4d}  normal={normal:<4d}  sickle={sickle:<4d}  quality={qs}{fp_flag}")
        except Exception as e:
            print(f"  {name:<30s}  ERROR: {e}")

    # ── Sickle smears ──
    sickle_files = sorted(glob.glob(os.path.join(SICKLE_DIR, "*.jpg")))
    if not sickle_files:
        sickle_files = sorted(glob.glob(os.path.join(SICKLE_DIR, "*.jpg.jpg")))
    print(f"\n{'SICKLE SMEARS':=^70}")
    print(f"Found {len(sickle_files)} sickle smear(s)\n")

    sickle_fn = 0
    for img_path in sickle_files:
        name = os.path.basename(img_path)
        try:
            result = provider.analyze(img_path)
            sickle = result.get("sickle_count", 0)
            total = result.get("total_cells", 0)
            normal = result.get("normal_count", 0)
            pct = result.get("sickle_percentage", 0.0)
            qs = result.get("quality_status", "?")
            fn_flag = " *** FALSE NEGATIVE ***" if sickle == 0 else ""
            if sickle == 0:
                sickle_fn += 1
            print(f"  {name:<30s}  total={total:<4d}  normal={normal:<4d}  sickle={sickle:<4d}  pct={pct:5.1f}%  quality={qs}{fn_flag}")
        except Exception as e:
            print(f"  {name:<30s}  ERROR: {e}")

    # ── Summary ──
    print(f"\n{'SUMMARY':=^70}")
    print(f"  Normal smears tested:  {len(normal_files)}")
    print(f"  False positives:       {normal_fp}")
    print(f"  Sickle smears tested:  {len(sickle_files)}")
    print(f"  False negatives:       {sickle_fn}")

    if normal_fp == 0 and sickle_fn == 0:
        print("\n  ✓ PASS — No FP on normal, no FN on sickle")
    else:
        if normal_fp > 0:
            print(f"\n  ✗ FAIL — {normal_fp} normal smear(s) had false-positive sickle detections")
        if sickle_fn > 0:
            print(f"\n  ✗ FAIL — {sickle_fn} sickle smear(s) had zero sickle detections (false negative)")

    print("=" * 70)
    return normal_fp, sickle_fn

if __name__ == "__main__":
    run_validation()
