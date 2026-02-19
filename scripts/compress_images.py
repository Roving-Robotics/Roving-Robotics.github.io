#!/usr/bin/env python3
"""
Compress image assets for the site.

Targets (source -> destination):
- images/original -> images/optimized
- projects/uncompressed-media -> projects/media

JPEG/PNG are resized down to max_dim pixels on the longest side and saved
with reasonable quality while keeping files under SIZE_LIMIT bytes.
SVG and other unsupported formats are copied through unchanged.

Run from repo root:
  python3 scripts/compress_images.py
"""
from pathlib import Path
import shutil
import io

try:
    from PIL import Image
except ImportError as e:
    raise SystemExit("Pillow is required. Install with: pip install pillow") from e

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "images" / "original"
OUT_DIR = ROOT / "images" / "optimized"
PROJECTS_SRC_DIR = ROOT / "projects" / "uncompressed-media"
PROJECTS_OUT_DIR = ROOT / "projects" / "media"
MAX_DIM = 1600
JPEG_QUALITY = 82
MIN_JPEG_QUALITY = 45
SIZE_LIMIT = 500 * 1024  # 500 KB
SCALE_STEP = 0.9
MIN_DIM = 640

def compress_image(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img = img.convert("RGB") if img.mode in ("P", "RGBA") else img
        w, h = img.size
        scale = min(1.0, MAX_DIM / max(w, h))
        if scale < 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        # Choose starting format based on source
        dst = dst.with_suffix(".jpg") if img.format == "JPEG" or src.suffix.lower() in [".jpg", ".jpeg"] else dst
        fmt = "JPEG" if dst.suffix.lower() in [".jpg", ".jpeg"] else "PNG"

        quality = JPEG_QUALITY
        current_img = img
        while True:
            buffer = io.BytesIO()
            if fmt == "JPEG":
                current_img.save(buffer, fmt, quality=quality, optimize=True)
            else:  # PNG
                current_img.save(buffer, fmt, optimize=True, compress_level=9)

            size = buffer.tell()
            if size <= SIZE_LIMIT:
                dst.write_bytes(buffer.getvalue())
                break

            # Try to reduce size: first lower quality (JPEG) else downscale slightly
            if fmt == "PNG":
                fmt = "JPEG"
                dst = dst.with_suffix(".jpg")
                quality = JPEG_QUALITY
                continue
            if fmt == "JPEG" and quality > MIN_JPEG_QUALITY:
                quality = max(MIN_JPEG_QUALITY, int(quality * 0.85))
            else:
                new_w, new_h = current_img.size
                if max(new_w, new_h) <= MIN_DIM:
                    # Can't shrink further without going too small; write best-effort
                    dst.write_bytes(buffer.getvalue())
                    break
                new_w = int(new_w * SCALE_STEP)
                new_h = int(new_h * SCALE_STEP)
                current_img = current_img.resize((new_w, new_h), Image.LANCZOS)

def copy_through(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def clear_output(out_dir: Path):
    if not out_dir.exists():
        return
    for item in sorted(out_dir.rglob("*"), reverse=True):
        if item.is_file():
            item.unlink()

def process_directory(src_dir: Path, out_dir: Path, label: str):
    if not src_dir.exists():
        print(f"Skipping {label}: source directory missing ({src_dir})")
        return
    clear_output(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in src_dir.rglob("*"):
        if src.is_dir():
            continue
        try:
            if src.is_relative_to(out_dir):  # avoid re-processing outputs
                continue
        except AttributeError:
            # Python < 3.9 fallback
            if out_dir in src.parents:
                continue
        rel = src.relative_to(src_dir)
        dst = out_dir / rel
        ext = src.suffix.lower()
        if ext in {".png", ".jpg", ".jpeg"}:
            compress_image(src, dst)
        else:
            copy_through(src, dst)
    print(f"Optimized {label} written to {out_dir}")


def main():
    targets = [
        (SRC_DIR, OUT_DIR, "site images"),
        (PROJECTS_SRC_DIR, PROJECTS_OUT_DIR, "project media"),
    ]

    for src_dir, out_dir, label in targets:
        process_directory(src_dir, out_dir, label)

if __name__ == "__main__":
    main()
