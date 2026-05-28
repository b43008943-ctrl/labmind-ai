import os
import cv2
import torch
import gc
from ultralytics import YOLO

# --- Configuration ---
RAW_DATA_PATH = "dataset_raw"
OUTPUT_BASE = "dataset"
MODEL_PATH = "blood_ai_v2.pt"  # Ensure this matches your YOLO model filename
IMG_SIZE = 128
CONF_THRESHOLD = 0.3

def process_and_crop():
    print("🚀 Initializing Smart Dataset Harvesting...")
    
    # Load the model
    try:
        model = YOLO(MODEL_PATH)
    except Exception as e:
        print(f"❌ Error loading YOLO model: {e}")
        return
    
    # Focus only on Sickle category as Normal is already done
    categories = ['Sickle'] 
    
    for category in categories:
        in_dir = os.path.join(RAW_DATA_PATH, category)
        out_dir = os.path.join(OUTPUT_BASE, category)
        os.makedirs(out_dir, exist_ok=True)
        
        # Get list of images
        images = [f for f in os.listdir(in_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        print(f"📂 Found {len(images)} images in {category} folder.")

        for i, img_name in enumerate(images):
            # Check if this image was already processed to skip it
            output_prefix = f"{category}_{img_name.split('.')[0]}"
            # Simple check: if any file starting with this prefix exists, skip
            if any(f.startswith(output_prefix) for f in os.listdir(out_dir)):
                print(f"⏩ Skipping {i+1}/{len(images)}: {img_name} (Already Processed)")
                continue

            img_path = os.path.join(in_dir, img_name)
            
            try:
                # Read Image
                img = cv2.imread(img_path)
                if img is None:
                    continue

                # Run YOLO detection
                results = model(img, conf=CONF_THRESHOLD, verbose=False)
                
                cell_count = 0
                for result in results:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    for j, box in enumerate(boxes):
                        x1, y1, x2, y2 = map(int, box)
                        
                        # Crop and Resize
                        cell_crop = img[y1:y2, x1:x2]
                        if cell_crop.size == 0:
                            continue
                        
                        cell_resized = cv2.resize(cell_crop, (IMG_SIZE, IMG_SIZE))
                        
                        # Save the cropped cell
                        save_name = f"{output_prefix}_cell_{j}.jpg"
                        save_path = os.path.join(out_dir, save_name)
                        cv2.imwrite(save_path, cell_resized)
                        cell_count += 1

                print(f"✅ Image {i+1}/{len(images)}: Extracted {cell_count} cells from {img_name}")

                # --- Crucial: Clear Memory after each image ---
                del img
                del results
                gc.collect()

            except Exception as e:
                print(f"⚠️ Error processing {img_name}: {e}")
                continue

    print("\n🎉 [DONE] Harvesting complete. Memory cleared and dataset is ready!")

if __name__ == "__main__":
    process_and_crop()
