import cv2
import numpy as np

def extract_single_cells(image_bgr, yolo_results):
    """
    STAGE 2: SEGMENTATION & CROPPING
    Takes the original high-res image and YOLO bounding box results,
    and returns a list of cropped, standardized individual cell image arrays
    ready for Stage 3 CNN classification.
    """
    cropped_cells = []
    
    # Iterate through all bounding boxes detected by YOLO in Stage 1
    for result in yolo_results:
        bounding_boxes = result.boxes
        
        for box in bounding_boxes:
            # 1. Extract raw coordinates: [x1, y1, x2, y2]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Extract metadata (useful for filtering what gets sent to the CNN)
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            
            # 2. Safety Bounds & Padding (Ensure we capture the whole cell edge)
            padding = 4
            h, w = image_bgr.shape[:2]
            
            x1_pad = max(0, x1 - padding)
            y1_pad = max(0, y1 - padding)
            x2_pad = min(w, x2 + padding)
            y2_pad = min(h, y2 + padding)
            
            # 3. OpenCV Slicing (The actual crop)
            cell_crop = image_bgr[y1_pad:y2_pad, x1_pad:x2_pad]
            
            # Skip invalid crops
            if cell_crop.size == 0:
                continue
                
            # 4. Standardization for CNN Input
            # Most MobileNet/ResNet models expect 128x128 or 224x224
            # (In production, you might pad to square to preserve aspect ratio)
            standardized_crop = cv2.resize(cell_crop, (128, 128))
            
            # Save the payload
            cropped_cells.append({
                "cell_image": standardized_crop,
                "original_bbox": [x1, y1, x2, y2],
                "yolo_class_id": cls_id,
                "yolo_confidence": conf
            })
            
    return cropped_cells

# --- Example Usage for the upcoming pipeline: ---
# 1. stage_1_results = model.predict(image, conf=0.15)
# 2. isolated_cells = extract_single_cells(original_cv2_image, stage_1_results)
# 3. for cell in isolated_cells:
#        prediction = cnn_model.predict(cell["cell_image"])
#        # Aggregate results...
