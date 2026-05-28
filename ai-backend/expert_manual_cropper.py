import cv2
import os
import uuid

raw_dir = "new_raw_images"
sickle_dir = os.path.join("dataset", "train", "Sickle")

os.makedirs(raw_dir, exist_ok=True)
os.makedirs(sickle_dir, exist_ok=True)

images = [f for f in os.listdir(raw_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

if not images:
    print(f"[ACTION REQUIRED] Please place your raw blood smear images inside the '{raw_dir}' folder and run again.")
    exit()

print("==================================================")
print("  SMART ANALYST: EXPERT MANUAL CROPPER")
print("==================================================")
print("1. Drag the mouse to draw a box around a cell.")
print("2. Press SPACE or ENTER to confirm the box.")
print("3. Press 's' to save as SICKLE.")
print("4. Press 'd' to skip to the NEXT IMAGE.")
print("5. Press 'q' to QUIT and save progress.")
print("==================================================")

for img_name in images:
    img_path = os.path.join(raw_dir, img_name)
    img = cv2.imread(img_path)
    if img is None: continue
    
    h, w = img.shape[:2]
    max_height = 800
    if h > max_height:
        scale = max_height / h
        img = cv2.resize(img, (int(w * scale), max_height))

    while True:
        clone = img.copy()
        cv2.putText(clone, f"Image: {img_name} | Draw box -> Enter -> 's'. 'd'=Next, 'q'=Quit", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        bbox = cv2.selectROI("Expert Cropper", clone, fromCenter=False, showCrosshair=True)
        
        if bbox == (0, 0, 0, 0): 
            break
            
        x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        if w > 0 and h > 0:
            crop_img = img[y:y+h, x:x+w]
            crop_img = cv2.resize(crop_img, (128, 128))
            
            cv2.imshow("Review Crop (s=Sickle, c=Cancel)", crop_img)
            key = cv2.waitKey(0) & 0xFF
            try:
                cv2.destroyWindow("Review Crop")
            except:
                pass
            
            unique_name = f"manual_{uuid.uuid4().hex[:8]}.jpg"
            
            if key == ord('s'):
                cv2.imwrite(os.path.join(sickle_dir, unique_name), crop_img)
                print(f" -> Saved 1 SICKLE cell.")
            elif key == ord('d'):
                break 
            elif key == ord('q'):
                print("Exiting...")
                exit()
