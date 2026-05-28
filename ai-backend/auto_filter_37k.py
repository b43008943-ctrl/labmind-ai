import os
import cv2
import shutil

input_dir = "new_cropped_cells"
normal_dir = os.path.join("dataset", "train", "Normal")
suspect_dir = "suspect_sickle_cells"

os.makedirs(normal_dir, exist_ok=True)
os.makedirs(suspect_dir, exist_ok=True)

images = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
total = len(images)

print("==================================================")
print(f"  SMART ANALYST: FILTERING {total} CELLS...")
print("==================================================")

normal_count = 0
suspect_count = 0

for idx, img_name in enumerate(images, 1):
    img_path = os.path.join(input_dir, img_name)
    img = cv2.imread(img_path)
    if img is None: continue
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    is_suspect = False
    if contours:
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        aspect_ratio = max(w, h) / float(min(w, h)) if min(w, h) > 0 else 1.0
        if aspect_ratio >= 1.25:
            is_suspect = True

    if is_suspect:
        shutil.move(img_path, os.path.join(suspect_dir, img_name))
        suspect_count += 1
    else:
        shutil.move(img_path, os.path.join(normal_dir, img_name))
        normal_count += 1
        
    if idx % 1000 == 0:
        print(f"[RUNNING] Processed {idx} / {total} cells...")

print("\n==================================================")
print("  FILTERING COMPLETE! SUMMARY:")
print("==================================================")
print(f" -> Sent to Normal (Auto-saved): {normal_count} cells")
print(f" -> Sent to Suspects (Needs your review): {suspect_count} cells")
