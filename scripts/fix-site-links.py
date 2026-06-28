#!/usr/bin/env python3
"""Fix corrupted WordPress mirror links and legacy index-p-* page aliases."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "miyagikan.com.au"
TEXT_SUFFIXES = {".html", ".htm", ".js"}

PAGE_ALIASES = {
    "1083": "locations",
    "1026": "enquiry",
    "1007": "links",
}

CORRUPT_CSS = re.compile(
    r"/wp-content/cache/autoptimize/css-family=[^/\"']+/autoptimize_([a-f0-9]+)\.css(?:-family=[^\"']+)?"
)

# Broader fix for css/text/css and js_composer paths mangled during filename sanitization.
CORRUPT_CSS_INLINE = re.compile(r"css-family=[^\"'\\s]+")
CORRUPT_TYPE_ATTR = re.compile(r'type="text/css-family=[^"]+"')

NAV_TARGETS = {
    "HOME": "/",
    "LOCATIONS": "/locations/",
    "LINKS": "/links/",
    "CONTACT": "/enquiry/",
}


def fix_corrupt_css(text: str) -> str:
    text = CORRUPT_CSS.sub(
        r"/wp-content/cache/autoptimize/css/autoptimize_\1.css",
        text,
    )
    text = CORRUPT_CSS_INLINE.sub("css", text)
    text = CORRUPT_TYPE_ATTR.sub('type="text/css"', text)
    return text


def fix_main_nav(text: str) -> str:
    for label, url in NAV_TARGETS.items():
        text = re.sub(
            rf'(<li[^>]*>\s*<a[^>]*href=")[^"]*("[^>]*>\s*{label}\s*</a>)',
            rf"\1{url}\2",
            text,
            flags=re.I,
        )
    return text


def fix_index_aliases(text: str) -> str:
    for page_id, slug in PAGE_ALIASES.items():
        token = f"index-p-{page_id}.html"
        bare = f"index-p-{page_id}"
        canonical = f"/{slug}/"

        # Root-level and absolute legacy WordPress URLs.
        for quote in ('"', "'"):
            text = text.replace(f"href={quote}{token}{quote}", f"href={quote}{canonical}{quote}")
            text = text.replace(f"href={quote}/{bare}{quote}", f"href={quote}{canonical}{quote}")
            text = text.replace(f"href={quote}{bare}{quote}", f"href={quote}{canonical}{quote}")
            text = text.replace(f"href={quote}../{token}{quote}", f"href={quote}{canonical}{quote}")

        # Preloader images incorrectly linked to page aliases.
        text = text.replace(
            f'src="../{token}"',
            'src="/wp-content/uploads/2020/01/MiyagiWhite.png"',
        )
        text = text.replace(
            f'src="{token}"',
            'src="/wp-content/uploads/2020/01/MiyagiWhite.png"',
        )

        # wp-json / feed paths that picked up the wrong page id.
        text = re.sub(
            rf"(['\"])(?:\.\./)*wp-json(?:/[^\"']*)?/{re.escape(token)}",
            r"\1/wp-json/",
            text,
        )
        text = re.sub(
            rf"(['\"])(?:\.\./)*(feed|comments/feed)/{re.escape(token)}",
            r"\1/\2/",
            text,
        )

        # Restore nested content links: hello-world/index-p-1083.html → hello-world/
        text = re.sub(
            rf"(?:\.\./)*((?:[a-zA-Z0-9][a-zA-Z0-9_-]*/)+){re.escape(token)}",
            r"\1",
            text,
        )

    text = re.sub(
        r'action="(?:\.\./)*search/index-p-\d+\.html"',
        'action="/search/"',
        text,
    )

    return fix_main_nav(text)


def sync_alias_pages() -> None:
    for page_id, slug in PAGE_ALIASES.items():
        src = SITE / slug / "index.html"
        dst = SITE / f"index-p-{page_id}.html"
        if src.exists():
            shutil.copy2(src, dst)


def main() -> None:
    sync_alias_pages()
    updated = 0
    for path in SITE.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        fixed = fix_index_aliases(fix_corrupt_css(text))
        if fixed != text:
            path.write_text(fixed, encoding="utf-8")
            updated += 1
    print(f"Synced alias pages and fixed links in {updated} files")


if __name__ == "__main__":
    main()
