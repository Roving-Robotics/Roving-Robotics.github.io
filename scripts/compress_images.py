#!/usr/bin/env python3
"""
Compress images from images/original into images/optimized.
- JPEG/PNG are resized down to max_dim pixels on the longest side and saved with reasonable quality.
- SVG and other unsupported formats are copied through unchanged.

Run from repo root:
  python3 scripts/compress_images.py
"""
from pathlib import Path
import shutil

try:
    from PIL import Image
except ImportError as e:
    raise SystemExit("Pillow is required. Install with: pip install pillow") from e

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "images" / "original"
OUT_DIR = ROOT / "images" / "optimized"
MAX_DIM = 1600
JPEG_QUALITY = 82

def compress_image(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img = img.convert("RGB") if img.mode in ("P", "RGBA") else img
        w, h = img.size
        scale = min(1.0, MAX_DIM / max(w, h))
        if scale < 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        dst = dst.with_suffix(".jpg") if img.format == "JPEG" or src.suffix.lower() in [".jpg", ".jpeg"] else dst
        fmt = "JPEG" if dst.suffix.lower() in [".jpg", ".jpeg"] else "PNG"
        save_kwargs = {"quality": JPEG_QUALITY, "optimize": True} if fmt == "JPEG" else {"optimize": True}
        img.save(dst, fmt, **save_kwargs)

def copy_through(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def main():
    if not SRC_DIR.exists():
        raise SystemExit(f"Source directory missing: {SRC_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for src in SRC_DIR.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(SRC_DIR)
        dst = OUT_DIR / rel
        ext = src.suffix.lower()
        if ext in {".png", ".jpg", ".jpeg"}:
            compress_image(src, dst)
        else:
            copy_through(src, dst)
    print("Optimized images written to", OUT_DIR)

if __name__ == "__main__":
    main()
