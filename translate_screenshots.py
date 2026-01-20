#!/usr/bin/env python3
"""
Translate App Store screenshots to multiple languages using Google Gemini API.

This script uses Gemini's image generation capabilities to recreate screenshots
with translated text while preserving the original design.

REQUIREMENTS
------------
    pip install google-genai Pillow python-dotenv

ENVIRONMENT VARIABLES
---------------------
Required in .env file:
    GOOGLE_API_KEY=your-api-key

Optional:
    GEMINI_MODEL=models/gemini-2.0-flash

USAGE
-----
    python translate_screenshots.py                  # Translate all PNGs
    python translate_screenshots.py --force          # Overwrite existing
    python translate_screenshots.py --languages de ja ko  # Specific languages
"""

import argparse
import io
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from PIL import Image

from . import config

# Default languages to translate to
DEFAULT_LANGUAGES = {
    "es-MX": "Spanish (Mexico)",
    "ja": "Japanese",
    "zh-CN": "Chinese Simplified",
    "de": "German",
    "ru": "Russian",
    "ko": "Korean",
    "pt-BR": "Portuguese (Brazil)"
}


def get_png_files(directory: Path) -> list:
    """Get all PNG files in the directory."""
    return list(directory.glob("*.png"))


def translate_image(client, image_path: Path, language_code: str, language_name: str):
    """Send image to Gemini and get translated version back."""
    image = Image.open(image_path)

    prompt = f"""This is an App Store screenshot with English text.
Recreate this exact image but translate ALL English text to {language_name}.
Keep the exact same layout, colors, fonts, and design - only change the language of the text."""

    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                temperature=0.4,
            )
        )

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return Image.open(io.BytesIO(part.inline_data.data))
                elif part.text:
                    print(f"  Model text: {part.text}")

        print(f"  Warning: No image returned for {image_path.name} -> {language_code}")
        return None

    except Exception as e:
        print(f"  Error translating {image_path.name} to {language_code}: {e}")
        return None


def translate_screenshots(base_dir: Path = None, languages: dict = None,
                          force: bool = False, env_path: str = None):
    """
    Translate screenshots to multiple languages.

    Args:
        base_dir: Directory containing PNG files (default: current directory)
        languages: Dict of {code: name} for target languages (default: DEFAULT_LANGUAGES)
        force: If True, overwrite existing translated files
        env_path: Path to .env file
    """
    if genai is None:
        print("Error: google-genai package not installed")
        print("Install with: pip install google-genai")
        return

    # Load configuration
    if env_path:
        config.load_config(env_path)
    else:
        config.load_config()

    api_key = config.GOOGLE_API_KEY
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment")
        print("Set GOOGLE_API_KEY in your .env file")
        return

    base_dir = base_dir or Path.cwd()
    languages = languages or DEFAULT_LANGUAGES

    client = genai.Client(api_key=api_key)

    png_files = get_png_files(base_dir)

    if not png_files:
        print("No PNG files found in directory")
        return

    print(f"Found {len(png_files)} PNG files to translate")
    print(f"Target languages: {', '.join(languages.values())}")
    print()

    for lang_code, lang_name in languages.items():
        lang_dir = base_dir / lang_code
        lang_dir.mkdir(exist_ok=True)

        print(f"Processing {lang_name} ({lang_code})...")

        for png_file in png_files:
            output_path = lang_dir / png_file.name

            if output_path.exists() and not force:
                print(f"  Skipping {png_file.name} (already exists)")
                continue

            print(f"  Translating {png_file.name}...")

            output_image = translate_image(client, png_file, lang_code, lang_name)

            if output_image:
                output_image.save(output_path)
                print(f"  Saved: {output_path}")

    print()
    print("Done!")


def main():
    parser = argparse.ArgumentParser(
        description="Translate App Store screenshots to multiple languages"
    )
    parser.add_argument("-f", "--force", action="store_true",
                        help="Force rerun, overwrite existing files")
    parser.add_argument("--languages", nargs="+",
                        help="Specific language codes to translate to (e.g., de ja ko)")
    parser.add_argument("--env", type=str,
                        help="Path to .env file")
    args = parser.parse_args()

    languages = DEFAULT_LANGUAGES
    if args.languages:
        languages = {code: DEFAULT_LANGUAGES.get(code, code) for code in args.languages
                     if code in DEFAULT_LANGUAGES}
        if not languages:
            print(f"No valid languages specified. Available: {', '.join(DEFAULT_LANGUAGES.keys())}")
            return

    translate_screenshots(languages=languages, force=args.force, env_path=args.env)


if __name__ == "__main__":
    main()
