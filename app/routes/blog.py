"""Blog: paginated listing with tag filter, and post pages with related posts."""

from __future__ import annotations

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.content import TAG_RE, get_post, paginate_posts, tag_counts
from app.services.markdown import render_markdown
from app.templating import render

router = APIRouter()
DB = Annotated[Session, Depends(get_db)]
PER_PAGE = 5


def _parse_page(raw: str | None) -> int:
    # Parsed by hand so "?page=abc" gives a friendly 404 page, not a JSON validation error.
    if raw is None:
        return 1
    if not raw.isdigit() or int(raw) < 1:
        raise HTTPException(status_code=404)
    return int(raw)


@router.get("/blog")
def blog_list(request: Request, db: DB, page: str | None = None, tag: str | None = None):
    if tag is not None and not TAG_RE.match(tag):
        raise HTTPException(status_code=404)
    page_no = _parse_page(page)
    result = paginate_posts(db, page_no, PER_PAGE, tag)
    if page_no > result.total_pages or (tag and result.total == 0):
        raise HTTPException(status_code=404)

    def url_for_page(n: int) -> str:
        params = {k: v for k, v in {"tag": tag, "page": n if n > 1 else None}.items() if v}
        return "/blog" + (f"?{urlencode(params)}" if params else "")

    return render(
        request,
        "pages/blog.html",
        {
            "result": result,
            "tag": tag,
            "tags": tag_counts(db),
            "url_for_page": url_for_page,
            # Filtered and deep pages are thin duplicates; keep them out of search results.
            "noindex": bool(tag) or page_no > 1,
        },
    )


@router.get("/blog/{slug}")
def blog_detail(request: Request, slug: str, db: DB):
    post = get_post(db, slug)
    if post is None:
        raise HTTPException(status_code=404)
    related = request.app.state.related_posts(db, post)
    return render(
        request,
        "pages/post_detail.html",
        {"post": post, "body_html": render_markdown(post.body), "related": related},
    )
