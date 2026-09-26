import { NextResponse } from "next/server";
import { validateSubmission } from "@/lib/validation";
import { saveSubmission } from "@/lib/submissions";
import { clientIp, rateLimit } from "@/lib/rateLimit";

export const runtime = "nodejs";

const MAX_BODY_BYTES = 20_000;

/** Receives both the volunteer and the general contact form. */
export async function POST(request: Request) {
  const ip = clientIp(request.headers);
  const limit = rateLimit(`contact:${ip}`);
  if (!limit.allowed) {
    return NextResponse.json(
      { ok: false, error: "Too many submissions. Please try again later." },
      { status: 429, headers: { "Retry-After": String(limit.retryAfterSeconds) } },
    );
  }

  const raw = await request.text();
  if (raw.length > MAX_BODY_BYTES) {
    return NextResponse.json({ ok: false, error: "Submission is too large." }, { status: 413 });
  }

  let body: unknown;
  try {
    body = JSON.parse(raw);
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid request body." }, { status: 400 });
  }

  // Honeypot filled in: pretend success so bots don't learn anything, but store nothing.
  if (body && typeof body === "object" && "website" in body && (body as { website?: unknown }).website) {
    return NextResponse.json({ ok: true }, { status: 201 });
  }

  const result = validateSubmission(body);
  if (!result.ok) {
    return NextResponse.json(
      { ok: false, error: "Please fix the highlighted fields.", fieldErrors: result.errors },
      { status: 422 },
    );
  }

  try {
    const saved = await saveSubmission(result.data, { ip });
    return NextResponse.json({ ok: true, id: saved.id }, { status: 201 });
  } catch (err) {
    console.error("Failed to save submission", err);
    return NextResponse.json(
      { ok: false, error: "We couldn't save your message. Please email us instead." },
      { status: 500 },
    );
  }
}
