#!/usr/bin/env python3
"""Remove hard-coded secrets from static HTML and optionally inject from env."""

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "miyagikan.com.au"

GOOGLE_KEY_PATTERN = re.compile(r"AIza[A-Za-z0-9_-]{20,}")
PLACEHOLDER = "__GOOGLE_MAPS_API_KEY__"


def sanitize_file(path: Path, google_key: str) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    original = text

    text = GOOGLE_KEY_PATTERN.sub(PLACEHOLDER, text)
    if google_key:
        text = text.replace(PLACEHOLDER, google_key)
    else:
        text = re.sub(
            r'var wcs_google_key = "[^"]*";',
            'var wcs_google_key = "";',
            text,
        )
        text = re.sub(
            r'var wcs_maps_url = "[^"]*";',
            'var wcs_maps_url = "";',
            text,
        )
        text = text.replace(PLACEHOLDER, "")

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    google_key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    updated = 0

    for path in SITE.rglob("*.html"):
        if sanitize_file(path, google_key):
            updated += 1

    if google_key:
        print(f"Injected Google Maps API key into {updated} file(s)")
    else:
        print(f"Removed Google Maps API key from {updated} file(s) (maps disabled)")


if __name__ == "__main__":
    main()
