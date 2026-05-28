import os
import cv2
import shutil

def is_elongated(img_path, min_aspect_ratio=1.45):
    """
    Analyzes a localized cell image, finds the bounding box of the cell mass,
    and calculates the Aspect Ratio (max(width, height) / min(width, height)).
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
    
    # Get the bounding rectangle for the contour
    x, y, w, h = cv2.boundingRect(c)
    
    if w == 0 or h == 0:
        return False
        
    # Aspect ratio: max dimension divided by min dimension
    aspect_ratio = max(w, h) / min(w, h)
    
    # Return True if the aspect ratio indicates it's elongated enough
    return aspect_ratio >= min_aspect_ratio

def main():
    print("==================================================")
    print("      DATASET CLEANER: STRICT ASPECT RATIO        ")
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
        
    print(f"\n[RUNNING] Analyzing {len(images)} potential sickle cells for strict elongation...")
    print(f"Targeting Aspect Ratio strictly >= 1.45 to KEEP.\n")
    
    square_count = 0
    crescent_count = 0
    
    for idx, img_name in enumerate(images, 1):
        img_path = os.path.join(sickle_dir, img_name)
        
        # Analyze shape
        if is_elongated(img_path, min_aspect_ratio=1.45):
            # The cell is distinctly elongated or crescent-shaped
            crescent_count += 1
        else:
            # The cell is too square/round. Move it.
            dest_path = os.path.join(iron_deficiency_dir, img_name)
            shutil.move(img_path, dest_path)
            square_count += 1
            
        # Progress output
        if idx % 500 == 0 or idx == len(images):
            print(f"Processed {idx}/{len(images)} cells...")
            
    print("\n==================================================")
    print("                 FILTERING COMPLETE                 ")
    print("==================================================")
    print(f"Total cells analyzed               : {len(images)}")
    print(f"True Elongated/Crescent kept       : {crescent_count}")
    print(f"Square/Round moved to Iron Def.    : {square_count}")
    print(f"Destination folder                 : {iron_deficiency_dir}")
    print("==================================================")
    print("Dataset strictly scrubbed. You can now retrain the CNN model.")

if __name__ == "__main__":
    main()
