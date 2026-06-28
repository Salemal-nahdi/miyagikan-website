#!/usr/bin/env python3
"""Wire mirrored WordPress forms to Netlify form handling."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "miyagikan.com.au"

SCRIPT_TAG = '<script src="{prefix}js/netlify-forms.js" defer></script>'
SEARCH_SCRIPT = '<script src="{prefix}js/site-search.js" defer></script>'

def contact_form_open(thank_you_prefix: str) -> str:
    return (
        '<form class="w-form-h netlify-contact-form" name="contact" method="POST" '
        'data-netlify="true" netlify-honeypot="bot-field" '
        'data-success-message="Thank you! Your message was sent." '
        f'data-redirect="{thank_you_prefix}thank-you/index.html" autocomplete="off">'
        '<input type="hidden" name="form-name" value="contact" />'
        '<p class="hidden" style="display:none"><label>Don\u2019t fill this out: '
        '<input name="bot-field" /></label></p>'
    )

CONTACT_FORM_PATTERN = re.compile(
    r'<form class="w-form-h" autocomplete="off" action="[^"]*" method="post">'
)
CONTACT_HIDDEN_PATTERN = re.compile(
    r'\s*<input type="hidden" name="action" value="us_ajax_cform"/>'
    r'\s*<input type="hidden" name="post_id" value="[^"]*"/>'
    r'\s*<input type="hidden" name="form_index" value="[^"]*"/>'
)

COMMENT_FORM_OPEN = (
    '<form name="blog-comment" method="POST" data-netlify="true" '
    'netlify-honeypot="bot-field" id="commentform" class="comment-form" '
    'data-success-message="Thank you! Your comment was submitted for review.">'
    '<input type="hidden" name="form-name" value="blog-comment" />'
    '<p class="hidden" style="display:none"><label>Don\u2019t fill this out: '
    '<input name="bot-field" /></label></p>'
)

def search_form(search_prefix: str) -> str:
    return (
        f'<form class="w-form-h site-search-form" autocomplete="off" '
        f'action="{search_prefix}search/index.html" method="get">'
    )


def depth_prefix(path: Path) -> str:
    rel = path.relative_to(SITE)
    depth = len(rel.parts) - 1
    return "../" * depth if depth else "./"


def inject_scripts(html: str, prefix: str) -> str:
    scripts = ""
    if 'data-netlify="true"' in html and SCRIPT_TAG.format(prefix=prefix) not in html:
        scripts += SCRIPT_TAG.format(prefix=prefix)
    if "site-search-form" in html and SEARCH_SCRIPT.format(prefix=prefix) not in html:
        scripts += SEARCH_SCRIPT.format(prefix=prefix)
    if scripts and "</body>" in html:
        html = html.replace("</body>", scripts + "</body>", 1)
    return html


def update_contact_forms(html: str, prefix: str) -> str:
    if "us_ajax_cform" not in html:
        return html
    html = CONTACT_FORM_PATTERN.sub(contact_form_open(prefix), html)
    html = CONTACT_HIDDEN_PATTERN.sub("", html)
    return html


def update_comment_forms(html: str, path: Path) -> str:
    if "wp-comments-post.php" not in html:
        return html
    html = re.sub(
        r'<form action="https?://miyagikan\.com\.au/wp-comments-post\.php" method="post" id="commentform" class="comment-form">',
        COMMENT_FORM_OPEN,
        html,
    )
    title_match = re.search(r"<title>([^<]+)</title>", html, re.I)
    title = title_match.group(1).split(" - ")[0] if title_match else path.parent.name
    hidden = (
        f'<input type="hidden" name="post_title" value="{title}" />'
        f'<input type="hidden" name="post_url" value="{path.as_posix()}" />'
    )
    html = html.replace(
        '<input type="hidden" name="form-name" value="blog-comment" />',
        '<input type="hidden" name="form-name" value="blog-comment" />' + hidden,
        1,
    )
    html = re.sub(
        r"<input type='hidden' name='comment_post_ID' value='[^']*' id='comment_post_ID' />",
        "",
        html,
    )
    html = re.sub(
        r"<input type='hidden' name='comment_parent' id='comment_parent' value='[^']*' />",
        "",
        html,
    )
    return html


def update_search_forms(html: str, prefix: str) -> str:
    return re.sub(
        r'<form class="w-form-h" autocomplete="off" action="https?://miyagikan\.com\.au/?" method="get">',
        search_form(prefix),
        html,
    )


def update_event_forms(html: str, prefix: str) -> str:
    if 'id="tribe-bar-form"' not in html:
        return html
    html = re.sub(
        r'(<form id="tribe-bar-form"[^>]*method=")post(")',
        r'\1get\2',
        html,
    ).replace(
        'action="https://miyagikan.com.au/events?post_type=tribe_events&#038;eventDisplay=default"',
        'action="index.html"',
    ).replace(
        'action="https://miyagikan.com.au/events/?post_type=tribe_events&#038;eventDisplay=default"',
        'action="index.html"',
    )
    tag = f'<script src="{prefix}js/events-filter.js" defer></script>'
    if tag not in html and "</body>" in html:
        html = html.replace("</body>", tag + "</body>", 1)
    return html


def add_hidden_forms(html: str, path: Path) -> str:
    if path.name != "index.html" or path.parent != SITE:
        return html
    if 'name="contact"' in html and 'hidden' in html and 'form-name' in html:
        return html
    hidden = """
<!-- Netlify form registration -->
<form name="contact" netlify netlify-honeypot="bot-field" hidden>
  <input name="name" /><input name="email" /><input name="phone" /><textarea name="message"></textarea>
</form>
<form name="blog-comment" netlify netlify-honeypot="bot-field" hidden>
  <input name="author" /><input name="email" /><input name="url" /><textarea name="comment"></textarea>
  <input name="post_title" /><input name="post_url" />
</form>
"""
    return html.replace("</body>", hidden + "</body>", 1)


if __name__ == "__main__":
    updated = 0
    for path in SITE.rglob("*.html"):
        text = path.read_text(encoding="utf-8", errors="replace")
        original = text
        prefix = depth_prefix(path)
        text = update_contact_forms(text, prefix)
        text = update_comment_forms(text, path.relative_to(ROOT))
        text = update_search_forms(text, prefix)
        text = update_event_forms(text, prefix)
        text = inject_scripts(text, prefix)
        if path.name == "index.html" and path.parent == SITE:
            text = add_hidden_forms(text, path)
        if text != original:
            path.write_text(text, encoding="utf-8")
            updated += 1
    print(f"Updated {updated} HTML files")
