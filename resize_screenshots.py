#!/usr/bin/env python3
"""
Resize screenshots to App Store dimensions.

Usage:
    python resize_screenshots.py [--ios|--ipad|--mac] [--local] [--dry-run]

Default is --ios (iPhone). Use --local to process current and parent dir
instead of language subdirs.

REQUIREMENTS
------------
    pip install Pillow
"""

import argparse
from pathlib import Path
from PIL import Image

# Target sizes by device type
SIZES = {
    "ios": [
        (1260, 2736),  # 6.5" portrait
        (2736, 1260),  # 6.5" landscape
        (1320, 2868),  # 6.7" portrait
        (2868, 1320),  # 6.7" landscape
        (1290, 2796),  # 6.9" portrait
        (2796, 1290),  # 6.9" landscape
    ],
    "ipad": [
        (2064, 2752),  # 13" portrait
        (2752, 2064),  # 13" landscape
        (2048, 2732),  # 12.9" portrait
        (2732, 2048),  # 12.9" landscape
    ],
    "mac": [
        (1280, 800),   # smallest
        (1440, 900),   # standard
        (2560, 1600),  # retina
        (2880, 1800),  # largest retina
    ],
}


def get_device_type(filename: str) -> str | None:
    """Get device type from filename (ios, ipad, mac) or None if not recognized."""
    name = filename.lower()
    if "mac" in name:
        return "mac"
    if "ipad" in name:
        return "ipad"
    if "ios" in name or "iphone" in name:
        return "ios"
    return None


def find_closest_size(width: int, height: int, target_sizes: list) -> tuple:
    """Find the target size with the closest aspect ratio."""
    current_ratio = width / height

    best_size = None
    best_diff = float('inf')

    for target_w, target_h in target_sizes:
        target_ratio = target_w / target_h
        diff = abs(current_ratio - target_ratio)

        if diff < best_diff:
            best_diff = diff
            best_size = (target_w, target_h)

    return best_size


def resize_image(input_path: Path, output_path: Path, target_size: tuple):
    """Resize image to target size."""
    with Image.open(input_path) as img:
        resized = img.resize(target_size, Image.Resampling.LANCZOS)
        resized.save(output_path, "PNG", optimize=True)


def process_directory(lang_dir: Path, device: str, dry_run: bool = False):
    """Process PNGs in a language directory based on device type."""
    png_files = list(lang_dir.glob("*.png"))
    target_sizes = SIZES[device]

    for png_path in png_files:
        file_device = get_device_type(png_path.name)

        # Skip files that don't match the target device
        if file_device != device:
            print(f"  Skipping {png_path.name} ({file_device or 'unknown'} shot)")
            continue

        with Image.open(png_path) as img:
            orig_size = img.size

        # Skip if already a target size
        if orig_size in target_sizes:
            print(f"  Skipping {png_path.name}: already at target size {orig_size}")
            continue

        target_size = find_closest_size(*orig_size, target_sizes)

        if dry_run:
            print(f"  {png_path.name}: {orig_size} -> {target_size}")
        else:
            print(f"  Resizing {png_path.name}: {orig_size} -> {target_size}")
            resize_image(png_path, png_path, target_size)


def resize_screenshots(base_dir: Path = None, device: str = "ios",
                       local: bool = False, dry_run: bool = False):
    """
    Resize screenshots in the given directory.

    Args:
        base_dir: Base directory to process (default: current directory)
        device: Device type - "ios", "ipad", or "mac"
        local: If True, process current and parent dir; otherwise process language subdirs
        dry_run: If True, preview without modifying files
    """
    base_dir = base_dir or Path.cwd()

    if dry_run:
        print("DRY RUN - No files will be modified\n")

    print(f"Device: {device.upper()}")
    print(f"Target sizes: {SIZES[device]}\n")

    if local:
        dirs_to_process = [base_dir, base_dir.parent]
        for d in dirs_to_process:
            print(f"\nProcessing {d.name}/")
            process_directory(d, device, dry_run)
    else:
        lang_dirs = [
            d for d in base_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".") and d.name != ".venv"
        ]

        if not lang_dirs:
            print("No language directories found.")
            return

        for lang_dir in sorted(lang_dirs):
            print(f"\nProcessing {lang_dir.name}/")
            process_directory(lang_dir, device, dry_run)

    print("\nDone!")


def main():
    parser = argparse.ArgumentParser(description="Resize screenshots for App Store")
    parser.add_argument("--ios", action="store_true", help="Resize for iPhone (default)")
    parser.add_argument("--ipad", action="store_true", help="Resize for iPad")
    parser.add_argument("--mac", action="store_true", help="Resize for Mac")
    parser.add_argument("--local", action="store_true",
                        help="Process current dir and parent dir instead of language subdirs")
    parser.add_argument("--dry-run", action="store_true", help="Preview without modifying")
    args = parser.parse_args()

    if args.mac:
        device = "mac"
    elif args.ipad:
        device = "ipad"
    else:
        device = "ios"

    resize_screenshots(device=device, local=args.local, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
