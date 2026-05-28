"""
LabMind AI — V1 Rebuild: 4-Class Manual Cell Sorting Tool

Displays each cropped cell image for manual classification into 4 RBC classes.

Controls:
  'n' → Normal
  's' → Sickle
  't' → Target
  'a' → Other Abnormal
  'd' → Delete (bad crop / artifact)
  'q' → Quit early

Usage:
  cd ai-backend
  python sort_tool_v1.py [source_directory]

  Default source: cropped_cells/sickle/
"""

import os
import sys
import shutil
import cv2


def main():
    # Source directory (default: cropped_cells/sickle for re-sorting)
    source_dir = sys.argv[1] if len(sys.argv) > 1 else "cropped_cells/sickle"

    # Destination directories
    base_dir = os.path.join("dataset_v1", "train")
    targets = {
        ord('n'): ("normal",         os.path.join(base_dir, "normal")),
        ord('s'): ("sickle",         os.path.join(base_dir, "sickle")),
        ord('t'): ("target",         os.path.join(base_dir, "target")),
        ord('a'): ("other_abnormal", os.path.join(base_dir, "other_abnormal")),
    }

    # Create all destination dirs
    for _, (_, path) in targets.items():
        os.makedirs(path, exist_ok=True)

    valid_exts = ('.jpg', '.png', '.jpeg', '.bmp')
    images = sorted([f for f in os.listdir(source_dir) if f.lower().endswith(valid_exts)])

    if not images:
        print(f"[EMPTY] No images found in '{source_dir}/'.")
        return

    print("=" * 56)
    print("   LABMIND V1: 4-CLASS CELL SORTING TOOL")
    print("=" * 56)
    print(f"Source: {source_dir}/")
    print(f"Found {len(images)} cells to classify.")
    print()
    print("  [n] Normal        [s] Sickle")
    print("  [t] Target        [a] Other Abnormal")
    print("  [d] Delete        [q] Quit")
    print("-" * 56)

    counts = {"normal": 0, "sickle": 0, "target": 0, "other_abnormal": 0, "deleted": 0}
    window_name = "[n]=Normal [s]=Sickle [t]=Target [a]=Abnormal [d]=Delete [q]=Quit"

    for i, img_name in enumerate(images, 1):
        img_path = os.path.join(source_dir, img_name)
        img = cv2.imread(img_path)
        if img is None:
            continue

        # Display at 256x256 for clear visibility
        display = cv2.resize(img, (256, 256), interpolation=cv2.INTER_NEAREST)
        cv2.imshow(window_name, display)

        print(f"  [{i}/{len(images)}] {img_name} → ", end="", flush=True)

        while True:
            key = cv2.waitKey(0) & 0xFF

            if key in targets:
                label, dest_dir = targets[key]
                shutil.move(img_path, os.path.join(dest_dir, img_name))
                counts[label] += 1
                print(label.upper())
                break
            elif key == ord('d'):
                os.remove(img_path)
                counts["deleted"] += 1
                print("DELETED")
                break
            elif key == ord('q'):
                print("QUIT")
                cv2.destroyAllWindows()
                _print_summary(counts, i - 1, len(images))
                return

    cv2.destroyAllWindows()
    _print_summary(counts, len(images), len(images))


def _print_summary(counts, done, total):
    print(f"\n[{'COMPLETE' if done == total else 'EARLY EXIT'}] "
          f"Sorted {done}/{total} cells.")
    for label, count in counts.items():
        if count > 0:
            print(f"  {label}: {count}")


if __name__ == '__main__':
    main()
