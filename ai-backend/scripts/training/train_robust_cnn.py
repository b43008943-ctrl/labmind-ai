"""
LabMind AI — Train Robust CNN
================================
Retrains CellClassifierCNN (2-class: normal/sickle) on the new clean dataset.

Architecture: IDENTICAL to ai_provider_v1.py CellClassifierCNN
Input: 128×128 RGB (matches production transform at line 169 of ai_provider_v1.py)
Classes: 0=normal, 1=sickle

Usage:
    python train_robust_cnn.py

Output:
    cell_classifier_2class_robust_best.pth   (best val_loss)
    cell_classifier_2class_robust_final.pth  (final epoch)
    training_log_robust.json                 (per-epoch metrics)
    test_evaluation_robust.json              (test set evaluation)
    model_comparison_robust.json             (old vs new)
    training_curves_robust.png               (loss/accuracy/f1 plots)
"""

import json
import time
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    print("[WARN] matplotlib not available — will skip training curves plot")

BASE = Path(__file__).resolve().parent
SPLITS = BASE / "dataset_clean" / "splits"
OLD_MODEL_PATH = BASE / "cell_classifier_2class_finetuned_best.pth"
BEST_PATH = BASE / "cell_classifier_2class_robust_best.pth"
FINAL_PATH = BASE / "cell_classifier_2class_robust_final.pth"

# ── Hyperparameters ──
INPUT_SIZE = 128
NUM_CLASSES = 2
BATCH_SIZE = 32
LR = 0.0001
WEIGHT_DECAY = 1e-4
MAX_EPOCHS = 50
EARLY_STOP_PATIENCE = 10
SCHEDULER_PATIENCE = 5
SCHEDULER_FACTOR = 0.5
MIN_LR = 1e-6
CLASS_NAMES = {0: "normal", 1: "sickle"}


# ═══════════════════════════════════════════════════════════════
#  Model — EXACT copy from ai_provider_v1.py lines 53-69
# ═══════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════
#  Data Loading
# ═══════════════════════════════════════════════════════════════

def create_dataloaders():
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])

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

    train_ds = datasets.ImageFolder(str(SPLITS / "train"), transform=train_transform)
    val_ds = datasets.ImageFolder(str(SPLITS / "val"), transform=eval_transform)
    test_ds = datasets.ImageFolder(str(SPLITS / "test"), transform=eval_transform)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False,
                            num_workers=0, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False,
                             num_workers=0, pin_memory=True)

    # Class mapping from ImageFolder
    print(f"  ImageFolder class_to_idx: {train_ds.class_to_idx}")
    print(f"  Train: {len(train_ds)} | Val: {len(val_ds)} | Test: {len(test_ds)}")

    return train_loader, val_loader, test_loader, train_ds


def compute_class_weights(dataset):
    """Compute inverse-frequency weights for imbalanced classes."""
    targets = [s[1] for s in dataset.samples]
    counts = defaultdict(int)
    for t in targets:
        counts[t] += 1
    total = len(targets)
    weights = []
    for i in range(NUM_CLASSES):
        w = total / (NUM_CLASSES * counts.get(i, 1))
        weights.append(w)
    print(f"  Class counts: {dict(counts)}")
    print(f"  Class weights: {[round(w, 4) for w in weights]}")
    return torch.tensor(weights, dtype=torch.float32)


# ═══════════════════════════════════════════════════════════════
#  Metrics
# ═══════════════════════════════════════════════════════════════

def compute_metrics(all_preds, all_labels):
    """Compute per-class precision, recall, f1 and overall accuracy."""
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
    for cls_idx in range(NUM_CLASSES):
        name = CLASS_NAMES[cls_idx]
        prec = tp[cls_idx] / (tp[cls_idx] + fp[cls_idx]) if (tp[cls_idx] + fp[cls_idx]) > 0 else 0
        rec = tp[cls_idx] / (tp[cls_idx] + fn[cls_idx]) if (tp[cls_idx] + fn[cls_idx]) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        metrics[f"{name}_precision"] = round(prec, 4)
        metrics[f"{name}_recall"] = round(rec, 4)
        metrics[f"{name}_f1"] = round(f1, 4)
        f1_sum += f1

    metrics["macro_f1"] = round(f1_sum / NUM_CLASSES, 4)
    return metrics


def confusion_matrix(all_preds, all_labels):
    """Build NxN confusion matrix."""
    cm = [[0] * NUM_CLASSES for _ in range(NUM_CLASSES)]
    for p, l in zip(all_preds, all_labels):
        cm[l][p] += 1
    return cm


def print_confusion_matrix(cm, label=""):
    print(f"\n  Confusion Matrix {label}")
    print(f"  {'':>15s}  Pred Normal  Pred Sickle")
    print(f"  {'True Normal':>15s}  {cm[0][0]:>11d}  {cm[0][1]:>11d}")
    print(f"  {'True Sickle':>15s}  {cm[1][0]:>11d}  {cm[1][1]:>11d}")


# ═══════════════════════════════════════════════════════════════
#  Training Loop
# ═══════════════════════════════════════════════════════════════

def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        preds = outputs.argmax(dim=1).cpu().tolist()
        all_preds.extend(preds)
        all_labels.extend(labels.cpu().tolist())

    avg_loss = total_loss / len(all_labels)
    metrics = compute_metrics(all_preds, all_labels)
    return avg_loss, metrics


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []

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
    cm = confusion_matrix(all_preds, all_labels)
    return avg_loss, metrics, cm, all_preds, all_labels


def train(model, train_loader, val_loader, device):
    print("\n" + "=" * 90)
    print("  TRAINING")
    print("=" * 90)

    # Class weights
    class_weights = compute_class_weights(train_loader.dataset).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", patience=SCHEDULER_PATIENCE,
        factor=SCHEDULER_FACTOR, min_lr=MIN_LR)

    best_val_loss = float("inf")
    best_epoch = 0
    patience_counter = 0
    history = []

    total_start = time.time()

    for epoch in range(1, MAX_EPOCHS + 1):
        epoch_start = time.time()

        # Train
        train_loss, train_metrics = train_one_epoch(model, train_loader, criterion, optimizer, device)

        # Validate
        val_loss, val_metrics, val_cm, _, _ = evaluate(model, val_loader, criterion, device)

        # Scheduler step
        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]["lr"]

        epoch_time = time.time() - epoch_start
        elapsed = time.time() - total_start
        eta = (elapsed / epoch) * (MAX_EPOCHS - epoch)

        record = {
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "val_loss": round(val_loss, 4),
            "lr": current_lr,
            "epoch_time_s": round(epoch_time, 1),
            **{f"train_{k}": v for k, v in train_metrics.items()},
            **{f"val_{k}": v for k, v in val_metrics.items()},
        }
        history.append(record)

        # Print
        print(f"  Epoch {epoch:>3d}/{MAX_EPOCHS} | "
              f"loss: {train_loss:.4f}/{val_loss:.4f} | "
              f"acc: {train_metrics['accuracy']:.3f}/{val_metrics['accuracy']:.3f} | "
              f"f1: {val_metrics['macro_f1']:.3f} | "
              f"lr: {current_lr:.1e} | "
              f"{epoch_time:.1f}s | ETA: {eta/60:.0f}m")

        # Confusion matrix every 5 epochs
        if epoch % 5 == 0 or epoch == 1:
            print_confusion_matrix(val_cm, f"(epoch {epoch})")

        # Best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            patience_counter = 0
            torch.save(model.state_dict(), str(BEST_PATH))
            print(f"    ✓ New best model saved (val_loss={val_loss:.4f})")
        else:
            patience_counter += 1

        # Early stopping
        if patience_counter >= EARLY_STOP_PATIENCE:
            print(f"\n  ⏹ Early stopping at epoch {epoch} (no improvement for {EARLY_STOP_PATIENCE} epochs)")
            break

    # Save final model
    torch.save(model.state_dict(), str(FINAL_PATH))
    total_time = time.time() - total_start
    print(f"\n  Training complete: {total_time/60:.1f} minutes")
    print(f"  Best epoch: {best_epoch} (val_loss={best_val_loss:.4f})")
    print(f"  Best model: {BEST_PATH.name}")
    print(f"  Final model: {FINAL_PATH.name}")

    return history, best_epoch


# ═══════════════════════════════════════════════════════════════
#  Test Evaluation
# ═══════════════════════════════════════════════════════════════

def evaluate_on_test(model, test_loader, device, label="New Model"):
    print(f"\n  ── Test Evaluation: {label} ──")
    criterion = nn.CrossEntropyLoss()
    test_loss, test_metrics, test_cm, preds, labels = evaluate(model, test_loader, criterion, device)

    print_confusion_matrix(test_cm, f"({label})")
    print(f"\n  Test Loss:     {test_loss:.4f}")
    print(f"  Accuracy:      {test_metrics['accuracy']:.4f}")
    print(f"  Normal  P/R/F1: {test_metrics['normal_precision']:.3f} / "
          f"{test_metrics['normal_recall']:.3f} / {test_metrics['normal_f1']:.3f}")
    print(f"  Sickle  P/R/F1: {test_metrics['sickle_precision']:.3f} / "
          f"{test_metrics['sickle_recall']:.3f} / {test_metrics['sickle_f1']:.3f}")
    print(f"  Macro F1:      {test_metrics['macro_f1']:.4f}")

    # Misclassification details
    n_as_s = test_cm[0][1]  # true normal predicted sickle
    s_as_n = test_cm[1][0]  # true sickle predicted normal
    print(f"\n  Misclassifications:")
    print(f"    Normal → Sickle (false positive): {n_as_s}")
    print(f"    Sickle → Normal (false negative): {s_as_n}")

    return test_loss, test_metrics, test_cm


# ═══════════════════════════════════════════════════════════════
#  Training Curves
# ═══════════════════════════════════════════════════════════════

def plot_curves(history, best_epoch):
    if not HAS_MPL:
        print("  ⚠ Skipping training curves (matplotlib not available)")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("LabMind AI — Robust CNN Training Curves", fontsize=14, fontweight="bold")

    epochs = [h["epoch"] for h in history]
    train_loss = [h["train_loss"] for h in history]
    val_loss = [h["val_loss"] for h in history]
    train_acc = [h["train_accuracy"] for h in history]
    val_acc = [h["val_accuracy"] for h in history]

    # Top left: Loss
    ax = axes[0][0]
    ax.plot(epochs, train_loss, "b-", label="Train Loss", linewidth=1.5)
    ax.plot(epochs, val_loss, "r-", label="Val Loss", linewidth=1.5)
    ax.axvline(x=best_epoch, color="green", linestyle="--", alpha=0.7, label=f"Best (ep {best_epoch})")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.set_title("Loss")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Top right: Accuracy
    ax = axes[0][1]
    ax.plot(epochs, train_acc, "b-", label="Train Acc", linewidth=1.5)
    ax.plot(epochs, val_acc, "r-", label="Val Acc", linewidth=1.5)
    ax.axvline(x=best_epoch, color="green", linestyle="--", alpha=0.7, label=f"Best (ep {best_epoch})")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Accuracy")
    ax.set_title("Accuracy")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Bottom left: Precision & Recall
    ax = axes[1][0]
    ax.plot(epochs, [h["val_normal_precision"] for h in history], "g-", label="Normal Prec", linewidth=1.2)
    ax.plot(epochs, [h["val_normal_recall"] for h in history], "g--", label="Normal Rec", linewidth=1.2)
    ax.plot(epochs, [h["val_sickle_precision"] for h in history], "r-", label="Sickle Prec", linewidth=1.2)
    ax.plot(epochs, [h["val_sickle_recall"] for h in history], "r--", label="Sickle Rec", linewidth=1.2)
    ax.axvline(x=best_epoch, color="green", linestyle="--", alpha=0.7)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Score")
    ax.set_title("Val Precision & Recall (per class)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Bottom right: F1
    ax = axes[1][1]
    ax.plot(epochs, [h["val_normal_f1"] for h in history], "g-", label="Normal F1", linewidth=1.5)
    ax.plot(epochs, [h["val_sickle_f1"] for h in history], "r-", label="Sickle F1", linewidth=1.5)
    ax.plot(epochs, [h["val_macro_f1"] for h in history], "b-", label="Macro F1", linewidth=1.5)
    ax.axvline(x=best_epoch, color="green", linestyle="--", alpha=0.7, label=f"Best (ep {best_epoch})")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("F1 Score")
    ax.set_title("Val F1 (per class)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = BASE / "training_curves_robust.png"
    plt.savefig(str(plot_path), dpi=150)
    plt.close()
    print(f"  ✓ Training curves: {plot_path}")


# ═══════════════════════════════════════════════════════════════
#  Old Model Comparison
# ═══════════════════════════════════════════════════════════════

def compare_with_old(new_metrics, new_cm, test_loader, device):
    print("\n" + "=" * 90)
    print("  MODEL COMPARISON (old vs new)")
    print("=" * 90)

    if not OLD_MODEL_PATH.exists():
        print(f"  ⚠ Old model not found: {OLD_MODEL_PATH}")
        return None

    # Load old model
    old_model = CellClassifierCNN(num_classes=2).to(device)
    old_model.load_state_dict(
        torch.load(str(OLD_MODEL_PATH), map_location=device, weights_only=True))
    old_model.eval()

    _, old_metrics, old_cm = evaluate_on_test(old_model, test_loader, device, "Old Model")

    # Print comparison table
    compare_keys = [
        ("accuracy", "Accuracy"),
        ("normal_precision", "Normal Precision"),
        ("normal_recall", "Normal Recall"),
        ("normal_f1", "Normal F1"),
        ("sickle_precision", "Sickle Precision"),
        ("sickle_recall", "Sickle Recall"),
        ("sickle_f1", "Sickle F1"),
        ("macro_f1", "Macro F1"),
    ]

    print(f"\n  {'Metric':<22s}{'Old Model':>12s}{'New Model':>12s}{'Change':>10s}")
    print(f"  {'─' * 56}")

    comparison = {}
    for key, label in compare_keys:
        old_val = old_metrics.get(key, 0)
        new_val = new_metrics.get(key, 0)
        diff = new_val - old_val
        print(f"  {label:<22s}{old_val:>12.4f}{new_val:>12.4f}{diff:>+10.4f}")
        comparison[key] = {"old": old_val, "new": new_val, "change": round(diff, 4)}

    print_confusion_matrix(old_cm, "(Old)")
    print_confusion_matrix(new_cm, "(New)")

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "old_model": str(OLD_MODEL_PATH),
        "new_model": str(BEST_PATH),
        "comparison": comparison,
        "old_confusion_matrix": old_cm,
        "new_confusion_matrix": new_cm,
    }

    comp_path = BASE / "model_comparison_robust.json"
    with open(comp_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n  ✓ Comparison: {comp_path}")
    return result


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 90)
    print("  LabMind AI — Train Robust CNN")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("═" * 90)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n  Device: {device}")
    if device.type == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  Memory: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")

    # Step 2: Data
    print("\n  ── DATA LOADING ──")
    train_loader, val_loader, test_loader, train_ds = create_dataloaders()

    # Step 1: Model
    print("\n  ── MODEL ──")
    model = CellClassifierCNN(num_classes=NUM_CLASSES).to(device)
    total_params = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Architecture: CellClassifierCNN (identical to ai_provider_v1.py)")
    print(f"  Input: {INPUT_SIZE}×{INPUT_SIZE} RGB")
    print(f"  Output: {NUM_CLASSES} classes (normal, sickle)")
    print(f"  Parameters: {total_params:,} total, {trainable:,} trainable")

    # Step 3+4: Train
    history, best_epoch = train(model, train_loader, val_loader, device)

    # Save training log
    log_path = BASE / "training_log_robust.json"
    with open(log_path, "w") as f:
        json.dump({"config": {
            "input_size": INPUT_SIZE, "num_classes": NUM_CLASSES,
            "batch_size": BATCH_SIZE, "lr": LR, "weight_decay": WEIGHT_DECAY,
            "max_epochs": MAX_EPOCHS, "early_stop_patience": EARLY_STOP_PATIENCE,
            "device": str(device), "best_epoch": best_epoch,
        }, "history": history}, f, indent=2)
    print(f"  ✓ Training log: {log_path}")

    # Step 5: Test evaluation (load best model)
    print("\n" + "=" * 90)
    print("  TEST EVALUATION")
    print("=" * 90)
    model.load_state_dict(torch.load(str(BEST_PATH), map_location=device, weights_only=True))
    test_loss, test_metrics, test_cm = evaluate_on_test(model, test_loader, device, "New Robust Model")

    eval_result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": str(BEST_PATH),
        "test_loss": round(test_loss, 4),
        "metrics": test_metrics,
        "confusion_matrix": test_cm,
        "misclassifications": {
            "normal_as_sickle": test_cm[0][1],
            "sickle_as_normal": test_cm[1][0],
        },
    }
    eval_path = BASE / "test_evaluation_robust.json"
    with open(eval_path, "w") as f:
        json.dump(eval_result, f, indent=2)
    print(f"  ✓ Test evaluation: {eval_path}")

    # Step 6: Training curves
    print("\n  ── TRAINING CURVES ──")
    plot_curves(history, best_epoch)

    # Step 7: Compare with old model
    compare_with_old(test_metrics, test_cm, test_loader, device)

    print("\n" + "═" * 90)
    print("  TRAINING COMPLETE")
    print(f"  Best model: {BEST_PATH.name}")
    print(f"  Test accuracy: {test_metrics['accuracy']:.4f}")
    print(f"  Test macro F1: {test_metrics['macro_f1']:.4f}")
    print("═" * 90 + "\n")


if __name__ == "__main__":
    main()
