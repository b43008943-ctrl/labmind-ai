"""
LabMind AI -- Complete Retraining and Pipeline Validation
Extract YOLO crops, retrain CNN, and validate full pipeline.
"""

import sys
import os
import shutil
import json
import uuid
import random
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent

def sep(text):
    print(f"\n=======================================================")
    print(f"  {text}")
    print(f"=======================================================\n")

# ---------------------------------------------------------------------
# STEP 1 & 2: EXTRACT CROPS
# ---------------------------------------------------------------------
def extract_yolo_crops():
    from ultralytics import YOLO
    
    yolo_model_path = SCRIPT_DIR / "yolo_dataset" / "blood_cell_detector" / "weights" / "best.pt"
    if not yolo_model_path.exists():
        print(f"ERROR: No YOLO weights at {yolo_model_path}")
        sys.exit(1)
        
    yolo = YOLO(str(yolo_model_path))
    
    yolo_crops_dir = SCRIPT_DIR / "yolo_crops"
    normal_dir = yolo_crops_dir / "normal"
    sickle_dir = yolo_crops_dir / "sickle"
    sickle_unlabeled_dir = yolo_crops_dir / "sickle_unlabeled"
    
    for d in [normal_dir, sickle_dir, sickle_unlabeled_dir]:
        d.mkdir(parents=True, exist_ok=True)
        
    total_mask_normal = 0
    total_mask_sickle = 0
    total_val_normal = 0
    
    # 1. ErythrocytesIDB2 and 3
    for db in ["erythrocytesIDB2", "erythrocytesIDB3"]:
        src_dir = SCRIPT_DIR / db
        if not src_dir.exists():
            continue
            
        circ_dir = src_dir / "circular"
        elong_dir = src_dir / "elongated"
        other_dir = src_dir / "other"
            
        for img_path in src_dir.iterdir():
            if img_path.is_file() and img_path.suffix.lower() in {".jpg", ".png"}:
                base = img_path.stem
                circ_mask = circ_dir / f"{base}.png"
                elong_mask = elong_dir / f"{base}.png"
                other_mask = other_dir / f"{base}.png"
                
                img = cv2.imread(str(img_path))
                if img is None: continue
                
                mc = cv2.imread(str(circ_mask), cv2.IMREAD_GRAYSCALE) if circ_mask.exists() else None
                me = cv2.imread(str(elong_mask), cv2.IMREAD_GRAYSCALE) if elong_mask.exists() else None
                mo = cv2.imread(str(other_mask), cv2.IMREAD_GRAYSCALE) if other_mask.exists() else None
                
                results = yolo(img, conf=0.1, verbose=False)
                for r in results:
                    boxes = r.boxes.xyxy.cpu().numpy()
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box)
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                        
                        label = None
                        if mc is not None and cy < mc.shape[0] and cx < mc.shape[1] and mc[cy, cx] > 127:
                            label = "normal"
                        elif me is not None and cy < me.shape[0] and cx < me.shape[1] and me[cy, cx] > 127:
                            label = "sickle"
                        elif mo is not None and cy < mo.shape[0] and cx < mo.shape[1] and mo[cy, cx] > 127:
                            label = "other"
                            
                        if label in ["normal", "sickle"]:
                            pad = 10
                            rx1 = max(0, x1 - pad)
                            ry1 = max(0, y1 - pad)
                            rx2 = min(img.shape[1], x2 + pad)
                            ry2 = min(img.shape[0], y2 + pad)
                            crop = img[ry1:ry2, rx1:rx2]
                            if crop.size > 0:
                                crop = cv2.resize(crop, (128, 128))
                                out_name = f"yc_{label}_{uuid.uuid4().hex[:8]}.jpg"
                                if label == "normal":
                                    cv2.imwrite(str(normal_dir / out_name), crop)
                                    total_mask_normal += 1
                                else:
                                    cv2.imwrite(str(sickle_dir / out_name), crop)
                                    total_mask_sickle += 1

    # 2. Validation Smears
    val_smears_dir = SCRIPT_DIR / "validation_smears"
    if val_smears_dir.exists():
        for sub in ["normal", "sickle"]:
            sub_dir = val_smears_dir / sub
            if not sub_dir.exists(): continue
            for img_path in sub_dir.iterdir():
                if img_path.is_file() and img_path.suffix.lower() in {".jpg", ".png"}:
                    img = cv2.imread(str(img_path))
                    if img is None: continue
                    results = yolo(img, conf=0.1, verbose=False)
                    for r in results:
                        boxes = r.boxes.xyxy.cpu().numpy()
                        for box in boxes:
                            x1, y1, x2, y2 = map(int, box)
                            pad = 10
                            rx1, ry1 = max(0, x1 - pad), max(0, y1 - pad)
                            rx2, ry2 = min(img.shape[1], x2 + pad), min(img.shape[0], y2 + pad)
                            crop = img[ry1:ry2, rx1:rx2]
                            if crop.size > 0:
                                crop = cv2.resize(crop, (128, 128))
                                out_name = f"yc_val_{uuid.uuid4().hex[:8]}.jpg"
                                if sub == "normal":
                                    cv2.imwrite(str(normal_dir / out_name), crop)
                                    total_val_normal += 1
                                else:
                                    cv2.imwrite(str(sickle_unlabeled_dir / out_name), crop)
                                    
    print(f"Extracted crops: normal (mask={total_mask_normal}, val={total_val_normal}), sickle (mask={total_mask_sickle})")

# ---------------------------------------------------------------------
# STEP 3: BUILD FINAL CNN DATASET
# ---------------------------------------------------------------------
def build_cnn_dataset():
    sep("STEP 3: BUILD CNN DATASET")
    
    out_dir = SCRIPT_DIR / "cnn_dataset_final"
    if out_dir.exists():
        shutil.rmtree(out_dir)
        
    for split in ["train", "val", "test"]:
        for cls_name in ["normal", "sickle"]:
            (out_dir / split / cls_name).mkdir(parents=True, exist_ok=True)
            
    # Gather inputs
    normal_pool = []
    normal_dir = SCRIPT_DIR / "yolo_crops" / "normal"
    if normal_dir.exists():
        normal_pool.extend(list(normal_dir.glob("*.jpg")))
        
    sickle_pool = []
    sickle_dir = SCRIPT_DIR / "yolo_crops" / "sickle"
    if sickle_dir.exists():
        sickle_pool.extend(list(sickle_dir.glob("*.jpg")))
        
    clean_sickle_dir = SCRIPT_DIR / "dataset_clean" / "sickle"
    if clean_sickle_dir.exists():
        sickle_pool.extend([p for p in clean_sickle_dir.glob("*.jpg") if "erydb_" in p.name])
        
    # Balance and Split
    random.seed(42)
    random.shuffle(normal_pool)
    random.shuffle(sickle_pool)
    
    # Cap ratio to 1.5:1
    max_normal = int(len(sickle_pool) * 1.5)
    if len(normal_pool) > max_normal:
        normal_pool = normal_pool[:max_normal]
        
    print(f"CNN Dataset: {len(normal_pool)} Normal, {len(sickle_pool)} Sickle")
    
    def distro(pool, cls_name):
        n = len(pool)
        n_train = int(n * 0.7)
        n_val = int(n * 0.15)
        # test gets the rest
        
        train_list = pool[:n_train]
        val_list = pool[n_train:n_train+n_val]
        test_list = pool[n_train+n_val:]
        
        # Augment only train
        train_target_dir = out_dir / "train" / cls_name
        for p in train_list:
            img = cv2.imread(str(p))
            if img is None: continue
            cv2.imwrite(str(train_target_dir / p.name), img)
            
            # Simple offline augment for training sets to ensure data
            # 1. Flip
            cv2.imwrite(str(train_target_dir / f"aug_flip_{p.name}"), cv2.flip(img, 1))
            # 2. Rot90
            cv2.imwrite(str(train_target_dir / f"aug_rot90_{p.name}"), cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE))
            
        for split_name, splits in [("val", val_list), ("test", test_list)]:
            target_dir = out_dir / split_name / cls_name
            for p in splits:
                shutil.copy2(p, target_dir / p.name)
                
    distro(normal_pool, "normal")
    distro(sickle_pool, "sickle")
    print("CNN Dataset successfully built.")

# ---------------------------------------------------------------------
# STEP 4: RETRAIN CNN
# ---------------------------------------------------------------------

class CellDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.classes = ["normal", "sickle"]
        self.samples = []
        for i, cls_name in enumerate(self.classes):
            cls_dir = self.data_dir / cls_name
            if cls_dir.exists():
                for p in cls_dir.glob("*.jpg"):
                    self.samples.append((p, i))
                    
    def __len__(self): return len(self.samples)
    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = cv2.imread(str(path))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if self.transform: img = self.transform(img)
        return img, label

def retrain_cnn():
    sep("STEP 4: RETRAIN CNN")
    from app.providers.ai_provider_v1 import CellClassifierCNN # reuse architecture
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    transform_train = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((128, 128)),
        transforms.ColorJitter(brightness=0.15),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    transform_val = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    ds_dir = SCRIPT_DIR / "cnn_dataset_final"
    train_ds = CellDataset(ds_dir / "train", transform_train)
    val_ds = CellDataset(ds_dir / "val", transform_val)
    
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False)
    
    print(f"Train samples: {len(train_ds)}, Val samples: {len(val_ds)}")
    
    # Class weights logic
    c0 = sum(1 for _, l in train_ds.samples if l == 0)
    c1 = sum(1 for _, l in train_ds.samples if l == 1)
    tot = c0 + c1
    w0 = tot / (2.0 * c0) if c0 > 0 else 1.0
    w1 = tot / (2.0 * c1) if c1 > 0 else 1.0
    class_weights = torch.FloatTensor([w0, w1]).to(device)
    print(f"Class weights: Normal={w0:.2f}, Sickle={w1:.2f}")

    model = CellClassifierCNN(num_classes=2).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5, factor=0.5)
    
    best_val_loss = float('inf')
    best_epoch = 0
    patience_cnt = 0
    best_model_path = SCRIPT_DIR / "cell_classifier_2class_yolo_cnn_best.pth"
    final_model_path = SCRIPT_DIR / "cell_classifier_2class_yolo_cnn_final.pth"
    
    for epoch in range(1, 51):
        model.train()
        train_loss = 0.0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * imgs.size(0)
            
        train_loss /= len(train_ds)
        
        model.eval()
        val_loss = 0.0
        correct = 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                outputs = model(imgs)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * imgs.size(0)
                preds = torch.argmax(outputs, dim=1)
                correct += torch.sum(preds == labels).item()
                
        val_loss /= len(val_ds)
        val_acc = correct / len(val_ds)
        scheduler.step(val_loss)
        
        print(f"Epoch {epoch:02d}: T-Loss {train_loss:.4f} | V-Loss {val_loss:.4f} | V-Acc {val_acc:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            torch.save(model.state_dict(), best_model_path)
            patience_cnt = 0
        else:
            patience_cnt += 1
            
        if patience_cnt >= 10:
            print(f"Early stopping at epoch {epoch}")
            break
            
    print(f"Training complete. Best epoch: {best_epoch} with val_loss={best_val_loss:.4f}")
    if os.path.exists(best_model_path):
        model.load_state_dict(torch.load(best_model_path))
    torch.save(model.state_dict(), final_model_path)


# ---------------------------------------------------------------------
# STEP 5: REGRESSION TESTING
# ---------------------------------------------------------------------
def step5_full_pipeline_regression():
    sep("STEP 5: FULL PIPELINE REGRESSION TEST")
    
    env_file = SCRIPT_DIR / ".env"
    best_cnn_pt = "cell_classifier_2class_yolo_cnn_best.pth"
    
    # 1. Update .env for CNN
    env_text = ""
    if env_file.exists():
        env_text = env_file.read_text(encoding="utf-8")
        
    lines = env_text.splitlines()
    updated_cnn = False
    for i, line in enumerate(lines):
        if line.startswith("CNN_MODEL_PATH"):
            lines[i] = f"CNN_MODEL_PATH={best_cnn_pt}"
            updated_cnn = True
    if not updated_cnn:
        lines.append(f"CNN_MODEL_PATH={best_cnn_pt}")
        
    env_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Updated .env CNN_MODEL_PATH={best_cnn_pt}")
    
    # 2. Backup current CNN weights if needed
    import app.core.config
    settings_old = app.core.config.Settings()
    old_cnn = SCRIPT_DIR / settings_old.CNN_MODEL_PATH
    bkp_cnn = SCRIPT_DIR / f"{settings_old.CNN_MODEL_PATH}.bak"
    if old_cnn.exists() and not bkp_cnn.exists():
        shutil.copy2(old_cnn, bkp_cnn)
    
    # Reload config
    import importlib
    importlib.reload(app.core.config)
    app.core.config.get_settings.cache_clear()
    
    # 3. Setup Provider with Monkeypatch
    import app.providers.ai_provider_v1
    app.providers.ai_provider_v1.YOLO_CLASS_MAP = {0: "rbc", 1: "rbc", 2: "rbc", 3: "rbc"}
    from app.providers.ai_provider_v1 import V1Provider
    provider = V1Provider()
    
    val_smears_dir = SCRIPT_DIR / "validation_smears"
    all_smears = []
    for sub in ["normal", "sickle"]:
        d = val_smears_dir / sub
        if d.exists():
            all_smears.extend([f for f in d.iterdir() if f.is_file() and f.suffix in {".jpg", ".png"}])
            
    print(f"{'Image':<20} | {'Total calls'} | {'Sickle'} | {'Sickle%'} | {'Result'}")
    print("-" * 75)
    
    results_list = []
    for img_path in all_smears:
        try:
            results = provider.analyze(str(img_path))
            tot = results["total_cells"]
            sck = results["sickle_count"]
            pct = results["sickle_percentage"]
            res = results.get("field_interpretation", {}).get("screening_result", results.get("quality_status", "?"))
            
            print(f"{img_path.name:<20} | {tot:<11} | {sck:<6} | {pct:<7.2f} | {res}")
            results_list.append({
                "image": img_path.name,
                "total": tot,
                "sickle": sck,
                "sickle_pct": pct,
                "result": res
            })
        except Exception as e:
            print(f"{img_path.name:<20} | ERROR: {e}")
            
    out_path = SCRIPT_DIR / "pipeline_regression_final.json"
    out_path.write_text(json.dumps(results_list, indent=2), encoding="utf-8")
    print(f"\nFinal tests saved to {out_path.name}")

if __name__ == "__main__":
    extract_yolo_crops()
    build_cnn_dataset()
    retrain_cnn()
    step5_full_pipeline_regression()
    sep("MISSION COMPLETE")
