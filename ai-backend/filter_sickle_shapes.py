import os
import cv2
import numpy as np
import shutil

def is_circular(img_path, circularity_threshold=0.80):
    """
    Analyzes a localized cell image and calculates its circularity index.
    A perfectly circular cell has an index of 1.0. Lower values indicate elongation or irregularity.
    """
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False
        
    # Apply Otsu's thresholding to isolate the dark cell from the background
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Find cell contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return False
        
    # Get the largest contour assuming it's the cell centered in the crop
    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    perimeter = cv2.arcLength(c, True)
    
    if perimeter == 0:
        return False
        
    # Calculate geometric circularity: 4 * pi * (Area / Perimeter^2)
    circularity = 4 * np.pi * (area / (perimeter * perimeter))
    
    # If the index is above the threshold, it is 'Too Circular'
    return circularity > circularity_threshold

def main():
    print("==================================================")
    print("        DATA DATASET CLEANER: SHAPE FILTER        ")
    print("==================================================")
    
    sickle_dir = os.path.join("dataset", "Sickle")
    iron_deficiency_dir = os.path.join("dataset", "Iron_Deficiency")
    
    if not os.path.exists(sickle_dir):
        print(f"[ERROR] Directory not found: {sickle_dir}")
        print("Please ensure you have run the bulk preparation script first.")
        return
        
    os.makedirs(iron_deficiency_dir, exist_ok=True)
    
    valid_exts = ('.jpg', '.png', '.jpeg', '.bmp')
    images = [f for f in os.listdir(sickle_dir) if f.lower().endswith(valid_exts)]
    
    if not images:
        print(f"[SKIP] No images found in {sickle_dir}.")
        return
        
    print(f"\n[RUNNING] Analyzing {len(images)} potential sickle cells for circularity contamination...")
    print(f"Targeting circularity strictly > 0.80 for removal.\n")
    
    circular_count = 0
    kept_count = 0
    
    for idx, img_name in enumerate(images, 1):
        img_path = os.path.join(sickle_dir, img_name)
        
        # Analyze shape
        if is_circular(img_path, circularity_threshold=0.80):
            # The cell is too circular to be a Sickle Cell. It's likely Iron Deficiency Anemia.
            dest_path = os.path.join(iron_deficiency_dir, img_name)
            shutil.move(img_path, dest_path)
            circular_count += 1
        else:
            # The cell is elongated or crescent enough to stay
            kept_count += 1
            
        # Progress output
        if idx % 500 == 0 or idx == len(images):
            print(f"Processed {idx}/{len(images)} cells...")
            
    print("\n==================================================")
    print("                 FILTERING COMPLETE                 ")
    print("==================================================")
    print(f"Total cells analyzed                  : {len(images)}")
    print(f"Elongated Sickle Cells kept (CLEANED) : {kept_count}")
    print(f"Circular Cells moved to Iron Def.     : {circular_count}")
    print(f"Destination folder                    : {iron_deficiency_dir}")
    print("==================================================")
    print("Dataset scrubbed. You can now retrain the CNN model.")

if __name__ == "__main__":
    main()
