# localization-connect

A complete pipeline for localizing App Store content using AI. Translate your app's metadata and screenshots to multiple languages, then upload directly to App Store Connect.

## Features

- **AI-Powered Translation**: Translate App Store metadata (descriptions, release notes, keywords) using Claude AI
- **Screenshot Translation**: Translate screenshot images using Google Gemini's image generation
- **Screenshot Resizing**: Automatically resize screenshots to App Store required dimensions
- **Direct Upload**: Push translations directly to App Store Connect via API
- **Smart Caching**: Skip already-translated content unless forced
- **Character Limit Enforcement**: Automatically retry translations that exceed App Store limits
- **URL Localization**: Update privacy policy and terms URLs for each locale

## Installation

### Requirements

- Python 3.10+
- API keys for Claude (Anthropic) and/or Google Gemini
- App Store Connect API credentials (for uploading)

### Install Dependencies

```bash
pip install requests PyJWT cryptography python-dotenv anthropic Pillow google-genai
```

Or create a requirements.txt:

```
requests>=2.28.0
PyJWT>=2.6.0
cryptography>=39.0.0
python-dotenv>=1.0.0
Pillow>=9.4.0
google-genai>=0.3.0
```

## Quick Start

### 1. Set Up Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```bash
# Required for translation
CLAUDE_API_KEY=sk-ant-api03-...

# Required for screenshot translation
GOOGLE_API_KEY=AIza...

# Required for uploading to App Store Connect
APP_STORE_KEY_ID=XXXXXXXXXX
APP_STORE_ISSUER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
APP_STORE_PRIVATE_KEY_PATH=/path/to/AuthKey.p8
IOS_APP_ID=1234567890
```

### 2. Create Directory Structure

```
your-project/
├── en/                     # English source (required)
│   ├── new.txt            # What's New / Release Notes
│   ├── desc.txt           # App Description
│   ├── promo.txt          # Promotional Text
│   └── keywords.txt       # Keywords (comma-separated)
├── de/                     # German (create empty folders)
├── es-MX/                  # Spanish (Mexico)
├── ja/                     # Japanese
├── ko/                     # Korean
├── pt-BR/                  # Portuguese (Brazil)
├── zh-CN/                  # Chinese (Simplified)
└── fr/                     # French
```

### 3. Translate

```bash
python -m localization_connect.app_store_connect --translate
```

### 4. Upload to App Store Connect

```bash
python -m localization_connect.app_store_connect --send --ios-version 1.0.0
```

## Detailed Usage

### Translating Metadata

The translation system uses Claude AI to translate your English source files while maintaining your brand voice and respecting App Store character limits.

```bash
# Translate all locales (skips files that already exist and pass limits)
python -m localization_connect.app_store_connect --translate

# Force retranslate everything
python -m localization_connect.app_store_connect --translate --force

# Translate only German
python -m localization_connect.app_store_connect --translate --only de

# Translate only German promotional text
python -m localization_connect.app_store_connect --translate --only de/promo.txt

# Use a specific .env file
python -m localization_connect.app_store_connect --translate --env /path/to/.env
```

### Fixing Localized URLs

If your app description contains privacy policy or terms of service URLs, you can automatically update them for each locale:

```bash
python -m localization_connect.app_store_connect --fix-urls
```

This transforms:
- English: `https://example.com/docs/PrivacyPolicy`
- German: `https://example.com/docs/de/PrivacyPolicy`
- Japanese: `https://example.com/docs/ja/PrivacyPolicy`

### Uploading to App Store Connect

```bash
# Upload all fields to iOS
python -m localization_connect.app_store_connect --send --ios-version 1.0.0

# Upload to both iOS and Mac
python -m localization_connect.app_store_connect --send --ios-version 1.0.0 --mac-version 1.0.0

# Upload only specific fields
python -m localization_connect.app_store_connect --send --ios-version 1.0.0 --fields new promo

# Upload only keywords
python -m localization_connect.app_store_connect --send --ios-version 1.0.0 --fields keywords
```

**Available fields:**
| Field | File | Character Limit | App Store Connect Field |
|-------|------|-----------------|------------------------|
| `new` | new.txt | 4000 | What's New |
| `desc` | desc.txt | 4000 | Description |
| `promo` | promo.txt | 170 | Promotional Text |
| `keywords` | keywords.txt | 100 | Keywords |

### Translating Screenshots

Use Google Gemini to translate text in your screenshots while preserving the design:

```bash
# Translate all PNG files in current directory
python -m localization_connect.translate_screenshots

# Force overwrite existing translations
python -m localization_connect.translate_screenshots --force

# Translate to specific languages only
python -m localization_connect.translate_screenshots --languages de ja ko
```

### Resizing Screenshots

Resize screenshots to App Store required dimensions:

```bash
# Resize iPhone screenshots (default)
python -m localization_connect.resize_screenshots --ios

# Resize iPad screenshots
python -m localization_connect.resize_screenshots --ipad

# Resize Mac screenshots
python -m localization_connect.resize_screenshots --mac

# Preview without modifying
python -m localization_connect.resize_screenshots --ios --dry-run

# Process current directory instead of language subdirs
python -m localization_connect.resize_screenshots --ios --local
```

**Supported Screenshot Sizes:**

| Device | Dimensions |
|--------|------------|
| iPhone 6.5" | 1260×2736, 2736×1260 |
| iPhone 6.7" | 1320×2868, 2868×1320 |
| iPhone 6.9" | 1290×2796, 2796×1290 |
| iPad 12.9" | 2048×2732, 2732×2048 |
| iPad 13" | 2064×2752, 2752×2064 |
| Mac | 1280×800 to 2880×1800 |

### Full Pipeline

Run the complete pipeline in one command:

```bash
python -m localization_connect.app_store_connect --translate --fix-urls --send --ios-version 1.0.0
```

## Configuration

### Environment Variables

| Variable | Required For | Description |
|----------|-------------|-------------|
| `CLAUDE_API_KEY` | Translation | Anthropic API key |
| `CLAUDE_MODEL` | Translation | Model ID (default: claude-sonnet-4-20250514) |
| `GOOGLE_API_KEY` | Screenshots | Google AI API key |
| `GEMINI_MODEL` | Screenshots | Gemini model (default: models/gemini-2.0-flash) |
| `APP_STORE_KEY_ID` | Upload | App Store Connect API Key ID |
| `APP_STORE_ISSUER_ID` | Upload | App Store Connect Issuer ID |
| `APP_STORE_PRIVATE_KEY_PATH` | Upload | Path to .p8 private key file |
| `IOS_APP_ID` | Upload | iOS App ID from App Store Connect |
| `MAC_APP_ID` | Upload | Mac App ID (optional) |
| `APP_NAME` | Translation | Your app name (for translation context) |
| `APP_DESCRIPTION` | Translation | Brief app description |
| `BRAND_VOICE` | Translation | Tone guidelines for translations |
| `BASE_PRIVACY_URL` | URL Fix | Base privacy policy URL |
| `BASE_TERMS_URL` | URL Fix | Base terms of service URL |

### Supported Locales

| Folder | App Store Locale | Language |
|--------|-----------------|----------|
| `en` | en-US | English (U.S.) |
| `de` | de-DE | German |
| `es-MX` | es-MX | Spanish (Mexico) |
| `fr` | fr-FR | French |
| `it` | it | Italian |
| `ja` | ja | Japanese |
| `ko` | ko | Korean |
| `pt-BR` | pt-BR | Portuguese (Brazil) |
| `ru` | ru | Russian |
| `zh-CN` | zh-Hans | Chinese (Simplified) |
| `zh-TW` | zh-Hant | Chinese (Traditional) |

## Using as a Library

You can also import and use the functions programmatically:

```python
from localization_connect import (
    config,
    translate_all,
    send_to_app_store,
    resize_screenshots,
    translate_screenshots,
)
from pathlib import Path

# Load configuration
config.load_config("/path/to/.env")

# Translate all metadata
translate_all(base_dir=Path("/your/project"), force=False)

# Upload to App Store Connect
send_to_app_store(ios_version="1.0.0", fields=["new", "promo"])

# Resize screenshots
resize_screenshots(base_dir=Path("/your/project"), device="ios")

# Translate screenshots
translate_screenshots(
    base_dir=Path("/your/project"),
    languages={"de": "German", "ja": "Japanese"},
    force=False
)
```

## Output Files

After running `--translate`, each locale folder will contain:

```
de/
├── new.txt                 # Translated What's New
├── desc.txt                # Translated Description
├── promo.txt               # Translated Promotional Text
├── keywords.txt            # Translated Keywords
└── full_translation.json   # All translations + translator notes
```

The `full_translation.json` includes translation considerations and notes from Claude, useful for review.

## Troubleshooting

### Translation exceeds character limit

The system automatically retries up to 2 times when translations exceed limits. If it still fails:
- Use `--only locale/file.txt` to retranslate just that file
- Consider shortening your English source text
- Check `full_translation.json` for the considerations

### API authentication errors

- **Claude**: Verify your `CLAUDE_API_KEY` starts with `sk-ant-`
- **App Store Connect**: Ensure your .p8 file path is correct and the key has appropriate permissions
- **Google**: Verify your `GOOGLE_API_KEY` and that the Gemini API is enabled

### Missing locale folders

Create empty folders for each target locale before running translation:

```bash
mkdir -p de es-MX ja ko pt-BR zh-CN fr
```

### Screenshots not translating

- Gemini image generation may not be available in all regions
- Ensure images are PNG format
- Check that `GOOGLE_API_KEY` has access to the Gemini API

## App Store Connect Setup

To get your App Store Connect credentials:

1. Go to [App Store Connect](https://appstoreconnect.apple.com)
2. Navigate to Users and Access → Keys
3. Generate a new API key with "App Manager" role
4. Download the .p8 file (only available once!)
5. Note the Key ID and Issuer ID

Your App ID can be found in your app's App Store Connect page URL or in the App Information section.

## License

MIT License - Feel free to use and modify for your projects.
