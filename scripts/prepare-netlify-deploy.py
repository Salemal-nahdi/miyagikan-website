#!/usr/bin/env python3
"""Prepare the static site for Netlify: vend fonts and fix asset paths."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "miyagikan.com.au"
TEXT_SUFFIXES = {".html", ".htm"}

ASSET_PREFIXES = (
    "wp-content/",
    "wp-includes/",
    "fonts.googleapis.com/",
    "fonts.gstatic.com/",
    "js/",
)


def copy_fonts() -> None:
    for name in ("fonts.googleapis.com", "fonts.gstatic.com"):
        src = ROOT / name
        dst = SITE / name
        if not src.exists():
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)


def fix_html_paths(text: str) -> str:
    for prefix in ASSET_PREFIXES:
        text = re.sub(
            rf'(\b(?:href|src)=["\'])(?:\.\./)+{re.escape(prefix)}',
            rf'\1/{prefix}',
            text,
        )
        text = re.sub(
            rf'(\b(?:href|src)=["\']){re.escape(prefix)}',
            rf'\1/{prefix}',
            text,
        )

    text = re.sub(
        r'(\b(?:href|src)=["\'])(?:\.\./)+js/',
        r'\1/js/',
        text,
    )
    text = re.sub(
        r'(\b(?:href|src)=["\'])\./js/',
        r'\1/js/',
        text,
    )

    # Preloader images were incorrectly linked to index.html during mirroring.
    text = text.replace(
        '<img src="index-p-1083.html" alt="" />',
        '<img src="/wp-content/uploads/2020/01/MiyagiWhite.png" alt="" />',
    )
    text = text.replace(
        '<img src="index.html" alt="" />',
        '<img src="/wp-content/uploads/2020/01/MiyagiWhite.png" alt="" />',
    )
    return text


def main() -> None:
    copy_fonts()
    updated = 0
    for path in SITE.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        fixed = fix_html_paths(text)
        if fixed != text:
            path.write_text(fixed, encoding="utf-8")
            updated += 1
    print(f"Vendored fonts into {SITE.name}/ and updated paths in {updated} HTML files")


if __name__ == "__main__":
    main()
