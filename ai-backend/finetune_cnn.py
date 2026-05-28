"""
LabMind — CNN Hard-Negative Fine-Tuning
Fine-tunes the existing CellClassifierCNN (2-class) using 265 hard negatives
from normal smears to fix CNN false positives on normal_04.

Steps:
  1. Copy hard negatives into training pool
  2. Fine-tune with weighted loss (10 epochs, lr=5e-5)
  3. Track top worst HN before/after
  4. Save best + final model

Usage: .venv\\Scripts\\python.exe finetune_cnn.py
"""
import json
import os
import sys
import shutil
import copy
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, transforms
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TRAIN_DIR = os.path.join("dataset_v1_2class", "train")
VAL_DIR = os.path.join("dataset_v1_2class", "val")
HN_DIR = "hard_negatives"
HN_MANIFEST = os.path.join(HN_DIR, "hard_negatives.json")
CURRENT_WEIGHTS = "cell_classifier_2class.pth"
BACKUP_WEIGHTS = "cell_classifier_2class_v1baseline_backup.pth"
OUTPUT_WEIGHTS_BEST = "cell_classifier_2class_finetuned_best.pth"
OUTPUT_WEIGHTS_FINAL = "cell_classifier_2class_finetuned_final.pth"
FINETUNE_LOG = "finetune_log.json"

# Training hyperparameters
EPOCHS = 10
LR = 5e-5
BATCH_SIZE = 16
SICKLE_LOSS_WEIGHT = 2.5  # compensate 2.5:1 normal-heavy imbalance
INPUT_SIZE = 128
ROTATION_DEGREES = 10  # reduced from 15° per user feedback


# ══════════════════════════════════════════════════════════════
# CNN ARCHITECTURE (same as pipeline)
# ══════════════════════════════════════════════════════════════
class CellClassifierCNN(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2, 2),
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.5), nn.Linear(128 * 8 * 8, 256), nn.ReLU(), nn.Linear(256, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)


# ══════════════════════════════════════════════════════════════
# TRANSFORMS
# ══════════════════════════════════════════════════════════════
train_transform = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(ROTATION_DEGREES),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

val_transform = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# For direct crop inference (same as pipeline)
inference_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def step1_prepare_dataset():
    """Copy hard negatives into training pool."""
    print("=" * 70)
    print("  STEP 1: DATASET PREPARATION")
    print("=" * 70)

    with open(HN_MANIFEST, "r") as f:
        manifest = json.load(f)

    hn_labels = manifest["labels"]
    dst_dir = os.path.join(TRAIN_DIR, "normal")
    copied = 0

    for entry in hn_labels:
        src = os.path.join(HN_DIR, entry["filename"])
        dst = os.path.join(dst_dir, entry["filename"])
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            copied += 1

    # Count final
    normal_count = len([f for f in os.listdir(os.path.join(TRAIN_DIR, "normal"))
                        if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    sickle_count = len([f for f in os.listdir(os.path.join(TRAIN_DIR, "sickle"))
                        if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

    print(f"  Hard negatives copied: {copied}")
    print(f"  Train normal: {normal_count}")
    print(f"  Train sickle: {sickle_count}")
    print(f"  Class ratio: {normal_count/sickle_count:.2f}:1")
    print()

    # Save provenance
    provenance = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hard_negatives_added": copied,
        "total_normal": normal_count,
        "total_sickle": sickle_count,
        "source": HN_MANIFEST,
    }
    prov_path = os.path.join("dataset_v1_2class", "finetune_manifest.json")
    with open(prov_path, "w") as f:
        json.dump(provenance, f, indent=2)
    print(f"  Provenance saved: {prov_path}")
    return normal_count, sickle_count


def get_top_worst_hn(n=15):
    """Get the top-N worst hard negatives for tracking."""
    with open(HN_MANIFEST, "r") as f:
        manifest = json.load(f)
    # Already sorted by sickle_prob descending
    return manifest["labels"][:n]


def score_hn_crops(model, hn_list):
    """Score a list of HN crops with the current model."""
    model.eval()
    results = []
    for entry in hn_list:
        crop_path = os.path.join(HN_DIR, entry["filename"])
        crop = cv2.imread(crop_path)
        if crop is None:
            continue
        tensor = inference_transform(crop).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            probs = torch.softmax(model(tensor), dim=1)[0]
        sickle_prob = probs[1].item()  # index 1 = sickle
        results.append({
            "filename": entry["filename"],
            "source_smear": entry["source_smear"],
            "sickle_prob": round(sickle_prob, 4),
        })
    return results


def step2_finetune(normal_count, sickle_count):
    """Fine-tune with weighted loss."""
    print("=" * 70)
    print("  STEP 2: FINE-TUNING")
    print("=" * 70)

    # ── Backup current weights ──
    if os.path.exists(CURRENT_WEIGHTS) and not os.path.exists(BACKUP_WEIGHTS):
        shutil.copy2(CURRENT_WEIGHTS, BACKUP_WEIGHTS)
        print(f"  Backup: {CURRENT_WEIGHTS} → {BACKUP_WEIGHTS}")

    # ── Load model ──
    model = CellClassifierCNN(num_classes=2).to(DEVICE)
    model.load_state_dict(torch.load(CURRENT_WEIGHTS, map_location=DEVICE, weights_only=True))
    print(f"  Loaded weights: {CURRENT_WEIGHTS}")

    # ── Track top worst HN BEFORE fine-tuning ──
    top_worst = get_top_worst_hn(15)
    before_scores = score_hn_crops(model, top_worst)
    print(f"\n  TOP 15 WORST HN (BEFORE):")
    for s in before_scores:
        print(f"    {s['filename']}: sickle_prob={s['sickle_prob']:.4f} ({s['source_smear']})")
    print()

    # ── Data loaders ──
    train_dataset = datasets.ImageFolder(TRAIN_DIR, transform=train_transform)
    val_dataset = datasets.ImageFolder(VAL_DIR, transform=val_transform)

    print(f"  Train samples: {len(train_dataset)} (classes: {train_dataset.class_to_idx})")
    print(f"  Val samples: {len(val_dataset)}")

    # Weighted sampler to balance batches
    class_counts = [0, 0]
    for _, label in train_dataset.samples:
        class_counts[label] += 1
    total = sum(class_counts)
    class_weights = [total / c for c in class_counts]
    sample_weights = [class_weights[label] for _, label in train_dataset.samples]
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(train_dataset), replacement=True)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    # ── Loss + Optimizer ──
    # Weighted cross-entropy: sickle class gets 2.5x weight
    # Class index mapping: ImageFolder sorts alphabetically → normal=0, sickle=1
    loss_weights = torch.tensor([1.0, SICKLE_LOSS_WEIGHT]).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=loss_weights)
    optimizer = optim.Adam(model.parameters(), lr=LR)

    print(f"\n  Hyperparameters:")
    print(f"    Epochs: {EPOCHS}")
    print(f"    LR: {LR}")
    print(f"    Batch size: {BATCH_SIZE}")
    print(f"    Loss weights: normal={loss_weights[0].item()}, sickle={loss_weights[1].item()}")
    print(f"    Rotation: {ROTATION_DEGREES}°")
    print(f"    Device: {DEVICE}")
    print()

    # ── Training loop ──
    best_val_loss = float('inf')
    best_model_state = None
    epoch_log = []

    for epoch in range(EPOCHS):
        # Train
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for batch_imgs, batch_labels in train_loader:
            batch_imgs, batch_labels = batch_imgs.to(DEVICE), batch_labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(batch_imgs)
            loss = criterion(outputs, batch_labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * batch_imgs.size(0)
            _, predicted = torch.max(outputs, 1)
            train_correct += (predicted == batch_labels).sum().item()
            train_total += batch_labels.size(0)

        train_loss /= train_total
        train_acc = train_correct / train_total

        # Validate
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        val_normal_correct = 0
        val_normal_total = 0
        val_sickle_correct = 0
        val_sickle_total = 0

        with torch.no_grad():
            for batch_imgs, batch_labels in val_loader:
                batch_imgs, batch_labels = batch_imgs.to(DEVICE), batch_labels.to(DEVICE)
                outputs = model(batch_imgs)
                loss = criterion(outputs, batch_labels)
                val_loss += loss.item() * batch_imgs.size(0)
                _, predicted = torch.max(outputs, 1)
                val_correct += (predicted == batch_labels).sum().item()
                val_total += batch_labels.size(0)

                # Per-class accuracy
                for i in range(batch_labels.size(0)):
                    if batch_labels[i].item() == 0:  # normal
                        val_normal_total += 1
                        if predicted[i].item() == 0:
                            val_normal_correct += 1
                    else:  # sickle
                        val_sickle_total += 1
                        if predicted[i].item() == 1:
                            val_sickle_correct += 1

        val_loss /= val_total
        val_acc = val_correct / val_total
        val_normal_acc = val_normal_correct / max(val_normal_total, 1)
        val_sickle_acc = val_sickle_correct / max(val_sickle_total, 1)

        epoch_info = {
            "epoch": epoch + 1,
            "train_loss": round(train_loss, 4),
            "train_acc": round(train_acc, 4),
            "val_loss": round(val_loss, 4),
            "val_acc": round(val_acc, 4),
            "val_normal_acc": round(val_normal_acc, 4),
            "val_sickle_acc": round(val_sickle_acc, 4),
        }
        epoch_log.append(epoch_info)

        marker = ""
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = copy.deepcopy(model.state_dict())
            marker = " ← best"

        print(f"  Epoch {epoch+1:2d}/{EPOCHS}: "
              f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} | "
              f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} | "
              f"normal={val_normal_acc:.3f} sickle={val_sickle_acc:.3f}{marker}")

    # ── Save models ──
    print()

    # Save best (by val loss)
    if best_model_state is not None:
        torch.save(best_model_state, OUTPUT_WEIGHTS_BEST)
        print(f"  Best model (val loss): {OUTPUT_WEIGHTS_BEST}")

    # Save final epoch
    torch.save(model.state_dict(), OUTPUT_WEIGHTS_FINAL)
    print(f"  Final model: {OUTPUT_WEIGHTS_FINAL}")

    # ── Track top worst HN AFTER fine-tuning (using best model) ──
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    after_scores = score_hn_crops(model, top_worst)
    print(f"\n  TOP 15 WORST HN (AFTER):")
    for s in after_scores:
        print(f"    {s['filename']}: sickle_prob={s['sickle_prob']:.4f} ({s['source_smear']})")

    # ── Comparison ──
    print(f"\n  ═══ BEFORE / AFTER COMPARISON (top HN) ═══")
    hn_comparison = []
    for before, after in zip(before_scores, after_scores):
        delta = after["sickle_prob"] - before["sickle_prob"]
        direction = "↓" if delta < 0 else "↑" if delta > 0 else "="
        print(f"    {before['filename']}: {before['sickle_prob']:.4f} → "
              f"{after['sickle_prob']:.4f} ({direction}{abs(delta):.4f})")
        hn_comparison.append({
            "filename": before["filename"],
            "before": before["sickle_prob"],
            "after": after["sickle_prob"],
            "delta": round(delta, 4),
        })

    # ── Save log ──
    log = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "base_weights": CURRENT_WEIGHTS,
        "epochs": EPOCHS,
        "lr": LR,
        "batch_size": BATCH_SIZE,
        "sickle_loss_weight": SICKLE_LOSS_WEIGHT,
        "rotation_degrees": ROTATION_DEGREES,
        "device": str(DEVICE),
        "train_samples": len(train_dataset),
        "val_samples": len(val_dataset),
        "class_to_idx": train_dataset.class_to_idx,
        "epoch_log": epoch_log,
        "best_val_loss": round(best_val_loss, 4),
        "hn_before_after": hn_comparison,
        "output_best": OUTPUT_WEIGHTS_BEST,
        "output_final": OUTPUT_WEIGHTS_FINAL,
    }
    with open(FINETUNE_LOG, "w") as f:
        json.dump(log, f, indent=2)
    print(f"\n  Training log: {FINETUNE_LOG}")

    return model, hn_comparison


def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  LabMind — CNN Hard-Negative Fine-Tuning                         ║")
    print("║  Fixing CNN false positives on normal smears                      ║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Step 1: Prepare dataset
    normal_count, sickle_count = step1_prepare_dataset()
    print()

    # Step 2: Fine-tune
    model, hn_comparison = step2_finetune(normal_count, sickle_count)
    print()

    print("=" * 70)
    print("  FINE-TUNING COMPLETE")
    print(f"  Best model: {OUTPUT_WEIGHTS_BEST}")
    print(f"  Final model: {OUTPUT_WEIGHTS_FINAL}")
    print(f"  Backup: {BACKUP_WEIGHTS}")
    print()
    print("  Next: swap weights and run run_baseline.py for acceptance testing")
    print("=" * 70)


if __name__ == "__main__":
    main()
