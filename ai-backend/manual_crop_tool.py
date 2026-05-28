"""
Manual Crop Tool for Validation Cells Curation (v2)
=====================================================
Usage:
    python manual_crop_tool.py <smear_image_path>

Example:
    python manual_crop_tool.py validation_smears/sickle/sickle_01.jpg.jpg

Controls:
    ── Navigation ──
    Mouse wheel     Zoom in / out (centered on cursor)
    Right-drag      Pan the zoomed image
    Middle-click    Reset zoom to fit

    ── Crop Size (cycle with bracket keys) ──
    [             Decrease crop size: 160 → 128 → 112 → 96
    ]             Increase crop size: 96 → 112 → 128 → 160

    ── Cell Selection ──
    Left-click    Select a cell center (shows preview + crosshair)

    ── Classification (after left-click) ──
    1             Save as normal
    2             Save as sickle
    3             Save as artifact
    4             Reject / skip (no save)

    ── Session ──
    z             Undo last saved crop
    q             Quit and save session

Output:
    validation_cells/raw/{class}/manual_{smear}_{NNN}.png    (raw NxN lossless)
    validation_cells/{class}/manual_{smear}_{NNN}.jpg        (128x128 model-ready)
    validation_cells/crop_log.json                           (append-only metadata)
"""
import sys
import os
import json
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

# ── Configuration ──
CROP_SIZES = [96, 112, 128, 160]
DEFAULT_CROP_IDX = 0  # start at 96
RESIZED_SIZE = 128
OUTPUT_BASE = Path("validation_cells")
CLASS_MAP = {
    ord("1"): "normal",
    ord("2"): "sickle",
    ord("3"): "artifact",
    ord("4"): "__skip__",
}
ZOOM_STEP = 1.25
MIN_ZOOM = 0.5
MAX_ZOOM = 10.0
WINDOW_W = 1200
WINDOW_H = 850


def load_crop_log():
    log_path = OUTPUT_BASE / "crop_log.json"
    if log_path.exists():
        with open(log_path) as f:
            return json.load(f)
    return []


def save_crop_log(log):
    log_path = OUTPUT_BASE / "crop_log.json"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2, default=str)


def get_next_index(smear_name, cls):
    """Find the next available index across raw and resized dirs."""
    indices = []
    for d in [OUTPUT_BASE / cls, OUTPUT_BASE / "raw" / cls]:
        if d.exists():
            for f in d.iterdir():
                if f.name.startswith(f"manual_{smear_name}_"):
                    parts = f.stem.replace(f"manual_{smear_name}_", "").split(".")
                    try:
                        indices.append(int(parts[0]))
                    except ValueError:
                        pass
    return max(indices) + 1 if indices else 0


def determine_smear_class(image_path):
    p = str(image_path).lower()
    if "normal" in p:
        return "normal"
    elif "sickle" in p:
        return "sickle"
    return "unknown"


class CropTool:
    def __init__(self, image_path):
        self.image_path = Path(image_path)
        self.smear_name = self.image_path.stem.replace(".jpg", "").replace(".png", "")
        self.smear_class = determine_smear_class(image_path)
        self.img_full = cv2.imread(str(image_path))
        if self.img_full is None:
            raise ValueError(f"Cannot read image: {image_path}")

        self.h_full, self.w_full = self.img_full.shape[:2]
        self.crop_log = load_crop_log()
        self.session_crops = []
        self.pending_click = None  # (x, y) in full-image coordinates
        self.crop_size_idx = DEFAULT_CROP_IDX
        self.needs_redraw = True

        # Zoom / Pan state — viewport defined in full-image coordinates
        # (vx, vy) = top-left corner of viewport in full image
        # zoom = how many screen pixels per full-image pixel
        fit_zoom = min(WINDOW_W / self.w_full, WINDOW_H / self.h_full)
        self.zoom = fit_zoom
        self.fit_zoom = fit_zoom
        self.vx = 0.0  # viewport left in full-image coords
        self.vy = 0.0  # viewport top in full-image coords

        # Pan drag state
        self._dragging = False
        self._drag_start = None  # (mouse_x, mouse_y)
        self._drag_vx0 = 0.0
        self._drag_vy0 = 0.0

        # Ensure output dirs
        for cls in ["normal", "sickle", "artifact"]:
            (OUTPUT_BASE / cls).mkdir(parents=True, exist_ok=True)
            (OUTPUT_BASE / "raw" / cls).mkdir(parents=True, exist_ok=True)

    @property
    def crop_size(self):
        return CROP_SIZES[self.crop_size_idx]

    @property
    def half_crop(self):
        return self.crop_size // 2

    def _clamp_viewport(self):
        """Keep viewport within image bounds."""
        view_w = WINDOW_W / self.zoom
        view_h = WINDOW_H / self.zoom
        self.vx = max(0, min(self.vx, self.w_full - view_w))
        self.vy = max(0, min(self.vy, self.h_full - view_h))

    def _screen_to_full(self, sx, sy):
        """Convert screen pixel to full-image coordinate."""
        fx = self.vx + sx / self.zoom
        fy = self.vy + sy / self.zoom
        return fx, fy

    def _full_to_screen(self, fx, fy):
        """Convert full-image coordinate to screen pixel."""
        sx = (fx - self.vx) * self.zoom
        sy = (fy - self.vy) * self.zoom
        return int(sx), int(sy)

    def _is_near_border(self, x, y):
        half = self.half_crop
        return (x < half or y < half or
                x >= self.w_full - half or y >= self.h_full - half)

    def _render(self):
        """Render the current viewport with overlays."""
        # Compute the region of the full image visible on screen
        view_w = WINDOW_W / self.zoom
        view_h = WINDOW_H / self.zoom

        x1 = int(max(0, self.vx))
        y1 = int(max(0, self.vy))
        x2 = int(min(self.w_full, self.vx + view_w))
        y2 = int(min(self.h_full, self.vy + view_h))

        if x2 <= x1 or y2 <= y1:
            return np.zeros((WINDOW_H, WINDOW_W, 3), dtype=np.uint8)

        region = self.img_full[y1:y2, x1:x2]
        out_w = int((x2 - x1) * self.zoom)
        out_h = int((y2 - y1) * self.zoom)
        out_w = min(out_w, WINDOW_W)
        out_h = min(out_h, WINDOW_H)

        display = cv2.resize(region, (out_w, out_h), interpolation=cv2.INTER_LINEAR)

        # Pad to window size if needed
        if out_w < WINDOW_W or out_h < WINDOW_H:
            canvas = np.zeros((WINDOW_H, WINDOW_W, 3), dtype=np.uint8)
            canvas[:out_h, :out_w] = display
            display = canvas

        # Draw saved crop markers
        for crop in self.session_crops:
            sx, sy = self._full_to_screen(crop["click_x"], crop["click_y"])
            half_s = int(crop["raw_crop_size"] / 2 * self.zoom)
            if -half_s < sx < WINDOW_W + half_s and -half_s < sy < WINDOW_H + half_s:
                color = (0, 255, 0) if crop["user_label"] == "normal" else \
                        (0, 0, 255) if crop["user_label"] == "sickle" else (0, 255, 255)
                cv2.rectangle(display, (sx - half_s, sy - half_s), (sx + half_s, sy + half_s), color, 1)

        # Draw pending click crosshair + crop box
        if self.pending_click:
            fx, fy = self.pending_click
            sx, sy = self._full_to_screen(fx, fy)
            half_s = int(self.half_crop * self.zoom)
            near = self._is_near_border(int(fx), int(fy))
            box_color = (0, 0, 255) if near else (0, 255, 255)

            # Crosshair lines (extend beyond crop box)
            cv2.line(display, (sx - half_s - 20, sy), (sx + half_s + 20, sy), box_color, 1)
            cv2.line(display, (sx, sy - half_s - 20), (sx, sy + half_s + 20), box_color, 1)
            # Crop box
            cv2.rectangle(display, (sx - half_s, sy - half_s), (sx + half_s, sy + half_s), box_color, 2)

            if near:
                cv2.putText(display, "BORDER", (sx - half_s, sy - half_s - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)

        # HUD overlay
        hud_bg = display[:65, :, :].copy()
        cv2.rectangle(display, (0, 0), (WINDOW_W, 65), (0, 0, 0), -1)
        display[:65, :, :] = cv2.addWeighted(hud_bg, 0.3, display[:65, :, :], 0.7, 0)

        cv2.putText(display, f"SMEAR: {self.smear_name}", (8, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
        cv2.putText(display, f"Crop: {self.crop_size}x{self.crop_size}",
                    (8, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(display, f"Output: {RESIZED_SIZE}x{RESIZED_SIZE}",
                    (195, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
        cv2.putText(display, f"ZOOM: {self.zoom:.1f}x", (390, 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        cv2.putText(display, f"SESSION: {len(self.session_crops)}", (530, 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        cv2.putText(display, "1=N 2=S 3=A 4=Skip | [/]=Size | Scroll=Zoom | RightDrag=Pan | Z=Undo Q=Quit",
                    (8, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (140, 140, 140), 1)

        return display

    def _on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and not self._dragging:
            fx, fy = self._screen_to_full(x, y)
            fx = max(0, min(fx, self.w_full - 1))
            fy = max(0, min(fy, self.h_full - 1))
            self.pending_click = (fx, fy)
            self.needs_redraw = True

        elif event == cv2.EVENT_RBUTTONDOWN:
            self._dragging = True
            self._drag_start = (x, y)
            self._drag_vx0 = self.vx
            self._drag_vy0 = self.vy

        elif event == cv2.EVENT_MOUSEMOVE and self._dragging:
            dx = x - self._drag_start[0]
            dy = y - self._drag_start[1]
            self.vx = self._drag_vx0 - dx / self.zoom
            self.vy = self._drag_vy0 - dy / self.zoom
            self._clamp_viewport()
            self.needs_redraw = True

        elif event == cv2.EVENT_RBUTTONUP:
            self._dragging = False

        elif event == cv2.EVENT_MBUTTONDOWN:
            # Reset zoom
            self.zoom = self.fit_zoom
            self.vx = 0.0
            self.vy = 0.0
            self.needs_redraw = True

        elif event == cv2.EVENT_MOUSEWHEEL:
            # Zoom centered on cursor
            fx, fy = self._screen_to_full(x, y)
            if flags > 0:
                self.zoom = min(MAX_ZOOM, self.zoom * ZOOM_STEP)
            else:
                self.zoom = max(MIN_ZOOM, self.zoom / ZOOM_STEP)
            # Adjust viewport so (fx, fy) stays under cursor (x, y)
            self.vx = fx - x / self.zoom
            self.vy = fy - y / self.zoom
            self._clamp_viewport()
            self.needs_redraw = True

    def _get_crop(self, x, y):
        """Extract raw crop from full image. Returns None if near border."""
        ix, iy = int(x), int(y)
        if self._is_near_border(ix, iy):
            return None
        half = self.half_crop
        crop = self.img_full[iy - half:iy + half, ix - half:ix + half].copy()
        if crop.shape[0] != self.crop_size or crop.shape[1] != self.crop_size:
            return None
        return crop

    def _save_crop(self, crop_img, cls, fx, fy):
        idx = get_next_index(self.smear_name, cls)
        base_name = f"manual_{self.smear_name}_{idx:03d}"

        # Raw lossless PNG
        raw_path = OUTPUT_BASE / "raw" / cls / f"{base_name}.png"
        cv2.imwrite(str(raw_path), crop_img)

        # Model-ready 128x128 JPG
        resized = cv2.resize(crop_img, (RESIZED_SIZE, RESIZED_SIZE), interpolation=cv2.INTER_AREA)
        resized_path = OUTPUT_BASE / cls / f"{base_name}.jpg"
        cv2.imwrite(str(resized_path), resized, [cv2.IMWRITE_JPEG_QUALITY, 95])

        entry = {
            "filename": f"{base_name}.jpg",
            "raw_filename": f"{base_name}.png",
            "user_label": cls,
            "source_image": str(self.image_path),
            "source_smear_class": self.smear_class,
            "click_x": int(fx),
            "click_y": int(fy),
            "raw_crop_size": self.crop_size,
            "resized_size": RESIZED_SIZE,
            "near_border": False,
            "preview_acceptance": "accepted",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.crop_log.append(entry)
        self.session_crops.append(entry)
        save_crop_log(self.crop_log)
        return base_name

    def _undo_last(self):
        if not self.session_crops:
            return None
        last = self.session_crops.pop()
        self.crop_log = [e for e in self.crop_log if e["filename"] != last["filename"]]
        save_crop_log(self.crop_log)
        cls = last["user_label"]
        for p in [OUTPUT_BASE / "raw" / cls / last["raw_filename"],
                  OUTPUT_BASE / cls / last["filename"]]:
            if p.exists():
                os.remove(p)
        return last["filename"]

    def run(self):
        win = "Manual Crop Tool v2"
        win_preview = "Preview"

        cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
        cv2.resizeWindow(win, WINDOW_W, WINDOW_H)
        cv2.setMouseCallback(win, self._on_mouse)
        cv2.namedWindow(win_preview, cv2.WINDOW_AUTOSIZE)

        print(f"\n  Manual Crop Tool v2")
        print(f"  Smear: {self.smear_name} ({self.smear_class})")
        print(f"  Size: {self.w_full}x{self.h_full}")
        print(f"  Hotkeys: 1=N 2=S 3=A 4=Skip | [/]=CropSize | Scroll=Zoom | RightDrag=Pan | Z=Undo Q=Quit\n")

        # Blank preview
        blank = np.zeros((256, 256, 3), dtype=np.uint8)
        cv2.putText(blank, "Click a cell", (60, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
        cv2.imshow(win_preview, blank)

        # Key codes: on Windows, cv2.waitKey may return VK codes not ASCII
        # [ = ASCII 91, Windows VK_OEM_4 = 219
        # ] = ASCII 93, Windows VK_OEM_6 = 221
        # Also accept - (45) and = (61) as universal fallbacks
        KEYS_SHRINK = {91, 219, 45}   # [, VK_OEM_4, -
        KEYS_GROW   = {93, 221, 61}   # ], VK_OEM_6, =

        while True:
            if self.needs_redraw:
                display = self._render()
                cv2.imshow(win, display)
                self.needs_redraw = False

            raw_key = cv2.waitKeyEx(30)
            key = raw_key & 0xFF

            if key == ord("q"):
                print(f"\n  Session ended. {len(self.session_crops)} crops saved.")
                break

            elif key in KEYS_SHRINK:
                old = self.crop_size
                self.crop_size_idx = max(0, self.crop_size_idx - 1)
                if self.crop_size != old:
                    print(f"  Crop size: {self.crop_size}x{self.crop_size}")
                    self.needs_redraw = True
                    display = self._render()
                    cv2.imshow(win, display)

            elif key in KEYS_GROW:
                old = self.crop_size
                self.crop_size_idx = min(len(CROP_SIZES) - 1, self.crop_size_idx + 1)
                if self.crop_size != old:
                    print(f"  Crop size: {self.crop_size}x{self.crop_size}")
                    self.needs_redraw = True
                    display = self._render()
                    cv2.imshow(win, display)

            elif key == ord("z"):
                undone = self._undo_last()
                if undone:
                    print(f"  \u21a9 Undone: {undone}")
                else:
                    print("  Nothing to undo.")
                self.pending_click = None
                self.needs_redraw = True

            elif key in CLASS_MAP and self.pending_click:
                fx, fy = self.pending_click
                cls = CLASS_MAP[key]

                if cls == "__skip__":
                    print(f"  \u2298 Skipped ({int(fx)}, {int(fy)})")
                    self.pending_click = None
                    self.needs_redraw = True
                    # Clear preview
                    blank = np.zeros((256, 256, 3), dtype=np.uint8)
                    cv2.putText(blank, "Skipped", (80, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 200), 1)
                    cv2.imshow(win_preview, blank)
                    continue

                crop = self._get_crop(fx, fy)
                if crop is None:
                    print(f"  \u2717 Border reject ({int(fx)}, {int(fy)})")
                else:
                    name = self._save_crop(crop, cls, fx, fy)
                    print(f"  \u2713 Saved: {name} \u2192 {cls} ({self.crop_size}x{self.crop_size})")

                self.pending_click = None
                self.needs_redraw = True

            # Update preview window when pending
            if self.pending_click:
                fx, fy = self.pending_click
                crop = self._get_crop(fx, fy)
                if crop is not None:
                    # Show preview scaled to 256x256 for visibility
                    preview = cv2.resize(crop, (256, 256), interpolation=cv2.INTER_NEAREST)
                    # Center crosshair
                    cv2.line(preview, (118, 128), (138, 128), (0, 255, 255), 1)
                    cv2.line(preview, (128, 118), (128, 138), (0, 255, 255), 1)
                    cv2.putText(preview, f"Crop: {self.crop_size}x{self.crop_size}", (5, 18),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
                    cv2.putText(preview, f"Output: {RESIZED_SIZE}x{RESIZED_SIZE}", (5, 36),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 180, 180), 1)
                    cv2.putText(preview, "1=N 2=S 3=A 4=Skip", (5, 248),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
                    cv2.imshow(win_preview, preview)
                else:
                    border_msg = np.zeros((256, 256, 3), dtype=np.uint8)
                    cv2.putText(border_msg, "TOO CLOSE", (55, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(border_msg, "TO BORDER", (58, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.imshow(win_preview, border_msg)

        cv2.destroyAllWindows()

        # Summary
        counts = {}
        for c in self.session_crops:
            counts[c["user_label"]] = counts.get(c["user_label"], 0) + 1
        print(f"\n  Session summary:")
        for cls, count in sorted(counts.items()):
            print(f"    {cls}: {count}")
        print(f"    total: {len(self.session_crops)}")
        print(f"  Log: {OUTPUT_BASE / 'crop_log.json'}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manual_crop_tool.py <smear_image_path>")
        print("Example: python manual_crop_tool.py validation_smears/sickle/sickle_01.jpg.jpg")
        sys.exit(1)

    tool = CropTool(sys.argv[1])
    tool.run()
