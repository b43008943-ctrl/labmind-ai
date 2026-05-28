"""
Sickle Cell Data Augmentation Engine
Generates 9 augmented variations per original sickle cell image
to increase the Sickle class from ~450 to ~4500 images.
"""
import os
import cv2
import numpy as np
import random
import uuid

sickle_dir = os.path.join("dataset", "train", "Sickle")

if not os.path.exists(sickle_dir):
    print(f"[ERROR] Directory '{sickle_dir}' not found.")
    exit()

valid_exts = ('.jpg', '.png', '.jpeg', '.bmp')
originals = [f for f in os.listdir(sickle_dir) if f.lower().endswith(valid_exts)]
original_count = len(originals)

if original_count == 0:
    print("[ERROR] No images found in Sickle directory.")
    exit()

print("==================================================")
print("  SICKLE CELL DATA AUGMENTATION ENGINE")
print("==================================================")
print(f"  Original Sickle images: {original_count}")
print(f"  Target: ~{original_count * 10} images (9 augments each)")
print("==================================================")


def random_rotation(img):
    """Rotate image by a random angle (0-360)."""
    angle = random.uniform(0, 360)
    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)


def horizontal_flip(img):
    """Flip image horizontally."""
    return cv2.flip(img, 1)


def vertical_flip(img):
    """Flip image vertically."""
    return cv2.flip(img, 0)


def brightness_contrast(img):
    """Randomly adjust brightness and contrast."""
    alpha = random.uniform(0.7, 1.3)  # contrast
    beta = random.randint(-30, 30)     # brightness
    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)


def zoom_shift(img):
    """Slight random zoom and shift to simulate off-center cells."""
    h, w = img.shape[:2]
    scale = random.uniform(0.85, 1.15)
    shift_x = random.randint(-8, 8)
    shift_y = random.randint(-8, 8)
    M = np.float32([
        [scale, 0, shift_x + (1 - scale) * w / 2],
        [0, scale, shift_y + (1 - scale) * h / 2]
    ])
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)


def gaussian_blur(img):
    """Apply slight Gaussian blur to simulate faint cells."""
    ksize = random.choice([3, 5])
    return cv2.GaussianBlur(img, (ksize, ksize), 0)


def gaussian_noise(img):
    """Add slight Gaussian noise."""
    noise = np.random.normal(0, 10, img.shape).astype(np.int16)
    noisy = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisy


# Define 9 augmentation pipelines
augment_pipelines = [
    lambda img: random_rotation(img),
    lambda img: horizontal_flip(img),
    lambda img: vertical_flip(img),
    lambda img: brightness_contrast(img),
    lambda img: zoom_shift(img),
    lambda img: gaussian_blur(random_rotation(img)),
    lambda img: brightness_contrast(horizontal_flip(img)),
    lambda img: gaussian_noise(random_rotation(img)),
    lambda img: zoom_shift(brightness_contrast(vertical_flip(img))),
]

augmented_count = 0

for idx, img_name in enumerate(originals, 1):
    img_path = os.path.join(sickle_dir, img_name)
    img = cv2.imread(img_path)
    if img is None:
        continue

    for pipeline in augment_pipelines:
        try:
            aug_img = pipeline(img)
            # Ensure output is 128x128
            aug_img = cv2.resize(aug_img, (128, 128))
            unique_name = f"aug_{uuid.uuid4().hex[:8]}.jpg"
            cv2.imwrite(os.path.join(sickle_dir, unique_name), aug_img)
            augmented_count += 1
        except Exception as e:
            continue

    if idx % 100 == 0:
        print(f"[RUNNING] Processed {idx} / {original_count} originals...")

final_count = len([f for f in os.listdir(sickle_dir) if f.lower().endswith(valid_exts)])

print("\n==================================================")
print("  AUGMENTATION COMPLETE! SUMMARY:")
print("==================================================")
print(f"  Original images: {original_count}")
print(f"  New augmented images: {augmented_count}")
print(f"  Total Sickle images now: {final_count}")
print("==================================================")
