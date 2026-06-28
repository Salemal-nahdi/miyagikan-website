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


def fix_nav_block(block: str) -> str:
    def fix_li(match: re.Match[str]) -> str:
        li = match.group(0)
        title = re.search(r'w-nav-title">\s*([^<]+)\s*</span>', li)
        if title:
            label = title.group(1).strip().upper()
        else:
            plain = re.search(r">\s*([^<]+)\s*</a>\s*</li>", li, re.I)
            if not plain:
                return li
            label = plain.group(1).strip().upper()
        url = NAV_TARGETS.get(label)
        if not url:
            return li
        return re.sub(r'(<a[^>]*href=")[^"]*(")', rf"\1{url}\2", li, count=1)

    return re.sub(r"<li\b.*?</li>", fix_li, block, flags=re.S)


def fix_main_nav(text: str) -> str:
    text = re.sub(
        r"(<header\b.*?</header>)",
        lambda match: fix_nav_block(match.group(1)),
        text,
        flags=re.I | re.S,
    )
    text = re.sub(
        r'(<div class="l-subfooter at_bottom".*?</div>\s*</div>)',
        lambda match: fix_nav_block(match.group(1)),
        text,
        flags=re.I | re.S,
    )
    return text


def fix_logo_link(text: str) -> str:
    return re.sub(r'(<a class="w-img-h" href=")[^"]*(")', r"\1/\2", text)


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

        # Same-page anchor links on mirrored location tabs.
        text = re.sub(
            rf'href=(["\'])\.\./{re.escape(token)}(#[^"\']*)\1',
            rf"href=\1{canonical}\2\1",
            text,
        )

        # ../index-p-1083.html without a hash was the corrupted home link on subpages.
        if page_id == "1083":
            text = text.replace(f'href="../{token}"', 'href="/"')
            text = text.replace(f"href='../{token}'", "href='/'")

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
    text = re.sub(r'action="index-p-\d+\.html"', 'action="/events/"', text)

    # Same-page anchors that incorrectly kept the legacy filename prefix.
    text = re.sub(r'index-p-\d+\.html(#[^"\']*)', r"\1", text)

    # Search index and other JSON blobs that still reference legacy home URLs.
    text = text.replace('{ url: "../index-p-1083.html"', '{ url: "/"')
    text = text.replace("{ url: '../index-p-1083.html'", "{ url: '/'")

    return fix_logo_link(fix_main_nav(text))


def remove_legacy_alias_pages() -> None:
    for page_id in PAGE_ALIASES:
        path = SITE / f"index-p-{page_id}.html"
        if path.exists():
            path.unlink()


def main() -> None:
    remove_legacy_alias_pages()
    updated = 0
    for path in SITE.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        fixed = fix_index_aliases(fix_corrupt_css(text))
        if path.name == "events-filter.js":
            fixed = fixed.replace(
                'window.location.href = base + date + "/index-p-1083.html";',
                'window.location.href = base + date + "/";',
            ).replace(
                'window.location.href = base + "index-p-1083.html";',
                "window.location.href = base;",
            )
        if fixed != text:
            path.write_text(fixed, encoding="utf-8")
            updated += 1
    print(f"Removed legacy alias pages and fixed links in {updated} files")


if __name__ == "__main__":
    main()
