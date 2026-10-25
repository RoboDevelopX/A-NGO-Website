"""Capture the README screenshots and the social-preview image.

    make screenshots            # or: python -m scripts.screenshots

The script starts its own copy of the site on a free port with a throwaway, freshly seeded
database, so screenshots are reproducible and never touch your local data. It needs the
optional Playwright package (``pip install -r requirements-tools.txt``) and a Chromium
build (``playwright install chromium``, once).

Outputs:
  docs/screenshots/*.png        used by README.md
  static/img/og-image.png       the 1200x630 Open Graph / social card image
"""

from __future__ import annotations

import argparse
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from contextlib import contextmanager
from html import escape
from pathlib import Path

import bcrypt

from app.config import BASE_DIR, BRAND

DESKTOP = {"width": 1280, "height": 800}
MOBILE = {"width": 390, "height": 844}

# (file name, path, viewport, full page?)
PAGES = [
    ("home-desktop", "/", DESKTOP, False),
    ("home-mobile", "/", MOBILE, False),
    ("about", "/about", DESKTOP, False),
    ("donate", "/donate", DESKTOP, False),
    ("events", "/events", DESKTOP, False),
    ("blog-mobile", "/blog", MOBILE, False),
]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def demo_server(workdir: Path, admin_password: str):
    """Seed a temporary database and run uvicorn against it until the block exits."""
    port = _free_port()
    env = {
        **os.environ,
        "APP_ENV": "development",
        "SECRET_KEY": secrets.token_urlsafe(32),
        "SITE_URL": f"http://127.0.0.1:{port}",
        "DATABASE_URL": f"sqlite:///{workdir / 'screenshots.db'}",
        "EMAIL_BACKEND": "memory",
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD_HASH": bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()).decode(),
        "RATE_LIMIT_MAX": "1000",
    }
    subprocess.run([sys.executable, "-m", "app.seed"], env=env, cwd=BASE_DIR, check=True)
    server = subprocess.Popen(  # noqa: S603 - fixed argv, no user input
        [sys.executable, "-m", "uvicorn", "--factory", "app.main:create_app", "--port", str(port)],
        env=env,
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(f"{base_url}/healthz", timeout=1)  # noqa: S310 - local URL
                break
            except OSError:
                time.sleep(0.2)
        else:
            raise RuntimeError("The demo server did not start")
        yield base_url
    finally:
        server.terminate()
        server.wait(timeout=10)


def capture_pages(browser, base_url: str, out: Path) -> None:
    for name, path, viewport, full_page in PAGES:
        page = browser.new_page(viewport=viewport)
        page.goto(base_url + path)
        page.screenshot(path=out / f"{name}.png", full_page=full_page)
        page.close()
        print(f"  {name}.png")


def capture_volunteer_flow(browser, base_url: str, out: Path) -> None:
    """Fill in the volunteer form and capture the matched-events section."""
    page = browser.new_page(viewport=DESKTOP)
    page.goto(base_url + "/volunteer")
    page.click("button[type=submit]")  # empty submit shows the client-side errors
    page.wait_for_timeout(600)  # let the smooth scroll to the first invalid field finish
    page.screenshot(path=out / "volunteer-errors.png")
    page.fill("#f-name", "Kavya Menon")
    page.fill("#f-email", "kavya@example.com")
    page.check("input[value=library]")
    page.check("input[value=events]")
    page.select_option("#f-availability", "weekends")
    page.fill("#f-message", "I run a book club in Udaipur and would love to help on weekends.")
    with page.expect_navigation():
        page.click("button[type=submit]")
    page.locator("section[aria-labelledby=suggested-title]").screenshot(
        path=out / "volunteer-matches.png"
    )
    page.close()
    print("  volunteer-errors.png, volunteer-matches.png")


def capture_related_posts(browser, base_url: str, out: Path) -> None:
    page = browser.new_page(viewport=DESKTOP)
    page.goto(base_url + "/blog")
    first_post = page.locator("main a[href^='/blog/']").first.get_attribute("href")
    page.goto(base_url + first_post)
    page.locator("section[aria-labelledby=related-title]").screenshot(
        path=out / "related-posts.png"
    )
    page.close()
    print("  related-posts.png")


def capture_admin(browser, base_url: str, out: Path, password: str) -> None:
    page = browser.new_page(viewport=DESKTOP)
    # A couple of submissions so the table isn't empty, one of them obvious spam.
    for name, email, message in [
        ("Rohan Gupta", "rohan@example.com", "Our company would like to discuss CSR in 2027."),
        (
            "SEO Expert",
            "seo@example.com",
            "Want your website on the first page of Google? Buy backlinks at the lowest "
            "price. Visit http://rank1-google.info now!",
        ),
    ]:
        page.goto(base_url + "/contact")
        page.fill("#f-name", name)
        page.fill("#f-email", email)
        page.select_option("#f-topic", index=1)
        page.fill("#f-message", message)
        with page.expect_navigation():
            page.click("button[type=submit]")
    page.goto(base_url + "/admin/login")
    page.fill("#f-username", "admin")
    page.fill("#f-password", password)
    with page.expect_navigation():
        page.click("button[type=submit]")
    page.goto(base_url + "/admin?spam=include")
    page.screenshot(path=out / "admin.png", full_page=True)
    page.close()
    print("  admin.png")


def og_image_html() -> str:
    """A self-contained HTML card in the brand colours, rendered at 1200x630."""
    c = BRAND.colors
    logo = (BASE_DIR / "static" / "img" / "logo.svg").read_text(encoding="utf-8")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
      body {{ margin: 0; width: 1200px; height: 630px; display: flex; background: {c.primary};
              font-family: system-ui, sans-serif; color: {c.background}; }}
      .card {{ margin: 48px; flex: 1; border-radius: 32px; background: {c.primary_dark};
               padding: 72px; display: flex; flex-direction: column; justify-content: center;
               position: relative; overflow: hidden; }}
      .logo svg {{ width: 112px; height: 112px; }}
      h1 {{ font: 700 84px/1.05 Georgia, "Iowan Old Style", serif; margin: 36px 0 20px; }}
      p {{ font-size: 38px; margin: 0; color: {c.primary_light}; }}
      .bar {{ position: absolute; left: 0; right: 0; bottom: 0; height: 14px;
              background: {c.accent}; }}
    </style></head><body><div class="card">
      <div class="logo">{logo}</div>
      <h1>{escape(BRAND.name)}</h1>
      <p>{escape(BRAND.tagline)}</p>
      <div class="bar"></div>
    </div></body></html>"""


def capture_og_image(browser, path: Path) -> None:
    page = browser.new_page(viewport={"width": 1200, "height": 630})
    page.set_content(og_image_html())
    page.screenshot(path=path)
    page.close()
    print(f"  {path.relative_to(BASE_DIR)}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--out", type=Path, default=BASE_DIR / "docs" / "screenshots")
    parser.add_argument(
        "--og-image", type=Path, default=BASE_DIR / "static" / "img" / "og-image.png"
    )
    args = parser.parse_args(argv)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright is not installed: pip install -r requirements-tools.txt")

    args.out.mkdir(parents=True, exist_ok=True)
    admin_password = secrets.token_urlsafe(16)
    with (
        tempfile.TemporaryDirectory() as tmp,
        demo_server(Path(tmp), admin_password) as base_url,
        sync_playwright() as playwright,
    ):
        try:
            browser = playwright.chromium.launch()
        except Exception as exc:
            sys.exit(f"Could not start Chromium ({exc}).\nRun once: playwright install chromium")
        print(f"Writing screenshots to {args.out}")
        capture_pages(browser, base_url, args.out)
        capture_volunteer_flow(browser, base_url, args.out)
        capture_related_posts(browser, base_url, args.out)
        capture_admin(browser, base_url, args.out, admin_password)
        capture_og_image(browser, args.og_image)
        browser.close()


if __name__ == "__main__":
    main()
