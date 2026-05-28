"""
Manual Cell Sorting Tool - Clinical-Grade Dataset Classification.
Displays each cropped cell for the Doctor to classify with a single keypress.

Controls:
  's' - Move to dataset/train/Sickle/
  'n' - Move to dataset/train/Normal/
  'd' - Delete (bad crop / artifact)
  'q' - Quit early
"""
import os
import cv2
import shutil

def main():
    source_dir = "suspect_sickle_cells"
    sickle_dir = os.path.join("dataset", "train", "Sickle")
    normal_dir = os.path.join("dataset", "train", "Normal")

    os.makedirs(sickle_dir, exist_ok=True)
    os.makedirs(normal_dir, exist_ok=True)

    valid_exts = ('.jpg', '.png', '.jpeg', '.bmp')
    images = sorted([f for f in os.listdir(source_dir) if f.lower().endswith(valid_exts)])

    if not images:
        print(f"[EMPTY] No images found in '{source_dir}/'. Nothing to sort.")
        return

    print("=" * 50)
    print("   MANUAL CELL SORTING TOOL")
    print("=" * 50)
    print(f"Found {len(images)} cells to classify.")
    print("Controls: 's'=Sickle | 'n'=Normal | 'd'=Delete | 'q'=Quit")
    print("-" * 50)

    sickle_count = 0
    normal_count = 0
    delete_count = 0
    window_name = "Sort Cell: [s]=Sickle  [n]=Normal  [d]=Delete  [q]=Quit"

    for i, img_name in enumerate(images, 1):
        img_path = os.path.join(source_dir, img_name)
        img = cv2.imread(img_path)
        if img is None:
            continue

        # Display at 256x256 for clear visibility (original file untouched)
        display = cv2.resize(img, (256, 256), interpolation=cv2.INTER_NEAREST)
        cv2.imshow(window_name, display)

        print(f"  [{i}/{len(images)}] {img_name} -> ", end="", flush=True)

        while True:
            key = cv2.waitKey(0) & 0xFF

            if key == ord('s'):
                shutil.move(img_path, os.path.join(sickle_dir, img_name))
                sickle_count += 1
                print("SICKLE")
                break
            elif key == ord('n'):
                shutil.move(img_path, os.path.join(normal_dir, img_name))
                normal_count += 1
                print("NORMAL")
                break
            elif key == ord('d'):
                os.remove(img_path)
                delete_count += 1
                print("DELETED")
                break
            elif key == ord('q'):
                print("QUIT")
                cv2.destroyAllWindows()
                print(f"\n[EARLY EXIT] Sorted {i-1}/{len(images)} cells.")
                print(f"  Sickle: {sickle_count} | Normal: {normal_count} | Deleted: {delete_count}")
                return

    cv2.destroyAllWindows()
    print(f"\n[COMPLETE] All {len(images)} cells sorted!")
    print(f"  Sickle: {sickle_count} | Normal: {normal_count} | Deleted: {delete_count}")
    print(f"  Sickle path: {os.path.abspath(sickle_dir)}")
    print(f"  Normal path: {os.path.abspath(normal_dir)}")

if __name__ == '__main__':
    main()
