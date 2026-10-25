# Contributing

Akshar Foundation: a server-rendered NGO site (FastAPI, Jinja2, SQLAlchemy and SQLite,
hand-written CSS, vanilla JS) with three offline scikit-learn features. The README covers
the full picture; this file holds what you need while changing the code.

## Commands

```bash
make run        # first run: venv, deps, .env (prints admin password once), train model, seed; then serve on :8000
make test       # pytest (unit and integration); must stay green
make lint       # ruff check + ruff format --check; must stay clean
make format     # ruff format + ruff check --fix
make reseed     # wipe the DB and reseed demo content
make train      # regenerate synthetic spam data and retrain; prints metrics and sanity checks
make screenshots  # optional: needs requirements-tools.txt and `playwright install chromium`
```

Run a single test with `.venv/bin/python -m pytest tests/unit/test_schemas.py -k email`.

## Hard rules

- **Payments.** Never integrate a real payment provider, and never collect or store card
  data. The demo card inputs must not have a `name` attribute; a test enforces this.
- **Config and secrets.** No hardcoded secrets. Config comes from environment variables
  via `Settings` in `app/config.py`. Add new settings there and to `.env.example`.
- **Branding.** Name, tagline, colours and contact details live only in `BRAND` in
  `app/config.py`. Templates read `brand.*`, and CSS reads the variables served by
  `/brand.css`. Don't hardcode brand values elsewhere.
- **ML.** It must run offline and be unit-tested. No external ML APIs, no PyTorch, and
  no frontend frameworks.
- **CSP.** The policy is strict. Use no inline `<script>` or `style=""`, and no CDNs.
  Put JS in `static/js/` and styles in `static/css/main.css`.

## Conventions

- **Layers.**
  - `routes/` stay thin: parse the request, call a service, render.
  - Logic goes in `services/`.
  - `app/ml/` has no FastAPI or SQLAlchemy imports.
  - The glue between ML and the database is `app/services/ml.py`.
- **App factory.** Use `create_app(settings)`, never a module-level app. Shared objects
  live on `app.state`: `db`, `email_service`, `payment_provider`, `related_posts`,
  `spam_filter`, `admin_suggestions` and `rate_limiter`.
- **Forms.**
  - Every public POST form includes `{% include "partials/form_security.html" %}`, which
    renders the CSRF token, the one-time nonce and the honeypot. Admin forms carry the
    CSRF token only.
  - Use `Depends(csrf_protected_form)`.
  - Successful posts use Post/Redirect/GET (303).
  - Validation lives in Pydantic models in `schemas.py`. Error copy lives in
    `FIELD_MESSAGES` (server) and `CLIENT_MESSAGES`, which is rendered as `data-msg-*`
    attributes for the JS, so both sides say the same thing.
- **Templates.** Use the macros in `templates/macros/` (`forms.html`, `ui.html`,
  `cards.html`, `icons.html`) rather than repeating markup. Pages set `page_title` and
  `page_description` with top-level `{% set %}`. Render with `app.templating.render(...)`.
- **Data.**
  - Money is integer paise.
  - Datetimes are naive UTC in the database (`app.db.utcnow()`), shown in IST with the
    `ist`, `date` and `datetime` filters.
  - Tags are stored comma-separated; use `split_tags` and `join_tags`.
- **Markdown.** Always render through `app/services/markdown.py`, which sanitises with
  nh3.
- **Accessibility.** Every field gets a label, errors are linked with
  `aria-describedby`, and focus states stay visible. If you change colours, keep
  `tests/unit/test_brand_contrast.py` passing.
- **Style.** Ruff runs with line length 100. Readable over clever. Comment the
  *why* of non-obvious decisions, not the what.

## Tests

- **Fixtures.** `tests/conftest.py` gives each test its own app, a temporary SQLite file
  and an in-memory email backend (`app.state.email_service.sent`). The spam filter is off
  unless a test turns it on.
- **Form helpers.** Use `tests/helpers.py` (`submit`, `form_tokens`, `VALID_VOLUNTEER`,
  `VALID_CONTACT`) to post real forms with valid tokens.
- **What a new page needs:** an integration test that it returns 200, and, if it is
  public, an entry in `sitemap_entries` in `app/routes/seo.py`.
- **What a new ML change needs:** unit tests in `tests/unit/test_ml_*.py`. Keep metric
  assertions as loose floors that catch a broken pipeline, not exact numbers.

## Spam model

`data/spam_model.joblib` is generated and gitignored. If it is missing, the app runs
with spam scoring off. The data is synthetic (`app/ml/spam_data.py`). After changing
features or templates, run `make train` and check two things:

- the grouped cross-validation metrics
- the hand-written sanity checks

If the metrics in the README change, update them.
