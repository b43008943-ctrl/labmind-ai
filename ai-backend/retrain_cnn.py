"""
CNN Fine-Tuning Script - Gently upgrades the existing cell_classifier.pth
with newly annotated ground-truth data from the Doctor.

Uses a LOW learning rate (0.0001) to preserve previously learned weights
while absorbing the new Sickle cell examples.
"""
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import warnings
warnings.filterwarnings('ignore')

# --- CNN Architecture (must match the original) ---
class CellClassifierCNN(nn.Module):
    def __init__(self, num_classes=2):
        super(CellClassifierCNN, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2, 2)
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.5), nn.Linear(128 * 8 * 8, 256), nn.ReLU(), nn.Linear(256, num_classes)
        )
    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)

def main():
    print("=" * 50)
    print("   CNN FINE-TUNING ENGINE")
    print("=" * 50)

    # --- CONFIG ---
    data_dir = "dataset/train"
    old_weights = "cell_classifier.pth"
    new_weights = "cell_classifier_v3.pth"
    epochs = 15
    lr = 0.0001  # Low LR to preserve existing knowledge
    batch_size = 32

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[SYSTEM] Device: {device.type.upper()}")

    # --- DATA PIPELINE WITH AUGMENTATION ---
    transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),
        transforms.RandomRotation(degrees=180),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    dataset = datasets.ImageFolder(data_dir, transform=transform)
    num_classes = len(dataset.classes)
    class_names = dataset.classes
    print(f"[DATA] Found {len(dataset)} images across {num_classes} classes: {class_names}")

    # --- INVERSE FREQUENCY CLASS WEIGHTS ---
    class_counts = [0] * num_classes
    for _, label in dataset.samples:
        class_counts[label] += 1

    total = sum(class_counts)
    class_weights = [total / (num_classes * count) if count > 0 else 1.0 for count in class_counts]
    weight_tensor = torch.FloatTensor(class_weights).to(device)

    for i, name in enumerate(class_names):
        print(f"  {name}: {class_counts[i]} images (weight: {class_weights[i]:.2f})")

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # --- LOAD EXISTING MODEL ---
    model = CellClassifierCNN(num_classes=num_classes).to(device)
    if os.path.exists(old_weights):
        model.load_state_dict(torch.load(old_weights, map_location=device, weights_only=True))
        print(f"\n[LOADED] Existing weights from '{old_weights}'")
        print(f"[MODE] Fine-tuning with lr={lr} (gentle weight adjustment)")
    else:
        print(f"\n[WARNING] '{old_weights}' not found. Training from scratch.")

    # --- OPTIMIZER & LOSS ---
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss(weight=weight_tensor)

    # --- TRAINING LOOP ---
    print(f"\n[TRAINING] {epochs} epochs on {len(dataset)} images...\n")
    model.train()

    for epoch in range(1, epochs + 1):
        running_loss = 0.0
        correct = 0
        total_samples = 0

        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, predicted = torch.max(outputs, 1)
            correct += (predicted == labels).sum().item()
            total_samples += labels.size(0)

        epoch_loss = running_loss / total_samples
        epoch_acc = 100.0 * correct / total_samples
        print(f"  Epoch {epoch:02d}/{epochs} | Loss: {epoch_loss:.4f} | Acc: {epoch_acc:.2f}%")

    # --- SAVE NEW WEIGHTS ---
    torch.save(model.state_dict(), new_weights)
    print(f"\n[SUCCESS] Fine-tuned model saved as '{new_weights}'")
    print(f"  Final Loss: {epoch_loss:.4f}")
    print(f"  Final Accuracy: {epoch_acc:.2f}%")
    print(f"\nTo use: Update main_diagnostic_system.py to load '{new_weights}' instead of '{old_weights}'")

if __name__ == '__main__':
    main()
