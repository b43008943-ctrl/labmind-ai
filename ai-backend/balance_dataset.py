import os
import random

normal_dir = os.path.join("dataset", "train", "Normal")
keep_count = 1500

images = [f for f in os.listdir(normal_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]

if len(images) <= keep_count:
    print(f"Dataset already balanced or has fewer than {keep_count} images. Contains {len(images)} images.")
    exit()

print("==================================================")
print(f"  BALANCING DATASET: Reducing from {len(images)} to {keep_count}")
print("==================================================")

# Randomly select images to delete
random.shuffle(images)
images_to_delete = images[keep_count:]

deleted = 0
for img_name in images_to_delete:
    try:
        os.remove(os.path.join(normal_dir, img_name))
        deleted += 1
    except Exception as e:
        print(f"Error deleting {img_name}: {e}")

print(f" -> Deleted {deleted} normal cells.")
print(f" -> Dataset is now balanced! Remaining: {len(os.listdir(normal_dir))}")
