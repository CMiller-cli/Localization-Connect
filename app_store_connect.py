#!/usr/bin/env python3
"""
App Store Connect Translation & Upload Tool

This script handles translation and upload of App Store metadata.

OVERVIEW
--------
1. Translates English App Store text to multiple languages using Claude AI
2. Uploads translated metadata to App Store Connect via API

DIRECTORY STRUCTURE
-------------------
The script expects this folder structure:

    /your-project/
    ├── app_store_connect.py    (this script)
    ├── en/                     (English source - REQUIRED)
    │   ├── new.txt            What's New / Release Notes (4000 char limit)
    │   ├── desc.txt           App Description (4000 char limit)
    │   ├── promo.txt          Promotional Text (170 char limit)
    │   └── keywords.txt       Keywords, comma-separated (100 char limit)
    ├── de/                     (German translations)
    ├── es-MX/                  (Spanish Mexico)
    └── ...                     (other locales)

COMMANDS
--------
Translation:
    python app_store_connect.py --translate
    python app_store_connect.py --translate --force
    python app_store_connect.py --translate --only de

Upload:
    python app_store_connect.py --send --ios-version 1.0.0
    python app_store_connect.py --send --ios-version 1.0.0 --mac-version 1.0.0

ENVIRONMENT VARIABLES
---------------------
Required in .env file:
    CLAUDE_API_KEY=sk-ant-...           (for translation)
    APP_STORE_KEY_ID=...                (for upload)
    APP_STORE_ISSUER_ID=...             (for upload)
    APP_STORE_PRIVATE_KEY_PATH=...      (for upload)
    IOS_APP_ID=...                      (for upload)

Optional:
    APP_NAME=Your App Name
    APP_DESCRIPTION=Description of your app
    BRAND_VOICE=Professional and friendly
    BASE_PRIVACY_URL=https://example.com/privacy
    BASE_TERMS_URL=https://example.com/terms

REQUIREMENTS
------------
    pip install requests PyJWT cryptography python-dotenv anthropic
"""
import jwt
import time
import requests
import json
import os
import re
import argparse
from pathlib import Path

from . import config


def get_script_dir():
    """Get the directory containing the script or current working directory."""
    return Path.cwd()


def load_english_source(base_dir: Path = None):
    """Load the English source text files."""
    base_dir = base_dir or get_script_dir()
    en_dir = base_dir / "en"

    sources = {}
    for filename in ["new.txt", "desc.txt", "promo.txt", "keywords.txt"]:
        filepath = en_dir / filename
        if filepath.exists():
            sources[filename] = filepath.read_text(encoding="utf-8").strip()
        else:
            print(f"Warning: {filepath} not found")

    return sources


def translate_with_claude(text: str, target_language: str, text_type: str,
                          char_limit: int = None, max_retries: int = 2) -> dict:
    """Send text to Claude for translation and get structured response with retry logic."""
    api_key = config.CLAUDE_API_KEY or os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        raise ValueError("CLAUDE_API_KEY environment variable not set")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }

    system_prompt = config.DEFAULT_SYSTEM_PROMPT.format(
        app_name=config.APP_NAME,
        app_description=config.APP_DESCRIPTION,
        brand_voice=config.BRAND_VOICE,
        target_language=target_language
    )

    limit_instruction = ""
    if char_limit:
        limit_instruction = f"\n\nCRITICAL: The translation MUST be {char_limit} characters or less. This is a hard App Store limit. Be concise."

    base_user_prompt = f"""Please translate the following {text_type} text to {target_language}.{limit_instruction}

SOURCE TEXT:
{text}

Remember: Use the exact delimiter format specified (===TRANSLATION_START===, etc.)."""

    messages = [{"role": "user", "content": base_user_prompt}]
    last_error = None

    for attempt in range(max_retries + 1):
        payload = {
            "model": config.CLAUDE_MODEL,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": messages
        }

        response = requests.post(config.CLAUDE_API_URL, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        content = result["content"][0]["text"]

        translation_match = re.search(
            r'===TRANSLATION_START===\s*([\s\S]*?)\s*===TRANSLATION_END===',
            content
        )
        considerations_match = re.search(
            r'===CONSIDERATIONS_START===\s*([\s\S]*?)\s*===CONSIDERATIONS_END===',
            content
        )

        if not translation_match:
            raise ValueError(f"Could not find translation in response:\n{content[:500]}")

        translation = translation_match.group(1).strip()
        considerations = considerations_match.group(1).strip() if considerations_match else "No considerations provided"

        if char_limit and len(translation) > char_limit:
            last_error = f"Translation is {len(translation)} chars, limit is {char_limit}"
            if attempt < max_retries:
                print(f"      Retry {attempt + 1}: {last_error}")
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": f"ERROR: Your translation is {len(translation)} characters but the MAXIMUM allowed is {char_limit} characters. This is a hard App Store Connect limit. Please shorten the translation significantly while preserving the key message. You MUST stay under {char_limit} characters."
                })
                continue
            else:
                raise ValueError(f"Failed after {max_retries} retries: {last_error}")

        return {
            "translation": translation,
            "considerations": considerations
        }

    raise ValueError(f"Translation failed: {last_error}")


def check_file_needs_translation(filepath: Path, char_limit: int = None) -> tuple:
    """Check if a file needs translation. Returns (needs_translation, reason)."""
    if not filepath.exists():
        return True, "file missing"

    content = filepath.read_text(encoding="utf-8").strip()
    if not content:
        return True, "file empty"

    if char_limit and len(content) > char_limit:
        return True, f"over limit ({len(content)}/{char_limit} chars)"

    return False, f"OK ({len(content)} chars)"


def translate_all(base_dir: Path = None, force: bool = False, only: str = None):
    """Translate all English source files to all target languages."""
    base_dir = base_dir or get_script_dir()
    sources = load_english_source(base_dir)

    if not sources:
        print("No source files found in en/ directory")
        return

    text_types = {
        "new.txt": "What's New / Release Notes",
        "desc.txt": "App Description",
        "promo.txt": "Promotional Text",
        "keywords.txt": "App Store Keywords (comma-separated search terms)"
    }

    only_locale = None
    only_file = None
    if only:
        if "/" in only:
            only_locale, only_file = only.split("/", 1)
        else:
            only_locale = only

    locale_folders = [
        d for d in base_dir.iterdir()
        if d.is_dir() and d.name in config.FOLDER_TO_LOCALE and d.name != "en"
    ]

    if only_locale:
        locale_folders = [d for d in locale_folders if d.name == only_locale]
        if not locale_folders:
            print(f"Error: Locale '{only_locale}' not found")
            return

    results = {"success": [], "failure": [], "skipped": []}

    for locale_folder in sorted(locale_folders):
        folder_name = locale_folder.name
        locale_code = config.FOLDER_TO_LOCALE.get(folder_name)
        locale_name = config.LOCALE_NAMES.get(locale_code, folder_name)

        print(f"\n{'='*50}")
        print(f"Translating to {locale_name} ({folder_name})")
        if force:
            print("(--force: retranslating all)")
        print('='*50)

        full_translations = {}
        any_translated = False

        files_to_process = sources.items()
        if only_file:
            files_to_process = [(f, s) for f, s in sources.items() if f == only_file]
            if not files_to_process:
                print(f"  Error: File '{only_file}' not found in sources")
                continue

        for filename, source_text in files_to_process:
            text_type = text_types.get(filename, "App Store text")
            char_limit = config.CHAR_LIMITS.get(filename)
            output_path = locale_folder / filename

            if not force:
                needs_translation, reason = check_file_needs_translation(output_path, char_limit)
                if not needs_translation:
                    print(f"\n  Skipping {filename}: {reason}")
                    results["skipped"].append(f"{folder_name}/{filename}: {reason}")
                    if output_path.exists():
                        full_translations[filename] = {
                            "translation": output_path.read_text(encoding="utf-8").strip(),
                            "considerations": "Existing translation (skipped)"
                        }
                    continue
                else:
                    print(f"\n  Translating {filename}: {reason}" + (f" (limit: {char_limit})" if char_limit else ""))
            else:
                print(f"\n  Translating {filename}..." + (f" (limit: {char_limit} chars)" if char_limit else ""))

            try:
                result = translate_with_claude(
                    source_text,
                    locale_name,
                    text_type,
                    char_limit=char_limit,
                    max_retries=2
                )

                output_path.write_text(result["translation"], encoding="utf-8")
                char_count = len(result["translation"])
                print(f"    Saved {filename} ({char_count} chars)")

                full_translations[filename] = {
                    "translation": result["translation"],
                    "considerations": result["considerations"]
                }

                print(f"    Considerations: {result['considerations'][:100]}...")
                results["success"].append(f"{folder_name}/{filename}")
                any_translated = True

            except Exception as e:
                print(f"    Error: {e}")
                full_translations[filename] = {
                    "translation": "",
                    "considerations": f"Error: {str(e)}"
                }
                results["failure"].append(f"{folder_name}/{filename}: {str(e)[:50]}")

        if any_translated or force:
            json_path = locale_folder / "full_translation.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(full_translations, f, ensure_ascii=False, indent=2)
            print(f"\n  Saved full_translation.json")

    print("\n" + "="*50)
    print("TRANSLATION SUMMARY")
    print("="*50)

    if results["success"]:
        print(f"\nTRANSLATED ({len(results['success'])}):")
        for item in results["success"]:
            print(f"  - {item}")
    else:
        print("\nTRANSLATED: None")

    if results["skipped"]:
        print(f"\nSKIPPED ({len(results['skipped'])}):")
        for item in results["skipped"]:
            print(f"  - {item}")

    if results["failure"]:
        print(f"\nFAILED ({len(results['failure'])}):")
        for item in results["failure"]:
            print(f"  - {item}")
    else:
        print("\nFAILED: None")

    print("\n" + "="*50)


def fix_urls(base_dir: Path = None):
    """
    Update Privacy Policy and Terms URLs in desc.txt for each locale.

    Uses BASE_PRIVACY_URL and BASE_TERMS_URL from config.
    """
    if not config.BASE_PRIVACY_URL or not config.BASE_TERMS_URL:
        print("Skipping URL fix: BASE_PRIVACY_URL or BASE_TERMS_URL not configured")
        return

    base_dir = base_dir or get_script_dir()

    locale_folders = [
        d for d in base_dir.iterdir()
        if d.is_dir() and d.name in config.FOLDER_TO_LOCALE and d.name != "en"
    ]

    print("\n" + "="*50)
    print("FIXING URLS IN desc.txt")
    print("="*50)

    results = {"updated": [], "skipped": [], "error": []}

    for locale_folder in sorted(locale_folders):
        folder_name = locale_folder.name
        desc_file = locale_folder / "desc.txt"

        if not desc_file.exists():
            print(f"\n  {folder_name}: desc.txt not found, skipping")
            results["skipped"].append(folder_name)
            continue

        content = desc_file.read_text(encoding="utf-8")
        original_content = content

        # Build localized URLs by inserting locale before the path
        base_privacy = config.BASE_PRIVACY_URL
        base_terms = config.BASE_TERMS_URL

        # Extract domain and path, insert locale
        privacy_parts = base_privacy.rsplit("/", 1)
        terms_parts = base_terms.rsplit("/", 1)

        localized_privacy = f"{privacy_parts[0]}/{folder_name}/{privacy_parts[1]}" if len(privacy_parts) > 1 else base_privacy
        localized_terms = f"{terms_parts[0]}/{folder_name}/{terms_parts[1]}" if len(terms_parts) > 1 else base_terms

        # Replace base URLs with localized versions
        content = content.replace(base_privacy, localized_privacy)
        content = content.replace(base_terms, localized_terms)

        if content != original_content:
            desc_file.write_text(content, encoding="utf-8")
            print(f"\n  {folder_name}: URLs updated")
            print(f"    Privacy: {localized_privacy}")
            print(f"    Terms:   {localized_terms}")
            results["updated"].append(folder_name)
        else:
            if localized_privacy in content and localized_terms in content:
                print(f"\n  {folder_name}: Already correct")
                results["skipped"].append(folder_name)
            else:
                print(f"\n  {folder_name}: No URLs found to update")
                results["skipped"].append(folder_name)

    print("\n" + "="*50)
    print("URL FIX SUMMARY")
    print("="*50)
    if results["updated"]:
        print(f"\nUPDATED ({len(results['updated'])}): {', '.join(results['updated'])}")
    if results["skipped"]:
        print(f"\nSKIPPED ({len(results['skipped'])}): {', '.join(results['skipped'])}")
    if results["error"]:
        print(f"\nERROR ({len(results['error'])}): {', '.join(results['error'])}")
    print("\n" + "="*50)


# =============================================================================
# App Store Connect API Functions
# =============================================================================

def generate_token():
    """Generate JWT token for App Store Connect API."""
    if not config.PRIVATE_KEY_PATH:
        raise ValueError("APP_STORE_PRIVATE_KEY_PATH not configured")

    with open(config.PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()

    payload = {
        "iss": config.ISSUER_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 1200,
        "aud": "appstoreconnect-v1"
    }

    return jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": config.KEY_ID})


def api_request(method, endpoint, data=None):
    """Make an authenticated request to App Store Connect API."""
    headers = {
        "Authorization": f"Bearer {generate_token()}",
        "Content-Type": "application/json"
    }
    url = f"{config.BASE_URL}{endpoint}"

    response = requests.request(method, url, headers=headers, json=data)
    if not response.ok:
        try:
            error_detail = response.json()
            errors = error_detail.get("errors", [])
            for err in errors:
                print(f"      API Error: {err.get('detail', err)}")
        except:
            pass
        response.raise_for_status()
    return response.json() if response.text else None


def get_version(app_id, platform="IOS", version_string=None):
    """Get app store version for a platform, optionally filtering by version string."""
    endpoint = f"/apps/{app_id}/appStoreVersions?filter[platform]={platform}"
    if version_string:
        endpoint += f"&filter[versionString]={version_string}"
    else:
        endpoint += "&limit=1"

    resp = api_request("GET", endpoint)
    if resp["data"]:
        version = resp["data"][0]
        print(f"    Found version: {version['attributes']['versionString']} (state: {version['attributes']['appStoreState']})")
        return version["id"]
    return None


def get_localizations(version_id):
    """Get existing localizations for a version."""
    resp = api_request("GET", f"/appStoreVersions/{version_id}/appStoreVersionLocalizations")
    return {loc["attributes"]["locale"]: loc["id"] for loc in resp["data"]}


def create_localization(version_id, locale):
    """Create a new localization."""
    data = {
        "data": {
            "type": "appStoreVersionLocalizations",
            "attributes": {"locale": locale},
            "relationships": {
                "appStoreVersion": {
                    "data": {"type": "appStoreVersions", "id": version_id}
                }
            }
        }
    }
    resp = api_request("POST", "/appStoreVersionLocalizations", data)
    return resp["data"]["id"]


def update_localization(localization_id, description=None, promotional_text=None, whats_new=None, keywords=None):
    """Update localization metadata."""
    attributes = {}
    if description:
        attributes["description"] = description
    if promotional_text:
        attributes["promotionalText"] = promotional_text
    if whats_new:
        attributes["whatsNew"] = whats_new
    if keywords:
        attributes["keywords"] = keywords

    if not attributes:
        print("      No fields to update")
        return

    data = {
        "data": {
            "type": "appStoreVersionLocalizations",
            "id": localization_id,
            "attributes": attributes
        }
    }
    api_request("PATCH", f"/appStoreVersionLocalizations/{localization_id}", data)


def load_translations_for_upload(base_dir: Path = None):
    """Load translated files from all locale folders."""
    base_dir = base_dir or get_script_dir()
    translations = {}

    for folder_name, locale_code in config.FOLDER_TO_LOCALE.items():
        folder_path = base_dir / folder_name
        if not folder_path.exists():
            continue

        locale_data = {}

        new_file = folder_path / "new.txt"
        desc_file = folder_path / "desc.txt"
        promo_file = folder_path / "promo.txt"
        keywords_file = folder_path / "keywords.txt"

        if new_file.exists():
            locale_data["whats_new"] = new_file.read_text(encoding="utf-8").strip()
        if desc_file.exists():
            locale_data["description"] = desc_file.read_text(encoding="utf-8").strip()
        if promo_file.exists():
            locale_data["promotional_text"] = promo_file.read_text(encoding="utf-8").strip()
        if keywords_file.exists():
            locale_data["keywords"] = keywords_file.read_text(encoding="utf-8").strip()

        if locale_data:
            translations[locale_code] = locale_data

    return translations


FIELD_MAP = {
    "new": "whats_new",
    "desc": "description",
    "promo": "promotional_text",
    "keywords": "keywords"
}

ALL_FIELDS = list(FIELD_MAP.keys())


def send_to_app_store(ios_version=None, mac_version=None, fields=None, base_dir: Path = None):
    """Send translations to App Store Connect for iOS and/or macOS."""
    translations = load_translations_for_upload(base_dir)

    if not translations:
        print("No translations found to upload")
        return

    if not fields:
        fields = ALL_FIELDS

    field_keys = [FIELD_MAP[f] for f in fields if f in FIELD_MAP]

    platforms = []
    if ios_version:
        platforms.append(("IOS", config.IOS_APP_ID, ios_version))
    if mac_version:
        platforms.append(("MAC_OS", config.MAC_APP_ID, mac_version))

    if not platforms:
        print("No platform versions specified. Use --ios-version and/or --mac-version")
        return

    print(f"Uploading fields: {', '.join(fields)}")

    for platform, app_id, version_string in platforms:
        print(f"\n{'='*50}")
        print(f"Uploading to {platform} version {version_string} (App ID: {app_id})")
        print('='*50)

        try:
            version_id = get_version(app_id, platform, version_string)
            if not version_id:
                print(f"  No version '{version_string}' found for {platform}")
                continue

            existing_locs = get_localizations(version_id)

            for locale, content in translations.items():
                locale_name = config.LOCALE_NAMES.get(locale, locale)
                print(f"\n  Processing {locale_name} ({locale})...")

                try:
                    if locale in existing_locs:
                        loc_id = existing_locs[locale]
                        print(f"    Updating existing localization...")
                    else:
                        loc_id = create_localization(version_id, locale)
                        print(f"    Created new localization...")

                    update_localization(
                        loc_id,
                        description=content.get("description") if "description" in field_keys else None,
                        promotional_text=content.get("promotional_text") if "promotional_text" in field_keys else None,
                        whats_new=content.get("whats_new") if "whats_new" in field_keys else None,
                        keywords=content.get("keywords") if "keywords" in field_keys else None
                    )
                    print(f"    Updated successfully")

                except Exception as e:
                    print(f"    Error: {e}")

        except Exception as e:
            print(f"  Platform error: {e}")

    print("\n" + "="*50)
    print("Upload complete!")
    print("="*50)


def main():
    parser = argparse.ArgumentParser(
        description="App Store Connect translation and upload tool"
    )

    parser.add_argument("--translate", action="store_true",
                        help="Translate English source files to all locales using Claude")
    parser.add_argument("--send", action="store_true",
                        help="Send translations to App Store Connect")
    parser.add_argument("--ios-version", type=str,
                        help="iOS app version number to update")
    parser.add_argument("--mac-version", type=str,
                        help="macOS app version number to update")
    parser.add_argument("--force", action="store_true",
                        help="Force retranslate all files")
    parser.add_argument("--only", type=str,
                        help="Only translate specific locale or file (e.g., 'de' or 'de/promo.txt')")
    parser.add_argument("--fields", type=str, nargs="+",
                        choices=["new", "desc", "promo", "keywords", "all"],
                        help="Which fields to upload")
    parser.add_argument("--fix-urls", action="store_true",
                        help="Update Privacy Policy and Terms URLs in desc.txt")
    parser.add_argument("--env", type=str,
                        help="Path to .env file")

    args = parser.parse_args()

    # Load configuration
    if args.env:
        config.load_config(args.env)
    else:
        config.load_config()

    if not args.translate and not args.send and not args.fix_urls:
        parser.print_help()
        print("\n" + "="*50)
        print("QUICK START")
        print("="*50)
        print("""
1. Create .env file with required API keys
2. Create en/ folder with source text files:
   - new.txt (What's New)
   - desc.txt (Description)
   - promo.txt (Promotional Text)
   - keywords.txt (Keywords)
3. Create locale folders: de/, es-MX/, ja/, etc.
4. Run: python -m localization_connect.app_store_connect --translate
5. Run: python -m localization_connect.app_store_connect --send --ios-version 1.0.0
""")
        return

    if args.translate:
        translate_all(force=args.force, only=args.only)

    if args.fix_urls:
        fix_urls()

    if args.send:
        if not args.ios_version and not args.mac_version:
            print("Error: --send requires at least one of --ios-version or --mac-version")
            return

        fields = None
        if args.fields:
            if "all" in args.fields:
                fields = None
            else:
                fields = args.fields

        send_to_app_store(ios_version=args.ios_version, mac_version=args.mac_version, fields=fields)


if __name__ == "__main__":
    main()
