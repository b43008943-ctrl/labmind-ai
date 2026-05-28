import cv2
import torch
import torch.nn as nn
from torchvision import transforms
from ultralytics import YOLO
import os
import numpy as np

# --- 1. DEFINE CNN ARCHITECTURE FOR INFERENCE ---
class CellClassifierCNN(nn.Module):
    def __init__(self, num_classes=3):
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

def check_blood_sample():
    print("Initializing Clinical Inference Engine...")
    
    # --- 2. LOAD MODELS ---
    try:
        yolo_model = YOLO('blood_ai_v2.pt')
        print("Stage 1 YOLO loaded.")
    except Exception as e:
        print(f"Error loading YOLO: {e}")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cnn_model = CellClassifierCNN(num_classes=2) # Adjust to 3 if you trained on Malaria too
    
    try:
        cnn_model.load_state_dict(torch.load('cell_classifier.pth', map_location=device, weights_only=True))
        cnn_model.to(device)
        cnn_model.eval()
        print("Stage 3 CNN weights loaded.")
    except Exception as e:
        print(f"Error loading CNN weights: {e}")
        return

    # Assuming alphabetical order from the dataset folders:
    class_names = ['Normal', 'Sickle'] # Update to ['Malaria', 'Normal', 'Sickle'] if 3 classes
    
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    test_dir = 'test_samples'
    results_dir = 'results'
    os.makedirs(test_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    image_files = [f for f in os.listdir(test_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        print(f"No test images found in {test_dir}. Please place some raw images there.")
        return

    for img_name in image_files:
        print(f"\nProcessing {img_name}...")
        img_path = os.path.join(test_dir, img_name)
        img = cv2.imread(img_path)
        if img is None: continue
        
        output_img = img.copy()
        h_img, w_img = img.shape[:2]
        
        # STAGE 1: YOLO Detection
        results = yolo_model(img, conf=0.15, verbose=False)
        
        total_rbcs = 0
        sickle_count = 0
        normal_count = 0

        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                if cls_id not in [1, 3]: # Filter out non-RBCs if applicable
                    continue
                    
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # STAGE 2: Cropping (with padding)
                padding = 4
                y1_p, y2_p = max(0, y1 - padding), min(h_img, y2 + padding)
                x1_p, x2_p = max(0, x1 - padding), min(w_img, x2 + padding)
                
                cell_crop = img[y1_p:y2_p, x1_p:x2_p]
                if cell_crop.size == 0: continue
                
                # STAGE 3: CNN Classification
                cell_rgb = cv2.cvtColor(cell_crop, cv2.COLOR_BGR2RGB)
                tensor = transform(cell_rgb).unsqueeze(0).to(device)
                
                with torch.no_grad():
                    outputs = cnn_model(tensor)
                    _, predicted = torch.max(outputs, 1)
                    label = class_names[predicted.item()]
                
                total_rbcs += 1
                if label == 'Sickle':
                    sickle_count += 1
                    color = (0, 0, 255) # Red
                else:
                    normal_count += 1
                    color = (0, 255, 0) # Green
                    
                # Draw Bounding Box
                cv2.rectangle(output_img, (x1, y1), (x2, y2), color, 2)
                # cv2.putText(output_img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # STAGE 4: Aggregation & Overlay
        sickle_percentage = 0.0
        if total_rbcs > 0:
            sickle_percentage = (sickle_count / total_rbcs) * 100
            
        overlay_text_1 = f"Cells Analyzed: {total_rbcs} (Sickle: {sickle_count}, Normal: {normal_count})"
        overlay_text_2 = f"Sickle Percentage: {sickle_percentage:.2f}%"
        
        # Add text overlay to image
        cv2.rectangle(output_img, (10, 10), (600, 90), (0, 0, 0), -1)
        cv2.putText(output_img, overlay_text_1, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        text_color = (0, 0, 255) if sickle_percentage > 5.0 else (0, 255, 0)
        cv2.putText(output_img, overlay_text_2, (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2)
        
        # Save output
        save_path = os.path.join(results_dir, f"annotated_{img_name}")
        cv2.imwrite(save_path, output_img)
        print(f"Saved annotated result to {save_path}")

    print("\nInference Complete!")

if __name__ == "__main__":
    check_blood_sample()
