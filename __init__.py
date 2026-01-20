"""
localization-connect: App Store localization pipeline

A library for translating and uploading App Store metadata and screenshots.

Modules:
    - app_store_connect: Translate metadata with Claude AI, upload to App Store Connect
    - resize_screenshots: Resize screenshots to App Store dimensions
    - translate_screenshots: Translate screenshot images using Google Gemini
    - config: Configuration management

Quick Start:
    1. Copy .env.example to .env and fill in your API keys
    2. Create en/ folder with your source text files
    3. Create locale folders (de/, es-MX/, ja/, etc.)
    4. Run: python -m localization_connect.app_store_connect --translate
    5. Run: python -m localization_connect.app_store_connect --send --ios-version 1.0.0
"""

__version__ = "1.0.0"

from . import config
from .app_store_connect import (
    translate_all,
    send_to_app_store,
    fix_urls,
    load_english_source,
)
from .resize_screenshots import resize_screenshots, SIZES
from .translate_screenshots import translate_screenshots, DEFAULT_LANGUAGES

__all__ = [
    "config",
    "translate_all",
    "send_to_app_store",
    "fix_urls",
    "load_english_source",
    "resize_screenshots",
    "SIZES",
    "translate_screenshots",
    "DEFAULT_LANGUAGES",
]
