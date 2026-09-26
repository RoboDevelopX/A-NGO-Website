# NGO Website Template

A reusable, config-driven website for any non-profit, built with Next.js (App Router) and TypeScript.
Rebrand it for a different organisation by editing **one file**: `site.config.ts`.

## Pages

| Route | What it is |
| --- | --- |
| `/` | Homepage: hero with mission and calls to action, impact stats, programmes, upcoming events, latest stories |
| `/about` | Story, vision, values, programmes in detail, team, partners |
| `/donate` | Impact per amount, **mock** checkout (no real payments), other ways to give |
| `/get-involved` | Working volunteer application and general enquiry form (`?type=contact` opens the enquiry tab) |
| `/events`, `/events/[slug]` | Upcoming and past events, detail pages |
| `/blog`, `/blog/[slug]` | Stories and news |
| `/admin` | Staff view of form submissions, protected by `ADMIN_TOKEN` |

## Quick start

```bash
npm install
cp .env.example .env.local   # set ADMIN_TOKEN
npm run dev                  # http://localhost:3000
```

Other scripts: `npm run build`, `npm start`, `npm run typecheck`, `npm test`.

## Adapting it for your NGO

1. Open `site.config.ts` and replace the sample "Brightpath Foundation" content: name, mission, colours,
   fonts, contact details, programmes, team, donation amounts, volunteer roles, events and blog posts.
2. Add photos to `public/images/` and set the `image` fields (e.g. `"/images/hero.jpg"`).
   Any image left empty renders a branded placeholder, so the site never looks broken.
3. Colours in `theme` become CSS variables, so the whole site re-skins from those few values.

No page contains hard-coded organisation content; the types in `lib/types.ts` tell your editor exactly
what each field needs.

## How the forms work

**Volunteer / contact** (`POST /api/contact`)

- One Zod schema (`lib/validation.ts`) validates in the browser for instant feedback and again on the server.
- Volunteer roles and availability options are checked against the lists in `site.config.ts`.
- Spam protection: a hidden honeypot field and a per-IP rate limit (5 submissions per 10 minutes).
- Bodies over 20 KB are rejected; malformed JSON returns 400; invalid fields return 422 with a message per field.
- Valid submissions are saved to `data/submissions.json` (override with `SUBMISSIONS_FILE`). Writes are
  serialised and atomic (temp file + rename), so concurrent submissions are never lost.
- Staff read them at `/admin` or `GET /api/submissions` with `Authorization: Bearer <ADMIN_TOKEN>`.

**Donate** (`POST /api/donate`) is a mock. It validates amount, name and email and returns a fake receipt ID.
Card fields are display-only and never leave the browser. To take real payments, replace that one route
with Stripe Checkout, PayPal, Razorpay or similar.

## Deploying

Any Node host with a writable disk (a VPS, Docker, Render, Railway, `npm start`) works as is.
On serverless hosts with a read-only filesystem (e.g. Vercel), replace `saveSubmission` and
`listSubmissions` in `lib/submissions.ts` with a database call (Postgres, SQLite/Turso, Supabase, etc.);
nothing else changes. The in-memory rate limiter is per-process; use your host's or Redis when scaling out.

## Project layout

```
site.config.ts        ← all organisation content (edit this)
app/                  pages and API routes
components/           UI building blocks and client-side forms
lib/                  types, content helpers, validation, storage, rate limiting, auth
tests/                API tests (Vitest)
```
