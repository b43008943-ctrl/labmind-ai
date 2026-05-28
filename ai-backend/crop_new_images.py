"""
YOLO Cell Cropper - Safe UUID-based cropping for dataset expansion.
Reads raw blood smear images, detects cells via YOLO, and saves
each crop with a unique UUID filename to prevent overwrites.
"""
import os
import cv2
import uuid
from ultralytics import YOLO
import warnings
warnings.filterwarnings('ignore')

def main():
    input_dir = "new_raw_images"
    output_dir = "new_cropped_cells"
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Load the same YOLO model used in the diagnostic pipeline
    model = YOLO("blood_ai_v2.pt")
    print("[SYSTEM] YOLO model loaded.")

    valid_exts = ('.jpg', '.png', '.jpeg', '.bmp')
    images = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_exts)]

    if not images:
        print(f"\n[ACTION REQUIRED] Place raw blood smear images in '{input_dir}/' and re-run.")
        return

    total_crops = 0

    for img_name in images:
        img_path = os.path.join(input_dir, img_name)
        img = cv2.imread(img_path)
        if img is None:
            continue

        h_img, w_img = img.shape[:2]
        results = model(img, conf=0.05, verbose=False)

        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()

            for box in boxes:
                x1, y1, x2, y2 = map(int, box)

                # Basic sanity: skip tiny noise or out-of-bounds
                w, h = x2 - x1, y2 - y1
                if w < 5 or h < 5:
                    continue

                # Pad by 4px for edge preservation
                y1_p = max(0, y1 - 4)
                y2_p = min(h_img, y2 + 4)
                x1_p = max(0, x1 - 4)
                x2_p = min(w_img, x2 + 4)

                crop = img[y1_p:y2_p, x1_p:x2_p]
                if crop.size == 0:
                    continue

                # Resize to CNN training standard
                crop = cv2.resize(crop, (128, 128))

                # Save with UUID filename to guarantee uniqueness
                unique_name = f"cell_{uuid.uuid4().hex[:8]}.jpg"
                cv2.imwrite(os.path.join(output_dir, unique_name), crop)
                total_crops += 1

    print(f"\n[SUCCESS] Cropped {total_crops} cells from {len(images)} images.")
    print(f"All crops saved to: {os.path.abspath(output_dir)}")

if __name__ == '__main__':
    main()
