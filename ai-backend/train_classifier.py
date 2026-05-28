import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import os

# --- 1. DEFINE THE LIGHTWEIGHT CNN ARCHITECTURE ---
# A lightweight 4-layer CNN optimized for individual 128x128 cell feature extraction.
class CellClassifierCNN(nn.Module):
    def __init__(self, num_classes=3):
        super(CellClassifierCNN, self).__init__()
        # Input shape: (3, 128, 128)
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # -> 64x64
            
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # -> 32x32
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # -> 16x16
            
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)  # -> 8x8
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(128 * 8 * 8, 256),
            nn.ReLU(),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x

def main():
    # --- 2. CONFIGURATION & DATASETS ---
    dataset_path = "./dataset" # Target root folder: /dataset/Normal, /dataset/Sickle, /dataset/Malaria
    model_save_path = "cell_classifier.pth"
    batch_size = 32
    num_epochs = 20
    learning_rate = 0.001

    if not os.path.exists(dataset_path):
        print(f"ERROR: Dataset directory '{dataset_path}' not found.")
        print("Please structure your cropped images into subfolders:")
        print("  dataset/Normal/")
        print("  dataset/Sickle/")
        print("  dataset/Malaria/")
        return

    # Transformations (Resize, Data Augmentation to prevent overfitting, Normalization)
    transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),
        transforms.RandomRotation(degrees=180),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # Load Dataset
    dataset = datasets.ImageFolder(root=dataset_path, transform=transform)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    num_classes = len(dataset.classes)
    class_names = dataset.classes
    print(f"Found {len(dataset)} images across {num_classes} classes: {class_names}")

    # --- 2.5 CALCULATE CLASS WEIGHTS TO HANDLE IMBALANCE ---
    # Normal cells heavily outnumber Sickle cells. Inverse frequency forces the model to care about the minority.
    class_counts = [0] * num_classes
    for _, label in dataset.samples:
        class_counts[label] += 1
        
    print(f"Class counts: {dict(zip(class_names, class_counts))}")
    
    total_samples = sum(class_counts)
    class_weights = []
    for count in class_counts:
        weight = total_samples / (num_classes * count) if count > 0 else 0.0
        class_weights.append(weight)
        
    print(f"Calculated Class Weights: {dict(zip(class_names, [round(w, 2) for w in class_weights]))}")

    # --- 3. INITIALIZE MODEL, LOSS & OPTIMIZER ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = CellClassifierCNN(num_classes=num_classes).to(device)
    
    # Apply the heavy punishment weights to the Loss Function natively on the hardware
    tensor_weights = torch.FloatTensor(class_weights).to(device)
    criterion = nn.CrossEntropyLoss(weight=tensor_weights)
    
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # --- 4. TRAINING LOOP ---
    print(f"Starting training on {device}...")
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for images, labels in dataloader:
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
        epoch_loss = running_loss / len(dataloader)
        epoch_acc = 100 * correct / total
        print(f"Epoch [{epoch+1}/{num_epochs}] | Loss: {epoch_loss:.4f} | Accuracy: {epoch_acc:.2f}%")

    # --- 5. SAVE WEIGHTS ---
    torch.save(model.state_dict(), model_save_path)
    print(f"Training complete! Model weights saved to {model_save_path}")
    print("Stage 3 classification model is ready for main.py induction!")

if __name__ == "__main__":
    main()
