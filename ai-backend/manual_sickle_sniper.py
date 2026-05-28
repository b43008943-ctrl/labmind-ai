import os
import cv2

# Global variables for mouse callback and cropping
cropping = False
x_start, y_start, x_end, y_end = 0, 0, 0, 0
current_img = None
display_img = None

def mouse_crop(event, x, y, flags, param):
    global x_start, y_start, x_end, y_end, cropping, current_img, display_img

    if event == cv2.EVENT_LBUTTONDOWN:
        x_start, y_start, x_end, y_end = x, y, x, y
        cropping = True
        
    elif event == cv2.EVENT_MOUSEMOVE:
        if cropping:
            display_img = current_img.copy()
            cv2.rectangle(display_img, (x_start, y_start), (x, y), (0, 0, 255), 2)
            
    elif event == cv2.EVENT_LBUTTONUP:
        x_end, y_end = x, y
        cropping = False
        display_img = current_img.copy()
        cv2.rectangle(display_img, (x_start, y_start), (x_end, y_end), (0, 255, 0), 2)

def main():
    print("==================================================")
    print("      MANUAL SICKLE SNIPER: CLINICAL ANNOTATION     ")
    print("==================================================")
    print("Instructions:")
    print(" - Click and drag left mouse button to draw a box.")
    print(" - Press 'c' to Crop & Save the selected cell.")
    print(" - Press 'n' to skip to the Next image.")
    print(" - Press 'q' to Quit the program.")
    print("==================================================")

    raw_dir = os.path.join("dataset_raw", "Sickle")
    out_dir = os.path.join("dataset", "Sickle")

    if not os.path.exists(raw_dir):
        print(f"[ERROR] Directory not found: {raw_dir}")
        return

    os.makedirs(out_dir, exist_ok=True)

    valid_exts = ('.jpg', '.png', '.jpeg', '.bmp')
    images = [f for f in os.listdir(raw_dir) if f.lower().endswith(valid_exts)]
    
    if not images:
        print(f"[SKIP] No raw images found in {raw_dir}.")
        return

    global current_img, display_img, x_start, y_start, x_end, y_end
    
    cv2.namedWindow("Sickle Sniper", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Sickle Sniper", cv2.WND_PROP_TOPMOST, 1)
    cv2.setMouseCallback("Sickle Sniper", mouse_crop)

    cell_counter = 0

    for idx, img_name in enumerate(images, 1):
        img_path = os.path.join(raw_dir, img_name)
        img_base = os.path.splitext(img_name)[0]
        
        current_img = cv2.imread(img_path)
        if current_img is None:
            continue
            
        display_img = current_img.copy()
        print(f"\n[Image {idx}/{len(images)}] Loaded: {img_name}")
        
        while True:
            cv2.imshow("Sickle Sniper", display_img)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('c'):
                # Handle inverse drawing (drag up-left instead of down-right)
                x1, x2 = min(x_start, x_end), max(x_start, x_end)
                y1, y2 = min(y_start, y_end), max(y_start, y_end)
                
                # Check if a valid box was drawn
                if x2 - x1 > 0 and y2 - y1 > 0:
                    roi = current_img[y1:y2, x1:x2]
                    
                    try:
                        # Resize to exact CNN dimension requirements
                        resized_roi = cv2.resize(roi, (128, 128))
                        cell_counter += 1
                        
                        save_name = f"manual_sickle_{img_base}_{cell_counter}.jpg"
                        save_path = os.path.join(out_dir, save_name)
                        
                        cv2.imwrite(save_path, resized_roi)
                        print(f"  [SAVED] Snipped cell {cell_counter} -> {save_path}")
                        
                        # Permanently draw a thick blue box on the master image indicating it was already chopped
                        cv2.rectangle(current_img, (x1, y1), (x2, y2), (255, 0, 0), 6)
                        cv2.putText(current_img, "SAVED", (x1, max(y1 - 10, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                        display_img = current_img.copy()
                        
                        # Reset coordinates so you can't double-save the same box
                        x_start, y_start, x_end, y_end = 0, 0, 0, 0
                        
                    except Exception as e:
                        print(f"  [ERROR] Crop failed (Box too close to edge or invalid): {e}")
                else:
                    print("  [WAIT] Please click and drag a box before pressing 'c'.")
                    
            elif key == ord('n'):
                # Move to next image
                break
                
            elif key == ord('q'):
                # Hard exit the program
                print("\n[QUIT] Exiting Manual Sniper.")
                cv2.destroyAllWindows()
                return

    cv2.destroyAllWindows()
    print("\n==================================================")
    print("               ANNOTATION COMPLETE                ")
    print("==================================================")
    print(f"Successfully harvested {cell_counter} pure sickle cells.")
    print(f"They are safely stored in: {out_dir}")
    print("You may now retrain your CNN with pristine data.")

if __name__ == "__main__":
    main()
