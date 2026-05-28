"""
LabMind AI — 2-Class RBC Classifier Training Script

Trains CellClassifierCNN with 2 classes only: normal, sickle.
Use this for the FIRST training run when target / other_abnormal data
is insufficient.  Once those classes have enough images (≥30 each),
switch back to train_classifier_v1.py for full 4-class training.

Usage:
    cd ai-backend
    .\.venv\Scripts\Activate.ps1
    python train_classifier_2class.py

Output:
    cell_classifier_2class.pth
"""

import os
import random
import shutil

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms


# ── CNN Architecture (same backbone as V1, but 2-class head) ──
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


# ── 2-class mapping ──
TARGET_CLASS_TO_IDX = {
    "normal": 0,
    "sickle": 1,
}


def auto_split_dataset(source_dir, train_dir, val_dir, val_ratio=0.2):
    """Auto-split a flat class-folder structure into train/val."""
    classes = sorted([d for d in os.listdir(source_dir)
                      if os.path.isdir(os.path.join(source_dir, d))])

    for cls in classes:
        if cls not in TARGET_CLASS_TO_IDX:
            continue  # skip target / other_abnormal folders
        src_cls = os.path.join(source_dir, cls)
        train_cls = os.path.join(train_dir, cls)
        val_cls = os.path.join(val_dir, cls)
        os.makedirs(train_cls, exist_ok=True)
        os.makedirs(val_cls, exist_ok=True)

        images = [f for f in os.listdir(src_cls)
                  if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        random.shuffle(images)
        split_idx = int(len(images) * (1 - val_ratio))

        for img in images[:split_idx]:
            shutil.copy2(os.path.join(src_cls, img), os.path.join(train_cls, img))
        for img in images[split_idx:]:
            shutil.copy2(os.path.join(src_cls, img), os.path.join(val_cls, img))

        print(f"  {cls}: {split_idx} train, {len(images) - split_idx} val")


def main():
    # ── Configuration ──
    dataset_root = "./dataset_v1_2class"
    train_dir = os.path.join(dataset_root, "train")
    val_dir = os.path.join(dataset_root, "val")
    model_save_path = "cell_classifier_2class.pth"
    batch_size = 32
    num_epochs = 30
    learning_rate = 0.001
    num_classes = 2

    # ── Validate dataset structure ──
    if not os.path.exists(train_dir):
        print(f"ERROR: Training directory '{train_dir}' not found.")
        print("Please create:")
        print("  dataset_v1/train/normal/")
        print("  dataset_v1/train/sickle/")
        return

    for cls_name in TARGET_CLASS_TO_IDX:
        cls_path = os.path.join(train_dir, cls_name)
        if not os.path.exists(cls_path):
            print(f"ERROR: Required class folder '{cls_path}' not found.")
            return
        count = len([f for f in os.listdir(cls_path)
                     if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
        if count < 10:
            print(f"ERROR: '{cls_name}' has only {count} images. Need at least 10.")
            return

    # ── Auto-create val if missing ──
    if not os.path.exists(val_dir):
        print("Val directory not found — auto-splitting from train (20%)...")
        temp_dir = train_dir + "_temp"
        os.rename(train_dir, temp_dir)
        os.makedirs(train_dir, exist_ok=True)
        os.makedirs(val_dir, exist_ok=True)
        auto_split_dataset(temp_dir, train_dir, val_dir)
        shutil.rmtree(temp_dir)

    # ── Transforms ──
    train_transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),
        transforms.RandomRotation(degrees=180),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
        transforms.RandomAffine(degrees=0, translate=(0.05, 0.05), scale=(0.9, 1.1)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # ── Load datasets (only normal + sickle) ──
    train_dataset = datasets.ImageFolder(root=train_dir, transform=train_transform)
    val_dataset = datasets.ImageFolder(root=val_dir, transform=val_transform)

    # Override class_to_idx to match our 2-class mapping
    train_dataset.class_to_idx = TARGET_CLASS_TO_IDX.copy()
    val_dataset.class_to_idx = TARGET_CLASS_TO_IDX.copy()

    # Rebuild samples with forced mapping (skips target/other_abnormal folders)
    train_dataset.samples = _rebuild_samples(train_dir, TARGET_CLASS_TO_IDX)
    train_dataset.targets = [s[1] for s in train_dataset.samples]
    val_dataset.samples = _rebuild_samples(val_dir, TARGET_CLASS_TO_IDX)
    val_dataset.targets = [s[1] for s in val_dataset.samples]

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    print("=" * 56)
    print("  LabMind AI — 2-Class RBC Classifier Training")
    print("  (normal vs sickle only)")
    print("=" * 56)
    print(f"Classes: {TARGET_CLASS_TO_IDX}")
    print(f"Train: {len(train_dataset)} images | Val: {len(val_dataset)} images")

    # ── Class weights (inverse frequency) ──
    class_counts = [0] * num_classes
    for _, label in train_dataset.samples:
        class_counts[label] += 1

    print(f"Class counts: { {k: class_counts[v] for k, v in TARGET_CLASS_TO_IDX.items()} }")

    total = sum(class_counts)
    class_weights = []
    for count in class_counts:
        w = total / (num_classes * count) if count > 0 else 1.0
        class_weights.append(w)
    print(f"Class weights: { {k: round(class_weights[v], 2) for k, v in TARGET_CLASS_TO_IDX.items()} }")

    # ── Model, Loss, Optimizer ──
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = CellClassifierCNN(num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss(weight=torch.FloatTensor(class_weights).to(device))
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # ── Training Loop with Validation ──
    best_val_acc = 0.0
    print(f"\nTraining on {device}...")
    print("-" * 56)

    for epoch in range(num_epochs):
        # Train
        model.train()
        train_loss, train_correct, train_total = 0.0, 0, 0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()

        train_acc = 100 * train_correct / train_total if train_total > 0 else 0

        # Validate
        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()

        val_acc = 100 * val_correct / val_total if val_total > 0 else 0
        t_loss = train_loss / max(len(train_loader), 1)
        v_loss = val_loss / max(len(val_loader), 1)

        marker = ""
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), model_save_path)
            marker = " ★ BEST"

        print(f"Epoch [{epoch+1:2d}/{num_epochs}] "
              f"train_loss={t_loss:.4f} train_acc={train_acc:.1f}% | "
              f"val_loss={v_loss:.4f} val_acc={val_acc:.1f}%{marker}")

    print("-" * 56)
    print(f"Training complete! Best val accuracy: {best_val_acc:.1f}%")
    print(f"Weights saved to: {model_save_path}")
    print()
    print("NOTE: This is a 2-class model (normal vs sickle).")
    print("Once you have ≥30 target and ≥30 other_abnormal images,")
    print("run train_classifier_v1.py for full 4-class training.")

    # ── Per-class Validation Report ──
    print("\n" + "=" * 56)
    print("  Per-Class Validation Report")
    print("=" * 56)
    model.load_state_dict(torch.load(model_save_path, map_location=device, weights_only=True))
    model.eval()

    idx_to_class = {v: k for k, v in TARGET_CLASS_TO_IDX.items()}
    tp = [0] * num_classes
    fp = [0] * num_classes
    fn = [0] * num_classes

    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            for p, t in zip(predicted, labels):
                p, t = p.item(), t.item()
                if p == t:
                    tp[t] += 1
                else:
                    fp[p] += 1
                    fn[t] += 1

    for i in range(num_classes):
        precision = tp[i] / (tp[i] + fp[i]) if (tp[i] + fp[i]) > 0 else 0
        recall = tp[i] / (tp[i] + fn[i]) if (tp[i] + fn[i]) > 0 else 0
        print(f"  {idx_to_class[i]:16s}  precision={precision:.2f}  recall={recall:.2f}")


def _rebuild_samples(root_dir, class_to_idx):
    """Rebuild ImageFolder samples using forced class mapping."""
    samples = []
    valid_exts = ('.jpg', '.jpeg', '.png', '.bmp')
    for cls_name, cls_idx in class_to_idx.items():
        cls_dir = os.path.join(root_dir, cls_name)
        if not os.path.isdir(cls_dir):
            continue
        for fname in sorted(os.listdir(cls_dir)):
            if fname.lower().endswith(valid_exts):
                samples.append((os.path.join(cls_dir, fname), cls_idx))
    return samples


if __name__ == "__main__":
    main()
