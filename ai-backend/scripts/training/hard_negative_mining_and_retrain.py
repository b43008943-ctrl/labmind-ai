import json
import os
import random
import shutil
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# Set determinism
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

from app.providers.ai_provider_v1 import V1Provider, CellClassifierCNN

BASE_DIR = Path(__file__).resolve().parent
V3_WEIGHTS = BASE_DIR / "cell_classifier_2class_robust_v3_best.pth"
V4_BEST_WEIGHTS = BASE_DIR / "cell_classifier_2class_robust_v4_best.pth"
V4_FINAL_WEIGHTS = BASE_DIR / "cell_classifier_2class_robust_v4_final.pth"
TRAIN_LOG_V4 = BASE_DIR / "training_log_robust_v4.json"
REGRESSION_JSON = BASE_DIR / "regression_test_robust_v4.json"
BASELINE_PATH = BASE_DIR / "baseline_results_v1_frozen.json"  # or baseline_results.json
if not BASELINE_PATH.exists():
    BASELINE_PATH = BASE_DIR / "baseline_results.json"

DATASET_CLEAN = BASE_DIR / "dataset_clean"
HARD_NEG_DIR = DATASET_CLEAN / "hard_negatives"
SPLITS_DIR = DATASET_CLEAN / "splits"
VALIDATION_DIR = BASE_DIR / "validation_smears"

TARGET_SMEARS = {"normal_02.jpg.jpg": 30, "normal_01.jpg.jpg": 20, "normal_04.jpg.jpg": 20}

# Crop params
TARGET_SIZE = (128, 128)
CROP_PAD = 15

# Training params
INPUT_SIZE = 64  # User specified: Input 64x64. Wait, step 5 says "Input 64x64". Wait, V3 is 128x128 but user said 64x64? I'll use 64x64 if requested, but architecture 128x128 -> pooling -> ... wait, CellClassifierCNN expects 64x64 or 128x128? Actually, user said: "Same CellClassifierCNN architecture and training settings: Input 64x64". Wait! If CellClassifierCNN architecture is unchanged from ai_provider_v1.py, and ai_provider_v1 uses transforms.Resize((128,128)), and train_robust_cnn.py uses 128. I better use 128 so we don't break the NN layers, OR I can use 64 if it's explicitly asked. Wait, let's use 64x64 because user request says so. Actually, wait. CNN has Linear(128 * 8 * 8, 256) which means after 4 maxpools (2^4 = 16 reduction). So 128 / 16 = 8. 8*8*128. If input is 64x64, it'll be 64/16 = 4. 4*4*128 = 2048, which would crash at Linear(8192, 256). 
# Ah! If the user says "Same CellClassifierCNN architecture and training settings: Input 64x64", they might have made a typo for 128x128. I MUST use 128x128 to prevent a tensor size mismatch if the architecture isn't modified. Let me use 128 to be safe, because ai_provider_v1.py resize is 128x128!
INPUT_SIZE = 128 
NUM_CLASSES = 2
BATCH_SIZE = 32
LR = 0.0001
WEIGHT_DECAY = 1e-4
MAX_EPOCHS = 50
EARLY_STOP_PATIENCE = 10


def setup_v3_provider():
    provider = V1Provider()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cnn = CellClassifierCNN(num_classes=2).to(device)
    cnn.load_state_dict(torch.load(str(V3_WEIGHTS), map_location=device, weights_only=True))
    cnn.eval()
    V1Provider._cnn_model = cnn
    V1Provider._classifier_mode = "v3_hard_negative_miner"
    return provider


def crop_roi(img, box, pad=10):
    h_img, w_img = img.shape[:2]
    x1, y1, x2, y2 = map(int, box)
    rx1, ry1 = max(0, x1 - pad), max(0, y1 - pad)
    rx2, ry2 = min(w_img, x2 + pad), min(h_img, y2 + pad)
    roi = img[ry1:ry2, rx1:rx2]
    if roi.size == 0:
        return None
    
    interp = cv2.INTER_AREA if roi.shape[1] > TARGET_SIZE[0] else cv2.INTER_CUBIC
    return cv2.resize(roi, TARGET_SIZE, interpolation=interp)


def step1_2_extract_hard_negatives():
    print("\n" + "="*80 + "\nSTEP 1 & 2: EXTRACT HARD NEGATIVES\n" + "="*80)
    HARD_NEG_DIR.mkdir(parents=True, exist_ok=True)
    provider = setup_v3_provider()

    all_smears = list(VALIDATION_DIR.rglob("*.jpg")) + list(VALIDATION_DIR.rglob("*.jpg.jpg"))
    unique_files = {f.name: f for f in all_smears}

    for target_name, tn_count in TARGET_SMEARS.items():
        if target_name not in unique_files:
            print(f"Warning: {target_name} not found.")
            continue
            
        file_path = unique_files[target_name]
        print(f"Mining {target_name}...")
        res = provider.analyze(str(file_path))
        img = cv2.imread(str(file_path))
        
        false_positives = []
        true_negatives = []
        
        for cell in res["cell_details"]:
            if cell["class_name"] == "sickle":
                false_positives.append(cell)
            elif cell["class_name"] == "rbc":
                true_negatives.append(cell)

        # Save false positives
        fp_saved = 0
        stem = file_path.name.replace(".jpg.jpg", "").replace(".jpg", "")
        for i, cell in enumerate(false_positives):
            crop = crop_roi(img, [cell["x1"], cell["y1"], cell["x2"], cell["y2"]])
            if crop is not None:
                out_path = HARD_NEG_DIR / f"{stem}_fp_{i:03d}.jpg"
                cv2.imwrite(str(out_path), crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
                fp_saved += 1
                
        # Save random true negatives
        tn_saved = 0
        random.shuffle(true_negatives)
        for i, cell in enumerate(true_negatives[:tn_count]):
            crop = crop_roi(img, [cell["x1"], cell["y1"], cell["x2"], cell["y2"]])
            if crop is not None:
                out_path = HARD_NEG_DIR / f"{stem}_tn_{i:03d}.jpg"
                cv2.imwrite(str(out_path), crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
                tn_saved += 1
                
        print(f"  -> Extracted {fp_saved} false positives (hard negatives) and {tn_saved} true negatives.")


def augment_img(img, aug_type):
    if aug_type == "r90": return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    if aug_type == "r180": return cv2.rotate(img, cv2.ROTATE_180)
    if aug_type == "r270": return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if aug_type == "hflip": return cv2.flip(img, 1)
    if aug_type == "bright": return cv2.convertScaleAbs(img, alpha=1.0, beta=38)
    if aug_type == "dark": return cv2.convertScaleAbs(img, alpha=0.85, beta=0)
    return img


def step3_add_to_training():
    print("\n" + "="*80 + "\nSTEP 3: ADD HARD NEGATIVES TO CLEAN DATASET\n" + "="*80)
    normal_dir = DATASET_CLEAN / "normal"
    normal_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean up old hn_ files
    for f in normal_dir.glob("hn_*.jpg"):
        f.unlink()
    
    crops = list(HARD_NEG_DIR.glob("*.jpg"))
    print(f"Found {len(crops)} extracted crops.")
    
    generated = 0
    for crop_path in crops:
        img = cv2.imread(str(crop_path))
        if img is None: continue
        
        # Base hn_
        base_name = f"hn_{crop_path.stem}"
        cv2.imwrite(str(normal_dir / f"{base_name}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        generated += 1
        
        # Augments
        for aug in ["r90", "r180", "r270", "hflip"]:
            a_img = augment_img(img, aug)
            cv2.imwrite(str(normal_dir / f"{base_name}_{aug}.jpg"), a_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
            generated += 1

    print(f"Added {generated} augmented hard negatives to dataset_clean/normal/")


def get_base_stem(filename):
    stem = Path(filename).stem
    # Standard augments
    for aug in ["r90", "r180", "r270", "hflip", "bright", "dark", "blur", "hue"]:
        if stem.endswith(f"_{aug}"):
            return stem[:-(len(aug) + 1)]
    return stem


def step4_rebuild_splits():
    print("\n" + "="*80 + "\nSTEP 4: REBUILD SPLITS\n" + "="*80)
    
    if SPLITS_DIR.exists():
        print("Clearing old splits...")
        shutil.rmtree(SPLITS_DIR)
        
    for sp in ["train", "val", "test"]:
        (SPLITS_DIR / sp / "normal").mkdir(parents=True, exist_ok=True)
        (SPLITS_DIR / sp / "sickle").mkdir(parents=True, exist_ok=True)

    counts = {"train": {"normal":0, "sickle":0}, "val": {"normal":0, "sickle":0}, "test": {"normal":0, "sickle":0}}

    for cls in ["normal", "sickle"]:
        src_dir = DATASET_CLEAN / cls
        files = [f for f in src_dir.iterdir() if f.is_file() and f.suffix.lower() == ".jpg"]
        
        # Group by stem to avoid leakage
        groups = defaultdict(list)
        hn_groups = defaultdict(list)
        
        for f in files:
            base = get_base_stem(f.name)
            if base.startswith("hn_"):
                hn_groups[base].append(f)
            else:
                groups[base].append(f)
                
        # Shuffle standard groups
        group_keys = sorted(groups.keys())
        random.shuffle(group_keys)
        n_grps = len(group_keys)
        
        train_end = int(n_grps * 0.70)
        val_end = int(n_grps * 0.85)
        
        for i, key in enumerate(group_keys):
            sp = "train" if i < train_end else "val" if i < val_end else "test"
            for f in groups[key]:
                shutil.copy2(f, SPLITS_DIR / sp / cls / f.name)
                counts[sp][cls] += 1
                
        # Force hn_ groups to train
        if cls == "normal":
            for key in hn_groups.keys():
                for f in hn_groups[key]:
                    shutil.copy2(f, SPLITS_DIR / "train" / "normal" / f.name)
                    counts["train"]["normal"] += 1

    print("Groups allocated:")
    print(f" Train: Normal={counts['train']['normal']}, Sickle={counts['train']['sickle']}")
    print(f" Val:   Normal={counts['val']['normal']}, Sickle={counts['val']['sickle']}")
    print(f" Test:  Normal={counts['test']['normal']}, Sickle={counts['test']['sickle']}")

    # Balance check: if train_normal > train_sickle * 1.5, augment sickle
    n_train = counts["train"]["normal"]
    s_train = counts["train"]["sickle"]
    if n_train > s_train * 1.5:
        target_s = int(n_train / 1.5)
        needed = target_s - s_train
        print(f"\nBalancing needed in training split: Need {needed} more sickle crops.")
        
        t_sickle_dir = SPLITS_DIR / "train" / "sickle"
        base_sickle = [f for f in t_sickle_dir.iterdir() if get_base_stem(f.name) == f.stem]
        random.shuffle(base_sickle)
        
        added = 0
        aug_types = ["r90", "r180", "r270", "hflip", "bright", "dark"]
        aug_idx = 0
        
        while added < needed and len(base_sickle) > 0:
            for bf in base_sickle:
                if added >= needed: break
                img = cv2.imread(str(bf))
                if img is None: continue
                # cycle augmentations
                aug_t = aug_types[aug_idx % len(aug_types)]
                a_img = augment_img(img, aug_t)
                a_name = f"{bf.stem}_{added}_{aug_t}.jpg"
                cv2.imwrite(str(t_sickle_dir / a_name), a_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                added += 1
                counts["train"]["sickle"] += 1
                aug_idx += 1
                
        print(f"Generated {added} new sickle augmentations in train split.")
        print(f"Final Train: Normal={counts['train']['normal']}, Sickle={counts['train']['sickle']}")


# ── TRAINING ──

def compute_metrics(all_preds, all_labels):
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    correct = 0

    for p, l in zip(all_preds, all_labels):
        if p == l:
            correct += 1
            tp[l] += 1
        else:
            fp[p] += 1
            fn[l] += 1

    accuracy = correct / len(all_labels) if all_labels else 0
    metrics = {"accuracy": round(accuracy, 4)}
    f1_sum = 0
    
    class_names = {0: "normal", 1: "sickle"}
    for cls_idx in range(NUM_CLASSES):
        name = class_names[cls_idx]
        prec = tp[cls_idx] / (tp[cls_idx] + fp[cls_idx]) if (tp[cls_idx] + fp[cls_idx]) > 0 else 0
        rec = tp[cls_idx] / (tp[cls_idx] + fn[cls_idx]) if (tp[cls_idx] + fn[cls_idx]) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        metrics[f"{name}_precision"] = round(prec, 4)
        metrics[f"{name}_recall"] = round(rec, 4)
        metrics[f"{name}_f1"] = round(f1, 4)
        f1_sum += f1

    metrics["macro_f1"] = round(f1_sum / NUM_CLASSES, 4)
    return metrics


@torch.no_grad()
def evaluate_model(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    all_preds, all_labels = [], []

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)

        total_loss += loss.item() * images.size(0)
        preds = outputs.argmax(dim=1).cpu().tolist()
        all_preds.extend(preds)
        all_labels.extend(labels.cpu().tolist())

    avg_loss = total_loss / len(all_labels)
    metrics = compute_metrics(all_preds, all_labels)
    return avg_loss, metrics


def step5_retrain():
    print("\n" + "="*80 + "\nSTEP 5: RETRAIN CNN\n" + "="*80)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

    train_transform = transforms.Compose([
        transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        normalize,
    ])

    eval_transform = transforms.Compose([
        transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
        transforms.ToTensor(),
        normalize,
    ])

    train_ds = datasets.ImageFolder(str(SPLITS_DIR / "train"), transform=train_transform)
    val_ds = datasets.ImageFolder(str(SPLITS_DIR / "val"), transform=eval_transform)
    
    # Class weights
    targets = [s[1] for s in train_ds.samples]
    counts = defaultdict(int)
    for t in targets: counts[t] += 1
    total = len(targets)
    weights = []
    for i in range(NUM_CLASSES):
        weights.append(total / (NUM_CLASSES * counts.get(i, 1)))
    class_weights = torch.tensor(weights, dtype=torch.float32).to(device)
    print(f"Class weights: {weights}")

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, pin_memory=True)

    model = CellClassifierCNN(num_classes=2).to(device)
    # Train from scratch since LR=0.0001 is too high for fine-tuning
    # No load_state_dict here
    
    # Class weights exact match to train_robust_cnn.py
    counts_dict = defaultdict(int)
    for t in targets: counts_dict[t] += 1
    w_list = []
    for i in range(NUM_CLASSES):
        w_list.append(total / (NUM_CLASSES * counts_dict.get(i, 1)))
    class_weights_final = torch.tensor(w_list, dtype=torch.float32).to(device)

    criterion = nn.CrossEntropyLoss(weight=class_weights_final)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", patience=5, factor=0.5, min_lr=1e-6)

    best_val_loss = float("inf")
    patience_counter = 0
    history = []

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        total_loss = 0
        all_preds, all_labels = [], []

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * images.size(0)
            all_preds.extend(outputs.argmax(dim=1).cpu().tolist())
            all_labels.extend(labels.cpu().tolist())

        train_loss = total_loss / len(all_labels)
        train_metrics = compute_metrics(all_preds, all_labels)
        
        val_loss, val_metrics = evaluate_model(model, val_loader, criterion, device)
        scheduler.step(val_loss)

        print(f"Epoch {epoch:>2d}/{MAX_EPOCHS} | loss: {train_loss:.4f}/{val_loss:.4f} | "
              f"acc: {train_metrics['accuracy']:.3f}/{val_metrics['accuracy']:.3f} | "
              f"val_f1: {val_metrics['macro_f1']:.3f}")

        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), str(V4_BEST_WEIGHTS))
            print(f"  -> New best model (val_loss={val_loss:.4f})")
        else:
            patience_counter += 1

        if patience_counter >= EARLY_STOP_PATIENCE:
            print(f"Early stopping at epoch {epoch}")
            break

    torch.save(model.state_dict(), str(V4_FINAL_WEIGHTS))
    
    with open(TRAIN_LOG_V4, "w") as f:
        json.dump(history, f, indent=2)
    print("Training complete, weights saved.")


def load_baseline():
    if not BASELINE_PATH.exists(): return {}
    with open(BASELINE_PATH, "r") as f: data = json.load(f)
    baseline = {}
    for sm_type, key in [("normal", "normal_smears"), ("sickle", "sickle_smears")]:
        smears = data.get("cell_level_metrics", {}).get(key, {}).get("per_smear_sickle", [])
        for entry in smears:
            fname = entry["label"]
            sickle = entry["sickle"]
            baseline[fname] = {"category": sm_type, "sickle_count": sickle}
    return baseline


def step6_regression_test():
    print("\n" + "="*80 + "\nSTEP 6: REGRESSION TEST\n" + "="*80)
    provider = V1Provider()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    new_cnn = CellClassifierCNN(num_classes=2).to(device)
    new_cnn.load_state_dict(torch.load(str(V4_BEST_WEIGHTS), map_location=device, weights_only=True))
    new_cnn.eval()
    
    V1Provider._cnn_model = new_cnn
    V1Provider._classifier_mode = "v4_regression_tester"
    
    baseline = load_baseline()
    
    # Also load V3 baseline for comparison
    v3_results_path = BASE_DIR / "regression_test_robust_v3.json"
    v3_data_json = {}
    if v3_results_path.exists():
        with open(v3_results_path, "r") as f: v3_data = json.load(f)
        v3_data_json = {k: v["v3"]["sickle_count"] for k, v in v3_data.get("comparison", {}).items() if "v3" in v and v["v3"] is not None}
        
    validation_files = list(VALIDATION_DIR.rglob("*.jpg")) + list(VALIDATION_DIR.rglob("*.jpg.jpg"))
    unique_files = {f.name: f for f in validation_files}
    
    results = {}
    print(f"{'Image':<20s} | {'ORIGINAL':<10s} | {'V3':<10s} | {'V4':<10s} | {'V4 Status':<20s}")
    print("-" * 80)
    
    passed_all = True
    v4_json_output = {}

    for file_name in sorted(unique_files.keys()):
        file_path = unique_files[file_name]
        
        orig_val = baseline.get(file_name, {}).get("sickle_count", "?")
        v3_val = v3_data_json.get(file_name, "?")
        
        res = provider.analyze(str(file_path))
        v4_val = res["sickle_count"]
        results[file_name] = v4_val
        
        status = "OK"
        if file_name == "normal_02.jpg.jpg" and v4_val >= 3: 
            status = "FAIL (Target: < 3)"
            passed_all = False
        elif file_name == "normal_04.jpg.jpg" and v4_val >= 5: 
            status = "FAIL (Target: < 5)"
            passed_all = False
        elif file_name.startswith("normal") and v4_val >= 5: # General rule
            status = "FAIL (Normal changed to Pos)"
        elif file_name.startswith("sickle") and v4_val < 1:
            status = "FAIL (Sickle changed to Neg)"
            passed_all = False
            
        print(f"{file_name:<20s} | {str(orig_val):<10s} | {str(v3_val):<10s} | {str(v4_val):<10s} | {status:<20s}")
        
        v4_json_output[file_name] = {
            "v4_sickle_count": v4_val,
            "v3_sickle_count": v3_val,
            "original_sickle_count": orig_val,
            "status": status
        }
        
    print("\nOVERALL STATUS:", "PASS" if passed_all else "FAIL")
    with open(REGRESSION_JSON, "w") as f:
        json.dump(v4_json_output, f, indent=2)


if __name__ == "__main__":
    t0 = time.time()
    step1_2_extract_hard_negatives()
    step3_add_to_training()
    step4_rebuild_splits()
    step5_retrain()
    step6_regression_test()
    print(f"\nExecution finished in {time.time() - t0:.1f} seconds")
