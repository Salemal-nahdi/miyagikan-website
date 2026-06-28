#!/usr/bin/env python3
"""Generate Netlify _redirects for clean URLs on a custom domain."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "miyagikan.com.au"
REDIRECTS = ROOT / "_redirects"

lines = [
    "/    /miyagikan.com.au/index.html    200",
    "/thank-you/    /miyagikan.com.au/thank-you/index.html    200",
    "/search/    /miyagikan.com.au/search/index.html    200",
]

for index in SITE.rglob("index.html"):
    rel = index.relative_to(SITE).parent.as_posix()
    if rel == ".":
        continue
    public_path = f"/{rel}/"
    target = f"/miyagikan.com.au/{rel}/index.html"
    lines.append(f"{public_path}    {target}    200")

REDIRECTS.write_text("\n".join(sorted(set(lines))) + "\n", encoding="utf-8")
print(f"Wrote {len(set(lines))} redirect rules to {REDIRECTS}")
