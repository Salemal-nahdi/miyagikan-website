#!/usr/bin/env python3
"""Rename mirrored files with invalid Netlify filename characters and fix references."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVALID_CHARS = ("?", "#", ":")
TEXT_SUFFIXES = {".html", ".css", ".js", ".json", ".svg", ".xml", ".txt", ".htm"}


def clean_basename(name: str) -> str:
    if name.startswith("index.html?"):
        query = name[len("index.html?") :]
        if query.endswith(".html"):
            query = query[: -len(".html")]
        slug = re.sub(r"[^A-Za-z0-9._-]+", "-", query).strip("-")
        return f"index-{slug}.html"

    if "?" in name:
        base, _query = name.split("?", 1)
        if re.search(r"\.(css|js|eot|woff2?|ttf|svg|html|png|jpe?g|gif|cur|ico)$", base, re.I):
            return base

    cleaned = name
    for char in INVALID_CHARS:
        cleaned = cleaned.replace(char, "-")
    return cleaned


def reference_variants(text: str) -> set[str]:
    variants: set[str] = set()

    def add(value: str) -> None:
        if not value:
            return
        variants.add(value)
        variants.add(value.replace("&", "&amp;"))
        variants.add(value.replace("?", "%3F"))
        variants.add(value.replace(":", "%3A"))
        variants.add(value.replace("#", "%23"))
        variants.add(value.replace("?", "%3F").replace("&", "&amp;"))
        variants.add(
            value.replace("?", "%3F")
            .replace(":", "%3A")
            .replace("#", "%23")
            .replace("&", "&amp;")
        )

    add(text)
    if "?" in text:
        base = text.split("?", 1)[0]
        if re.search(r"\.(css|js|eot|woff2?|ttf|svg|html|png|jpe?g|gif|cur|ico)$", base, re.I):
            add(base)
    return variants


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name == "_redirects"


def main() -> None:
    invalid_files = sorted(
        (
            p
            for p in ROOT.rglob("*")
            if p.is_file() and ".git" not in p.parts and any(c in p.name for c in INVALID_CHARS)
        ),
        key=lambda p: len(p.parts),
        reverse=True,
    )

    replacements: dict[str, str] = {}
    to_delete: list[Path] = []

    for path in invalid_files:
        new_name = clean_basename(path.name)
        target = path.with_name(new_name)
        old_rel = path.relative_to(ROOT).as_posix()
        new_rel = target.relative_to(ROOT).as_posix()

        for old_variant in reference_variants(path.name):
            replacements[old_variant] = target.name
        for old_variant in reference_variants(old_rel):
            replacements[old_variant] = new_rel

        if target.exists() and target.resolve() != path.resolve():
            to_delete.append(path)
        elif target != path:
            target.parent.mkdir(parents=True, exist_ok=True)
            path.rename(target)

    for path in to_delete:
        if path.exists():
            path.unlink()

    updated_files = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or not is_text_file(path):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        original = text
        for old in sorted(replacements, key=len, reverse=True):
            text = text.replace(old, replacements[old])
        if text != original:
            path.write_text(text, encoding="utf-8")
            updated_files += 1

    remaining = [
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob("*")
        if p.is_file() and ".git" not in p.parts and any(c in p.name for c in INVALID_CHARS)
    ]

    print(f"Processed {len(invalid_files)} invalid filenames")
    print(f"Deleted {len(to_delete)} duplicate files")
    print(f"Updated references in {updated_files} text files")
    if remaining:
        print("Remaining invalid filenames:")
        for name in remaining:
            print(f"  {name}")
        raise SystemExit(1)
    print("All filenames are Netlify-safe")


if __name__ == "__main__":
    main()
