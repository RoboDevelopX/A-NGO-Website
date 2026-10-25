"""Markdown to safe HTML for posts and events.

Content is seeded by us today, but an admin editor is an obvious next feature, so we treat
Markdown as untrusted: render it, then sanitise the HTML with an allow-list (nh3, a Rust
port of the battle-tested ammonia library). Anything not on the list is stripped.
"""

from __future__ import annotations

from functools import lru_cache

import markdown as md
import nh3
from markupsafe import Markup

ALLOWED_TAGS = {
    "p", "br", "hr", "h2", "h3", "h4", "strong", "em", "code", "pre", "blockquote",
    "ul", "ol", "li", "a", "table", "thead", "tbody", "tr", "th", "td",
}  # fmt: skip
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}, "th": {"align"}, "td": {"align"}}


@lru_cache(maxsize=256)
def render_markdown(text: str) -> Markup:
    html = md.markdown(text, extensions=["tables", "sane_lists"], output_format="html")
    clean = nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer",
    )
    return Markup(clean)  # noqa: S704 - sanitised by nh3 on the line above
