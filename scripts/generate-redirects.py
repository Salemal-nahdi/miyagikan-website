#!/usr/bin/env python3
"""Generate Netlify _redirects for clean URLs."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "miyagikan.com.au"
REDIRECTS = SITE / "_redirects"

LEGACY_PAGE_REDIRECTS = {
    "index-p-1083": "/locations/",
    "index-p-1026": "/enquiry/",
    "index-p-1007": "/links/",
}

lines = [
    "/    /index.html    200",
    "/thank-you/    /thank-you/index.html    200",
    "/search/    /search/index.html    200",
]

for legacy, target in LEGACY_PAGE_REDIRECTS.items():
    lines.append(f"/{legacy}    {target}    301")
    lines.append(f"/{legacy}.html    {target}    301")

for index in SITE.rglob("index.html"):
    rel = index.relative_to(SITE).parent.as_posix()
    if rel == ".":
        continue
    public_path = f"/{rel}/"
    target = f"/{rel}/index.html"
    lines.append(f"{public_path}    {target}    200")

REDIRECTS.write_text("\n".join(sorted(set(lines))) + "\n", encoding="utf-8")
print(f"Wrote {len(set(lines))} redirect rules to {REDIRECTS}")
