"""
LabMind AI — Purge Contamination and Retrain (v2)
=================================================
1. Identifies and removes validation smear crops from training sets.
2. Re-augments and re-splits the dataset safely.
3. Retrains CellClassifierCNN robust model (v2).
4. Runs full regression comparison.
"""

import os
import json
import shutil
import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

import torch
import cv2
import numpy as np

# Import local modules
import train_robust_cnn
from app.providers.ai_provider_v1 import V1Provider, CellClassifierCNN
import regression_test_robust

# Supress noisy logs
logging.getLogger("labmind.v1provider").setLevel(logging.WARNING)

random.seed(42)
np.random.seed(42)

BASE_DIR = Path(__file__).resolve().parent

BAD_IDS = [
    "normal_01", "normal_02", "normal_03", "normal_04", "normal_05",
    "sickle_01", "sickle_02", "sickle_03", "sickle_04", "sickle_05",
    "Sickle_Cell_Blood_Smear"
]

V1_DIR = BASE_DIR / "dataset_v1_2class"
CLEAN_DIR = BASE_DIR / "dataset_clean"
CONTAM_DIR = CLEAN_DIR / "contaminated"
LOG_PATH = CLEAN_DIR / "contamination_log.json"

OLD_MODEL = BASE_DIR / "cell_classifier_2class_finetuned_best.pth"
V1_MODEL = BASE_DIR / "cell_classifier_2class_robust_best.pth"
V2_MODEL = BASE_DIR / "cell_classifier_2class_robust_v2_best.pth"

AUG_TYPES = ["r90", "r180", "r270", "hflip", "bright", "dark", "blur", "hue"]
PREFIX_PRIORITY = ["orig_", "erydb_c_", "erydb_e_", "kaggle_neg_", "kaggle_pos_"]


# ═══════════════════════════════════════════════════════════════
# 1 & 2: Purge
# ═══════════════════════════════════════════════════════════════
def step_purge():
    print("\n" + "="*80)
    print("STEP 1 & 2: PURGE CONTAMINATED FILES")
    print("="*80)
    
    CONTAM_DIR.mkdir(parents=True, exist_ok=True)
    
    if V1_DIR.exists():
        print(f"\nScanning {V1_DIR.name}...")
        for f in V1_DIR.rglob("*.*"):
            if f.is_file() and any(b.lower() in f.name.lower() for b in BAD_IDS):
                print(f"  [v1 matched] {f.relative_to(BASE_DIR)}")

    purged_files = []
    print(f"\nScanning {CLEAN_DIR.name}...")
    # Include all files, if they matchBAD_IDS, move them
    for f in CLEAN_DIR.rglob("*.*"):
        if f.is_file() and any(b.lower() in f.name.lower() for b in BAD_IDS):
            if "contaminated" in f.parts:
                continue
            
            rel_path = f.relative_to(BASE_DIR)
            print(f"  [PURGING] {rel_path}")
            
            dst = CONTAM_DIR / f.name
            counter = 1
            while dst.exists():
                dst = CONTAM_DIR / f"{f.stem}_{counter}{f.suffix}"
                counter += 1
                
            shutil.move(str(f), str(dst))
            
            origin = "unknown"
            for b in BAD_IDS:
                if b.lower() in f.name.lower():
                    origin = b
                    break
            
            purged_files.append({
                "original_path": str(rel_path),
                "moved_to": str(dst.relative_to(BASE_DIR)),
                "validation_source": origin
            })
            
    # Load old log if exists to append instead of overwriting
    if LOG_PATH.exists() and purged_files:
        try:
            with open(LOG_PATH, "r") as f:
                old_log = json.load(f)
            purged_files = old_log + purged_files
        except: pass
        
    if purged_files:
        with open(LOG_PATH, "w") as out:
            json.dump(purged_files, out, indent=2)
            
    print(f"\nPurged newly found contaminated files. Total in log: {len(purged_files)}")

# ═══════════════════════════════════════════════════════════════
# 3: Rebuild splits natively
# ═══════════════════════════════════════════════════════════════
def prefix_order(f_name):
    for i, p in enumerate(PREFIX_PRIORITY):
        if f_name.startswith(p): return i
    return len(PREFIX_PRIORITY)

def augment_image(img, aug_type):
    if aug_type == "r90": return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif aug_type == "r180": return cv2.rotate(img, cv2.ROTATE_180)
    elif aug_type == "r270": return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif aug_type == "hflip": return cv2.flip(img, 1)
    elif aug_type == "bright": return cv2.convertScaleAbs(img, alpha=1.0, beta=38)
    elif aug_type == "dark": return cv2.convertScaleAbs(img, alpha=0.85, beta=0)
    elif aug_type == "blur": return cv2.GaussianBlur(img, (3, 3), 0)
    elif aug_type == "hue":
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0].astype(int) + 10) % 180
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return img

def get_base_stem(filename):
    stem = Path(filename).stem
    for aug in AUG_TYPES:
        if stem.endswith(f"_{aug}"):
            return stem[:-(len(aug) + 1)]
    return stem

def step_rebuild():
    print("\n" + "="*80)
    print("STEP 3: REBUILD SPLITS (Custom logic without prefix bug)")
    print("="*80)
    
    splits_dir = CLEAN_DIR / "splits"
    if splits_dir.exists():
        shutil.rmtree(splits_dir)
        
    # Clear out old generated augmentations to prevent accumulation
    for cls in ["normal", "sickle"]:
        d = CLEAN_DIR / cls
        if d.exists():
            for f in d.iterdir():
                if f.is_file() and any(f.stem.endswith(f"_{a}") for a in AUG_TYPES):
                    f.unlink()
                    
    # Augment
    sickle_dir = CLEAN_DIR / "sickle"
    normal_dir = CLEAN_DIR / "normal"
    
    base_sickle = [f for f in sickle_dir.iterdir() if f.suffix.lower() in [".jpg", ".png"]]
    base_normal = [f for f in normal_dir.iterdir() if f.suffix.lower() in [".jpg", ".png"]]
    print(f"Base normal count: {len(base_normal)}")
    print(f"Base sickle count: {len(base_sickle)}")
    
    base_sickle.sort(key=lambda x: prefix_order(x.name))
    target_sickle = 500
    aug_count = 0
    
    if len(base_sickle) < target_sickle:
        needed = target_sickle - len(base_sickle)
        for f in base_sickle:
            if aug_count >= needed: break
            img = cv2.imread(str(f))
            if img is None: continue
            for a in AUG_TYPES:
                if aug_count >= needed: break
                aimg = augment_image(img, a)
                out = sickle_dir / f"{f.stem}_{a}.jpg"
                cv2.imwrite(str(out), aimg, [cv2.IMWRITE_JPEG_QUALITY, 95])
                aug_count += 1
                
    curr_sickle = len([f for f in sickle_dir.iterdir() if f.is_file()])
    curr_normal = len([f for f in normal_dir.iterdir() if f.is_file()])
    
    # Normal balance if ratio < 1.0
    if curr_normal < curr_sickle:
        needed = curr_sickle - curr_normal
        n_aug_count = 0
        base_normal.sort(key=lambda x: prefix_order(x.name))
        for f in base_normal:
            if n_aug_count >= needed: break
            img = cv2.imread(str(f))
            if img is None: continue
            for a in AUG_TYPES:
                if n_aug_count >= needed: break
                aimg = augment_image(img, a)
                out = normal_dir / f"{f.stem}_{a}.jpg"
                cv2.imwrite(str(out), aimg, [cv2.IMWRITE_JPEG_QUALITY, 95])
                n_aug_count += 1
                
    print(f"Final Normal: {len(list(normal_dir.iterdir()))}")
    print(f"Final Sickle: {len(list(sickle_dir.iterdir()))}")
    
    # Split
    for split in ["train", "val", "test"]:
        for cls in ["normal", "sickle"]:
            (splits_dir / split / cls).mkdir(parents=True, exist_ok=True)
            
    for cls in ["normal", "sickle"]:
        src_dir = CLEAN_DIR / cls
        all_files = sorted([f for f in src_dir.iterdir() if f.is_file()])
        groups = defaultdict(list)
        for f in all_files:
            groups[get_base_stem(f.name)].append(f)
            
        keys = sorted(groups.keys())
        random.shuffle(keys)
        n = len(keys)
        
        t_end = int(n * 0.70)
        v_end = int(n * 0.85)
        
        for i, k in enumerate(keys):
            if i < t_end: s = "train"
            elif i < v_end: s = "val"
            else: s = "test"
            
            for f in groups[k]:
                shutil.copy2(str(f), str(splits_dir / s / cls / f.name))
                
# ═══════════════════════════════════════════════════════════════
# 4: Retrain
# ═══════════════════════════════════════════════════════════════
def step_retrain():
    print("\n" + "="*80)
    print("STEP 4: RETRAIN CNN")
    print("="*80)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    train_robust_cnn.BEST_PATH = V2_MODEL
    train_robust_cnn.FINAL_PATH = BASE_DIR / "cell_classifier_2class_robust_v2_final.pth"
    
    train_loader, val_loader, test_loader, train_ds = train_robust_cnn.create_dataloaders()
    model = train_robust_cnn.CellClassifierCNN(num_classes=2).to(device)
    
    history, best_epoch = train_robust_cnn.train(model, train_loader, val_loader, device)
    
    with open(BASE_DIR / "training_log_robust_v2.json", "w") as f:
        json.dump({"config": {
            "device": str(device), "best_epoch": best_epoch,
        }, "history": history}, f, indent=2)

# ═══════════════════════════════════════════════════════════════
# 5 & 6: Test
# ═══════════════════════════════════════════════════════════════
def run_model_on_files(weights_path, file_list):
    provider = V1Provider()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cnn = CellClassifierCNN(num_classes=2).to(device)
    cnn.load_state_dict(torch.load(weights_path, map_location=device, weights_only=True))
    cnn.eval()
    
    V1Provider._cnn_model = cnn
    V1Provider._classifier_mode = "v2_tester"
    
    results = {}
    for f in file_list:
        res = provider.analyze(str(f))
        results[f.name] = {
            "sickle_count": res["sickle_count"],
            "screening_result": res["field_interpretation"]["screening_result"]
        }
    return results

def step_test():
    print("\n" + "="*80)
    print("STEP 5 & 6: REGRESSION TEST")
    print("="*80)
    
    val_dir = BASE_DIR / "validation_smears"
    files = list(val_dir.rglob("*.jpg")) + list(val_dir.rglob("*.jpg.jpg"))
    unique_files = {f.name: f for f in files}
    
    baseline = regression_test_robust.load_baseline()
    files_to_run = [f for name, f in unique_files.items() if name in baseline]
    
    print("Running Model V1 (robust_best.pth)...")
    res_v1 = run_model_on_files(V1_MODEL, files_to_run)
    print("Running Model V2 (robust_v2_best.pth)...")
    res_v2 = run_model_on_files(V2_MODEL, files_to_run)
    
    print("\n" + "-"*90)
    print(f"{'Image':<23s} | {'ORIGINAL':<12s} | {'ROBUST v1':<12s} | {'ROBUST v2':<12s} | {'v2 Status':<10s}")
    print("-"*90)
    
    summary = {"normal_improved": 0, "normal_worse": 0, "sickle_improved": 0, "sickle_worse": 0}
    
    for name in sorted(baseline.keys()):
        if name not in res_v2: continue
            
        old = baseline[name]
        v1 = res_v1[name]
        v2 = res_v2[name]
        
        status = regression_test_robust.get_status(old['category'], old['sickle_count'], v2['sickle_count'])
        
        if status == "BETTER":
            if old['category'] == "normal": summary["normal_improved"] += 1
            else: summary["sickle_improved"] += 1
        elif status == "WORSE":
            if old['category'] == "normal": summary["normal_worse"] += 1
            else: summary["sickle_worse"] += 1
            
        print(f"{name:<23s} | {old['sickle_count']:>2d} sickle   | "
              f"{v1['sickle_count']:>2d} sickle   | {v2['sickle_count']:>2d} sickle   | "
              f"{status:<10s}")
              
    print("\n" + "=" * 80)
    print("VERDICT")
    
    n02_fp = res_v2.get("normal_02.jpg.jpg", {}).get("sickle_count", -1)
    print(f"- normal_02 40 FP fixed: {n02_fp <= 5} (now {n02_fp})")
    
    pass_verdict = (summary["normal_worse"] == 0 and summary["sickle_worse"] == 0) or \
                   ((summary["normal_improved"] + summary["sickle_improved"]) > (summary["normal_worse"] + summary["sickle_worse"]))
                   
    if n02_fp > 5: pass_verdict = False
    
    overall = "PASS" if pass_verdict else "FAIL"
    print(f"OVERALL: {overall}")
    
    report = {
        "verdict": overall,
        "summary": summary,
        "comparison": {
            name: {
                "old": baseline[name],
                "v1": res_v1.get(name),
                "v2": res_v2.get(name),
                "v2_status": regression_test_robust.get_status(baseline[name]["category"], baseline[name]["sickle_count"], res_v2.get(name, {"sickle_count": -1})["sickle_count"])
            }
            for name in baseline
        }
    }
    with open("purge_and_retrain_report.json", "w") as f:
        json.dump(report, f, indent=2)
    with open("regression_test_robust_v2.json", "w") as f:
        json.dump(report, f, indent=2)

def main():
    try:
        step_purge()
        step_rebuild()
        step_retrain()
        step_test()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nFATAL ERROR: {e}")

if __name__ == "__main__":
    main()
