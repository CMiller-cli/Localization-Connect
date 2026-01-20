"""
Configuration module for localization-connect.

All settings are loaded from environment variables or can be overridden programmatically.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from current directory or specified path
def load_config(env_path: str = None):
    """Load environment variables from .env file."""
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()

# App Store Connect Configuration (required for --send)
KEY_ID = os.environ.get("APP_STORE_KEY_ID", "")
ISSUER_ID = os.environ.get("APP_STORE_ISSUER_ID", "")
PRIVATE_KEY_PATH = os.environ.get("APP_STORE_PRIVATE_KEY_PATH", "")
IOS_APP_ID = os.environ.get("IOS_APP_ID", "")
MAC_APP_ID = os.environ.get("MAC_APP_ID", "")
BASE_URL = "https://api.appstoreconnect.apple.com/v1"

# Claude API Configuration (required for --translate)
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# Google API Configuration (required for screenshot translation)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "models/gemini-2.0-flash")

# Folder name to App Store Connect locale mapping
FOLDER_TO_LOCALE = {
    "en": "en-US",
    "zh-CN": "zh-Hans",
    "zh-TW": "zh-Hant",
    "de": "de-DE",
    "ja": "ja",
    "ko": "ko",
    "pt-BR": "pt-BR",
    "es-MX": "es-MX",
    "fr": "fr-FR",
    "it": "it",
    "ru": "ru",
}

# Human-readable locale names
LOCALE_NAMES = {
    "en-US": "English (U.S.)",
    "zh-Hans": "Chinese (Simplified)",
    "zh-Hant": "Chinese (Traditional)",
    "de-DE": "German",
    "ja": "Japanese",
    "ko": "Korean",
    "pt-BR": "Portuguese (Brazil)",
    "es-MX": "Spanish (Mexico)",
    "fr-FR": "French",
    "it": "Italian",
    "ru": "Russian",
}

# Character limits for App Store Connect fields
CHAR_LIMITS = {
    "promo.txt": 170,
    "new.txt": 4000,
    "desc.txt": 4000,
    "keywords.txt": 100,
}

# Default translation system prompt template
# {app_name}, {app_description}, {brand_voice}, and {target_language} will be replaced
DEFAULT_SYSTEM_PROMPT = """You are a professional translator for App Store content. You are translating content for {app_name}.

ABOUT THE APP:
{app_description}

BRAND VOICE GUIDELINES:
{brand_voice}

TRANSLATION REQUIREMENTS:
- Translate to natural, fluent {target_language}
- Preserve the professional tone
- Keep technical terms accurate
- Maintain App Store formatting conventions for the target locale
- Do NOT use markdown formatting - output plain text suitable for App Store Connect
- Preserve line breaks and bullet points where they exist in the source

RESPONSE FORMAT:
You must respond using this exact format with delimiters:

===TRANSLATION_START===
(Your translated text here, preserving all formatting and line breaks)
===TRANSLATION_END===

===CONSIDERATIONS_START===
(Brief notes about translation choices, tone decisions, and any cultural adaptations made)
===CONSIDERATIONS_END==="""

# App-specific settings (override these for your app)
APP_NAME = os.environ.get("APP_NAME", "Your App")
APP_DESCRIPTION = os.environ.get("APP_DESCRIPTION", "A great application.")
BRAND_VOICE = os.environ.get("BRAND_VOICE", "Professional and friendly.")

# URL templates for localized links (optional)
BASE_PRIVACY_URL = os.environ.get("BASE_PRIVACY_URL", "")
BASE_TERMS_URL = os.environ.get("BASE_TERMS_URL", "")
